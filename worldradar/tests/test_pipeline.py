"""離線測試：新聞內容為「測試夾具」，只在測試中使用，絕不會出現在正式系統。"""
import datetime as dt, json, pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from worldradar import collect, process, ai, telegram, report, run as runmod, config, db

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 11, 14, 0, 0, tzinfo=UTC)


def rfc(t):
    return t.strftime("%a, %d %b %Y %H:%M:%S GMT")


def rss(items):
    body = "".join(f"<item><title>{t}</title><link>{l}</link><pubDate>{rfc(d)}</pubDate><description>&lt;p&gt;{s}&lt;/p&gt;</description></item>" for t, l, d, s in items)
    return f"<?xml version='1.0'?><rss version='2.0'><channel>{body}</channel></rss>".encode()


H = dt.timedelta(hours=1)
EVENTS = {
    "war": ["Russia launches missile attack on Kyiv energy grid", "Russian missile attack hits Kyiv energy grid overnight", "Missile attack on Kyiv energy grid as Russia presses war"],
    "rates": ["Central bank cuts interest rates as inflation eases in Europe", "European central bank cuts interest rates, inflation eases", "ECB central bank cuts interest rates as inflation eases"],
    "quake": ["Strong earthquake strikes Japan coast, tsunami warning issued", "Japan earthquake triggers tsunami warning along coast", "Earthquake strikes Japan coast with tsunami warning"],
    "taiwan": ["Taiwan chip exports surge as semiconductor demand grows", "Taiwan semiconductor chip exports surge on demand", "Semiconductor chip exports from Taiwan surge amid demand"],
}
SRC_ORDER = ["bbc", "guardian", "dw", "france24"]


def fixture_fetcher(fail=()):
    def f(url, **kw):
        for key, name, u, w in config.FEEDS:
            if u == url:
                if key in fail:
                    raise IOError("boom")
                items = []
                if key in SRC_ORDER:
                    i = SRC_ORDER.index(key)
                    for ev, titles in EVENTS.items():
                        if i < len(titles):
                            items.append((titles[i], f"https://example.test/{key}/{ev}", NOW - H * (i + 1), "Officials said details were still emerging."))
                    items.append(("Old story from two days ago about nothing", f"https://example.test/{key}/old", NOW - H * 50, "old"))
                return rss(items)
        if "gdeltproject" in url:
            return json.dumps({"articles": [{"url": "https://www.reuters.com/x1", "title": "Missile attack on Kyiv energy grid as Russia presses war", "seendate": (NOW - H * 2).strftime("%Y%m%dT%H%M%SZ"), "domain": "reuters.com"}]}).encode()
        raise IOError("unknown url")
    return f


class FakeAI:
    sleep = 0
    def complete(self, system, user):
        if "overview" in system:
            return json.dumps({"overview": "今日總覽測試", "trends": ["趨勢一", "趨勢二", "趨勢三"], "knowledge": [{"term": "NATO", "explain": "北大西洋公約組織"}] * 3,
                               "people_orgs": [{"name": "聯合國", "explain": "x"}] * 3, "terms": [{"term": "通膨", "explain": "x"}] * 3,
                               "think": "思考題", "quiz": [{"q": "q", "options": ["a", "b", "c", "d"], "answer": 1, "explain": "e"}] * 3})
        return "```json\n" + json.dumps({"title_zh": "測試標題", "short": "測試摘要 999", "what": "發生了 999 件事", "background": "背景", "why": "重要", "international": "國際", "taiwan": "台灣影響",
                                          "watch": ["a"], "people": ["某人"], "certainty": [{"claim": "c", "level": "媒體報導"}], "score_reason": "r"}, ensure_ascii=False) + "\n```"


class Tests(unittest.TestCase):
    def test_parse_rss_and_atom(self):
        items = collect.parse_feed(rss([("Hello world", "https://a.test/1", NOW, "desc")]), "bbc", "BBC", 0.9)
        self.assertEqual(items[0]["summary"], "desc")
        atom = b"<feed xmlns='http://www.w3.org/2005/Atom'><entry><title>T</title><link href='https://a.test/2'/><updated>2026-11-13T10:00:00Z</updated><summary>s</summary></entry></feed>"
        self.assertEqual(collect.parse_feed(atom, "x", "X", 0.5)[0]["url"], "https://a.test/2")

    def test_filter_recent(self):
        mk = lambda u, d: {"url": u, "published": d}
        got = process.filter_recent([mk("a", NOW - H), mk("a", NOW - H), mk("b", NOW - H * 30), mk("c", NOW + H * 5)], NOW)
        self.assertEqual([x["url"] for x in got], ["a"])

    def test_cluster_and_select(self):
        f = fixture_fetcher()
        items, st = collect.collect_all(f)
        recent = process.filter_recent(items, NOW)
        clusters = process.cluster(recent)
        self.assertEqual(len(clusters), 4)  # 四個事件被正確合併，舊新聞被排除
        stories = [process.build_story(c, "2026-11-14") for c in clusters]
        top = process.select_top(stories)
        self.assertLessEqual(len(top), 4)  # 不足十則時不硬湊
        self.assertTrue(all(s["source_count"] >= 2 for s in top))
        war = [s for s in stories if "Kyiv" in s["title"]][0]
        self.assertEqual(war["country"], "烏克蘭" if war["country"] == "烏克蘭" else war["country"])
        self.assertGreaterEqual(war["source_count"], 4)  # 含 GDELT 的 reuters.com

    def test_telegram_chunk_lossless(self):
        text = "\n\n".join(("段落%d " % i) + "字" * 900 for i in range(20)) + "\n\n" + "長" * 9000
        parts = telegram.chunk(text)
        self.assertTrue(all(len(p) <= telegram.LIMIT for p in parts))
        joined = "".join(parts).replace("\n", "")
        self.assertEqual(joined.count("字"), 20 * 900)
        self.assertEqual(joined.count("長"), 9000)

    def test_ai_helpers(self):
        self.assertEqual(ai.parse_json('```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(ai.check_consistency({"what": "死亡 1234 人", "short": ""}, "dozens killed"), ["1234"])
        self.assertEqual(ai.check_consistency({"what": "死亡 1234 人", "short": ""}, "1,234 killed"), [])

    def test_full_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            sent = []
            sender = lambda text, tok, chat, btn: sent.append((text, btn)) or len(telegram.chunk(text))
            import os
            os.environ.update(TELEGRAM_BOT_TOKEN="t", TELEGRAM_CHAT_ID="1", SITE_URL="https://x.test/")
            res = runmod.run(now=NOW, fetcher=fixture_fetcher(fail=("cnn", "ft")), provider=FakeAI(), sender=sender,
                             url_checker=lambda u: True, db_path=td / "t.db", docs_dir=td / "docs")
            self.assertEqual(res["status"], "ok")
            data = json.loads((td / "docs/data/latest.json").read_text(encoding="utf-8"))
            self.assertEqual(data["date"], "2026-11-14")
            self.assertGreaterEqual(len(data["stories"]), 3)
            self.assertTrue(data["source_status"]["CNN"]["ok"] is False)  # 單一來源失敗不影響整體
            self.assertTrue(all(src["url"].startswith("https://") for s in data["stories"] for src in s["sources"]))
            self.assertEqual(data["stories"][0]["title_zh"], "測試標題")
            self.assertTrue(data["stories"][0]["ai"]["unverified_numbers"])  # 999 不在來源 → 被標記
            self.assertTrue(any(w["timeline"] for w in data["watch"]))
            self.assertIn("GLOBAL DAILY BRIEFING", sent[0][0])
            self.assertTrue((td / "docs/data/index.json").exists())
            conn = db.connect(td / "t.db")
            self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0], 3)
            self.assertEqual(conn.execute("SELECT status FROM runs").fetchone()[0], "ok")
            # 第二次執行同一天：事件不應重複寫入歷史資料庫
            runmod.run(now=NOW, fetcher=fixture_fetcher(), provider=None, send=False, url_checker=lambda u: True, db_path=td / "t.db", docs_dir=td / "docs")
            self.assertEqual(conn.execute("SELECT COUNT(DISTINCT date) FROM stories").fetchone()[0], 1)

    def test_total_failure_is_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            res = runmod.run(now=NOW, fetcher=lambda u, **k: (_ for _ in ()).throw(IOError("down")), provider=None, send=False,
                             db_path=td / "t.db", docs_dir=td / "docs")
            self.assertEqual(res["status"], "failed")

    def test_telegram_failure_does_not_lose_data(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            def bad(*a, **k): raise RuntimeError("telegram down")
            import os
            os.environ.update(TELEGRAM_BOT_TOKEN="t", TELEGRAM_CHAT_ID="1")
            res = runmod.run(now=NOW, fetcher=fixture_fetcher(), provider=None, sender=bad, url_checker=lambda u: True, db_path=td / "t.db", docs_dir=td / "docs")
            self.assertEqual(res["status"], "telegram_failed")
            self.assertTrue((td / "docs/data/latest.json").exists())


if __name__ == "__main__":
    unittest.main()

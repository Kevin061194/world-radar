"""每日主流程。用法：python -m worldradar.run [--no-ai] [--no-telegram]"""
import argparse, datetime as dt, json, logging, re, sys
from . import config, collect, process, db, ai, report, telegram
from .http import fetch, check_url

log = logging.getLogger("worldradar")
UTC = dt.timezone.utc
TW = dt.timezone(dt.timedelta(hours=8))


def setup_logging(date_str):
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    log.setLevel(logging.INFO)
    for h in list(log.handlers):
        log.removeHandler(h)
        h.close()
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(config.LOG_DIR / f"run-{date_str}.log", encoding="utf-8")):
        h.setFormatter(fmt)
        log.addHandler(h)


def public(s):
    return {k: v for k, v in s.items() if k != "_text"}


def build_watch(conn, clusters_all, top, date):
    out = []
    for t in config.WATCH_TOPICS:
        rx = re.compile(t["regex"])
        hits = [s for s in clusters_all if rx.search(s["_text"]) and s["score"] >= 4]
        hits.sort(key=lambda s: (-s["score"], -s["source_count"]))
        for s in hits[:3]:
            db.save_watch(conn, t["key"], date, s["title"], s["sources"][0]["url"], s["score"])
        tl = db.watch_timeline(conn, t["key"])
        analyzed = [s for s in top if rx.search(s["_text"]) and s.get("ai")]
        people = sorted({p for s in analyzed for p in s["ai"].get("people", []) if isinstance(p, str)})[:8]
        today = [x for x in tl if x["date"] == date]
        out.append({"key": t["key"], "name": t["name"], "first_seen": db.watch_first_seen(conn, t["key"]),
                    "latest": tl[0] if tl else None, "status": "今日有新進展" if today else "今日無新的重大報導",
                    "countries": t["countries"], "people": people, "timeline": tl,
                    "sources": (hits[0]["sources"][:3] if hits else [])})
    return out


def run(now=None, use_ai=True, send=True, fetcher=fetch, provider="env", sender=telegram.send,
        url_checker=check_url, db_path=None, docs_dir=None):
    now = now or dt.datetime.now(UTC)
    date = now.astimezone(TW).strftime("%Y-%m-%d")
    setup_logging(date)
    docs_dir = docs_dir or config.DOCS
    conn = db.connect(db_path or config.DB_PATH)
    detail = {"date": date}
    log.info("=== WORLD RADAR %s 開始 ===", date)

    # STEP 1-2 蒐集與篩選
    items, source_status = collect.collect_all(fetcher)
    detail["sources"] = source_status
    ok_sources = sum(1 for v in source_status.values() if v["ok"])
    log.info("蒐集完成：%s 篇，來源成功 %s/%s", len(items), ok_sources, len(source_status))
    recent = process.filter_recent(items, now)
    if not recent:
        detail["error"] = "沒有取得任何 24 小時內的新聞（可能是網路或來源全部失敗）"
        db.save_run(conn, now.isoformat(), "failed", detail)
        log.error(detail["error"])
        return {"status": "failed", "detail": detail}
    db.save_articles(conn, recent, now.isoformat())

    # STEP 3-5 去重合併、評分、選出十大
    clusters = process.cluster(recent)
    stories_all = [process.build_story(c, date) for c in clusters]
    top = process.select_top(stories_all)
    top_ids = {s["id"] for s in top}
    rest = sorted((s for s in stories_all if s["id"] not in top_ids), key=lambda s: -s["score"])
    extra = [{"title": s["title"], "source": s["sources"][0]["name"], "url": s["sources"][0]["url"], "category": s["category"],
              "region": s["region"], "country": s["country"], "score": s["score"]} for s in rest[:60]]
    note = ""
    if len(top) < 10:
        note = f"今日符合重大新聞標準的事件只有 {len(top)} 則，系統不會用不重要的新聞湊數。"
    log.info("事件 %s 件，選出 %s 則", len(stories_all), len(top))

    # 來源網址有效性檢查
    for s in top:
        for src in s["sources"]:
            src["url_ok"] = bool(url_checker(src["url"]))
        if not any(x["url_ok"] for x in s["sources"]):
            log.warning("所有來源網址皆無法開啟：%s", s["title"][:60])

    # STEP 6 AI 分析
    prov = ai.Provider.from_env() if provider == "env" else provider
    digest = None
    if use_ai and prov and top:
        ai.analyze_all(prov, top)
        digest = ai.make_digest(prov, top, [x["title"] for x in extra])
        detail["ai"] = {"analyzed": sum(1 for s in top if s.get("ai")), "total": len(top), "digest": bool(digest)}
    else:
        log.warning("未啟用 AI（沒有 AI_API_KEY 或使用 --no-ai），新聞將以原文呈現")
        detail["ai"] = {"analyzed": 0, "total": len(top), "digest": False}

    # STEP 7 資料庫
    db.save_stories(conn, date, [public(s) for s in top])
    if digest:
        db.save_digest(conn, date, digest)
    watch = build_watch(conn, stories_all, top, date)

    # STEP 8 網站資料
    payload = {"date": date, "generated_at": now.astimezone(TW).isoformat(), "stories": [public(s) for s in top], "extra": extra,
               "digest": digest, "watch": watch, "shortfall_note": note, "ai_enabled": bool(digest),
               "source_status": source_status, "stats": {"articles": len(recent), "events": len(stories_all), "sources_ok": ok_sources, "sources_total": len(source_status)},
               "links": {"site": config.env("SITE_URL"), "actions": config.env("ACTIONS_URL")}}
    d = docs_dir / "data"
    d.mkdir(parents=True, exist_ok=True)
    for name in ("latest.json", f"{date}.json"):
        (d / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    idx = []
    for dd in db.list_dates(conn):
        rows = conn.execute("SELECT data FROM stories WHERE date=? ORDER BY rank LIMIT 3", (dd,)).fetchall()
        idx.append({"date": dd, "headlines": [json.loads(r["data"]).get("title_zh") or json.loads(r["data"])["title"] for r in rows]})
    (d / "index.json").write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")

    # STEP 9-10 簡報與推播
    text = report.briefing(date, payload["stories"], digest, note)
    (d / "latest-briefing.html.txt").write_text(text, encoding="utf-8")
    status = "ok"
    token, chat = config.env("TELEGRAM_BOT_TOKEN"), config.env("TELEGRAM_CHAT_ID")
    if send and token and chat:
        try:
            detail["telegram_messages"] = sender(text, token, chat, telegram.buttons_from_env())
            log.info("Telegram 已傳送 %s 則", detail["telegram_messages"])
        except Exception as e:  # noqa
            status = "telegram_failed"
            detail["telegram_error"] = str(e)[:300]
            log.error("Telegram 推播失敗：%s", e)
    else:
        log.info("略過 Telegram（未設定或使用 --no-telegram）")

    # STEP 11 執行紀錄
    db.save_run(conn, now.isoformat(), status, detail)
    log.info("=== 完成，狀態：%s ===", status)
    return {"status": status, "detail": detail, "top": top}


if __name__ == "__main__":
    config.load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ai", action="store_true")
    ap.add_argument("--no-telegram", action="store_true")
    a = ap.parse_args()
    res = run(use_ai=not a.no_ai, send=not a.no_telegram)
    sys.exit(0 if res["status"] == "ok" else 1)

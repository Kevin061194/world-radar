import re, hashlib, datetime as dt
from . import config

STOP = set("the and for with from that this have has had are was were will would says said after over into about amid more than new its his her their who what when where why how not but you your can could may might out off all one two".split())
CAT_RE = [(c, re.compile(r"\b(?:%s)\b" % p)) for c, p in config.CATEGORY_KEYWORDS]
IMPACT_RE = [(re.compile(p), w) for p, w in config.IMPACT_KEYWORDS]
COUNTRY_RE = [(re.compile(p), v) for p, v in config.COUNTRIES.items()]


def tokens(title):
    return {w for w in re.findall(r"[a-z0-9]{3,}", title.lower()) if w not in STOP}


def similar(a, b):
    if not a or not b:
        return False
    inter = len(a & b)
    return inter / len(a | b) >= 0.4 or (inter >= 4 and inter / min(len(a), len(b)) >= 0.6)


def filter_recent(items, now, hours=24):
    """只保留過去 24 小時內、發布時間不在未來的文章，並以網址去重。"""
    seen, out = set(), []
    for it in items:
        age = now - it["published"]
        if dt.timedelta(minutes=-10) <= age <= dt.timedelta(hours=hours) and it["url"] not in seen:
            seen.add(it["url"])
            out.append(it)
    return out


def cluster(items):
    """把報導同一事件的文章合併。"""
    groups = []
    for it in sorted(items, key=lambda x: x["published"], reverse=True):
        tk = tokens(it["title"])
        for g in groups:
            if similar(tk, g["tokens"]):
                g["items"].append(it)
                break
        else:
            groups.append({"tokens": tk, "items": [it]})
    return [g["items"] for g in groups]


def classify_category(text):
    best, best_n = "國際政治與外交", 0
    for cat, rx in CAT_RE:
        n = len(rx.findall(text))
        if n > best_n:
            best, best_n = cat, n
    return best


def detect_country(text):
    hits = {}
    for rx, v in COUNTRY_RE:
        n = len(rx.findall(text))
        if n:
            hits[v] = n
    if not hits:
        return ("全球", "全球性事件", 0.0, 0.0)
    return max(hits, key=hits.get)


def score_cluster(articles):
    text = " ".join(a["title"] + " " + a["summary"] for a in articles).lower()
    by_src = {}
    for a in articles:
        by_src.setdefault(a["source_key"], a)
    n = len(by_src)
    kw = min(3.0, sum(w for rx, w in IMPACT_RE if rx.search(text)))
    cred = sum(a["weight"] for a in by_src.values())
    raw = 1.0 + 1.3 * min(n, 4) + kw + (0.5 if cred >= 2.5 else 0)
    return max(1, min(10, round(raw))), n, text


def build_story(articles, date_str):
    score, n, text = score_cluster(articles)
    lead = max(articles, key=lambda a: (a["weight"], len(a["summary"])))
    country, region, lat, lon = detect_country(lead["title"].lower() + " " + text)
    srcs, seen = [], set()
    for a in sorted(articles, key=lambda a: -a["weight"]):
        if a["source_key"] in seen:
            continue
        seen.add(a["source_key"])
        srcs.append({"name": a["source"], "url": a["url"], "title": a["title"], "published": a["published"].isoformat()})
    return {
        "id": hashlib.sha1((date_str + lead["title"]).encode()).hexdigest()[:8],
        "title": lead["title"], "summary_en": lead["summary"], "country": country, "region": region,
        "lat": lat, "lon": lon, "category": classify_category(text), "score": score, "source_count": n,
        "verification": "多來源報導（已交叉比對）" if n >= 2 else "單一來源（尚未交叉驗證）",
        "sources": srcs[:6], "published": max(a["published"] for a in articles).isoformat(),
        "_text": text,
    }


def select_top(stories, n=10, region_cap=4):
    """門檻：多來源且分數>=5，或單一來源但分數>=7。不足 n 則不硬湊。"""
    ok = [s for s in stories if (s["source_count"] >= 2 and s["score"] >= 5) or s["score"] >= 7]
    ok.sort(key=lambda s: (-s["score"], -s["source_count"]))
    top, counts = [], {}
    for s in ok:
        if len(top) >= n:
            break
        if counts.get(s["region"], 0) >= region_cap:
            continue
        counts[s["region"]] = counts.get(s["region"], 0) + 1
        top.append(s)
    for s in ok:  # 因地區上限而不足時，補回高分者
        if len(top) >= n:
            break
        if s not in top:
            top.append(s)
    top.sort(key=lambda s: (-s["score"], -s["source_count"]))
    for i, s in enumerate(top, 1):
        s["rank"] = i
    return top

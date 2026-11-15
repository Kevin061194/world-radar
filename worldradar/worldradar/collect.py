import json, logging, re, html, email.utils, datetime as dt
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from . import config

log = logging.getLogger("worldradar")
UTC = dt.timezone.utc


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def _clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except Exception:  # noqa
        d = None
    if d is None:
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:  # noqa
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC)


def parse_feed(xml_bytes, key, name, weight):
    """解析 RSS 2.0 / RSS 1.0 / Atom，回傳文章列表。"""
    root = ET.fromstring(xml_bytes)
    items = []
    for el in root.iter():
        if _local(el.tag) not in ("item", "entry"):
            continue
        f = {"title": "", "link": "", "date": "", "desc": "", "src": ""}
        for c in el:
            t = _local(c.tag)
            if t == "title":
                f["title"] = _clean(c.text)
            elif t == "link":
                f["link"] = (c.get("href") or c.text or "").strip() or f["link"]
            elif t in ("pubdate", "published", "updated", "date"):
                f["date"] = f["date"] or (c.text or "")
            elif t in ("description", "summary", "content", "encoded"):
                f["desc"] = f["desc"] or _clean(c.text)
            elif t == "source":
                f["src"] = _clean(c.text)
        pub = parse_date(f["date"])
        if not f["title"] or not f["link"] or pub is None:
            continue
        if f["src"] and key in ("reuters", "ap"):  # Google News 標題尾端會附「 - Reuters」
            f["title"] = re.sub(r"\s+-\s+" + re.escape(f["src"]) + r"$", "", f["title"])
        items.append({"title": f["title"], "url": f["link"], "source": name, "source_key": key,
                      "published": pub, "summary": f["desc"][:600], "weight": weight})
    return items


def parse_gdelt(raw):
    data = json.loads(raw)
    out = []
    for a in data.get("articles", []):
        domain = (a.get("domain") or urlparse(a.get("url", "")).netloc).lower().replace("www.", "")
        try:
            pub = dt.datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        except Exception:  # noqa
            continue
        if not a.get("title") or not a.get("url"):
            continue
        out.append({"title": _clean(a["title"]), "url": a["url"], "source": domain, "source_key": domain,
                    "published": pub, "summary": "", "weight": config.DOMAIN_WEIGHTS.get(domain, config.DEFAULT_GDELT_WEIGHT)})
    return out


def collect_all(fetcher):
    """逐一蒐集所有來源；單一來源失敗只記錄，不中斷整體。回傳 (items, 各來源狀態)。"""
    items, status = [], {}
    for key, name, url, weight in config.FEEDS:
        try:
            got = parse_feed(fetcher(url), key, name, weight)
            items += got
            status[name] = {"ok": True, "count": len(got)}
        except Exception as e:  # noqa
            log.error("來源失敗 %s: %s", name, e)
            status[name] = {"ok": False, "error": str(e)[:200]}
    try:
        got = parse_gdelt(fetcher(config.GDELT_URL))
        items += got
        status["GDELT"] = {"ok": True, "count": len(got)}
    except Exception as e:  # noqa
        log.error("來源失敗 GDELT: %s", e)
        status["GDELT"] = {"ok": False, "error": str(e)[:200]}
    return items, status

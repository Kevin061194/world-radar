"""抓取新聞文章全文（只用標準庫）。付費牆或擋機器人的網站會抓不到，抓不到就回傳空字串。"""
import re
from html.parser import HTMLParser

SKIP = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"}


class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip, self.in_p, self.buf, self.out = 0, False, [], []

    def handle_starttag(self, t, a):
        if t in SKIP:
            self.skip += 1
        if t == "p" and not self.skip:
            self.in_p, self.buf = True, []

    def handle_endtag(self, t):
        if t in SKIP and self.skip:
            self.skip -= 1
        if t == "p" and self.in_p:
            self.in_p = False
            x = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if len(x) >= 60:
                self.out.append(x)

    def handle_data(self, d):
        if self.in_p and not self.skip:
            self.buf.append(d)


def extract_text(raw, limit=5000):
    txt = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else raw
    p = _P()
    try:
        p.feed(txt)
    except Exception:  # noqa
        pass
    return " ".join(p.out)[:limit]


def get_fulltext(fetcher, url):
    if "news.google.com" in url:  # Google News 轉址連結無法直接取得原文
        return ""
    try:
        t = extract_text(fetcher(url, timeout=12, retries=1))
        return t if len(t) >= 200 else ""
    except Exception:  # noqa
        return ""

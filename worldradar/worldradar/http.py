import logging, time, urllib.request, urllib.error

log = logging.getLogger("worldradar")
UA = "Mozilla/5.0 (compatible; WorldRadar/1.0; personal news research)"


def fetch(url, timeout=20, retries=3, headers=None, data=None, method=None):
    """下載網址內容（bytes）。網路錯誤時自動重試，間隔 1、2 秒。"""
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})}, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa
            last = e
            log.warning("fetch 失敗 (%s/%s) %s: %s", i + 1, retries, url[:90], e)
            if i < retries - 1:
                time.sleep(2 ** i)
    raise last


def check_url(url, timeout=10):
    """檢查網址是否可開啟。Google News 轉址連結無法驗證，視為有效。"""
    if "news.google.com" in url:
        return True
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status < 400
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):  # 網站擋機器人，但網址存在
                return True
            if method == "HEAD" and e.code in (405, 501):
                continue
            return False
        except Exception:  # noqa
            if method == "HEAD":
                continue
            return False
    return False

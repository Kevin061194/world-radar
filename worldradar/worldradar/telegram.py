import html, json, logging, sys, time, urllib.parse
from . import config
from .http import fetch

log = logging.getLogger("worldradar")
LIMIT = 3800  # Telegram 單則上限 4096 字，保留餘裕


def chunk(text, limit=LIMIT):
    """依空行切段；單段過長再依換行、最後硬切。保證不遺失任何內容。"""
    out, cur = [], ""
    for block in text.split("\n\n"):
        pieces = [block]
        if len(block) > limit:
            pieces, buf = [], ""
            for line in block.split("\n"):
                while len(line) > limit:
                    if buf:
                        pieces.append(buf); buf = ""
                    pieces.append(line[:limit]); line = line[limit:]
                if len(buf) + len(line) + 1 > limit:
                    pieces.append(buf); buf = line
                else:
                    buf = (buf + "\n" + line) if buf else line
            if buf:
                pieces.append(buf)
        for p in pieces:
            if len(cur) + len(p) + 2 > limit and cur:
                out.append(cur); cur = p
            else:
                cur = (cur + "\n\n" + p) if cur else p
    if cur:
        out.append(cur)
    return out


def send(text, token, chat_id, buttons=None, fetcher=fetch):
    """傳送長訊息（HTML 格式）。回傳傳送的則數；失敗會丟出例外。"""
    parts = chunk(text)
    for i, part in enumerate(parts):
        form = {"chat_id": chat_id, "text": part, "parse_mode": "HTML", "disable_web_page_preview": "true"}
        if buttons and i == len(parts) - 1:
            form["reply_markup"] = json.dumps({"inline_keyboard": [buttons]})
        raw = fetcher(f"https://api.telegram.org/bot{token}/sendMessage",
                      data=urllib.parse.urlencode(form).encode(), method="POST")
        if not json.loads(raw).get("ok"):
            raise RuntimeError("Telegram 回應失敗：" + raw.decode("utf-8", "ignore")[:200])
        time.sleep(0.5)
    return len(parts)


def buttons_from_env():
    site, actions = config.env("SITE_URL"), config.env("ACTIONS_URL")
    b = []
    if site.startswith("http"):
        b += [{"text": "開啟完整網站", "url": site}, {"text": "重新整理", "url": site + ("&" if "?" in site else "?") + "r=1"}]
    if actions.startswith("http"):
        b.append({"text": "立即更新新聞", "url": actions})
    return b


esc = html.escape

if __name__ == "__main__":  # python -m worldradar.telegram test|chatid
    config.load_dotenv()
    token = config.env("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit("請先在 .env 填入 TELEGRAM_BOT_TOKEN")
    if len(sys.argv) > 1 and sys.argv[1] == "chatid":
        data = json.loads(fetch(f"https://api.telegram.org/bot{token}/getUpdates"))
        ids = {(m["message"]["chat"]["id"], m["message"]["chat"].get("first_name", "")) for m in data.get("result", []) if "message" in m}
        print(ids or "沒有找到訊息：請先在 Telegram 對你的機器人傳送任何一句話，再重新執行。")
    else:
        n = send("WORLD RADAR 測試訊息：看到這則代表 Telegram 設定成功。", token, config.env("TELEGRAM_CHAT_ID"), buttons_from_env())
        print("已送出", n, "則")

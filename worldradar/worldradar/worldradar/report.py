from .telegram import esc


def briefing(date, stories, digest, shortfall_note=""):
    """產生 Telegram 每日簡報（HTML）。"""
    d = date.replace("-", "/")
    out = [f"<b>WORLD RADAR</b>\n<b>GLOBAL DAILY BRIEFING</b>\n\n日期：{d}"]
    if shortfall_note:
        out.append(esc(shortfall_note))
    out.append("<b>一、今日全球局勢總覽</b>\n" + esc((digest or {}).get("overview") or "（今日未啟用 AI，僅提供程式篩選的原始新聞清單。）"))
    out.append("<b>二、全球十大重要新聞</b>")
    for s in stories:
        a = s.get("ai") or {}
        title = a.get("title_zh") or s.get("title_zh") or s["title"]
        link = s["sources"][0]["url"] if s["sources"] else ""
        extra = "\n".join(f'<a href="{esc(x["url"])}">{esc(x["name"])}</a>' for x in s["sources"][1:3])
        block = [f"<b>{s['rank']}. {esc(title)}</b>",
                 f"國家：{esc(s['country'])}｜重要性：{s['score']}/10｜{esc(s['verification'])}",
                 "摘要：" + esc(a.get("short") or s.get("gist") or ("（未翻譯）" + s["title"]))]
        if a.get("why"):
            block.append("為什麼重要：" + esc(a["why"]))
        if a.get("taiwan"):
            block.append("對台灣的影響：" + esc(a["taiwan"]))
        if a.get("unverified_numbers"):
            block.append("⚠️ 摘要中的數字 " + esc("、".join(a["unverified_numbers"])) + " 未在來源摘要出現，請以原文為準")
        block.append(f'<a href="{esc(link)}">原始新聞</a>' + ("｜" + extra.replace("\n", "｜") if extra else ""))
        out.append("\n".join(block))
    if digest:
        out.append("<b>三、今日最值得注意的三個國際趨勢</b>\n" + "\n".join(f"{i}. {esc(t)}" for i, t in enumerate(digest.get("trends", [])[:3], 1)))
        k = (digest.get("knowledge") or [{}])[0]
        if k.get("term"):
            out.append(f"<b>四、今日國際知識</b>\n<b>{esc(k['term'])}</b>：{esc(k.get('explain', ''))}")
        if digest.get("think"):
            out.append("<b>五、今日值得思考的問題</b>\n" + esc(digest["think"]))
    return "\n\n".join(out)

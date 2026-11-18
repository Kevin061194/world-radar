import json, logging, re, time, urllib.request, urllib.error
from . import config
from .http import UA

log = logging.getLogger("worldradar")
ERRORS = []  # 本次執行的 AI 錯誤（會顯示在網站上，方便查原因）


def note(e):
    ERRORS.append(str(e)[:300])


def _post(url, body, headers, waits=(15, 30, 60)):
    """POST 到 AI 服務。遇到 429（太快）或伺服器忙碌時，等待後自動重試。"""
    last = None
    for i in range(len(waits) + 1):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"User-Agent": UA, **headers}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:250]}")
            if e.code in (429, 500, 502, 503, 504) and i < len(waits):
                log.warning("AI 暫時失敗 HTTP %s，%s 秒後重試", e.code, waits[i])
                time.sleep(waits[i])
                continue
            raise last
        except Exception as e:  # noqa
            last = e
            if i < len(waits):
                time.sleep(waits[i])
                continue
            raise
    raise last


class Provider:
    """可替換的 AI 提供者：kind = 'openai'（任何 OpenAI 相容 API）或 'gemini'。"""

    def __init__(self, kind, key, model, base_url="https://api.openai.com/v1", sleep=7.0):
        self.kind, self.key, self.model, self.base, self.sleep = kind, key, model, base_url.rstrip("/"), sleep

    @classmethod
    def from_env(cls):
        key = config.env("AI_API_KEY")
        if not key:
            return None
        kind = config.env("AI_PROVIDER", "gemini").lower()
        default_model = "gemini-2.5-flash" if kind == "gemini" else "gpt-4o-mini"
        return cls(kind, key, config.env("AI_MODEL", default_model), config.env("AI_BASE_URL", "https://api.openai.com/v1"))

    def complete(self, system, user):
        if self.kind == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            body = {"systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
            raw = _post(url, body, {"Content-Type": "application/json", "x-goog-api-key": self.key})
            return json.loads(raw)["candidates"][0]["content"]["parts"][0]["text"]
        body = {"model": self.model, "temperature": 0.2,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if config.env("AI_JSON_MODE", "1") == "1":
            body["response_format"] = {"type": "json_object"}
        raw = _post(self.base + "/chat/completions", body, {"Content-Type": "application/json", "Authorization": "Bearer " + self.key})
        return json.loads(raw)["choices"][0]["message"]["content"]


def parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < 0:
        raise ValueError("AI 回應中找不到 JSON")
    return json.loads(text[a:b + 1])


SYS_STORY = """你是資深國際新聞研究員。只能根據使用者提供的新聞來源內容撰寫，一律使用繁體中文（台灣用語）。
規則：
1. 事實（人名、數字、日期、引述）只能來自提供的來源內容，不可捏造；來源沒寫的就不要寫。
2. 「background」可使用一般常識，但不得包含來源沒有的具體數字或日期；
3. 區分資訊等級：已確認事實、媒體報導、官方說法、未證實。推測必須明說是推測。
4. 只輸出 JSON，欄位：
title_zh(字串), short(60字內摘要), what(發生了什麼事，要寫得完整詳細，至少 200 字，交代人、事、時、地、數字與各方說法), background(事件背景), why(為什麼重要),
international(國際影響), taiwan(對台灣的影響，涉及外交/經濟/科技/能源/安全，若關聯有限就如實說明), 
watch(字串陣列，接下來觀察什麼), people(陣列，來源中提到的重要人物或組織), 
certainty(陣列，每項 {"claim":字串,"level":"已確認事實|媒體報導|官方說法|未證實"}), 
score_reason(說明為何是這個重要性分數，需對照：全球政治、國際經濟、國家安全、科技產業、國際社會、緊急程度、連鎖影響)"""

SYS_DIGEST = """你是國際情報分析師，一律使用繁體中文（台灣用語），只能根據提供的今日新聞標題與摘要，不可捏造。只輸出 JSON，欄位：
overview(今日全球局勢總覽，150~250字), trends(3 個字串，今日最值得注意的國際趨勢),
knowledge(3 個 {"term":..,"explain":..}，國際知識，需詳細說明是什麼、為什麼重要、與台灣的關係),
people_orgs(3 個 {"name":..,"explain":..}), terms(3 個 {"term":..,"explain":..} 專業詞彙),
think(一個值得思考的國際議題，字串),
quiz(3 題 {"q":..,"options":[4 個字串],"answer":0~3 的整數,"explain":..}，必須根據今日新聞與上述知識)"""


def _story_prompt(s):
    parts = [f"事件標題（英文）：{s['title']}", f"程式判定：{s['country']}／{s['category']}／重要性 {s['score']}/10／{s['verification']}", "來源內容："]
    for src in s["sources"]:
        parts.append(f"- [{src['name']}] {src['title']} ({src['published']}) {src['url']}")
    if s.get("summary_en"):
        parts.append("摘要原文：" + s["summary_en"])
    if s.get("_full"):
        parts.append("文章全文節錄（請以此為主要依據）：\n" + s["_full"][:5000])
    return "\n".join(parts)


def check_consistency(analysis, source_text):
    """一致性檢查：AI 寫出的數字若未出現在來源中，標記為需人工查證。"""
    nums = set(re.findall(r"\d[\d,\.]*\d|\d", analysis.get("what", "") + analysis.get("short", "")))
    src = source_text.replace(",", "")
    bad = sorted(n for n in nums if n.replace(",", "") not in src and len(n) >= 2)
    return bad


def analyze_story(provider, s):
    for attempt in range(2):
        try:
            out = parse_json(provider.complete(SYS_STORY, _story_prompt(s)))
            for k in ("title_zh", "short", "what", "why", "taiwan"):
                if not out.get(k):
                    raise ValueError("缺少欄位 " + k)
            out["unverified_numbers"] = check_consistency(out, s["_text"] + " " + s["title"] + " " + s.get("_full", ""))
            return out
        except Exception as e:  # noqa
            log.error("AI 分析失敗 (%s) %s: %s", attempt + 1, s["title"][:60], e)
            note(e)
            time.sleep(provider.sleep)
    return None


def make_digest(provider, stories, extra_titles):
    lines = [f"{s['rank']}. [{s['country']}/{s['category']}] {s.get('title_zh') or s['title']} - {s.get('short') or s['summary_en'][:150]}" for s in stories]
    prompt = "今日十大新聞：\n" + "\n".join(lines) + "\n\n其他今日標題：\n" + "\n".join(extra_titles[:15])
    for attempt in range(2):
        try:
            return parse_json(provider.complete(SYS_DIGEST, prompt))
        except Exception as e:  # noqa
            log.error("AI 摘要失敗 (%s): %s", attempt + 1, e)
            note(e)
            time.sleep(provider.sleep)
    return None


def analyze_all(provider, stories):
    for s in stories:
        out = analyze_story(provider, s)
        s["ai"] = out
        if out:
            s["title_zh"] = out["title_zh"]
        time.sleep(provider.sleep)


SYS_TR = """你是新聞編輯。把英文新聞標題翻成繁體中文（台灣用語），並用一句話說明重點（只能依標題與摘要，不可補充沒有的資訊）。
只輸出 JSON：{"items":[{"i":編號,"zh":"繁體中文標題","gist":"一句話重點"}]}"""


def translate_headlines(provider, rows):
    """rows = [(英文標題, 英文摘要)]，回傳 {編號: (中文標題, 一句話重點)}。每 30 則一次呼叫。"""
    out = {}
    for st in range(0, len(rows), 30):
        prompt = "\n".join(f"{st + i}. {t} || {s[:200]}" for i, (t, s) in enumerate(rows[st:st + 30]))
        for attempt in range(2):
            try:
                for it in parse_json(provider.complete(SYS_TR, prompt)).get("items", []):
                    if isinstance(it.get("i"), int) and it.get("zh"):
                        out[it["i"]] = (it["zh"], it.get("gist", ""))
                break
            except Exception as e:  # noqa
                log.error("標題翻譯失敗 (%s): %s", attempt + 1, e)
                note(e)
                time.sleep(provider.sleep)
        time.sleep(provider.sleep)
    return out

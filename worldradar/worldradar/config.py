import os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
DB_PATH = DATA / "worldradar.db"
LOG_DIR = DATA / "logs"


def load_dotenv():
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def env(key, default=""):
    return os.environ.get(key, default).strip()


# (key, 顯示名稱, RSS 網址, 可信度權重)
# Reuters / AP 已不提供官方 RSS，改用 Google News 的站內搜尋 RSS。
FEEDS = [
    ("reuters", "Reuters", "https://news.google.com/rss/search?q=site:reuters.com+when:1d&hl=en-US&gl=US&ceid=US:en", 1.0),
    ("ap", "AP", "https://news.google.com/rss/search?q=site:apnews.com+when:1d&hl=en-US&gl=US&ceid=US:en", 1.0),
    ("bbc", "BBC", "https://feeds.bbci.co.uk/news/world/rss.xml", 0.95),
    ("ft", "Financial Times", "https://www.ft.com/world?format=rss", 0.95),
    ("guardian", "The Guardian", "https://www.theguardian.com/world/rss", 0.9),
    ("dw", "DW", "https://rss.dw.com/rdf/rss-en-all", 0.9),
    ("france24", "France 24", "https://www.france24.com/en/rss", 0.9),
    ("nhk", "NHK WORLD", "https://www3.nhk.or.jp/nhkworld/en/news/feeds/", 0.9),
    ("nikkei", "Nikkei Asia", "https://asia.nikkei.com/rss/feed/nar", 0.9),
    ("aljazeera", "Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", 0.85),
    ("cna", "CNA (Channel NewsAsia)", "https://www.channelnewsasia.com/rssfeeds/8395986", 0.85),
    ("cnbc", "CNBC", "https://www.cnbc.com/id/100727362/device/rss/rss.html", 0.85),
    ("cnn", "CNN", "http://rss.cnn.com/rss/edition_world.rss", 0.8),
]

GDELT_URL = ("https://api.gdeltproject.org/api/v2/doc/doc?query="
             "(war%20OR%20election%20OR%20economy%20OR%20sanctions%20OR%20earthquake%20OR%20tariff%20OR%20chip)"
             "%20sourcelang:english&mode=artlist&maxrecords=100&format=json&timespan=24h&sort=hybridrel")

DOMAIN_WEIGHTS = {"reuters.com": 1.0, "apnews.com": 1.0, "bbc.com": 0.95, "bbc.co.uk": 0.95, "ft.com": 0.95,
                  "theguardian.com": 0.9, "dw.com": 0.9, "france24.com": 0.9, "aljazeera.com": 0.85,
                  "nhk.or.jp": 0.9, "asia.nikkei.com": 0.9, "cnbc.com": 0.85, "cnn.com": 0.8,
                  "channelnewsasia.com": 0.85, "bloomberg.com": 0.95, "nytimes.com": 0.9, "wsj.com": 0.9,
                  "washingtonpost.com": 0.9, "economist.com": 0.9, "politico.com": 0.85, "axios.com": 0.8, "npr.org": 0.85,
                  "scmp.com": 0.8, "japantimes.co.jp": 0.85, "straitstimes.com": 0.85, "abc.net.au": 0.85, "cbc.ca": 0.85,
                  "nikkei.com": 0.9, "focustaiwan.tw": 0.85, "taipeitimes.com": 0.8, "koreaherald.com": 0.8,
                  "techcrunch.com": 0.75, "theverge.com": 0.75, "cnbc.com": 0.85, "aljazeera.com": 0.85}
DEFAULT_GDELT_WEIGHT = 0.6

CATEGORIES = ["國際政治與外交", "戰爭與軍事安全", "全球經濟與金融", "國際貿易與產業", "科技與人工智慧",
              "能源與氣候", "自然災害與公共安全", "醫療與公共衛生", "社會與文化", "科學與重大發現"]
REGIONS = ["北美洲", "南美洲", "歐洲", "東亞", "東南亞", "南亞", "中東", "非洲", "大洋洲", "全球性事件"]

# 關鍵字 -> (中文國名, 地區, 緯度, 經度)
COUNTRIES = {
    r"united states|u\.s\.|washington|white house|pentagon|trump|congress": ("美國", "北美洲", 38.9, -77.0),
    r"canada|canadian|ottawa": ("加拿大", "北美洲", 45.4, -75.7),
    r"mexico|mexican": ("墨西哥", "北美洲", 19.4, -99.1),
    r"brazil|brazilian|brasilia": ("巴西", "南美洲", -15.8, -47.9),
    r"argentin": ("阿根廷", "南美洲", -34.6, -58.4),
    r"venezuela": ("委內瑞拉", "南美洲", 10.5, -66.9),
    r"colombia": ("哥倫比亞", "南美洲", 4.7, -74.1),
    r"chile|chilean": ("智利", "南美洲", -33.4, -70.7),
    r"united kingdom|britain|british|london|uk government": ("英國", "歐洲", 51.5, -0.1),
    r"france|french|paris|macron": ("法國", "歐洲", 48.9, 2.35),
    r"germany|german|berlin": ("德國", "歐洲", 52.5, 13.4),
    r"italy|italian|rome": ("義大利", "歐洲", 41.9, 12.5),
    r"spain|spanish|madrid": ("西班牙", "歐洲", 40.4, -3.7),
    r"poland|polish|warsaw": ("波蘭", "歐洲", 52.2, 21.0),
    r"european union|\beu\b|brussels|european commission": ("歐盟", "歐洲", 50.85, 4.35),
    r"russia|russian|moscow|kremlin|putin": ("俄羅斯", "歐洲", 55.75, 37.6),
    r"ukrain|kyiv|kiev|zelensky": ("烏克蘭", "歐洲", 50.45, 30.5),
    r"taiwan|taipei|taiwanese": ("台灣", "東亞", 25.0, 121.5),
    r"china|chinese|beijing|xi jinping|hong kong": ("中國", "東亞", 39.9, 116.4),
    r"japan|japanese|tokyo": ("日本", "東亞", 35.7, 139.7),
    r"north korea|pyongyang": ("北韓", "東亞", 39.0, 125.75),
    r"south korea|seoul|korean": ("南韓", "東亞", 37.55, 127.0),
    r"indonesia|jakarta": ("印尼", "東南亞", -6.2, 106.8),
    r"philippine|manila": ("菲律賓", "東南亞", 14.6, 121.0),
    r"vietnam|hanoi": ("越南", "東南亞", 21.0, 105.85),
    r"thailand|thai |bangkok": ("泰國", "東南亞", 13.75, 100.5),
    r"myanmar|burma": ("緬甸", "東南亞", 19.75, 96.1),
    r"singapore": ("新加坡", "東南亞", 1.35, 103.8),
    r"malaysia": ("馬來西亞", "東南亞", 3.1, 101.7),
    r"india|indian|delhi|modi": ("印度", "南亞", 28.6, 77.2),
    r"pakistan|islamabad": ("巴基斯坦", "南亞", 33.7, 73.05),
    r"afghanistan|taliban|kabul": ("阿富汗", "南亞", 34.5, 69.2),
    r"bangladesh|dhaka": ("孟加拉", "南亞", 23.8, 90.4),
    r"israel|gaza|hamas|netanyahu|west bank": ("以色列／加薩", "中東", 31.8, 35.2),
    r"iran|tehran": ("伊朗", "中東", 35.7, 51.4),
    r"saudi|riyadh": ("沙烏地阿拉伯", "中東", 24.7, 46.7),
    r"turkey|turkish|ankara|erdogan": ("土耳其", "中東", 39.9, 32.85),
    r"syria|damascus": ("敘利亞", "中東", 33.5, 36.3),
    r"lebanon|beirut|hezbollah": ("黎巴嫩", "中東", 33.9, 35.5),
    r"yemen|houthi": ("葉門", "中東", 15.4, 44.2),
    r"iraq|baghdad": ("伊拉克", "中東", 33.3, 44.4),
    r"egypt|cairo": ("埃及", "中東", 30.05, 31.25),
    r"nigeria|abuja|lagos": ("奈及利亞", "非洲", 9.1, 7.4),
    r"ethiopia": ("衣索比亞", "非洲", 9.0, 38.75),
    r"sudan|khartoum": ("蘇丹", "非洲", 15.6, 32.5),
    r"south africa|pretoria": ("南非", "非洲", -25.7, 28.2),
    r"kenya|nairobi": ("肯亞", "非洲", -1.3, 36.8),
    r"congo|kinshasa": ("剛果", "非洲", -4.3, 15.3),
    r"australia|australian|canberra": ("澳洲", "大洋洲", -35.3, 149.1),
    r"new zealand|wellington": ("紐西蘭", "大洋洲", -41.3, 174.8),
}

CATEGORY_KEYWORDS = [
    ("戰爭與軍事安全", r"war|missile|military|troops|strike|attack|drone|army|navy|invasion|bomb|ceasefire|hostage|nuclear|defen[cs]e|killed"),
    ("科技與人工智慧", r"ai|artificial intelligence|chip|chips|semiconductor|tsmc|nvidia|software|cyber|tech|robot|quantum|openai"),
    ("全球經濟與金融", r"inflation|interest rate|rates|central bank|fed|recession|gdp|stocks?|bond|currency|dollar|yuan|economy|economic|market|markets|bank"),
    ("國際貿易與產業", r"tariffs?|trade|exports?|imports?|supply chain|manufactur\w*|industry|shipping|sanctions?"),
    ("能源與氣候", r"oil|gas|opec|energy|climate|emissions?|renewable|solar|coal|power grid|cop\d+"),
    ("自然災害與公共安全", r"earthquake|tsunami|hurricane|typhoon|flood\w*|wildfire|storm|volcano|disaster|crash|explosion"),
    ("醫療與公共衛生", r"virus|outbreak|pandemic|vaccine|health|disease|who|hospital|cancer|measles|bird flu"),
    ("科學與重大發現", r"scientists?|space|nasa|discovery|research|telescope|fossil|mars|study"),
    ("社會與文化", r"protest\w*|culture|court|migrants?|refugees?|religio\w*|festival|rights|police"),
    ("國際政治與外交", r"election|president|minister|summit|talks|diplomat\w*|treaty|parliament|government|vote|embassy"),
]

IMPACT_KEYWORDS = [
    (r"war|invasion|missile|nuclear|attack|troops|military", 2.0),
    (r"ceasefire|sanctions?|summit|treaty|coup|resign\w*|election", 1.5),
    (r"tariffs?|rate cut|rate hike|inflation|recession|central bank|opec|oil price", 1.5),
    (r"earthquake|tsunami|hurricane|typhoon|outbreak|pandemic", 1.5),
    (r"semiconductor|chips?|tsmc|nvidia|artificial intelligence|\bai\b", 1.2),
    (r"taiwan|taipei|taiwan strait", 2.0),
    (r"nvidia|jensen huang|openai|tsmc|microsoft|apple|elon musk|tesla|alphabet|google", 1.2),
    (r"trump|xi jinping|putin|zelensky|netanyahu|modi|macron|white house|supreme court|midterm", 1.2),
]

WATCH_TOPICS = [
    {"key": "us-china", "name": "美國與中國關係", "regex": r"(us|u\.s\.|united states|washington).{0,60}(china|beijing)|(china|beijing).{0,60}(us|u\.s\.|united states|washington)|xi jinping", "countries": ["美國", "中國"]},
    {"key": "taiwan-strait", "name": "台海局勢", "regex": r"taiwan|taipei|taiwan strait", "countries": ["台灣", "中國", "美國"]},
    {"key": "ukraine", "name": "俄烏戰爭", "regex": r"ukrain|kyiv|zelensky|russia.{0,40}(war|attack|troops)", "countries": ["俄羅斯", "烏克蘭"]},
    {"key": "middle-east", "name": "中東局勢", "regex": r"gaza|israel|hamas|iran|hezbollah|houthi|lebanon|syria|red sea", "countries": ["以色列", "伊朗", "黎巴嫩", "葉門"]},
    {"key": "politics", "name": "全球主要國家政治變動", "regex": r"election|prime minister|president.{0,30}(resign|elected|sworn)|coup|parliament|snap vote", "countries": []},
    {"key": "trade-war", "name": "國際貿易戰", "regex": r"tariffs?|trade war|export controls?|trade deal|trade talks", "countries": []},
    {"key": "inflation-rates", "name": "全球通膨與利率", "regex": r"inflation|interest rates?|rate cut|rate hike|central bank|\bfed\b|ecb|bank of japan", "countries": []},
    {"key": "energy", "name": "能源供應與石油市場", "regex": r"opec|oil price|crude|natural gas|lng|energy supply|pipeline", "countries": []},
    {"key": "ai-chips", "name": "AI 與半導體競爭", "regex": r"semiconductor|chips?\b|tsmc|nvidia|artificial intelligence|\bai\b|openai|export controls?", "countries": ["美國", "中國", "台灣"]},
    {"key": "security", "name": "重大國際安全事件", "regex": r"attack|terror|missile|nuclear|hostage|cyberattack|military strike|assassinat", "countries": []},
]

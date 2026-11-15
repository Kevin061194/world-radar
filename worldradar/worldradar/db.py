import sqlite3, json

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles(url TEXT PRIMARY KEY, title TEXT, source TEXT, published TEXT, fetched TEXT, summary TEXT);
CREATE TABLE IF NOT EXISTS stories(id TEXT, date TEXT, rank INTEGER, data TEXT, PRIMARY KEY(id, date));
CREATE TABLE IF NOT EXISTS digests(date TEXT PRIMARY KEY, data TEXT);
CREATE TABLE IF NOT EXISTS watch(topic TEXT, date TEXT, title TEXT, url TEXT, score INTEGER, PRIMARY KEY(topic, url));
CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, status TEXT, detail TEXT);
"""


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(path))
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def save_articles(c, items, fetched):
    c.executemany("INSERT OR IGNORE INTO articles VALUES(?,?,?,?,?,?)",
                  [(i["url"], i["title"], i["source"], i["published"].isoformat(), fetched, i["summary"]) for i in items])
    c.commit()


def save_stories(c, date, stories):
    c.execute("DELETE FROM stories WHERE date=?", (date,))
    c.executemany("INSERT INTO stories VALUES(?,?,?,?)",
                  [(s["id"], date, s["rank"], json.dumps(s, ensure_ascii=False)) for s in stories])
    c.commit()


def save_digest(c, date, digest):
    c.execute("INSERT OR REPLACE INTO digests VALUES(?,?)", (date, json.dumps(digest, ensure_ascii=False)))
    c.commit()


def save_watch(c, topic, date, title, url, score):
    c.execute("INSERT OR IGNORE INTO watch VALUES(?,?,?,?,?)", (topic, date, title, url, score))
    c.commit()


def watch_timeline(c, topic, limit=15):
    return [dict(r) for r in c.execute(
        "SELECT date,title,url,score FROM watch WHERE topic=? ORDER BY date DESC, score DESC LIMIT ?", (topic, limit))]


def watch_first_seen(c, topic):
    r = c.execute("SELECT MIN(date) d FROM watch WHERE topic=?", (topic,)).fetchone()
    return r["d"]


def save_run(c, ts, status, detail):
    c.execute("INSERT INTO runs(ts,status,detail) VALUES(?,?,?)", (ts, status, json.dumps(detail, ensure_ascii=False)))
    c.commit()


def list_dates(c):
    return [r["date"] for r in c.execute("SELECT DISTINCT date FROM stories ORDER BY date DESC")]

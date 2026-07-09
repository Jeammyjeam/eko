import requests
import psycopg2
import time
import os
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

conn = psycopg2.connect(host="127.0.0.1", database="projectdb", user="cortex", password="cortex123")
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS repos (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        full_name VARCHAR(255) UNIQUE,
        stars INTEGER,
        license VARCHAR(100),
        description TEXT,
        url VARCHAR(500),
        discovered_at TIMESTAMP,
        tier INTEGER DEFAULT 1
    )
""")
conn.commit()

def get_tier(l):
    if not l: return 3
    l = l.lower()
    if any(x in l for x in ["mit","apache","bsd"]): return 1
    if any(x in l for x in ["gpl","lgpl","mozilla"]): return 2
    return 3

# Multiple search queries to cover different categories
QUERIES = [
    "stars:>1000 license:mit topic:ai",
    "stars:>1000 license:mit topic:machine-learning",
    "stars:>1000 license:mit topic:automation",
    "stars:>1000 license:mit topic:python",
    "stars:>1000 license:mit topic:nodejs",
    "stars:>1000 license:mit topic:devtools",
    "stars:>1000 license:mit topic:llm",
    "stars:>1000 license:mit topic:agent",
]

def fetch_repos(query):
    r = requests.get(
        "https://api.github.com/search/repositories",
        params={"q": query, "sort": "stars", "order": "desc", "per_page": 10},
        headers=HEADERS
    )
    if r.status_code == 403:
        print(f"Rate limited — waiting 60s")
        time.sleep(60)
        return {"items": []}
    return r.json()

def save_repos(data):
    saved = 0
    for repo in data.get("items", []):
        ln = repo["license"]["name"] if repo.get("license") else None
        try:
            cur.execute("""
                INSERT INTO repos (name,full_name,stars,license,description,url,discovered_at,tier)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (full_name) DO UPDATE SET stars=EXCLUDED.stars,tier=EXCLUDED.tier
            """, (
                repo["name"], repo["full_name"], repo["stargazers_count"],
                ln, repo.get("description",""), repo["html_url"],
                datetime.now(), get_tier(ln)
            ))
            saved += 1
        except Exception as e:
            print(f"Error: {e}")
    conn.commit()
    return saved

if __name__ == "__main__":
    print("CORTEX GitHub Monitor — expanded search starting...")
    total = 0
    for i, query in enumerate(QUERIES):
        print(f"[{i+1}/{len(QUERIES)}] Searching: {query}")
        data = fetch_repos(query)
        saved = save_repos(data)
        total += saved
        print(f"  Saved {saved} repos")
        time.sleep(3)  # respect rate limits

    cur.execute("SELECT COUNT(*) FROM repos")
    count = cur.fetchone()[0]
    print(f"\nDone. Total repos in database: {count}")
    cur.close()
    conn.close()

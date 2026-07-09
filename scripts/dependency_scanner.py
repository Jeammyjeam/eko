import os
import json
import base64
import psycopg2
import requests
from datetime import datetime

DB = dict(host="127.0.0.1", port="5432", dbname="projectdb", user="cortex", password="cortex123")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
API = "https://api.github.com"

def get_tier(l):
    if not l: return 3
    l = l.lower()
    if any(x in l for x in ["mit","apache","bsd"]): return 1
    if any(x in l for x in ["gpl","lgpl","mozilla"]): return 2
    return 3

conn = psycopg2.connect(**DB)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS dependencies (
        id SERIAL PRIMARY KEY,
        repo_id INTEGER REFERENCES repos(id),
        package_name TEXT NOT NULL,
        version TEXT,
        ecosystem VARCHAR(10),
        UNIQUE(repo_id, package_name, ecosystem)
    )
""")
conn.commit()

cur.execute("SELECT id, url FROM repos")
repos = cur.fetchall()

total = 0
for repo_id, repo_url in repos:
    try:
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        
        for filename, ecosystem in [("package.json","npm"),("requirements.txt","pip")]:
            r = requests.get(f"{API}/repos/{owner}/{repo}/contents/{filename}", headers=HEADERS)
            if r.status_code != 200:
                continue
            content = base64.b64decode(r.json()["content"]).decode("utf-8")
            
            if ecosystem == "npm":
                data = json.loads(content)
                deps = {**data.get("dependencies",{}), **data.get("devDependencies",{})}
                for name, version in deps.items():
                    try:
                        cur.execute("INSERT INTO dependencies (repo_id, package_name, version, ecosystem) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",(repo_id, name, version, ecosystem))
                        total += 1
                    except: pass
            else:
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts2 = line.split("==",1)
                        name = parts2[0].strip()
                        version = parts2[1].strip() if len(parts2) > 1 else None
                        try:
                            cur.execute("INSERT INTO dependencies (repo_id, package_name, version, ecosystem) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",(repo_id, name, version, ecosystem))
                            total += 1
                        except: pass
        conn.commit()
    except Exception as e:
        print(f"Error: {repo_url}: {e}")

print(f"Done. Saved {total} dependencies.")
cur.close()
conn.close()

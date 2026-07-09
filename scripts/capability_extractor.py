import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

import time
import random
import json
import requests
import psycopg2
from google import genai
import os

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)
model = client

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json", "Authorization": "token " + os.environ.get("GITHUB_TOKEN", "")}

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# Create capabilities table
cur.execute("""
    CREATE TABLE IF NOT EXISTS capabilities (
        id SERIAL PRIMARY KEY,
        repo_id INTEGER REFERENCES repos(id),
        language TEXT,
        category TEXT,
        key_capabilities TEXT,
        use_cases TEXT,
        extracted_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(repo_id)
    )
""")
conn.commit()

def fetch_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    r = requests.get(url, headers=GITHUB_HEADERS)
    if r.status_code == 200:
        import base64
        content = r.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore")[:3000]
    return None

def extract_capabilities(readme_text, repo_name):
    prompt = f"""Analyze this GitHub repository README for "{repo_name}" and extract structured information.
Return ONLY a JSON object with these exact keys:
{{
  "language": "primary programming language",
  "category": "one of: automation, ai-ml, database, frontend, backend, devops, security, data-science, utility, other",
  "key_capabilities": "comma separated list of 3-5 key capabilities",
  "use_cases": "comma separated list of 2-3 main use cases"
}}

README:
{readme_text[:2000]}

Return only valid JSON, nothing else."""
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt + random.uniform(0, 1))
    return None

# Fetch repos
cur.execute("SELECT id, name, url FROM repos")
repos = cur.fetchall()
print(f"Processing {len(repos)} repos...")

for i, (repo_id, name, url) in enumerate(repos):
    print(f"[{i+1}/{len(repos)}] Processing {name}...")
    try:
        parts = url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        readme = fetch_readme(owner, repo)
        if not readme:
            print(f"  No README found for {name}")
            continue
        caps = extract_capabilities(readme, name)
        if caps:
            cur.execute("""
                INSERT INTO capabilities (repo_id, language, category, key_capabilities, use_cases)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (repo_id) DO UPDATE SET
                    language=EXCLUDED.language,
                    category=EXCLUDED.category,
                    key_capabilities=EXCLUDED.key_capabilities,
                    use_cases=EXCLUDED.use_cases,
                    extracted_at=NOW()
            """, (repo_id, caps.get("language"), caps.get("category"), 
                  caps.get("key_capabilities"), caps.get("use_cases")))
            conn.commit()
            print(f"  Saved: {caps.get('category')} — {caps.get('key_capabilities')[:50]}")
        time.sleep(4)
    except Exception as e:
        print(f"  Error: {e}")

print("Capability extraction complete.")
cur.close()
conn.close()

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import time
import json
import base64
import requests
import psycopg2
from ollama import chat
from pydantic import BaseModel, Field
from typing import List

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json"}
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
if GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

class RepoCapabilities(BaseModel):
    category: str = Field(description="The general software domain of this project, e.g. 'Web Framework', 'CLI Tool', 'Machine Learning', 'Developer Tool'")
    key_capabilities: List[str] = Field(description="3-5 concrete technical features this specific project provides, grounded in the README text")
    use_cases: List[str] = Field(description="2-4 practical scenarios a developer would use this project for")

def fetch_repo_meta(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
    if r.status_code == 200:
        data = r.json()
        return data.get("language") or "Unknown"
    return "Unknown"

def fetch_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    r = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
    if r.status_code == 200:
        content = r.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore")[:3000]
    return None

def extract_capabilities(readme_text, repo_name, language):
    for attempt in range(3):
        try:
            response = chat(
                model="qwen2.5-coder:1.5b",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise software documentation analyst. Extract ONLY the category, key_capabilities, and use_cases of the project based strictly on the README text provided. Do not guess the programming language — it is already known. Respond using JSON."
                    },
                    {
                        "role": "user",
                        "content": f"Project name: '{repo_name}'. Primary language: {language}.\n\nREADME content:\n{readme_text[:2000]}\n\nExtract the category, key_capabilities, and use_cases."
                    }
                ],
                format=RepoCapabilities.model_json_schema(),
                options={"temperature": 0}
            )
            data = json.loads(response.message.content)
            return data
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None

def run():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT r.id, r.name, r.url
        FROM repos r
        LEFT JOIN capabilities c ON r.id = c.repo_id
        WHERE c.id IS NULL
           OR c.language IN ('HTML', 'English')
    """)
    repos = cur.fetchall()
    print(f"Repos to process (uncapped + bad language): {len(repos)}")

    success = 0
    failed = 0

    for i, (repo_id, name, url) in enumerate(repos):
        print(f"[{i+1}/{len(repos)}] {name}...")
        try:
            parts = url.rstrip("/").split("/")
            owner, repo = parts[-2], parts[-1]

            language = fetch_repo_meta(owner, repo)
            readme = fetch_readme(owner, repo)
            if not readme:
                print(f"  No README — using description only")
                readme = ""

            caps = extract_capabilities(readme, name, language)
            if not caps:
                print(f"  Extraction failed — skipping")
                failed += 1
                continue

            cur.execute("""
                INSERT INTO capabilities (repo_id, language, category, key_capabilities, use_cases)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (repo_id) DO UPDATE SET
                    language=EXCLUDED.language,
                    category=EXCLUDED.category,
                    key_capabilities=EXCLUDED.key_capabilities,
                    use_cases=EXCLUDED.use_cases,
                    extracted_at=NOW()
            """, (
                repo_id,
                language,
                caps.get("category", "other"),
                ", ".join(caps.get("key_capabilities", [])),
                ", ".join(caps.get("use_cases", []))
            ))
            conn.commit()
            print(f"  [{language}] {caps.get('category')} — {', '.join(caps.get('key_capabilities', []))[:60]}")
            success += 1
            time.sleep(1)

        except Exception as e:
            print(f"  Error: {e}")
            failed += 1

    cur.close()
    conn.close()
    print(f"\nDone. Success: {success} | Failed: {failed}")

if __name__ == "__main__":
    run()

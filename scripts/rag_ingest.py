import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import json
import time
import base64
import psycopg
import requests
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

DB = "dbname={} user={} password={} host={} port={}".format(os.getenv("DB_NAME","projectdb"),os.getenv("DB_USER","cortex"),os.getenv("DB_PASSWORD",""),os.getenv("DB_HOST","127.0.0.1"),os.getenv("DB_PORT","5432"))
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json"}

def get_embedding(text):
    for attempt in range(3):
        try:
            response = client.models.embed_content(
                model="gemini-embedding-2",
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"Embedding failed attempt {attempt+1}: {e}")
            time.sleep(2 ** attempt)
    return None

def fetch_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    r = requests.get(url, headers=GITHUB_HEADERS)
    if r.status_code == 200:
        content = r.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore")[:4000]
    return None

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

conn = psycopg.connect(DB)
cur = conn.cursor()

cur.execute("SELECT id, name, url FROM repos")
repos = cur.fetchall()
print(f"Processing {len(repos)} repos for RAG ingestion...")

for repo_id, name, url in repos:
    try:
        parts = url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        readme = fetch_readme(owner, repo)
        if not readme:
            print(f"  No README: {name}")
            continue
        chunks = chunk_text(readme)
        print(f"  {name}: {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:5]):
            embedding = get_embedding(chunk)
            if embedding:
                cur.execute("""
                    INSERT INTO cortex_capabilities 
                    (repo_name, file_path, content_chunk, capability_tags, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    ON CONFLICT DO NOTHING
                """, (name, f"README.md#chunk{i}", chunk, [name], str(embedding)))
                conn.commit()
        time.sleep(2)
    except Exception as e:
        print(f"  Error {name}: {e}")

print("RAG ingestion complete.")
cur.close()
conn.close()

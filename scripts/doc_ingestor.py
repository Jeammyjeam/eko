import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import json
import time
import hashlib
import psycopg
from pathlib import Path
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
DB = "dbname={} user={} password={} host={} port={}".format(os.getenv("DB_NAME","projectdb"),os.getenv("DB_USER","cortex"),os.getenv("DB_PASSWORD",""),os.getenv("DB_HOST","127.0.0.1"),os.getenv("DB_PORT","5432"))
WATCH_DIR = os.path.expanduser("~/cortex/docs_inbox")
PROCESSED_DIR = os.path.expanduser("~/cortex/docs_processed")

os.makedirs(WATCH_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def extract_text(filepath):
    ext = Path(filepath).suffix.lower()
    try:
        if ext == ".pdf":
            import fitz
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        elif ext in [".docx", ".doc"]:
            from docx import Document
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif ext in [".txt", ".md", ".py", ".js", ".json", ".csv"]:
            with open(filepath, "r", errors="ignore") as f:
                return f.read()
        else:
            return None
    except Exception as e:
        print(f"  Extract error: {e}")
        return None

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def get_embedding(text):
    for attempt in range(3):
        try:
            response = client.models.embed_content(
                model="gemini-embedding-2",
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"  Embedding error attempt {attempt+1}: {e}")
            time.sleep(2 ** attempt)
    return None

def ingest_file(filepath):
    filename = Path(filepath).name
    print(f"Ingesting: {filename}")
    
    text = extract_text(filepath)
    if not text or len(text.strip()) < 50:
        print(f"  No usable text extracted")
        return 0
    
    print(f"  Extracted {len(text)} chars")
    chunks = chunk_text(text)
    print(f"  Split into {len(chunks)} chunks")
    
    conn = psycopg.connect(DB)
    cur = conn.cursor()
    
    # Use filename as repo_name so it appears in RAG search
    doc_name = Path(filepath).stem
    
    embedded = 0
    for i, chunk in enumerate(chunks[:10]):  # max 10 chunks per doc
        embedding = get_embedding(chunk)
        if embedding:
            cur.execute("""
                INSERT INTO cortex_capabilities
                (repo_name, file_path, content_chunk, capability_tags, embedding)
                VALUES (%s, %s, %s, %s, %s::vector)
                ON CONFLICT DO NOTHING
            """, (f"doc:{doc_name}", filepath, chunk, [doc_name, "document"], str(embedding)))
            conn.commit()
            embedded += 1
        time.sleep(1)
    
    conn.close()
    print(f"  Embedded {embedded} chunks")
    return embedded

def run():
    files = list(Path(WATCH_DIR).iterdir())
    supported = [f for f in files if f.suffix.lower() in [".pdf",".docx",".doc",".txt",".md",".py",".js",".json",".csv"]]
    
    if not supported:
        print(f"No files found in {WATCH_DIR}")
        print("Drop PDF, DOCX, TXT, MD, or code files there and run again.")
        return
    
    print(f"Found {len(supported)} files to ingest")
    total = 0
    for f in supported:
        total += ingest_file(str(f))
        # Move to processed
        import shutil
        shutil.move(str(f), os.path.join(PROCESSED_DIR, f.name))
        print(f"  Moved to processed/")
    
    print(f"\nDone. Total chunks embedded: {total}")
    print(f"Search with: python3 ~/cortex/scripts/rag_query.py 'your query'")

if __name__ == "__main__":
    run()

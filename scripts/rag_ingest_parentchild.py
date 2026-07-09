import os
import re
import psycopg2
import google.genai as genai
from pathlib import Path
from datetime import datetime

CORTEX_ROOT = Path(__file__).resolve().parents[1]
DB_PARAMS = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_conn():
    return psycopg2.connect(**DB_PARAMS)

def embed(text):
    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    return result.embeddings[0].values

def chunk_text(text, chunk_size=200):
    """Split into small chunks for precise vector search"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) <= chunk_size:
            current += " " + sentence
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:chunk_size]]

def ingest_file(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return

    full_content = path.read_text(encoding="utf-8", errors="ignore")
    if not full_content.strip():
        return

    conn = get_conn()
    cur = conn.cursor()

    # Check if already ingested
    cur.execute("SELECT id FROM cortex_documents WHERE file_path = %s", (str(path),))
    existing = cur.fetchone()
    if existing:
        print(f"Already ingested: {path.name}")
        conn.close()
        return

    # Store parent document
    cur.execute("""
        INSERT INTO cortex_documents (file_name, file_path, full_content, doc_type)
        VALUES (%s, %s, %s, %s) RETURNING id
    """, (path.name, str(path), full_content, path.suffix.lstrip(".")))
    doc_id = cur.fetchone()[0]

    # Store child chunks with embeddings
    chunks = chunk_text(full_content)
    print(f"  Ingesting {path.name} — {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        try:
            vector = embed(chunk)
            cur.execute("""
                INSERT INTO cortex_document_chunks 
                (document_id, chunk_text, chunk_index, summary_vector)
                VALUES (%s, %s, %s, %s)
            """, (doc_id, chunk, i, vector))
        except Exception as e:
            print(f"    Chunk {i} failed: {e}")

    conn.commit()
    conn.close()
    print(f"  Done: {path.name} — {len(chunks)} chunks stored")

def search(query, limit=3):
    """Search chunks, return full parent document context"""
    vector = embed(query)
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT d.file_name, d.full_content, c.chunk_text,
               1 - (c.summary_vector <=> %s::vector) as similarity
        FROM cortex_document_chunks c
        JOIN cortex_documents d ON c.document_id = d.id
        ORDER BY c.summary_vector <=> %s::vector
        LIMIT %s
    """, (vector, vector, limit))
    
    results = cur.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "search":
            query = " ".join(sys.argv[2:])
            print(f"Searching: {query}")
            results = search(query)
            for fname, full_content, chunk, sim in results:
                print(f"[{sim:.3f}] {fname}: {chunk[:100]}")
        else:
            ingest_file(sys.argv[1])
    else:
        # Ingest all skills
        skills_dir = CORTEX_ROOT / "skills"
        for md_file in skills_dir.rglob("*.md"):
            ingest_file(md_file)

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import psycopg
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
DB = "dbname={} user={} password={} host={} port={}".format(os.getenv("DB_NAME","projectdb"),os.getenv("DB_USER","cortex"),os.getenv("DB_PASSWORD",""),os.getenv("DB_HOST","127.0.0.1"),os.getenv("DB_PORT","5432"))

def get_embedding(text):
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    return response.embeddings[0].values

def search(query, k=5):
    embedding = get_embedding(query)
    conn = psycopg.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT repo_name, content_chunk,
               1 - (embedding_half <=> %s::halfvec(3072)) as similarity
        FROM cortex_capabilities
        ORDER BY embedding_half <=> %s::halfvec(3072)
        LIMIT %s
    """, (str(embedding), str(embedding), k))
    results = cur.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "AI agent framework"
    print(f"Searching for: {query}\n")
    results = search(query)
    for repo, chunk, score in results:
        print(f"[{score:.3f}] {repo}")
        print(f"  {chunk[:150]}...")
        print()

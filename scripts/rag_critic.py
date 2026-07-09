import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import psycopg2
import json
from datetime import datetime

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))

def get_conn():
    return psycopg2.connect(**DB)

def find_short_chunks():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, repo_name, content_chunk
        FROM cortex_capabilities
        WHERE length(content_chunk) < 100
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def find_duplicate_repos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT repo_name, COUNT(*) as chunks
        FROM cortex_capabilities
        GROUP BY repo_name
        ORDER BY chunks DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def find_empty_chunks():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, repo_name, content_chunk
        FROM cortex_capabilities
        WHERE content_chunk IS NULL OR trim(content_chunk) = ''
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def log_issue(issue_type, repo_name, chunk_id, details):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO rag_audit_log (issue_type, repo_name, chunk_id, details, status)
        VALUES (%s, %s, %s, %s, 'flagged')
    """, (issue_type, repo_name, chunk_id, details))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cortex_capabilities")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT repo_name) FROM cortex_capabilities")
    repos = cur.fetchone()[0]
    cur.execute("SELECT AVG(length(content_chunk)) FROM cortex_capabilities")
    avg_len = cur.fetchone()[0]
    conn.close()
    return total, repos, float(round(avg_len or 0, 1))

def run():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] RAG Critic starting...")
    
    total, repos, avg_len = get_stats()
    print(f"Stats: {total} chunks, {repos} repos, avg chunk length: {avg_len} chars")
    
    issues = 0
    
    # Check short chunks
    short = find_short_chunks()
    if short:
        print(f"Short chunks found: {len(short)}")
        for chunk_id, repo_name, content in short:
            log_issue("short_chunk", repo_name, chunk_id, f"Only {len(content)} chars: {content[:80]}")
            issues += 1
    else:
        print("No short chunks found")

    # Check empty chunks
    empty = find_empty_chunks()
    if empty:
        print(f"Empty chunks found: {len(empty)}")
        for chunk_id, repo_name, content in empty:
            log_issue("empty_chunk", repo_name, chunk_id, "Empty or null content")
            issues += 1
    else:
        print("No empty chunks found")

    # Chunk distribution
    dist = find_duplicate_repos()
    print("Chunk distribution per repo:")
    for repo_name, count in dist:
        print(f"  {repo_name}: {count} chunks")
        if count > 10:
            log_issue("high_chunk_count", repo_name, None, f"{count} chunks — consider pruning")
            issues += 1

    # Summary
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_chunks": total,
        "total_repos": repos,
        "avg_chunk_length": avg_len,
        "issues_found": issues,
        "status": "CLEAN" if issues == 0 else "ISSUES_FOUND"
    }
    
    print(f"\nRAG Audit complete: {issues} issues found")
    print(f"Status: {summary['status']}")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    run()

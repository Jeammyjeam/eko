import json
import time
import psycopg2
import subprocess
import os
from datetime import datetime
from cortex_cloud_env import CortexCloudConfig

DB = CortexCloudConfig.DB_PARAMS

def get_conn():
    return psycopg2.connect(**DB)

def claim_task():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("""
            SELECT id, task_type, payload FROM cortex_task_queue
            WHERE status = 'QUEUED'
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)
        row = cur.fetchone()
        if not row:
            conn.rollback()
            conn.close()
            return None
        task_id, task_type, payload = row
        cur.execute("""
            UPDATE cortex_task_queue
            SET status = 'PROCESSING', updated_at = NOW()
            WHERE id = %s
        """, (task_id,))
        conn.commit()
        conn.close()
        return task_id, task_type, payload
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Claim error: {e}")
        return None

def complete_task(task_id, result, success=True):
    conn = get_conn()
    cur = conn.cursor()
    status = "SUCCESS" if success else "FAILED"
    cur.execute("""
        UPDATE cortex_task_queue
        SET status = %s, updated_at = NOW()
        WHERE id = %s
    """, (status, task_id))
    conn.commit()
    conn.close()

def execute_task(task_type, payload):
    scripts = CortexCloudConfig.SCRIPTS_DIR
    if task_type == "web_search":
        query = payload.get("query", "")
        result = subprocess.run(
            ["python3", os.path.join(scripts, "web_search.py"), query],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout[:500]
    elif task_type == "rag_search":
        query = payload.get("query", "")
        result = subprocess.run(
            ["python3", os.path.join(scripts, "rag_query.py"), query],
            capture_output=True, text=True, timeout=30,
            env={**os.environ}
        )
        return result.stdout[:500]
    elif task_type == "health_check":
        result = subprocess.run(
            ["python3", os.path.join(scripts, "health_monitor.py")],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout[:500]
    elif task_type == "goal_run":
        result = subprocess.run(
            ["python3", os.path.join(scripts, "goal_engine.py"), "run"],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout[:500]
    else:
        return f"Unknown task type: {task_type}"

def run():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Task Queue Worker starting...")
    while True:
        task = claim_task()
        if task:
            task_id, task_type, payload = task
            print(f"  Processing [{task_id}] {task_type}")
            try:
                result = execute_task(task_type, payload)
                complete_task(task_id, result, success=True)
                print(f"  Done [{task_id}]: {str(result)[:80]}")
            except Exception as e:
                complete_task(task_id, str(e), success=False)
                print(f"  Failed [{task_id}]: {e}")
        time.sleep(5)

if __name__ == "__main__":
    run()

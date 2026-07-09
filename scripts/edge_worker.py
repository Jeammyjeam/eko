import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Master node connection over Tailscale
DB_CONFIG = {
    "host": "100.120.242.76",
    "database": "projectdb",
    "user": "cortex",
    "password": "cortex123",
    "port": 5432,
    "connect_timeout": 10
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def process_task():
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("BEGIN")
        cur.execute("""
            SELECT id, task_type, payload FROM cortex_task_queue
            WHERE status = 'QUEUED' 
            AND (payload->>'target_node' = 'android_edge' 
                 OR payload->>'target_node' IS NULL)
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)
        task = cur.fetchone()
        if not task:
            conn.rollback()
            conn.close()
            return False

        task_id = task['id']
        task_type = task['task_type']
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing [{task_id}] {task_type}")

        cur.execute("""
            UPDATE cortex_task_queue 
            SET status = 'PROCESSING', updated_at = NOW() 
            WHERE id = %s
        """, (task_id,))
        conn.commit()

        # Execute lightweight tasks only
        result = f"Processed by Android edge node at {datetime.now()}"
        cur.execute("""
            UPDATE cortex_task_queue 
            SET status = 'SUCCESS', updated_at = NOW() 
            WHERE id = %s
        """, (task_id,))
        conn.commit()
        print(f"  Done [{task_id}]")
        cur.close()
        conn.close()
        return True

    except psycopg2.OperationalError as e:
        print(f"Connection dropped: {e} — retrying in 10s")
        time.sleep(10)
        return False
    except Exception as e:
        print(f"Worker error: {e}")
        return False

if __name__ == "__main__":
    print("CORTEX Android Edge Worker starting...")
    print(f"Connecting to master node at {DB_CONFIG['host']}...")
    while True:
        process_task()
        time.sleep(5)

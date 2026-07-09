import time
import psycopg2
from datetime import datetime
from pathlib import Path

DB_PARAMS = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}

def log_action(agent_name, task_description, model_provider, latency_ms, status, tokens=0, error=None):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cortex_agent_telemetry 
            (agent_name, task_description, model_provider, tokens_consumed, latency_ms, execution_status, error_payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (agent_name, task_description, model_provider, tokens, latency_ms, status, error))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Telemetry log error: {e}")

class Timer:
    def __init__(self):
        self.start = time.time()
    
    def elapsed_ms(self):
        return int((time.time() - self.start) * 1000)

if __name__ == "__main__":
    # Test telemetry
    t = Timer()
    time.sleep(0.1)
    log_action("test_agent", "telemetry test", "system", t.elapsed_ms(), "SUCCESS", tokens=10)
    
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT agent_name, task_description, latency_ms, execution_status FROM cortex_agent_telemetry ORDER BY id DESC LIMIT 3")
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        print(row)

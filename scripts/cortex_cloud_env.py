import os
from pathlib import Path
import psycopg2
from datetime import datetime

class CortexCloudConfig:
    ROOT_DIR = Path(__file__).resolve().parents[1]
    SKILLS_DIR = str(ROOT_DIR / "skills")
    SCRIPTS_DIR = str(ROOT_DIR / "scripts")
    INBOX_DIR = str(ROOT_DIR / "docs_inbox")
    PROCESSED_DIR = str(ROOT_DIR / "docs_processed")
    HEARTBEAT_FILE = str(ROOT_DIR / "HEARTBEAT.md")

    DB_PARAMS = {
        "host": "127.0.0.1",
        "port": 5432,
        "dbname": "projectdb",
        "user": "cortex",
        "password": "cortex123"
    }

    HERMES_URL = "http://localhost:8642/v1/chat/completions"
    HERMES_KEY = "cortex-local-key"

    TAILSCALE_IP = "100.120.242.76"
    TAILSCALE_PORT = 2222

    @classmethod
    def get_conn(cls):
        return psycopg2.connect(**cls.DB_PARAMS)

    @classmethod
    def initialize(cls):
        for path in [cls.SKILLS_DIR, cls.SCRIPTS_DIR, cls.INBOX_DIR, cls.PROCESSED_DIR]:
            os.makedirs(path, exist_ok=True)

        # Update node heartbeat
        try:
            conn = cls.get_conn()
            cur = conn.cursor()
            cur.execute("""
                UPDATE cortex_cloud_nodes
                SET last_heartbeat = NOW(), status = 'ACTIVE'
                WHERE node_name = 'wsl2-master-core'
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Node heartbeat error: {e}")

        print(f"CORTEX Cloud initialized — root: {cls.ROOT_DIR}")
        return cls

if __name__ == "__main__":
    config = CortexCloudConfig.initialize()
    print(f"Skills dir: {config.SKILLS_DIR}")
    print(f"Scripts dir: {config.SCRIPTS_DIR}")
    print(f"DB: {config.DB_PARAMS['dbname']}@{config.DB_PARAMS['host']}")
    print(f"Tailscale: {config.TAILSCALE_IP}:{config.TAILSCALE_PORT}")

    # Show node status
    conn = config.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT node_name, connection_type, status, last_heartbeat FROM cortex_cloud_nodes")
    nodes = cur.fetchall()
    conn.close()
    print(f"\nCORTEX Cloud Nodes ({len(nodes)}):")
    for n in nodes:
        print(f"  [{n[2]}] {n[0]} via {n[1]} — last seen {n[3].strftime('%Y-%m-%d %H:%M')}")

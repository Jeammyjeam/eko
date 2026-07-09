import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import json
import subprocess
from datetime import datetime

CORTEX_DIR = os.path.expanduser("~/cortex")
BACKUP_DIR = os.path.expanduser("~/cortex_migration_payload")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def run_cmd(cmd, desc=""):
    print(f"  {desc}..." if desc else f"  Running: {cmd[:60]}")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:200]}")
        return False
    return True

def export():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] CORTEX Migration Exporter starting...")
    os.makedirs(BACKUP_DIR, exist_ok=True)

    print("\n[1/7] Freezing PM2 state...")
    run_cmd("pm2 save --force", "Saving PM2 process list")

    print("\n[2/7] Exporting environment config...")
    env_keys = {}
    bashrc = os.path.expanduser("~/.bashrc")
    with open(bashrc, "r") as f:
        for line in f:
            if line.startswith("export ") and "=" in line:
                key = line.replace("export ", "").split("=")[0].strip()
                env_keys[key] = f"<SET_{key}_HERE>"
    with open(f"{BACKUP_DIR}/env_template.json", "w") as f:
        json.dump(env_keys, f, indent=2)
    print(f"  Saved {len(env_keys)} env var keys to env_template.json")

    print("\n[3/7] Dumping PostgreSQL database...")
    pg_cmd = f"PGPASSWORD={os.getenv('DB_PASSWORD','')} pg_dump -h {os.getenv('DB_HOST','127.0.0.1')} -U {os.getenv('DB_USER','cortex')} -d {os.getenv('DB_NAME','projectdb')} --clean --if-exists --format=p -f {BACKUP_DIR}/cortex_db.sql"
    if run_cmd(pg_cmd, "pg_dump projectdb"):
        size = os.path.getsize(f"{BACKUP_DIR}/cortex_db.sql")
        print(f"  Database dump: {size // 1024}KB")

    print("\n[4/7] Exporting PM2 config...")
    run_cmd(f"cp ~/.pm2/dump.pm2 {BACKUP_DIR}/pm2_dump.json", "Copying PM2 dump")

    print("\n[5/7] Exporting skills...")
    run_cmd(f"cp -r {CORTEX_DIR}/skills {BACKUP_DIR}/skills", "Copying skills directory")

    print("\n[6/7] Exporting config files...")
    for fname in ["HEARTBEAT.md", "ecosystem.config.js"]:
        src = os.path.join(CORTEX_DIR, fname)
        if os.path.exists(src):
            run_cmd(f"cp {src} {BACKUP_DIR}/{fname}", f"Copying {fname}")

    print("\n[7/7] Creating migration manifest...")
    manifest = {
        "timestamp": TIMESTAMP,
        "source": "WSL2 Ubuntu 24.04 x86_64",
        "target": "Oracle Cloud ARM64 Ubuntu 22.04",
        "stack": {
            "postgresql": "16 + pgvector",
            "gitea": "1.25.0",
            "n8n": "via PM2",
            "hermes": "v0.14 port 8642",
            "python": "3.12",
            "nodejs": "22"
        },
        "warnings": [
            "Fresh pip install required on ARM64 — do NOT copy venv",
            "pgvector must be recompiled on target before pg_restore",
            "All paths now use os.path.expanduser — no hardcoded paths",
            "Add keep-alive cron: 0 * * * * openssl speed rsa2048 > /dev/null 2>&1",
            "Open ports in Oracle dashboard AND ufw: 8501, 5678, 8642, 3000"
        ],
        "restore_order": [
            "1. Provision Oracle Cloud ARM64 4 cores 24GB RAM",
            "2. Install: build-essential libpq-dev git python3.12 nodejs npm",
            "3. Install PostgreSQL 16 + recompile pgvector for ARM64",
            "4. git clone github.com/Jeammyjeam/cortex-backup ~/cortex",
            "5. pip install -r requirements.txt (fresh ARM64 wheels)",
            "6. psql -U cortex -d projectdb -f cortex_db.sql",
            "7. Set env vars from env_template.json in ~/.bashrc",
            "8. npm install -g pm2 && pm2 resurrect",
            "9. hermes gateway restart",
            "10. Add keep-alive cron",
            "11. python3 ~/cortex/scripts/health_monitor.py"
        ]
    }
    with open(f"{BACKUP_DIR}/migration_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Migration payload ready: {BACKUP_DIR}")
    for f in os.listdir(BACKUP_DIR):
        fpath = os.path.join(BACKUP_DIR, f)
        size = os.path.getsize(fpath) if os.path.isfile(fpath) else 0
        print(f"  {f} ({size // 1024}KB)" if size else f"  {f}/")
    print(f"{'='*50}")
    print("When ready: scp -r ~/cortex_migration_payload user@oracle-ip:~/")

if __name__ == "__main__":
    export()

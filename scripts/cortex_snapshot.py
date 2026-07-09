import subprocess
import os
import json
import gzip
import shutil
from datetime import datetime
from pathlib import Path

CORTEX_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = Path.home() / "cortex_snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)
MAX_SNAPSHOTS = 10  # Keep last 10 snapshots

DB_PARAMS = {
    "host": "127.0.0.1", "port": "5432",
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}

def create_snapshot(reason="manual", risk_score=0.0):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = SNAPSHOT_DIR / f"snapshot_{ts}"
    snapshot_path.mkdir()

    print(f"[SNAPSHOT] Creating snapshot: {ts} (reason={reason}, risk={risk_score:.2f})")

    # 1. Database dump
    db_file = snapshot_path / "cortex_db.sql.gz"
    env = {**os.environ, "PGPASSWORD": DB_PARAMS["password"]}
    result = subprocess.run([
        "pg_dump", "-h", DB_PARAMS["host"], "-U", DB_PARAMS["user"],
        "-d", DB_PARAMS["dbname"]
    ], capture_output=True, env=env)
    
    if result.returncode == 0:
        with gzip.open(db_file, "wb") as f:
            f.write(result.stdout)
        print(f"  DB dump: {db_file.stat().st_size // 1024}KB")
    else:
        print(f"  DB dump failed: {result.stderr.decode()[:100]}")

    # 2. Scripts backup
    scripts_backup = snapshot_path / "scripts"
    shutil.copytree(CORTEX_ROOT / "scripts", scripts_backup)
    print(f"  Scripts: {len(list(scripts_backup.iterdir()))} files")

    # 3. Skills backup
    skills_backup = snapshot_path / "skills"
    shutil.copytree(CORTEX_ROOT / "skills", skills_backup)
    print(f"  Skills: backed up")

    # 4. Manifest
    manifest = {
        "timestamp": ts,
        "reason": reason,
        "risk_score": risk_score,
        "pm2_processes": _get_pm2_state(),
        "git_commit": _get_git_commit()
    }
    (snapshot_path / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # 5. Prune old snapshots
    _prune_old_snapshots()

    print(f"[SNAPSHOT] Complete: {snapshot_path}")
    return str(snapshot_path)

def restore_latest():
    snapshots = sorted(SNAPSHOT_DIR.iterdir(), reverse=True)
    if not snapshots:
        print("[SNAPSHOT] No snapshots found")
        return False

    latest = snapshots[0]
    print(f"[SNAPSHOT] Restoring from: {latest.name}")

    db_file = latest / "cortex_db.sql.gz"
    if db_file.exists():
        env = {**os.environ, "PGPASSWORD": DB_PARAMS["password"]}
        with gzip.open(db_file, "rb") as f:
            sql_content = f.read()
        result = subprocess.run([
            "psql", "-h", DB_PARAMS["host"], "-U", DB_PARAMS["user"],
            "-d", DB_PARAMS["dbname"]
        ], input=sql_content, capture_output=True, env=env)
        if result.returncode == 0:
            print("  DB restored")
        else:
            print(f"  DB restore failed: {result.stderr.decode()[:100]}")

    scripts_backup = latest / "scripts"
    if scripts_backup.exists():
        for f in scripts_backup.iterdir():
            shutil.copy2(f, CORTEX_ROOT / "scripts" / f.name)
        print("  Scripts restored")

    return True

def list_snapshots():
    snapshots = sorted(SNAPSHOT_DIR.iterdir(), reverse=True)
    print(f"[SNAPSHOT] {len(snapshots)} snapshots found:")
    for s in snapshots[:5]:
        manifest_path = s / "manifest.json"
        if manifest_path.exists():
            m = json.loads(manifest_path.read_text())
            print(f"  {s.name} — reason={m['reason']}, risk={m.get('risk_score', 0):.2f}")
    return snapshots

def _get_pm2_state():
    try:
        result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
        processes = json.loads(result.stdout)
        return [{"name": p["name"], "status": p["pm2_env"]["status"]} for p in processes]
    except:
        return []

def _get_git_commit():
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                               capture_output=True, text=True, cwd=str(CORTEX_ROOT))
        return result.stdout.strip()
    except:
        return "unknown"

def _prune_old_snapshots():
    snapshots = sorted(SNAPSHOT_DIR.iterdir(), reverse=True)
    for old in snapshots[MAX_SNAPSHOTS:]:
        shutil.rmtree(old)
        print(f"  Pruned: {old.name}")

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "create"
    if cmd == "create":
        create_snapshot(reason="manual")
    elif cmd == "list":
        list_snapshots()
    elif cmd == "restore":
        restore_latest()

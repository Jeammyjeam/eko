import subprocess
import os
from pathlib import Path
from datetime import datetime

CORTEX_DB_DIR = Path.home() / "cortex-db" / "migrations"

def export_migration(description="schema_update"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = sorted(CORTEX_DB_DIR.glob("*.sql"))
    next_num = len(files) + 1
    filename = f"{next_num:03d}_{description}.sql"
    output_path = CORTEX_DB_DIR / filename

    result = subprocess.run([
        "pg_dump", "-h", "127.0.0.1", "-U", "cortex",
        "-d", "projectdb", "--schema-only"
    ], capture_output=True, text=True,
    env={**os.environ, "PGPASSWORD": "cortex123"})

    if result.returncode == 0:
        output_path.write_text(result.stdout)
        print(f"Migration exported: {filename}")
        # Auto commit to cortex-db
        subprocess.run(["git", "add", "."], cwd=CORTEX_DB_DIR.parent)
        subprocess.run(["git", "commit", "-m", f"migration: {description}"], cwd=CORTEX_DB_DIR.parent)
        subprocess.run(["git", "push", "origin", "main"], cwd=CORTEX_DB_DIR.parent)
        print("Pushed to cortex-db repo")
    else:
        print(f"Export failed: {result.stderr}")

if __name__ == "__main__":
    import sys
    desc = sys.argv[1] if len(sys.argv) > 1 else "schema_update"
    export_migration(desc)

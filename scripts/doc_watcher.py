import os
import time
import subprocess
from pathlib import Path

WATCH_DIR = os.path.expanduser("~/cortex/docs_inbox")
LOCK_FILE = "/tmp/cortex_doc_watcher.lock"
CHECK_INTERVAL = 30  # seconds

SUPPORTED = {".pdf", ".docx", ".doc", ".txt", ".md", ".py", ".js", ".json", ".csv"}

def get_files():
    return [f for f in Path(WATCH_DIR).iterdir() if f.suffix.lower() in SUPPORTED]

def run():
    os.makedirs(WATCH_DIR, exist_ok=True)
    print(f"CORTEX Doc Watcher started — watching {WATCH_DIR}")
    print(f"Check interval: {CHECK_INTERVAL}s")

    while True:
        files = get_files()
        if files:
            print(f"[{time.strftime('%H:%M:%S')}] Found {len(files)} file(s) — running ingestor")
            result = subprocess.run(
                ["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "doc_ingestor.py")],
                capture_output=True, text=True, timeout=300,
                env={**os.environ}
            )
            if result.stdout:
                print(result.stdout.strip())
            if result.returncode != 0 and result.stderr:
                print(f"Error: {result.stderr[:200]}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()

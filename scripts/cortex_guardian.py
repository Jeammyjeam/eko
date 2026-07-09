import subprocess
import time
import os
import ast
import shutil
import psycopg2
import requests
import json
from datetime import datetime
from pathlib import Path

CORTEX_ROOT = Path(__file__).resolve().parents[1]
DB_PARAMS = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:1.5b"
CHECK_INTERVAL = 60
MAX_RESTARTS_THRESHOLD = 3

GUARDABLE = {
    "doc-watcher": "doc_watcher.py",
    "task-queue": "task_queue_worker.py",
    "cortex-telemetry": "telemetry_throttler.py",
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] GUARDIAN: {msg}")

def get_conn():
    return psycopg2.connect(**DB_PARAMS)

def log_healing(process, error, patch, success):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO healing_log (timestamp, script_name, healed, attempt_count, status, notes)
            VALUES (NOW(), %s, %s, 1, %s, %s)
        """, (process, success, "SUCCESS" if success else "FAILED", 
              f"Guardian patch: {patch[:200] if patch else error[:200]}"))
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"DB log error: {e}")

def get_pm2_errors(process_name, lines=30):
    try:
        result = subprocess.run(
            ["pm2", "logs", process_name, "--lines", str(lines), "--nostream", "--err"],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout + result.stderr
    except:
        return ""

def get_restart_count(process_name):
    try:
        result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
        processes = json.loads(result.stdout)
        for p in processes:
            if p.get("name") == process_name:
                return p.get("pm2_env", {}).get("restart_time", 0)
    except:
        pass
    return 0

def ask_ollama(error_log, script_content):
    prompt = f"""You are a Python code repair expert. A script crashed with this error:

ERROR LOG:
{error_log[-1000:]}

CURRENT SCRIPT:
{script_content[:2000]}

Provide ONLY the fixed Python script with no explanation, no markdown, no backticks. Just pure Python code."""
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"num_ctx": 16384}},
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("response", "")
    except Exception as e:
        log(f"Ollama error: {e}")
    return ""

def is_valid_python(code):
    try:
        ast.parse(code)
        return True
    except:
        return False

def apply_patch(script_path, new_code, process_name):
    # Backup original
    backup_path = str(script_path) + f".guardian_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(script_path, backup_path)
    log(f"Backup saved: {backup_path}")

    # Validate AST
    if not is_valid_python(new_code):
        log(f"AST check FAILED — patch rejected for {process_name}")
        return False

    # Write patch
    with open(script_path, "w") as f:
        f.write(new_code)

    # Git commit the patch
    try:
        subprocess.run(
            ["git", "add", str(script_path)],
            cwd=str(CORTEX_ROOT), capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"guardian: auto-patch {script_path.name}"],
            cwd=str(CORTEX_ROOT), capture_output=True
        )
    except:
        pass

    # Restart process
    subprocess.run(["pm2", "restart", process_name], capture_output=True)
    log(f"Patch applied and {process_name} restarted")
    return True

def monitor():
    log("CORTEX Guardian starting — monitoring PM2 processes...")
    
    while True:
        for process_name, script_name in GUARDABLE.items():
            restarts = get_restart_count(process_name)
            
            if restarts >= MAX_RESTARTS_THRESHOLD:
                log(f"ALERT: {process_name} has {restarts} restarts — attempting auto-heal")
                
                error_log = get_pm2_errors(process_name)
                script_path = CORTEX_ROOT / "scripts" / script_name
                
                if not script_path.exists():
                    log(f"Script not found: {script_path}")
                    continue
                
                script_content = script_path.read_text()
                log(f"Asking Ollama to patch {script_name}...")
                
                patch = ask_ollama(error_log, script_content)
                
                if patch and len(patch) > 50:
                    success = apply_patch(script_path, patch, process_name)
                    log_healing(process_name, error_log[:500], patch[:500], success)
                    
                    if success:
                        log(f"Auto-heal SUCCESS: {process_name}")
                        # Reset restart counter
                        subprocess.run(["pm2", "reset", process_name], capture_output=True)
                    else:
                        log(f"Auto-heal FAILED: {process_name} — manual intervention needed")
                else:
                    log(f"Ollama returned no valid patch for {process_name}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()

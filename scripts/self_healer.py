import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import ast
import sys
import json
import subprocess
import psycopg2
import requests
import tempfile
import shutil
from datetime import datetime, timedelta

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))
HERMES_URL = "http://localhost:8642/v1/chat/completions"
HERMES_KEY = "cortex-local-key"
CORTEX_DIR = os.path.expanduser("~/cortex")
COOLDOWN_MINUTES = 10
MAX_ATTEMPTS = 3

# Only heal PM2-managed scripts
HEALABLE = ["doc_watcher.py", "n8n", "metabase", "task-queue"]
MONITOR_ONLY = ["gitea"]  # Binary services — monitor but dont attempt script healing

def get_conn():
    return psycopg2.connect(**DB)

def log_heal(script_name, error_detected, patch_applied, healed, attempt_count, status, notes):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO healing_log (script_name, error_detected, patch_applied, healed, attempt_count, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (script_name, error_detected[:500] if error_detected else "", patch_applied, healed, attempt_count, status, notes))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log error: {e}")

def get_attempt_count(script_name):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM healing_log
            WHERE script_name = %s
            AND timestamp > NOW() - INTERVAL '1 hour'
        """, (script_name,))
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def is_in_cooldown(script_name):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp FROM healing_log
            WHERE script_name = %s
            ORDER BY id DESC LIMIT 1
        """, (script_name,))
        row = cur.fetchone()
        conn.close()
        if row:
            last = row[0]
            if datetime.now() - last < timedelta(minutes=COOLDOWN_MINUTES):
                return True
        return False
    except:
        return False

def evolution_branch_exists(script_name):
    """Never heal while Layer D evolution branch exists for same script."""
    name = script_name.replace(".py", "")
    result = subprocess.run(
        ["git", "-C", CORTEX_DIR, "branch"],
        capture_output=True, text=True
    )
    return f"evolution/{name}" in result.stdout

def fetch_pm2_errors(service_name, lines=50):
    try:
        result = subprocess.run(
            ["pm2", "logs", service_name, "--lines", str(lines), "--nostream", "--err"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        return str(e)

def is_pm2_errored(service_name):
    try:
        result = subprocess.run(
            ["pm2", "jlist"],
            capture_output=True, text=True, timeout=5
        )
        processes = json.loads(result.stdout)
        for p in processes:
            if p.get("name") == service_name:
                status = p.get("pm2_env", {}).get("status", "")
                restarts = p.get("pm2_env", {}).get("restart_time", 0)
                if status == "errored" or restarts > 5:
                    return True, status, restarts
        return False, "online", 0
    except Exception as e:
        return False, str(e), 0

def call_hermes(prompt):
    try:
        response = requests.post(
            HERMES_URL,
            headers={"Authorization": f"Bearer {HERMES_KEY}", "Content-Type": "application/json"},
            json={"model": "hermes", "messages": [{"role": "user", "content": prompt}]},
            timeout=120
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Hermes error: {e}"

def extract_code(response):
    if "```python" in response:
        start = response.index("```python") + 9
        end = response.index("```", start)
        return response[start:end].strip()
    elif "```" in response:
        start = response.index("```") + 3
        end = response.index("```", start)
        return response[start:end].strip()
    return response.strip()

def verify_ast(code_string):
    try:
        ast.parse(code_string)
        return True, "AST valid"
    except SyntaxError as e:
        return False, f"Syntax error line {e.lineno}: {e.msg}"

def test_in_sandbox(script_path):
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", "128m",
                "--cpus", "0.5",
                "-v", f"{script_path}:/sandbox/target.py:ro",
                "python:3.12-slim",
                "python3", "-m", "py_compile", "/sandbox/target.py"
            ],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True, "Sandbox compile passed"
        return False, f"Sandbox failed: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "Sandbox timed out"
    except Exception as e:
        return False, f"Sandbox error: {e}"

def heal(script_name):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Healing: {script_name}")

    # Guardrail — cooldown
    if is_in_cooldown(script_name):
        print(f"  SKIP — in cooldown ({COOLDOWN_MINUTES}min)")
        return False

    # Guardrail — max attempts circuit breaker
    attempts = get_attempt_count(script_name)
    if attempts >= MAX_ATTEMPTS:
        print(f"  CRITICAL_UNRESOLVED — {attempts} attempts failed, disabling via PM2")
        subprocess.run(["pm2", "stop", script_name.replace(".py", "")], capture_output=True)
        log_heal(script_name, "max attempts exceeded", False, False, attempts, "CRITICAL_UNRESOLVED",
            f"Stopped after {attempts} failed attempts")
        return False

    # Guardrail — no Layer D evolution branch active
    if evolution_branch_exists(script_name):
        print(f"  SKIP — Layer D evolution branch exists for {script_name}")
        return False

    # Get PM2 service name
    service_name = script_name.replace(".py", "")
    errored, status, restarts = is_pm2_errored(service_name)

    if not errored:
        print(f"  OK — {service_name} status: {status}, restarts: {restarts}")
        return False

    print(f"  ERROR detected — status: {status}, restarts: {restarts}")

    # Fetch error logs
    error_logs = fetch_pm2_errors(service_name)
    if not error_logs.strip():
        error_logs = f"PM2 status: {status}, restarts: {restarts}"

    print(f"  Error logs: {error_logs[:100]}...")

    # Find script path
    script_path = f"{CORTEX_DIR}/scripts/{script_name}"
    if not os.path.exists(script_path):
        print(f"  SKIP — script not found: {script_path}")
        return False

    with open(script_path) as f:
        original_code = f.read()

    # Call Hermes for patch
    prompt = f"""You are a Python debugging assistant for CORTEX, a personal AI OS.
This script is failing with the following error logs. Generate a fixed version.
Return ONLY the fixed Python code in a code block, no explanations.

Script: {script_name}
Error logs:
{error_logs[:500]}

Original code:
````python
{original_code[:2000]}
```"""

    print(f"  Calling Hermes for patch...")
    response = call_hermes(prompt)

    if "Hermes error" in response:
        print(f"  ABORT — {response}")
        log_heal(script_name, error_logs, False, False, attempts+1, "hermes_failed", response)
        return False

    patched_code = extract_code(response)
    if len(patched_code) < 50:
        print(f"  ABORT — insufficient patch returned")
        log_heal(script_name, error_logs, False, False, attempts+1, "bad_patch", "Insufficient code")
        return False

    # AST check
    ast_ok, ast_msg = verify_ast(patched_code)
    print(f"  AST: {ast_msg}")
    if not ast_ok:
        log_heal(script_name, error_logs, False, False, attempts+1, "ast_failed", ast_msg)
        return False

    # Sandbox test
    tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    tmp.write(patched_code)
    tmp.close()

    sandbox_ok, sandbox_msg = test_in_sandbox(tmp.name)
    print(f"  Sandbox: {sandbox_msg}")

    if not sandbox_ok:
        os.unlink(tmp.name)
        log_heal(script_name, error_logs, False, False, attempts+1, "sandbox_failed", sandbox_msg)
        return False

    # Git branch
    branch = f"heal/repair-{script_name.replace('.py','')}-{datetime.now().strftime('%Y%m%d-%H%M')}"
    subprocess.run(["git", "-C", CORTEX_DIR, "checkout", "-b", branch], capture_output=True)

    # Backup + apply patch
    backup_path = f"{script_path}.heal.bak"
    shutil.copy2(script_path, backup_path)
    shutil.copy2(tmp.name, script_path)
    os.unlink(tmp.name)

    # Test by restarting PM2 service
    restart = subprocess.run(
        ["pm2", "restart", service_name],
        capture_output=True, text=True, timeout=15
    )

    import time
    time.sleep(5)
    still_errored, new_status, new_restarts = is_pm2_errored(service_name)

    if not still_errored:
        # Merge to master
        subprocess.run(["git", "-C", CORTEX_DIR, "add", script_path], capture_output=True)
        subprocess.run(["git", "-C", CORTEX_DIR, "commit",
            "-m", f"heal: {script_name} self-repaired via Hermes"], capture_output=True)
        subprocess.run(["git", "-C", CORTEX_DIR, "checkout", "master"], capture_output=True)
        subprocess.run(["git", "-C", CORTEX_DIR, "merge", branch], capture_output=True)
        subprocess.run(["git", "-C", CORTEX_DIR, "branch", "-d", branch], capture_output=True)
        print(f"  HEALED — {script_name} running, merged to master")
        log_heal(script_name, error_logs, True, True, attempts+1, "healed", f"Patch applied, service restored")
        return True
    else:
        # Rollback
        shutil.copy2(backup_path, script_path)
        subprocess.run(["git", "-C", CORTEX_DIR, "checkout", "master"], capture_output=True)
        subprocess.run(["git", "-C", CORTEX_DIR, "branch", "-D", branch], capture_output=True)
        subprocess.run(["pm2", "restart", service_name], capture_output=True)
        print(f"  FAILED — patch did not fix, rolled back")
        log_heal(script_name, error_logs, True, False, attempts+1, "patch_failed", "Rolled back")
        return False

def run():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] CORTEX Self-Healer starting...")
    healed = 0
    for script_name in HEALABLE:
        result = heal(script_name)
        if result:
            healed += 1
    print(f"Self-Healer complete: {healed} healed")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        heal(sys.argv[1])
    else:
        run()

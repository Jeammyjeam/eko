import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import ast
import sys
import subprocess
import psycopg2
import requests
import tempfile
import shutil
from datetime import datetime

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))
HERMES_URL = "http://localhost:8642/v1/chat/completions"
HERMES_KEY = "cortex-local-key"
CORTEX_DIR = os.path.expanduser("~/cortex")

# Guardrail — only these scripts can be evolved
WHITELIST = [
    "rag_query.py",
    "rag_critic.py",
    "dependency_scanner.py",
    "github_monitor.py",
    "rag_ingest_retry.py",
    "web_search.py",
    "skill_loader.py",
]

# Never touch these — PM2 or core infrastructure
BLACKLIST = [
    "heartbeat.py",
    "health_monitor.py",
    "orchestrator.py",
    "doc_watcher.py",
    "dashboard.py",
    "sandbox.py",
    "skills_promoter.py",
    "code_evolver.py",
]

def get_conn():
    return psycopg2.connect(**DB)

def log_evolution(script_name, branch, ast_passed, sandbox_passed, promoted, notes):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO evolution_log (script_name, branch, ast_passed, sandbox_passed, promoted, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (script_name, branch, ast_passed, sandbox_passed, promoted, notes))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log error: {e}")

def check_health():
    try:
        result = subprocess.run(
            ["python3", f"{CORTEX_DIR}/scripts/health_monitor.py"],
            capture_output=True, text=True, timeout=15
        )
        import json
        health = json.loads(result.stdout)
        ram = health["telemetry"]["ram_available_mb"]
        status = health["status"]
        if status == "RED" or ram < 1000:
            return False, f"Health {status}, RAM {ram}MB — aborting"
        return True, f"Health {status}, RAM {ram}MB"
    except Exception as e:
        return False, str(e)

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
        return False, "Sandbox timed out after 30s"
    except Exception as e:
        return False, f"Sandbox error: {e}"

def extract_code(response):
    """Extract Python code from Hermes response."""
    if "```python" in response:
        start = response.index("```python") + 9
        end = response.index("```", start)
        return response[start:end].strip()
    elif "```" in response:
        start = response.index("```") + 3
        end = response.index("```", start)
        return response[start:end].strip()
    return response.strip()

def evolve(script_name):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Evolving: {script_name}")

    # Guardrail — whitelist check
    if script_name not in WHITELIST:
        print(f"  ABORT — {script_name} not in whitelist")
        return False

    if script_name in BLACKLIST:
        print(f"  ABORT — {script_name} is blacklisted")
        return False

    script_path = f"{CORTEX_DIR}/scripts/{script_name}"
    if not os.path.exists(script_path):
        print(f"  ABORT — script not found: {script_path}")
        return False

    # Guardrail — health check
    healthy, health_msg = check_health()
    print(f"  Health: {health_msg}")
    if not healthy:
        log_evolution(script_name, "none", False, False, False, health_msg)
        return False

    # Read original
    with open(script_path) as f:
        original_code = f.read()

    print(f"  Read {len(original_code)} chars")

    # Call Hermes for improvement
    prompt = f"""You are a Python code optimizer for CORTEX, a personal AI OS.
Analyze this script and return an improved version with better error handling,
efficiency, and reliability. Keep the same functionality. Return ONLY the improved
Python code in a code block, no explanations.

Script: {script_name}

````python
{original_code[:3000]}
```"""

    print(f"  Calling Hermes...")
    response = call_hermes(prompt)

    if "Hermes error" in response:
        print(f"  ABORT — {response}")
        log_evolution(script_name, "none", False, False, False, response)
        return False

    # Extract code
    improved_code = extract_code(response)
    if len(improved_code) < 50:
        print(f"  ABORT — Hermes returned too little code")
        log_evolution(script_name, "none", False, False, False, "Insufficient code returned")
        return False

    print(f"  Hermes returned {len(improved_code)} chars")

    # Guardrail — AST check
    ast_ok, ast_msg = verify_ast(improved_code)
    print(f"  AST: {ast_msg}")
    if not ast_ok:
        log_evolution(script_name, "none", False, False, False, ast_msg)
        return False

    # Write to temp file for sandbox test
    tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    tmp.write(improved_code)
    tmp.close()

    # Guardrail — sandbox test
    sandbox_ok, sandbox_msg = test_in_sandbox(tmp.name)
    print(f"  Sandbox: {sandbox_msg}")

    if not sandbox_ok:
        os.unlink(tmp.name)
        log_evolution(script_name, "none", ast_ok, False, False, sandbox_msg)
        return False

    # Create feature branch
    branch = f"evolution/{script_name.replace('.py', '')}-{datetime.now().strftime('%Y%m%d-%H%M')}"
    try:
        subprocess.run(["git", "-C", CORTEX_DIR, "checkout", "-b", branch], capture_output=True)
        print(f"  Branch: {branch}")
    except Exception as e:
        print(f"  Branch error: {e}")
        os.unlink(tmp.name)
        return False

    # Backup original
    backup_path = f"{script_path}.bak"
    shutil.copy2(script_path, backup_path)
    print(f"  Backup: {backup_path}")

    # Write improved version
    shutil.copy2(tmp.name, script_path)
    os.unlink(tmp.name)
    print(f"  Improved version written")

    # Git commit on feature branch
    try:
        subprocess.run(["git", "-C", CORTEX_DIR, "add", script_path], capture_output=True)
        subprocess.run(["git", "-C", CORTEX_DIR, "commit", "-m",
            f"evolve: {script_name} — automated improvement via Hermes"], capture_output=True)
        print(f"  Git commit on {branch}")
    except Exception as e:
        print(f"  Git commit error: {e}")

    # Switch back to master
    subprocess.run(["git", "-C", CORTEX_DIR, "checkout", "master"], capture_output=True)

    log_evolution(script_name, branch, ast_ok, sandbox_ok, True,
        f"Improved {len(original_code)} -> {len(improved_code)} chars")

    print(f"  Evolution complete. Branch: {branch}")
    print(f"  Review with: git -C ~/cortex diff master {branch}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 code_evolver.py <script_name>")
        print(f"Whitelist: {WHITELIST}")
        sys.exit(1)
    script_name = sys.argv[1]
    evolve(script_name)

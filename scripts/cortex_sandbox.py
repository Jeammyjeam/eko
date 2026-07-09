import subprocess
import psycopg2
import uuid
import os
import ast
import shutil
from datetime import datetime
from pathlib import Path

CORTEX_ROOT = Path(__file__).resolve().parents[1]
SANDBOX_DIR = CORTEX_ROOT / "sandbox"
DB_PARAMS = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}

class CortexSandbox:
    def __init__(self, agent_name="cortex_sandbox", session_id=None):
        self.agent_name = agent_name
        self.session_id = session_id or str(uuid.uuid4())
        SANDBOX_DIR.mkdir(exist_ok=True)

    def _log_event(self, event_type, target_path, command, exit_code, stdout, stderr):
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cortex_event_log 
                (session_id, agent_name, event_type, target_path, command_payload, exit_code, stdout_capture, stderr_capture)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.session_id, self.agent_name, event_type, 
                  str(target_path) if target_path else None,
                  command[:2000] if command else None,
                  exit_code,
                  stdout[:2000] if stdout else None,
                  stderr[:2000] if stderr else None))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SANDBOX] Event log error: {e}")

    def write_file(self, filename, content):
        target = SANDBOX_DIR / filename
        target.write_text(content)
        self._log_event("WRITE_FILE", target, content[:200], 0, f"Written {len(content)} chars", "")
        return target

    def execute(self, command, timeout=10):
        try:
            result = subprocess.Popen(
                command, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(SANDBOX_DIR),
                env={**os.environ}
            )
            stdout, stderr = result.communicate(timeout=timeout)
            stdout = stdout.decode("utf-8", errors="replace")
            stderr = stderr.decode("utf-8", errors="replace")
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            result.kill()
            stdout, stderr = "", "TIMEOUT: Execution exceeded limit"
            exit_code = -1
        except Exception as e:
            stdout, stderr = "", str(e)
            exit_code = -1

        self._log_event("EXECUTE_BASH", None, command, exit_code, stdout, stderr)
        return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}

    def test_python(self, filename):
        target = SANDBOX_DIR / filename
        if not target.exists():
            return {"exit_code": -1, "stdout": "", "stderr": "File not found"}

        # AST check first
        try:
            ast.parse(target.read_text())
        except SyntaxError as e:
            self._log_event("TEST_COMPILE", target, "", 1, "", str(e))
            return {"exit_code": 1, "stdout": "", "stderr": f"SyntaxError: {e}"}

        # Run it
        result = self.execute(f"python3 {filename}", timeout=10)
        self._log_event("TEST_COMPILE", target, "", result["exit_code"], 
                       result["stdout"], result["stderr"])
        return result

    def promote_to_production(self, sandbox_filename, production_script_name):
        src = SANDBOX_DIR / sandbox_filename
        dst = CORTEX_ROOT / "scripts" / production_script_name

        if not src.exists():
            return False, "Sandbox file not found"

        # Final AST check
        try:
            ast.parse(src.read_text())
        except SyntaxError as e:
            return False, f"AST failed: {e}"

        # Backup production file
        if dst.exists():
            backup = str(dst) + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(dst, backup)

        shutil.copy2(src, dst)
        self._log_event("PROMOTE", dst, sandbox_filename, 0, f"Promoted to {dst}", "")
        return True, f"Promoted to {dst}"

    def cleanup(self):
        for f in SANDBOX_DIR.iterdir():
            if f.is_file():
                f.unlink()
        self._log_event("CLEANUP", SANDBOX_DIR, "", 0, "Sandbox cleared", "")

if __name__ == "__main__":
    print("Testing CortexSandbox...")
    sb = CortexSandbox(agent_name="test")
    
    # Write a test script
    sb.write_file("test_script.py", "print('Hello from CORTEX sandbox!')")
    
    # Test it
    result = sb.test_python("test_script.py")
    print(f"Exit code: {result['exit_code']}")
    print(f"Output: {result['stdout'].strip()}")
    
    # Check event log
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT event_type, exit_code, stdout_capture FROM cortex_event_log ORDER BY id DESC LIMIT 3")
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        print(f"Event: {row[0]} | Exit: {row[1]} | Output: {row[2][:50] if row[2] else ''}")
    
    sb.cleanup()
    print("Sandbox test complete.")

import os
import uuid
import json
import ast
import shutil
import psycopg2
import requests
from pathlib import Path
from datetime import datetime
from google import genai

CORTEX_ROOT = Path(__file__).resolve().parents[1]
DB_PARAMS = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

class CortexCrossSession:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.session_id = str(uuid.uuid4())

    def _log(self, agent, event_type, payload, exit_code=0, stdout="", stderr=""):
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cortex_event_log
                (session_id, agent_name, event_type, command_payload, exit_code, stdout_capture, stderr_capture)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (self.session_id, agent, event_type,
                  str(payload)[:2000], exit_code,
                  str(stdout)[:1000], str(stderr)[:1000]))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[LOG ERROR] {e}")

    def _gemini_architect(self, script_path, objective, original_code):
        print("-> Tunnel A (Gemini) — generating patch...")
        prompt = f"""You are the Principal Systems Architect for CORTEX AI OS.
Target: {script_path}
Objective: {objective}

Current code:
{original_code[:3000]}

Provide ONLY the complete updated Python script. No markdown, no explanation."""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            code = response.text.replace("```python", "").replace("```", "").strip()
            self._log("Gemini-Architect", "PROPOSE_PATCH", objective, stdout=code[:500])
            return code
        except Exception as e:
            self._log("Gemini-Architect", "PROPOSE_PATCH", objective, exit_code=1, stderr=str(e))
            return None

    def _qwen_auditor(self, proposed_code):
        print("-> Tunnel B (Qwen) — auditing patch...")
        prompt = f"""You are the CORTEX Local Code Auditor.
Review this Python code for syntax errors, memory leaks, or 8GB RAM issues.

{proposed_code[:3000]}

If safe, reply exactly: APPROVED
If flawed, reply: REJECTED: [brief reason]"""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": "qwen2.5-coder:1.5b", "prompt": prompt,
                      "stream": False, "options": {"num_ctx": 16384}},
                timeout=60
            )
            result = response.json()["response"].strip()
            approved = "APPROVED" in result
            self._log("Qwen-Auditor", "AUDIT_APPROVE" if approved else "AUDIT_REJECT",
                     result, exit_code=0 if approved else 1)
            return approved, result
        except Exception as e:
            return False, str(e)

    def run(self, script_name, objective):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] CORTEX Cross-Session")
        print(f"Session: {self.session_id[:8]}...")
        print(f"Target: {script_name} | Objective: {objective}\n")

        script_path = CORTEX_ROOT / "scripts" / script_name
        if not script_path.exists():
            print(f"Script not found: {script_path}")
            return {"status": "ERROR", "reason": "script not found"}

        original_code = script_path.read_text()

        # Phase 1 — Gemini architects
        proposed_code = self._gemini_architect(str(script_path), objective, original_code)
        if not proposed_code:
            return {"status": "FAILED", "reason": "Gemini returned no patch"}

        # AST check
        try:
            ast.parse(proposed_code)
        except SyntaxError as e:
            print(f"  AST FAILED: {e}")
            self._log("AST-Gate", "AST_FAIL", str(e), exit_code=1)
            return {"status": "FAILED", "reason": f"AST failed: {e}"}

        # Phase 2 — Qwen audits
        approved, audit_result = self._qwen_auditor(proposed_code)

        if approved:
            print(f"\n[✓] Consensus reached — applying patch")
            backup = str(script_path) + f".cross_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            shutil.copy2(script_path, backup)
            script_path.write_text(proposed_code)
            print(f"  Backup: {backup}")
            print(f"  Patch applied to: {script_path.name}")
            return {"status": "SUCCESS", "session_id": self.session_id, "backup": backup}
        else:
            print(f"\n[✗] Qwen rejected patch: {audit_result[:100]}")
            return {"status": "REJECTED", "reason": audit_result}

if __name__ == "__main__":
    import sys
    script = sys.argv[1] if len(sys.argv) > 1 else "web_search.py"
    objective = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "add error handling for network timeouts"
    session = CortexCrossSession()
    result = session.run(script, objective)
    print(f"\nResult: {json.dumps(result, indent=2)}")

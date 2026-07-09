import paramiko
import json
import uuid
import psycopg2
import sys
import os
from pathlib import Path
from datetime import datetime

CORTEX_ROOT = Path(__file__).resolve().parents[1]
DB_PARAMS = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}

class CortexWebAgent:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 22
        self.username = "jjeam"
        self.key_path = str(Path.home() / ".ssh" / "cortex_host_key")
        self.worker_path = "C:/Users/jjeam/cortex_browser_worker.py"

    def _log_event(self, session_id, event_type, command, exit_code, stdout, stderr):
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cortex_event_log
                (session_id, agent_name, event_type, target_path, command_payload, exit_code, stdout_capture, stderr_capture)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_id, "cortex_web_agent", event_type,
                  self.worker_path, command[:1000] if command else None,
                  exit_code,
                  stdout[:2000] if stdout else None,
                  stderr[:2000] if stderr else None))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WEB AGENT] Log error: {e}")

    def _deploy_worker(self, objective):
        """Write browser_worker.py to Windows via SFTP"""
        worker_code = f'''import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def run():
    objective = """{objective}"""
    results = {{"objective": objective, "steps": [], "summary": ""}}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        try:
            # Navigate based on objective
            if "github" in objective.lower():
                query = objective.replace("search github for", "").strip()
                await page.goto(f"https://github.com/search?q={{query}}&type=repositories", 
                               wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
                repos = await page.query_selector_all("[data-testid=results-list] .search-title")
                for r in repos[:5]:
                    text = await r.inner_text()
                    results["steps"].append({{"action": "found_repo", "value": text.strip()}})
                    
            elif "duckduckgo" in objective.lower() or "search" in objective.lower():
                query = objective.replace("search for", "").replace("duckduckgo", "").strip()
                await page.goto("https://duckduckgo.com", wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_selector("input[name=q]", timeout=5000)
                await page.type("input[name=q]", query, delay=80)
                await page.press("input[name=q]", "Enter")
                await page.wait_for_timeout(2000)
                items = await page.query_selector_all("article h2")
                for item in items[:5]:
                    text = await item.inner_text()
                    if text.strip():
                        results["steps"].append({{"action": "search_result", "value": text.strip()}})
                        
            else:
                await page.goto(objective if objective.startswith("http") else f"https://{{objective}}", 
                               wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(1500)
                text = await page.inner_text("body")
                clean = " ".join(text.split())[:1500]
                results["steps"].append({{"action": "page_content", "value": clean}})
            
            results["summary"] = f"Completed {{len(results['steps'])}} steps"
            
        except Exception as e:
            results["error"] = str(e)
        finally:
            await browser.close()
    
    print(json.dumps(results))

asyncio.run(run())
'''
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            pkey = paramiko.Ed25519Key.from_private_key_file(self.key_path)
            ssh.connect(self.host, port=self.port, username=self.username, pkey=pkey, timeout=10)
            sftp = ssh.open_sftp()
            with sftp.open(self.worker_path, "w") as f:
                f.write(worker_code)
            sftp.close()
            ssh.close()
            return True
        except Exception as e:
            print(f"Deploy error: {e}")
            return False

    def execute(self, objective):
        session_id = str(uuid.uuid4())
        print(f"[WEB AGENT] Objective: {objective}")

        # Deploy worker to Windows
        if not self._deploy_worker(objective):
            return {"error": "Failed to deploy browser worker"}

        # Execute via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            pkey = paramiko.Ed25519Key.from_private_key_file(self.key_path)
            ssh.connect(self.host, port=self.port, username=self.username, pkey=pkey, timeout=10)
            stdin, stdout, stderr = ssh.exec_command(
                f"python {self.worker_path}", timeout=60
            )
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()
            ssh.close()

            self._log_event(session_id, "BROWSER_ACTION", objective, 0, output, error)

            try:
                return json.loads(output)
            except:
                return {"output": output, "error": error}

        except Exception as e:
            self._log_event(session_id, "BROWSER_ACTION", objective, -1, "", str(e))
            return {"error": str(e)}

if __name__ == "__main__":
    agent = CortexWebAgent()
    objective = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "search for open source AI agents 2026"
    result = agent.execute(objective)
    print(json.dumps(result, indent=2))

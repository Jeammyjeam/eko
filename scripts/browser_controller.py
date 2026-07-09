import paramiko
import json
import sys
import os
sys.path.insert(0, '/home/junaid-eko/cortex/scripts')
from telemetry import log_action, Timer
from pathlib import Path

class CortexBrowserBridge:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 22
        self.username = "jjeam"
        self.key_path = str(Path.home() / ".ssh" / "cortex_host_key")

    def _ssh_exec(self, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            pkey = paramiko.Ed25519Key.from_private_key_file(self.key_path)
            ssh.connect(self.host, port=self.port, username=self.username, pkey=pkey, timeout=30)
            stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()
            ssh.close()
            return output, error
        except Exception as e:
            return "", str(e)

    def _write_and_run(self, script_content):
        """Write script to Windows temp file and execute it"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            pkey = paramiko.Ed25519Key.from_private_key_file(self.key_path)
            ssh.connect(self.host, port=self.port, username=self.username, pkey=pkey, timeout=30)
            
            # Write script to Windows temp file via SFTP
            sftp = ssh.open_sftp()
            with sftp.open("C:/Users/jjeam/cortex_tmp.py", "w") as f:
                f.write(script_content)
            sftp.close()
            
            # Execute the temp file
            stdin, stdout, stderr = ssh.exec_command("python C:/Users/jjeam/cortex_tmp.py", timeout=60)
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()
            ssh.close()
            return output, error
        except Exception as e:
            return "", str(e)

    def search_google(self, query):
        t = Timer()
        script = f"""import asyncio, json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://duckduckgo.com", wait_until="domcontentloaded")
        await page.wait_for_selector("input[name='q']")
        await page.type("input[name='q']", "{query}", delay=80)
        await page.press("input[name='q']", "Enter")
        await page.wait_for_timeout(2000)
        # Try multiple selectors for Google results
        titles = []
        for selector in ["h3", ".LC20lb", ".DKV0Md", "[data-ved] h3"]:
            results = await page.query_selector_all(selector)
            for r in results[:5]:
                text = await r.inner_text()
                if text.strip() and len(text.strip()) > 5:
                    titles.append(text.strip())
            if titles:
                break
        await browser.close()
        print(json.dumps({{"query": "{query}", "results": titles}}))

asyncio.run(run())
"""
        output, error = self._write_and_run(script)
        try:
            data = json.loads(output)
            log_action("browser_controller", f"google_search:{query[:30]}", "playwright_windows", t.elapsed_ms(), "SUCCESS")
            return data
        except:
            log_action("browser_controller", f"google_search:{query[:30]}", "playwright_windows", t.elapsed_ms(), "FAILED", error=error)
            return {"error": error or output}

    def get_page_text(self, url):
        t = Timer()
        script = f"""import asyncio, json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("{url}", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        text = await page.inner_text("body")
        clean = " ".join(text.split())[:2000]
        await browser.close()
        print(json.dumps({{"url": "{url}", "content": clean}}))

asyncio.run(run())
"""
        output, error = self._write_and_run(script)
        try:
            data = json.loads(output)
            log_action("browser_controller", f"get_page:{url[:30]}", "playwright_windows", t.elapsed_ms(), "SUCCESS")
            return data
        except:
            log_action("browser_controller", f"get_page:{url[:30]}", "playwright_windows", t.elapsed_ms(), "FAILED", error=error)
            return {"error": error or output}

if __name__ == "__main__":
    bridge = CortexBrowserBridge()
    action = sys.argv[1] if len(sys.argv) > 1 else "search"
    query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "latest AI agents 2026"
    
    if action == "search":
        print("Searching Google...")
        result = bridge.search_google(query)
        print(json.dumps(result, indent=2))
    elif action == "page":
        print(f"Getting page: {query}")
        result = bridge.get_page_text(query)
        print(json.dumps(result, indent=2))

import paramiko
import json
import sys
import os
sys.path.insert(0, '/home/junaid-eko/cortex/scripts')
from telemetry import log_action, Timer
from pathlib import Path

class WindowsGateway:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 22
        self.username = "jjeam"
        self.key_path = str(Path.home() / ".ssh" / "cortex_host_key")

    def execute(self, action):
        WHITELIST = {
            "get_stats": "powershell.exe -NoProfile -Command \"Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory | ConvertTo-Json\"",
            "get_cpu": "powershell.exe -NoProfile -Command \"Get-CimInstance Win32_Processor | Select-Object LoadPercentage | ConvertTo-Json\"",
            "get_disk": "powershell.exe -NoProfile -Command \"Get-PSDrive C | Select-Object Used,Free | ConvertTo-Json\"",
            "get_uptime": "powershell.exe -NoProfile -Command \"((Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime).ToString()\"",
            "get_processes": "powershell.exe -NoProfile -Command \"Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name,CPU | ConvertTo-Json\"",
            "get_drives": "wmic logicaldisk get size,freespace,caption /value",
        }

        if action not in WHITELIST:
            return {"error": f"Action '{action}' not whitelisted. Allowed: {list(WHITELIST.keys())}"}

        t = Timer()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            pkey = paramiko.Ed25519Key.from_private_key_file(self.key_path)
            ssh.connect(self.host, port=self.port, username=self.username, pkey=pkey, timeout=10)
            stdin, stdout, stderr = ssh.exec_command(WHITELIST[action])
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()
            ssh.close()

            log_action("windows_gateway", action, "windows_ssh", t.elapsed_ms(), "SUCCESS")

            try:
                return json.loads(output)
            except:
                return {"output": output, "error": error}

        except Exception as e:
            log_action("windows_gateway", action, "windows_ssh", t.elapsed_ms(), "FAILED", error=str(e))
            return {"error": str(e)}

if __name__ == "__main__":
    gw = WindowsGateway()
    action = sys.argv[1] if len(sys.argv) > 1 else "get_stats"
    print(f"Running: {action}")
    result = gw.execute(action)
    print(json.dumps(result, indent=2))

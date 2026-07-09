import subprocess
import shutil
import psutil
import json
from datetime import datetime

def check_service(name, check_cmd):
    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def get_health():
    # RAM
    ram = psutil.virtual_memory()
    ram_total = round(ram.total / 1024**2)
    ram_available = round(ram.available / 1024**2)
    ram_used_pct = ram.percent

    # Disk
    disk = shutil.disk_usage("/")
    disk_free_gb = round(disk.free / 1024**3, 2)
    disk_used_pct = round((disk.used / disk.total) * 100, 1)

    # CPU
    cpu_pct = psutil.cpu_percent(interval=1)

    # Services
    services = {
        "postgresql": check_service("postgresql", ["pg_isready", "-h", "127.0.0.1", "-U", "cortex"]),
        "n8n":        check_service("n8n",        ["pgrep", "-x", "node"]),
        "hermes":     check_service("hermes",     ["curl", "-sf", "http://localhost:8642/health"]),
        "gitea":      check_service("gitea",      ["curl", "-sf", "http://localhost:3000"]),
        "streamlit":  check_service("streamlit",  ["pgrep", "-f", "streamlit"]),
        "docker":     check_service("docker",     ["pgrep", "-x", "dockerd"]),
        "ssh":        check_service("ssh",        ["pgrep", "-x", "sshd"]),
    }

    # Status
    status = "GREEN"
    directives = []

    if ram_available < 400:
        status = "RED"
        directives.append("Memory critical — terminate background agent tasks immediately")
    elif ram_available < 1000:
        status = "YELLOW"
        directives.append("Memory pressure — restrict reasoning steps")

    if disk_free_gb < 5:
        status = "RED"
        directives.append("Disk critical — freeze RAG embedding tasks")
    elif disk_free_gb < 20:
        if status != "RED":
            status = "YELLOW"
        directives.append("Disk low — monitor storage usage")

    if cpu_pct > 90:
        if status != "RED":
            status = "YELLOW"
        directives.append("CPU high — defer heavy tasks")

    # Only these services are critical — streamlit/docker are optional UI/sandbox tools
    CRITICAL_SERVICES = {"postgresql", "n8n", "hermes", "gitea", "ssh"}
    dead_services = [s for s, alive in services.items() if not alive]
    dead_critical = [s for s in dead_services if s in CRITICAL_SERVICES]
    dead_optional = [s for s in dead_services if s not in CRITICAL_SERVICES]
    if dead_critical:
        if status == "GREEN":
            status = "YELLOW"
        directives.append(f"Dead critical services: {', '.join(dead_critical)}")
    if dead_optional:
        directives.append(f"Dead optional services (non-blocking): {', '.join(dead_optional)}")

    return {
        "status": status,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "telemetry": {
            "ram_total_mb": ram_total,
            "ram_available_mb": ram_available,
            "ram_used_pct": ram_used_pct,
            "disk_free_gb": disk_free_gb,
            "disk_used_pct": disk_used_pct,
            "cpu_pct": cpu_pct,
        },
        "services": services,
        "directives": directives
    }

if __name__ == "__main__":
    result = get_health()
    print(json.dumps(result, indent=2))

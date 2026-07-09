import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import json
import psutil
import platform
import psycopg2
from datetime import datetime

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))

def get_profile():
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "os": platform.system(),
        "os_version": platform.version()[:50],
        "cpu_cores": psutil.cpu_count(),
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "ram_total_mb": vm.total // 1024**2,
        "ram_available_mb": vm.available // 1024**2,
        "disk_total_gb": disk.total // 1024**3,
        "disk_free_gb": disk.free // 1024**3,
        "disk_used_pct": round(disk.percent, 1),
        "profiled_at": datetime.now().isoformat()
    }

def save_profile(profile):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_profile (
            id SERIAL PRIMARY KEY,
            os TEXT,
            os_version TEXT,
            cpu_cores INTEGER,
            cpu_cores_physical INTEGER,
            ram_total_mb INTEGER,
            ram_available_mb INTEGER,
            disk_total_gb INTEGER,
            disk_free_gb INTEGER,
            disk_used_pct REAL,
            profiled_at TIMESTAMP DEFAULT NOW()
        )
    """)
    # Keep only latest — delete old entries
    cur.execute("DELETE FROM system_profile")
    cur.execute("""
        INSERT INTO system_profile (
            os, os_version, cpu_cores, cpu_cores_physical,
            ram_total_mb, ram_available_mb, disk_total_gb,
            disk_free_gb, disk_used_pct, profiled_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        profile["os"], profile["os_version"],
        profile["cpu_cores"], profile["cpu_cores_physical"],
        profile["ram_total_mb"], profile["ram_available_mb"],
        profile["disk_total_gb"], profile["disk_free_gb"],
        profile["disk_used_pct"], profile["profiled_at"]
    ))
    conn.commit()
    cur.close()
    conn.close()

def load_profile():
    """Load current system profile from DB."""
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM system_profile ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        cols = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return dict(zip(cols, row)) if row else None
    except Exception:
        return None

def check_install_feasibility(ram_mb_required, disk_mb_required=500):
    """Check if system can handle installing a tool."""
    profile = load_profile()
    if not profile:
        # No profile yet — run fresh
        profile = get_profile()
    issues = []
    if profile["ram_available_mb"] < ram_mb_required:
        issues.append(f"Insufficient RAM: need {ram_mb_required}MB, have {profile['ram_available_mb']}MB available")
    if profile["disk_free_gb"] < (disk_mb_required / 1024):
        issues.append(f"Insufficient disk: need {disk_mb_required}MB, have {profile['disk_free_gb']}GB free")
    return len(issues) == 0, issues

if __name__ == "__main__":
    profile = get_profile()
    save_profile(profile)
    print(json.dumps(profile, indent=2))

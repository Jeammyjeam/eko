import time
import subprocess
import psutil
from datetime import datetime

CRITICAL_RAM_MB = 1200
RECOVERY_RAM_MB = 1200
HEAVY_PROCESSES = ["metabase", "gitea"]
CHECK_INTERVAL = 30

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def pm2_action(action, process):
    try:
        subprocess.run(f"pm2 {action} {process}", shell=True, check=True, 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"PM2 {action}: {process}")
    except:
        pass

def get_free_ram():
    return psutil.virtual_memory().available // (1024 * 1024)

def main():
    log("CORTEX Telemetry Throttler starting...")
    throttled = False
    
    while True:
        free_ram = get_free_ram()
        
        if free_ram < CRITICAL_RAM_MB and not throttled:
            log(f"ALERT: Free RAM {free_ram}MB < {CRITICAL_RAM_MB}MB — throttling heavy processes")
            for proc in HEAVY_PROCESSES:
                pm2_action("stop", proc)
            throttled = True
            
        elif free_ram >= RECOVERY_RAM_MB and throttled:
            log(f"RECOVERY: Free RAM {free_ram}MB >= {RECOVERY_RAM_MB}MB — restoring full stack")
            for proc in HEAVY_PROCESSES:
                pm2_action("start", proc)
            throttled = False
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

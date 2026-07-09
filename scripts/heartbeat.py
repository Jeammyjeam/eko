import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

import json
import os
import time
import re
import subprocess
import psycopg2
import requests
from datetime import datetime

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))
HERMES_URL = "http://localhost:8642/v1/chat/completions"
HERMES_KEY = "cortex-local-key"
SKILLS_DIR = os.path.join(os.path.expanduser("~/cortex"), "skills")
MAX_CONSECUTIVE = 5
HEARTBEAT_FILE = os.path.expanduser("~/cortex/HEARTBEAT.md")

# Only core skills can auto-execute
SAFE_SKILLS = ["web_search", "rag_search", "health_check", "code_sandbox"]

def get_health():
    try:
        result = subprocess.run(
            ["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "health_monitor.py")],
            capture_output=True, text=True, timeout=15
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"status": "RED", "directives": [f"Health check failed: {e}"], "telemetry": {}, "services": {}}

def get_consecutive_count():
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("SELECT consecutive_actions FROM heartbeat_log ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except:
        return 0

def get_last_action():
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("SELECT action_taken FROM heartbeat_log ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return row[0] if row else ""
    except:
        return ""

def log_result(health_status, action_taken, result, consecutive):
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO heartbeat_log (health_status, action_taken, result, consecutive_actions) VALUES (%s, %s, %s, %s)",
            (health_status, action_taken, result, consecutive)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log error: {e}")

def call_hermes(prompt):
    try:
        response = requests.post(
            HERMES_URL,
            headers={"Authorization": f"Bearer {HERMES_KEY}", "Content-Type": "application/json"},
            json={"model": "hermes", "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Hermes error: {e}"

def load_skill(skill_name):
    path = os.path.join(SKILLS_DIR, "core", f"{skill_name}.md")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None

def extract_command(skill_content, task):
    lines = skill_content.split("\n")
    for i, line in enumerate(lines):
        if "## Command" in line and i + 1 < len(lines):
            cmd = lines[i + 1].strip().strip("`")
            return cmd
    return None

def execute_skill(skill_name, task):
    if skill_name not in SAFE_SKILLS:
        return f"Skill {skill_name} not in safe whitelist — requires manual approval"
    
    skill_content = load_skill(skill_name)
    if not skill_content:
        return f"Skill {skill_name} not found"

    if skill_name == "web_search":
        result = subprocess.run(
            ["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "web_search.py"), task],
            capture_output=True, text=True, timeout=30,
            env={**os.environ}
        )
        return result.stdout[:500] or result.stderr[:200]

    elif skill_name == "rag_search":
        result = subprocess.run(
            ["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "rag_query.py"), task],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "")}
        )
        return result.stdout[:500] or result.stderr[:200]

    elif skill_name == "health_check":
        result = subprocess.run(
            ["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "health_monitor.py")],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout[:500]

    return f"No executor for {skill_name}"

def pick_skill(task_summary):
    task_lower = task_summary.lower()
    if any(w in task_lower for w in ["new repos", "repo", "capabilit"]):
        return "rag_search"
    elif any(w in task_lower for w in ["search", "latest", "news"]):
        return "web_search"
    elif any(w in task_lower for w in ["health", "service", "ram"]):
        return "health_check"
    return None

def read_heartbeat():
    try:
        with open(HEARTBEAT_FILE, "r") as f:
            return f.read()
    except:
        return "HEARTBEAT.md not found"

def check_new_repos():
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM repos WHERE discovered_at > NOW() - INTERVAL '30 minutes'")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def check_uncapped_repos():
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM repos r LEFT JOIN capabilities c ON r.id = c.repo_id WHERE c.id IS NULL")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def check_unskilted_repos(limit=5):
    """Find capped repos with no synthesized skill yet."""
    import yaml
    skilled = set()
    skills_dir = os.path.expanduser("~/cortex/skills")
    for category in ["core", "custom", "experimental"]:
        path = os.path.join(skills_dir, category)
        if not os.path.exists(path):
            continue
        for fname in os.listdir(path):
            if not fname.endswith(".md"):
                continue
            with open(os.path.join(path, fname)) as f:
                raw = f.read()
            if raw.startswith("---"):
                try:
                    end = raw.index("---", 3)
                    meta = yaml.safe_load(raw[3:end])
                    src = meta.get("source_repo")
                    if src:
                        skilled.add(src.lower())
                except Exception:
                    pass
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("""
            SELECT r.name FROM repos r
            JOIN capabilities c ON r.id = c.repo_id
            WHERE c.language NOT IN ('Unknown')
            AND c.category NOT IN ('other')
            AND (c.synthesis_status IS NULL)
            ORDER BY r.name
        """)
        rows = cur.fetchall()
        conn.close()
        return [name for (name,) in rows if name.lower() not in skilled][:limit]
    except Exception as e:
        print(f"check_unskilted_repos error: {e}")
        return []

def check_experimental_skills():
    path = os.path.expanduser("~/cortex/skills/experimental")
    if not os.path.exists(path):
        return 0
    return len([f for f in os.listdir(path) if f.endswith(".md")])

def run():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] CORTEX Heartbeat starting...")

    health = get_health()
    status = health["status"]
    print(f"Health: {status}")

    if status == "RED":
        log_result(status, "ABORTED", "Health RED — no actions taken", 0)
        print("RED status — aborting")
        return

    consecutive = get_consecutive_count()
    # Reset counter if last action was PAUSED — each cycle is a fresh window
    if consecutive >= MAX_CONSECUTIVE:
        last_action = get_last_action()
        if last_action == "PAUSED":
            consecutive = 0
        else:
            log_result(status, "PAUSED", f"Max consecutive actions reached — awaiting /approve", consecutive)
            print(f"Max consecutive actions ({consecutive}) — pausing")
            return

    new_repos = check_new_repos()
    uncapped = check_uncapped_repos()
    experimental = check_experimental_skills()

    tasks = []
    if new_repos > 0:
        tasks.append(f"{new_repos} new repos discovered in last 30 minutes")
    if uncapped > 0:
        tasks.append(f"{uncapped} repos have no capabilities mapped yet")
    if experimental > 0:
        tasks.append(f"{experimental} experimental skills awaiting promotion")

    # Check unskilted repos and add to task list
    unskilted = check_unskilted_repos(limit=5)
    if unskilted:
        tasks.append(f"{len(unskilted)} repos queued for skill synthesis: {', '.join(unskilted)}")

    if not tasks:
        log_result(status, "HEARTBEAT_OK", "No tasks — all clear", 0)
        print("HEARTBEAT_OK — no action needed")
        return

    task_summary = ", ".join(tasks)
    print(f"Tasks found: {task_summary}")

    # Run goal engine tick
    print("Running goal engine...")
    goal = subprocess.run(
        ["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "goal_engine.py"), "run"],
        capture_output=True, text=True, timeout=120
    )
    if goal.stdout:
        print(goal.stdout.strip()[:300])

    # Run self-healer
    print("Running self-healer...")
    healer = subprocess.run(
        ["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "self_healer.py")],
        capture_output=True, text=True, timeout=120
    )
    if healer.stdout:
        print(healer.stdout.strip()[:300])

    # Run skills promoter if experimental skills found
    if experimental > 0:
        print(f"Running skills promoter for {experimental} experimental skill(s)")
        result = subprocess.run(
            ["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "skills_promoter.py")],
            capture_output=True, text=True, timeout=180
        )
        print(result.stdout[:300] if result.stdout else "No output")

    # Check RAM before synthesis — skip if system is under pressure
    import psutil
    available_mb = psutil.virtual_memory().available // 1024**2
    MIN_RAM_FOR_SYNTHESIS = 800  # MB — Hermes needs headroom
    if available_mb < MIN_RAM_FOR_SYNTHESIS:
        print(f"RAM low ({available_mb}MB available) — skipping synthesis this cycle")
        log_result(status, "RAM_THROTTLE", f"Synthesis skipped — only {available_mb}MB RAM available", consecutive)
        return

    # Synthesize skills from unskilted repos (up to 5 per cycle)
    if unskilted:
        print(f"Synthesizing skills for {len(unskilted)} unskilted repo(s): {unskilted}")
        synthesizer = os.path.join(os.path.expanduser("~/cortex"), "scripts", "skill_synthesizer.py")
        for repo_name in unskilted:
            try:
                result = subprocess.run(
                    ["python3", synthesizer, repo_name],
                    capture_output=True, text=True, timeout=120
                )
                output = result.stdout.strip()
                print(f"  {repo_name}: {output[:100]}")
                time.sleep(8)  # Respect Gemini RPM limit between calls
            except Exception as e:
                print(f"  {repo_name}: synthesis error — {e}")

    # Pick and execute skill
    skill_name = pick_skill(task_summary)
    skill_result = None

    if skill_name:
        print(f"Executing skill: {skill_name}")
        skill_result = execute_skill(skill_name, task_summary)
        print(f"Skill result: {skill_result[:100] if skill_result else None}")

    # Log result
    action = f"skill:{skill_name} | {task_summary}" if skill_name else task_summary
    result = skill_result[:500] if skill_result else "No skill executed"
    log_result(status, action, result, consecutive + 1)
    print("Heartbeat complete")

if __name__ == "__main__":
    run()

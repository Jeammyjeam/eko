import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import sys
import json
import subprocess
import psycopg2
import requests
from datetime import datetime

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))
HERMES_URL = "http://localhost:8642/v1/chat/completions"
HERMES_KEY = "cortex-local-key"
CORTEX_DIR = os.path.expanduser("~/cortex")
SKILLS_DIR = f"{CORTEX_DIR}/skills"
MAX_SUBTASKS = 5
MAX_RETRIES = 2
MAX_ACTIVE_GOALS = 3

def get_conn():
    return psycopg2.connect(**DB)

def get_active_skills():
    """Load all active skill names from skills directory."""
    skills = []
    for category in ["core", "custom"]:
        path = os.path.join(SKILLS_DIR, category)
        if not os.path.exists(path):
            continue
        for fname in os.listdir(path):
            if fname.endswith(".md"):
                skills.append(fname.replace(".md", ""))
    return skills

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

def add_goal(goal_name, description=""):
    """Add a new goal to PostgreSQL."""
    conn = get_conn()
    cur = conn.cursor()
    # Guardrail — max 3 active goals
    cur.execute("SELECT COUNT(*) FROM cortex_goals WHERE status IN ('PENDING', 'ACTIVE')")
    active = cur.fetchone()[0]
    if active >= MAX_ACTIVE_GOALS:
        conn.close()
        print(f"  ABORT — max active goals ({MAX_ACTIVE_GOALS}) reached")
        return None
    cur.execute(
        "INSERT INTO cortex_goals (goal_name, description, status) VALUES (%s, %s, 'PENDING') RETURNING id",
        (goal_name, description)
    )
    goal_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    print(f"  Goal created: [{goal_id}] {goal_name}")
    return goal_id

def decompose_goal(goal_id, goal_name, description):
    """Use Hermes to break goal into subtasks."""
    active_skills = get_active_skills()
    prompt = f"""You are CORTEX goal planner. Break this goal into subtasks.
Available skills: {", ".join(active_skills)}

Goal: {goal_name}
Description: {description}

Return a JSON array of subtasks (max {MAX_SUBTASKS}). Each subtask must have:
- "name": short description
- "skill": must be one of the available skills exactly
- "order": execution order (1, 2, 3...)

Return ONLY valid JSON array, no explanation. Example:
[{{"name": "search for X", "skill": "web_search", "order": 1}}]"""

    response = call_hermes(prompt)
    if "Hermes error" in response:
        print(f"  Hermes error: {response}")
        return []

    # Extract JSON
    try:
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.index("```") + 3
            end = response.index("```", start)
            response = response[start:end].strip()
        subtasks = json.loads(response)
    except Exception as e:
        print(f"  JSON parse error: {e}")
        return []

    # Validate and cap
    active_skills = get_active_skills()
    valid = []
    for s in subtasks[:MAX_SUBTASKS]:
        skill = s.get("skill", "")
        if skill not in active_skills:
            print(f"  SKIP subtask — unknown skill: {skill}")
            continue
        valid.append(s)

    return valid

def save_subtasks(goal_id, subtasks):
    """Save subtasks to PostgreSQL."""
    conn = get_conn()
    cur = conn.cursor()
    for s in subtasks:
        cur.execute("""
            INSERT INTO cortex_subtasks (goal_id, subtask_name, assigned_skill, execution_order, status)
            VALUES (%s, %s, %s, %s, 'PENDING')
        """, (goal_id, s["name"], s["skill"], s["order"]))
    conn.commit()
    conn.close()
    print(f"  Saved {len(subtasks)} subtasks")

def execute_subtask(subtask):
    """Execute a subtask using the assigned skill via orchestrator."""
    skill = subtask[3]  # assigned_skill
    task_name = subtask[2]  # subtask_name
    print(f"    Executing: [{skill}] {task_name}")
    try:
        result = subprocess.run(
            ["python3", f"{CORTEX_DIR}/scripts/orchestrator.py", task_name],
            capture_output=True, text=True, timeout=60,
            env={**os.environ}
        )
        output = result.stdout[:500] if result.stdout else result.stderr[:200]
        return True, output
    except subprocess.TimeoutExpired:
        return False, "Subtask timed out"
    except Exception as e:
        return False, str(e)

def update_subtask(subtask_id, status, output="", retry_count=0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE cortex_subtasks
        SET status=%s, output_data=%s, retry_count=%s, updated_at=NOW()
        WHERE id=%s
    """, (status, output[:500], retry_count, subtask_id))
    conn.commit()
    conn.close()

def update_goal(goal_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE cortex_goals SET status=%s, updated_at=NOW() WHERE id=%s
    """, (status, goal_id))
    conn.commit()
    conn.close()

def process_active_goals():
    """Main tick — process one step of each active goal."""
    conn = get_conn()
    cur = conn.cursor()

    # Get PENDING goals and activate them
    cur.execute("SELECT id, goal_name, description FROM cortex_goals WHERE status='PENDING' ORDER BY id LIMIT 3")
    pending = cur.fetchall()
    conn.close()

    for goal_id, goal_name, description in pending:
        print(f"\n  Activating goal [{goal_id}]: {goal_name}")
        subtasks = decompose_goal(goal_id, goal_name, description or "")
        if not subtasks:
            update_goal(goal_id, "FAILED")
            print(f"  Goal FAILED — could not decompose")
            continue
        save_subtasks(goal_id, subtasks)
        update_goal(goal_id, "ACTIVE")

    # Process ACTIVE goals
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, goal_name FROM cortex_goals WHERE status='ACTIVE' ORDER BY id")
    active_goals = cur.fetchall()
    conn.close()

    for goal_id, goal_name in active_goals:
        print(f"\n  Processing goal [{goal_id}]: {goal_name}")
        conn = get_conn()
        cur = conn.cursor()

        # Get next PENDING subtask
        cur.execute("""
            SELECT id, goal_id, subtask_name, assigned_skill, execution_order, retry_count
            FROM cortex_subtasks
            WHERE goal_id=%s AND status='PENDING'
            ORDER BY execution_order LIMIT 1
        """, (goal_id,))
        subtask = cur.fetchone()
        conn.close()

        if not subtask:
            # Check if all subtasks completed
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM cortex_subtasks
                WHERE goal_id=%s AND status != 'SUCCESS'
            """, (goal_id,))
            remaining = cur.fetchone()[0]
            conn.close()
            if remaining == 0:
                update_goal(goal_id, "COMPLETED")
                print(f"  Goal COMPLETED: {goal_name}")
            continue

        subtask_id = subtask[0]
        retry_count = subtask[5]

        # Guardrail — max retries
        if retry_count >= MAX_RETRIES:
            update_subtask(subtask_id, "FAILED", "Max retries exceeded", retry_count)
            update_goal(goal_id, "FAILED")
            print(f"  Goal FAILED — subtask exceeded {MAX_RETRIES} retries")
            continue

        # Execute subtask
        update_subtask(subtask_id, "RUNNING", "", retry_count)
        success, output = execute_subtask(subtask)

        if success:
            update_subtask(subtask_id, "SUCCESS", output, retry_count)
            print(f"    SUCCESS: {output[:80]}")
        else:
            update_subtask(subtask_id, "PENDING", output, retry_count + 1)
            print(f"    FAILED (retry {retry_count+1}/{MAX_RETRIES}): {output[:80]}")

def show_goals():
    """Display all goals and their subtasks."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, goal_name, status, created_at FROM cortex_goals ORDER BY id DESC LIMIT 10")
    goals = cur.fetchall()
    print(f"\nCORTEX Goals ({len(goals)} total):")
    for g in goals:
        print(f"  [{g[0]}] {g[1]} — {g[2]} ({g[3].strftime('%Y-%m-%d %H:%M')})")
        cur.execute("""
            SELECT subtask_name, assigned_skill, execution_order, status, retry_count
            FROM cortex_subtasks WHERE goal_id=%s ORDER BY execution_order
        """, (g[0],))
        subtasks = cur.fetchall()
        for s in subtasks:
            print(f"    {s[2]}. [{s[1]}] {s[0]} — {s[3]} (retries: {s[4]})")
    conn.close()

def run():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] CORTEX Goal Engine tick...")
    process_active_goals()
    show_goals()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "add" and len(sys.argv) >= 3:
            goal_name = sys.argv[2]
            description = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            add_goal(goal_name, description)
        elif cmd == "show":
            show_goals()
        elif cmd == "run":
            run()
        else:
            print("Usage: goal_engine.py add <goal_name> [description]")
            print("       goal_engine.py show")
            print("       goal_engine.py run")
    else:
        run()

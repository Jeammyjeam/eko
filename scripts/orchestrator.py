import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import json
import subprocess
import sys
import psycopg2
from ddgs import DDGS
from skill_loader import load_skills, route_by_skills

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))
CORTEX = os.path.expanduser("~/cortex")

def web_search(task):
    with DDGS() as ddgs:
        results = list(ddgs.text(task, max_results=5, timeout=20))
    output = ""
    for r in results:
        output += f"[{r['title']}]\n  {r['href']}\n  {r['body'][:150]}\n\n"
    return output

def health_check(task=None):
    result = subprocess.run(
        ["python3", f"{CORTEX}/scripts/health_monitor.py"],
        capture_output=True, text=True, timeout=15
    )
    return result.stdout

def execute_code(task):
    code = task.replace("run code:", "").replace("execute:", "").strip()
    result = subprocess.run(
        ["python3", f"{CORTEX}/scripts/sandbox.py"],
        input=code, capture_output=True, text=True, timeout=60
    )
    return result.stdout or result.stderr

def query_database(task):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    if "star" in task.lower():
        cur.execute("SELECT name, stars, tier FROM repos ORDER BY stars DESC LIMIT 5")
    elif "capabilit" in task.lower():
        cur.execute("SELECT r.name, c.category, c.key_capabilities FROM repos r JOIN capabilities c ON r.id = c.repo_id LIMIT 10")
    elif "depend" in task.lower():
        cur.execute("SELECT package_name, ecosystem, COUNT(*) as count FROM dependencies GROUP BY package_name, ecosystem ORDER BY count DESC LIMIT 10")
    elif "heartbeat" in task.lower():
        cur.execute("SELECT * FROM heartbeat_log ORDER BY id DESC LIMIT 5")
    else:
        cur.execute("SELECT name, stars FROM repos ORDER BY stars DESC LIMIT 5")
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    conn.close()
    result = []
    for row in rows:
        result.append(dict(zip(cols, [str(v) for v in row])))
    return json.dumps(result, indent=2)

def rag_search(task):
    result = subprocess.run(
        ["python3", f"{CORTEX}/scripts/rag_query.py", task],
        capture_output=True, text=True, timeout=30,
        env={**os.environ}
    )
    return result.stdout

def doc_ingest(task):
    result = subprocess.run(
        ["python3", f"{CORTEX}/scripts/doc_ingestor.py"],
        capture_output=True, text=True, timeout=120,
        env={**os.environ}
    )
    return result.stdout or result.stderr

def code_evolver(task):
    script_name = task.replace("evolve", "").replace("improve script", "").replace("optimize code", "").strip()
    if not script_name.endswith(".py"):
        script_name = script_name + ".py"
    result = subprocess.run(
        ["python3", f"{CORTEX}/scripts/code_evolver.py", script_name],
        capture_output=True, text=True, timeout=180,
        env={**os.environ}
    )
    return result.stdout or result.stderr

def goal_engine(task):
    task_lower = task.lower()
    if "show" in task_lower or "status" in task_lower:
        cmd = ["python3", f"{CORTEX}/scripts/goal_engine.py", "show"]
    elif "add goal" in task_lower or "create goal" in task_lower or "new goal" in task_lower:
        goal_text = task_lower.replace("add goal", "").replace("create goal", "").replace("new goal", "").strip()
        cmd = ["python3", f"{CORTEX}/scripts/goal_engine.py", "add", goal_text]
    else:
        cmd = ["python3", f"{CORTEX}/scripts/goal_engine.py", "run"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env={**os.environ})
    return result.stdout or result.stderr

EXECUTORS = {
    "web_search": web_search,
    "health_check": health_check,
    "code_sandbox": execute_code,
    "rag_search": rag_search,
    "doc_ingest": doc_ingest,
    "query_database": query_database,
    "code_evolver": code_evolver,
    "goal_engine": goal_engine,
}

def execute_synthesized_skill(command, task):
    """Execute any synthesized skill by running its command field directly."""
    cmd = command.replace("{query}", task).replace("{{query}}", task)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=120, env={**os.environ}
        )
        return result.stdout or result.stderr or "No output"
    except subprocess.TimeoutExpired:
        return "Skill timed out after 120s"
    except Exception as e:
        return f"Skill execution error: {e}"

def orchestrate(task):
    skills = load_skills()
    tool = route_by_skills(task, skills)
    skill_info = skills.get(tool, {})
    print(f"Loaded {len(skills)} skills | Routing to: {tool}")
    if skill_info.get("ram_mb"):
        print(f"RAM budget: ~{skill_info['ram_mb']}MB")
    # Try hardcoded executor first
    executor = EXECUTORS.get(tool)
    if executor:
        return executor(task)
    # Fall back to dynamic skill execution via command field
    command = skill_info.get("command", "")
    if command:
        print(f"Executing synthesized skill: {command[:60]}...")
        return execute_synthesized_skill(command, task)
    # Last resort — web search
    print("No executor or command found — falling back to web search")
    return web_search(task)

if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "top repos by stars"
    print(f"Task: {task}\n")
    result = orchestrate(task)
    print(result)

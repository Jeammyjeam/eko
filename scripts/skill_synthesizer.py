import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
import re
import json
import base64
import requests
import psycopg2
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from ollama import chat as ollama_chat

DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), port=int(os.getenv("DB_PORT",5432)), dbname=os.getenv("DB_NAME","projectdb"), user=os.getenv("DB_USER","cortex"), password=os.getenv("DB_PASSWORD",""))
HERMES_URL = "http://localhost:8642/v1/chat/completions"
HERMES_KEY = "cortex-local-key"
SKILLS_DIR = os.path.expanduser("~/cortex/skills/experimental")
SCRIPTS_DIR = os.path.expanduser("~/cortex/scripts/synthesized")
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json"}
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
if GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


def get_repo(name):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.name, r.url, r.description, c.language, c.category, c.key_capabilities, c.use_cases
        FROM repos r
        JOIN capabilities c ON r.id = c.repo_id
        WHERE r.name = %s
    """, (name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def update_synthesis_status(repo_name, status):
    """Mark repo as synthesized or rejected in capabilities table."""
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("""
            UPDATE capabilities SET synthesis_status = %s
            WHERE repo_id = (SELECT id FROM repos WHERE name = %s)
        """, (status, repo_name))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Status update error: {e}")

def fetch_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    r = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
    if r.status_code == 200:
        content = r.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore")[:4000]
    return ""


class SkillSchema(BaseModel):
    skill_name: str = Field(description="Normalized snake_case name of the tool or skill")
    triggers: List[str] = Field(description="Array of semantic text triggers")
    install_command: str = Field(description="Exact bash command to install it inside Ubuntu")
    cli_args: List[str] = Field(description="CLI args array e.g. ['tool', '{query}']")
    ram_mb: int = Field(description="Estimated RAM consumption ceiling in MB")
    requires: List[str] = Field(description="Prerequisites like apt packages or system binaries")
    description: str = Field(description="High-level functional summary with safety caveats")
    feasible: bool = Field(description="True if it can run natively inside an isolated Linux shell")

def ask_ollama(readme_text, repo_name, language, category):
    system_prompt = (
        "You are a deterministic repository analysis agent. Your job is to extract technical "
        "capability signatures from a GitHub README. You must output a single, flat JSON object "
        "strictly following the required schema. Do not include markdown formatting or commentary."
    )
    user_prompt = f"""Analyze this repository README text and extract the capability metadata.

[CRITICAL INSTRUCTIONS]:
- feasible: Set to true ONLY if the tool can be run as a simple CLI command on Ubuntu/Linux.
- ram_mb: Estimate minimum RAM overhead (standard CLI = 50, heavy = 512). Integer only.
- triggers: List semantic keyword phrases that should activate this skill.
- cli_args: Array like ["tool_binary", "--flag", "{{query}}"] using {{query}} as placeholder.

Repo: {repo_name} | Language: {language} | Category: {category}

[README CONTENT]:
{readme_text[:2500]}

Extract values for: skill_name, triggers, install_command, cli_args, ram_mb, requires, description, feasible."""

    try:
        response = ollama_chat(
            model='qwen2.5-coder:1.5b',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            format=SkillSchema.model_json_schema(),
            options={'temperature': 0.0, 'num_predict': 1024}
        )
        return json.loads(response.message.content)
    except Exception as e:
        print(f"Ollama extraction failed: {e}")
        return {}


def slugify(name):
    return re.sub(r"[^a-z0-9_]", "_", name.lower())


def generate_wrapper(skill_name, cli_args, description):
    """Generate a thin Python subprocess wrapper for a CLI tool."""
    # cli_args is a list like ["thefuck", "--command", "{query}"]
    # We replace {query} with sys.argv[1] at runtime
    args_repr = json.dumps(cli_args)
    return f'''import subprocess
import sys

# Auto-generated CORTEX skill wrapper for: {skill_name}
# {description[:100]}

def execute_skill(query=""):
    args = {args_repr}
    # Replace {{query}} placeholder with actual input
    args = [a.replace("{{{{query}}}}", query) for a in args]
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode != 0:
            print(f"CLI Error: {{result.stderr}}", file=sys.stderr)
            sys.exit(result.returncode)
        print(result.stdout)
    except FileNotFoundError:
        print(f"Error: CLI tool not found — is it installed?", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"Error: Command timed out after 15s", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Execution Failed: {{str(e)}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    execute_skill(query)
'''


def already_synthesized(repo_name):
    """Check if a skill already exists for this repo across all skill directories."""
    import yaml
    for category in ["core", "custom", "experimental"]:
        path = os.path.join(os.path.expanduser("~/cortex/skills"), category)
        if not os.path.exists(path):
            continue
        for fname in os.listdir(path):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(path, fname)
            with open(fpath) as f:
                raw = f.read()
            if raw.startswith("---"):
                try:
                    end = raw.index("---", 3)
                    meta = yaml.safe_load(raw[3:end])
                    if meta.get("source_repo", "").lower() == repo_name.lower():
                        return category, fname
                except Exception:
                    pass
    return None

def synthesize(repo_name):
    # Check for existing skill before calling Hermes
    existing = already_synthesized(repo_name)
    if existing:
        category, fname = existing
        print(f"Skill already exists for '{repo_name}': {fname} in {category}/ — skipping.")
        return

    row = get_repo(repo_name)
    if not row:
        print(f"Repo '{repo_name}' not found or not capped yet.")
        return

    repo_id, name, url, description, language, category, key_caps, use_cases = row
    parts = url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]
    readme = fetch_readme(owner, repo)

    print(f"Synthesizing skill from: {name} ({language}, {category})")



    spec = ask_ollama(readme, name, language, category)
    if not spec:
        print(f"Ollama extraction failed — skipping")
        update_synthesis_status(name, "rejected")
        return
    if not spec.get("feasible", False):
        print(f"NOT FEASIBLE: {spec.get('description', 'no reason given')}")
        update_synthesis_status(repo_name, "rejected")
        return

    skill_name = slugify(spec["skill_name"])
    cli_args = spec.get("cli_args", [])

    # Generate and save the Python wrapper script
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    wrapper_path = os.path.join(SCRIPTS_DIR, f"{skill_name}.py")
    wrapper_code = generate_wrapper(skill_name, cli_args, spec.get("description", ""))
    with open(wrapper_path, "w") as f:
        f.write(wrapper_code)

    # Build the SKILL.md pointing to the wrapper script
    os.makedirs(SKILLS_DIR, exist_ok=True)
    filepath = os.path.join(SKILLS_DIR, f"{skill_name}.md")

    import yaml
    frontmatter = {
        "name": skill_name,
        "version": "0.1",
        "category": "experimental",
        "status": "experimental",
        "triggers": spec.get("triggers", []),
        "command": f"python3 {wrapper_path} {{query}}",
        "ram_mb": spec.get("ram_mb", 50),
        "requires": spec.get("requires", []),
        "install_command": spec.get("install_command", ""),
        "source_repo": name,
        "source_url": url,
        "synthesized_at": datetime.now().isoformat()
    }
    yaml_block = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    content = f"""---
{yaml_block}---
# {skill_name.replace('_', ' ').title()} Skill

{spec.get('description', '')}

**Source repo:** [{name}]({url})

**Install:**
**Wrapper:** `{wrapper_path}`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.
"""

    with open(filepath, "w") as f:
        f.write(content)

    update_synthesis_status(repo_name, "synthesized")
    print(f"\nWritten skill:   {filepath}")
    print(f"Written wrapper: {wrapper_path}")
    print(f"Skill name:      {skill_name}")
    print(f"Install:         {spec.get('install_command')}")
    print(f"CLI args:        {cli_args}")
    print(f"\nNext: run skills_promoter.py to validate and promote.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 skill_synthesizer.py <repo_name>")
        sys.exit(1)
    synthesize(sys.argv[1])

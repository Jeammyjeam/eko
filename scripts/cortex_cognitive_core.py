import uuid
import json
import os
import re
import requests
import psycopg2
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cortex_tree_orchestrator import CortexTreeOrchestrator

DB_PARAMS = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:1.5b"
SKILLS_DIR = Path.home() / "cortex" / "workspace" / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

class CortexSkillEvolver:
    def distill_session(self, session_id):
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("""
            SELECT agent_name, event_type, command_payload, stdout_capture
            FROM cortex_event_log WHERE session_id = %s ORDER BY created_at ASC
        """, (str(session_id),))
        rows = cur.fetchall()
        if not rows:
            conn.close()
            return None

        trace = "\n".join([
            f"[{r[0]}-{r[1]}]: {(r[2] or '')[:300]}\nOutput: {(r[3] or '')[:200]}"
            for r in rows
        ])

        prompt = f"""You are CORTEX Meta-Cognitive Engine.
A task was successfully resolved. Review this execution trace:
{trace[:3000]}

Synthesize into a reusable skill sheet. Output ONLY valid JSON:
{{"skill_name": "snake_case_name", "trigger_keywords": ["kw1", "kw2", "kw3"], "markdown_content": "# Skill\\n## Usage\\nContent here..."}}"""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                      "options": {"num_ctx": 8192, "temperature": 0.2}},
                timeout=60
            )
            text = response.json()["response"].strip()
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if not json_match:
                conn.close()
                return None

            skill_data = json.loads(json_match.group())
            skill_name = skill_data.get("skill_name", f"skill_{session_id[:8]}")
            keywords = skill_data.get("trigger_keywords", [])
            content = skill_data.get("markdown_content", "")

            # Save markdown file
            skill_path = SKILLS_DIR / f"{skill_name}.md"
            skill_path.write_text(content)

            # Register in DB
            cur.execute("""
                INSERT INTO cortex_skills_registry
                (skill_id, skill_name, trigger_keywords, raw_markdown_path)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (skill_name) DO UPDATE SET
                    success_count = cortex_skills_registry.success_count + 1,
                    last_refined_at = NOW()
            """, (str(uuid.uuid4()), skill_name, keywords, str(skill_path)))
            conn.commit()
            conn.close()
            print(f"[COGNITIVE] Skill synthesized: {skill_name} — {len(keywords)} triggers")
            return skill_name
        except Exception as e:
            print(f"[COGNITIVE] Skill synthesis error: {e}")
            conn.close()
            return None

class CortexCognitiveCore:
    def __init__(self):
        self.evolver = CortexSkillEvolver()

    def _lookup_skill(self, goal):
        """Check if relevant skill exists in registry"""
        keywords = goal.lower().split()[:5]
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT skill_name, raw_markdown_path, success_count
                FROM cortex_skills_registry
                WHERE trigger_keywords && %s
                ORDER BY success_count DESC LIMIT 1
            """, (keywords,))
            row = cur.fetchone()
            conn.close()
            return row
        except:
            conn.close()
            return None

    def _load_skill_context(self, skill_path):
        """Load skill markdown as system context"""
        try:
            return Path(skill_path).read_text()[:2000]
        except:
            return ""

    def execute(self, goal):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] CORTEX Cognitive Core")
        print(f"Goal: {goal}\n")

        # Step 1 — Check skill registry
        skill = self._lookup_skill(goal)
        skill_context = ""
        if skill:
            skill_name, skill_path, count = skill
            print(f"[MEMORY] Found relevant skill: {skill_name} (used {count}x)")
            skill_context = self._load_skill_context(skill_path)
            if skill_context:
                print(f"[MEMORY] Injecting skill context into execution ({len(skill_context)} chars)")
                goal = f"SYSTEM SKILL CONTEXT:\n{skill_context}\n\nTASK: {goal}"
        else:
            print("[MEMORY] No existing skill found — exploring fresh")

        # Step 2 — Run MCTS orchestrator
        orchestrator = CortexTreeOrchestrator()
        result = orchestrator.run(goal)

        # Step 3 — Distill successful session into new skill
        if result.get("status") == "SUCCESS":
            print(f"\n[COGNITIVE] Distilling successful session into skill...")
            skill_name = self.evolver.distill_session(orchestrator.session_id)
            result["skill_synthesized"] = skill_name

        return result

if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
           "fix database connection timeout errors in task queue"
    core = CortexCognitiveCore()
    result = core.execute(goal)
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")

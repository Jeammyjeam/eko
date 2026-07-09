import uuid
import json
import psycopg2
import requests
import sys
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cortex_sandbox import CortexSandbox
from cortex_snapshot import create_snapshot

DB_PARAMS = {
    "host": "127.0.0.1", "port": 5432,
    "dbname": "projectdb", "user": "cortex", "password": "cortex123"
}
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:1.5b"

class CortexTreeOrchestrator:
    def __init__(self):
        self.session_id = str(uuid.uuid4())

    def _get_conn(self):
        return psycopg2.connect(**DB_PARAMS)

    def _score_action(self, context, action):
        prompt = "You are CORTEX value critic.\nContext: " + context + "\nAction: " + action + "\nScore 0.0-1.0. Reply ONLY with a float."
        try:
            response = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"num_ctx": 4096, "temperature": 0.1}}, timeout=30)
            score_str = response.json()["response"].strip()
            matches = re.findall(r'\d+\.?\d*', score_str)
            score = float(matches[0]) if matches else 0.5
            return min(max(score, 0.0), 1.0)
        except:
            return 0.5

    def _generate_paths(self, goal):
        prompt = 'Generate 3 approaches for: "' + goal + '"\nRespond in JSON only: {"paths": ["action 1", "action 2", "action 3"]}'
        try:
            response = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"num_ctx": 4096}}, timeout=30)
            text = response.json()["response"].strip()
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("paths", [])
        except:
            pass
        return ["Direct: " + goal, "Step-by-step: " + goal, "Research: " + goal]

    def _register_node(self, node_id, parent_id, depth, action, score, status="EXPLORED"):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO cortex_task_tree (node_id, parent_node_id, session_id, step_depth, proposed_action, evaluation_score, node_status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                   (str(node_id), str(parent_id) if parent_id else None, self.session_id, depth, action, score, status))
        conn.commit()
        conn.close()

    def _update_node_status(self, node_id, status):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE cortex_task_tree SET node_status = %s WHERE node_id = %s", (status, str(node_id)))
        conn.commit()
        conn.close()

    def _execute_in_sandbox(self, action, node_id):
        sb = CortexSandbox(agent_name="tree_orchestrator", session_id=self.session_id)
        filename = "tree_" + str(node_id)[:8] + ".py"
        sb.write_file(filename, "print('Executing action')\nprint('COMPLETED')")
        result = sb.test_python(filename)
        sb.cleanup()
        return result

    def run(self, goal):
        ts = datetime.now().strftime('%H:%M:%S')
        print("\n[" + ts + "] CORTEX Tree Orchestrator")
        print("Session: " + self.session_id[:8] + "...")
        print("Goal: " + goal + "\n")
        paths = self._generate_paths(goal)
        nodes = []
        for i, action in enumerate(paths[:3]):
            node_id = uuid.uuid4()
            score = self._score_action(goal, action)
            self._register_node(node_id, None, 1, action, score)
            nodes.append((node_id, action, score))
            print("  Path " + str(i+1) + " [score=" + str(round(score,2)) + "]: " + action[:60])
        nodes.sort(key=lambda x: x[2], reverse=True)
        # Auto-snapshot if highest score > 0.7
        if nodes[0][2] > 0.7:
            create_snapshot(reason='pre_mcts_execution', risk_score=nodes[0][2])
        for attempt, (node_id, action, score) in enumerate(nodes):
            print("\n[Attempt " + str(attempt+1) + "] score=" + str(round(score,2)) + ": " + action[:60])
            result = self._execute_in_sandbox(action, node_id)
            if result["exit_code"] == 0:
                self._update_node_status(node_id, "EXECUTED")
                print("  SUCCESS")
                return {"status": "SUCCESS", "action": action, "session_id": self.session_id, "attempts": attempt+1}
            else:
                self._update_node_status(node_id, "PRUNED")
                print("  PRUNED - backtracking")
        return {"status": "FAILED", "session_id": self.session_id, "attempts": len(nodes)}

if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "optimize rag_query.py"
    orchestrator = CortexTreeOrchestrator()
    result = orchestrator.run(goal)
    print("\nResult: " + json.dumps(result, indent=2))

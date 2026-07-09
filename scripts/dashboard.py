import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

import streamlit as st
import psycopg2
import psycopg
import pandas as pd
import os
import json
import subprocess
from google import genai

st.set_page_config(page_title="CORTEX Dashboard", page_icon="⚕", layout="wide")
st.title("⚕ CORTEX Dashboard")
st.caption("Personal AI Operating System — Jeam")

conn2 = psycopg2.connect(host="127.0.0.1", port=5432, dbname="projectdb", user="cortex", password="cortex123")

# --- METRICS ---
col1, col2, col3, col4, col5, col6 = st.columns(6)
df_repos = pd.read_sql("SELECT * FROM repos ORDER BY stars DESC", conn2)
df_caps = pd.read_sql("SELECT r.name, r.stars, r.tier, c.language, c.category, c.key_capabilities FROM repos r LEFT JOIN capabilities c ON r.id = c.repo_id ORDER BY r.stars DESC", conn2)
rag_count = pd.read_sql("SELECT COUNT(*) as count FROM cortex_capabilities", conn2).iloc[0]["count"]
dep_count = pd.read_sql("SELECT COUNT(*) as count FROM dependencies", conn2).iloc[0]["count"]
hb_count = pd.read_sql("SELECT COUNT(*) as count FROM heartbeat_log", conn2).iloc[0]["count"]

# Count skills
skills_count = sum(
    len([f for f in os.listdir(os.path.join(os.path.join(os.path.expanduser("~/cortex"), "skills"), cat)) if f.endswith(".md")])
    for cat in ["core", "custom", "experimental"]
    if os.path.exists(os.path.join(os.path.join(os.path.expanduser("~/cortex"), "skills"), cat))
)

with col1: st.metric("Total Repos", len(df_repos))
with col2: st.metric("RAG Chunks", int(rag_count))
with col3: st.metric("Dependencies", int(dep_count))
with col4: st.metric("Heartbeats", int(hb_count))
with col5: st.metric("Skills", skills_count)
with col6: st.metric("Capabilities", df_caps["category"].notna().sum())

# --- HEALTH ---
st.divider()
st.subheader("🟢 System Health")
try:
    result = subprocess.run(["python3", os.path.join(os.path.expanduser("~/cortex"), "scripts", "health_monitor.py")], capture_output=True, text=True, timeout=15)
    health = json.loads(result.stdout)
    status = health["status"]
    color = "🟢" if status == "GREEN" else "🟡" if status == "YELLOW" else "🔴"
    st.metric("Status", f"{color} {status}")
    t = health["telemetry"]
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("RAM Available", f"{t['ram_available_mb']}MB")
    with c2: st.metric("Disk Free", f"{t['disk_free_gb']}GB")
    with c3: st.metric("CPU", f"{t['cpu_pct']}%")
    st.json(health["services"])
    if health["directives"]:
        for d in health["directives"]:
            st.warning(d)
except Exception as e:
    st.error(f"Health monitor error: {e}")

# --- HEARTBEAT LOG ---
st.divider()
st.subheader("💓 Heartbeat Log")
df_hb = pd.read_sql("SELECT timestamp, health_status, action_taken, consecutive_actions FROM heartbeat_log ORDER BY id DESC LIMIT 10", conn2)
st.dataframe(df_hb, use_container_width=True)

# --- RAG SEARCH ---
st.divider()
st.subheader("🔍 Semantic Search")
query = st.text_input("Search your repo knowledge base...", placeholder="e.g. AI agent framework, frontend library")
if query:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        with st.spinner("Searching..."):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.embed_content(model="gemini-embedding-2", contents=query)
                embedding = response.embeddings[0].values
                conn3 = psycopg.connect("dbname={} user={} password={} host={} port={}".format(os.getenv("DB_NAME","projectdb"),os.getenv("DB_USER","cortex"),os.getenv("DB_PASSWORD",""),os.getenv("DB_HOST","127.0.0.1"),os.getenv("DB_PORT","5432")))
                cur = conn3.cursor()
                cur.execute("SELECT repo_name, content_chunk, 1 - (embedding <=> %s::vector) as similarity FROM cortex_capabilities ORDER BY embedding <=> %s::vector LIMIT 5", (str(embedding), str(embedding)))
                results = cur.fetchall()
                conn3.close()
                for repo, chunk, score in results:
                    with st.expander(f"[{score:.3f}] {repo}"):
                        st.write(chunk[:300] + "...")
            except Exception as e:
                st.error(f"Search error: {e}")
    else:
        st.warning("GEMINI_API_KEY not set")

# --- SKILLS ---
st.divider()
st.subheader("⚡ Skills Inventory")
import yaml
skills_dir = os.path.join(os.path.expanduser("~/cortex"), "skills")
skill_data = []
for category in ["core", "custom", "experimental"]:
    path = os.path.join(skills_dir, category)
    if os.path.exists(path):
        for fname in os.listdir(path):
            if fname.endswith(".md"):
                fpath = os.path.join(path, fname)
                with open(fpath) as f:
                    raw = f.read()
                meta = {}
                if raw.startswith("---"):
                    try:
                        end = raw.index("---", 3)
                        meta = yaml.safe_load(raw[3:end])
                    except Exception:
                        meta = {}
                skill_data.append({
                    "skill": meta.get("name", fname.replace(".md","")),
                    "version": meta.get("version", "1.0"),
                    "category": category,
                    "status": meta.get("status", "unknown"),
                    "ram_mb": meta.get("ram_mb", 0),
                    "triggers": ", ".join(meta.get("triggers", [])[:3])
                })
if skill_data:
    st.dataframe(pd.DataFrame(skill_data), use_container_width=True)

# --- GOALS ---
st.divider()
st.subheader("🎯 Goal Engine")
df_goals = pd.read_sql("SELECT id, goal_name, status, created_at FROM cortex_goals ORDER BY id DESC LIMIT 10", conn2)
if not df_goals.empty:
    st.dataframe(df_goals, use_container_width=True)
    # Subtasks for active goals
    active_ids = df_goals[df_goals["status"] == "ACTIVE"]["id"].tolist()
    if active_ids:
        df_sub = pd.read_sql(f"SELECT goal_id, subtask_name, assigned_skill, execution_order, status, retry_count FROM cortex_subtasks WHERE goal_id IN ({','.join(map(str, active_ids))}) ORDER BY goal_id, execution_order", conn2)
        if not df_sub.empty:
            st.caption("Active subtasks")
            st.dataframe(df_sub, use_container_width=True)
else:
    st.info("No goals yet. Add one: python3 ~/cortex/scripts/goal_engine.py add 'goal name' 'description'")

# --- EVOLUTION LOG ---
st.divider()
st.subheader("🧬 Evolution Log")
df_evo = pd.read_sql("SELECT timestamp, script_name, ast_passed, sandbox_passed, promoted, notes FROM evolution_log ORDER BY id DESC LIMIT 10", conn2)
if not df_evo.empty:
    st.dataframe(df_evo, use_container_width=True)
else:
    st.info("No evolutions yet.")

# --- HEALING LOG ---
st.divider()
st.subheader("🩺 Healing Log")
df_heal = pd.read_sql("SELECT timestamp, script_name, healed, attempt_count, status, notes FROM healing_log ORDER BY id DESC LIMIT 10", conn2)
if not df_heal.empty:
    st.dataframe(df_heal, use_container_width=True)
else:
    st.success("No healing attempts — all services healthy.")

# --- DOC WATCHER STATUS ---
st.divider()
st.subheader("📥 Document Ingestor")
inbox = os.path.expanduser("~/cortex/docs_inbox")
processed = os.path.expanduser("~/cortex/docs_processed")
inbox_files = [f for f in os.listdir(inbox)] if os.path.exists(inbox) else []
processed_files = [f for f in os.listdir(processed)] if os.path.exists(processed) else []
c1, c2 = st.columns(2)
with c1: st.metric("Files in Inbox", len(inbox_files))
with c2: st.metric("Files Processed", len(processed_files))
if inbox_files:
    st.warning(f"Pending: {', '.join(inbox_files)}")
else:
    st.success("Inbox clear — watcher running via PM2")

# --- DEPENDENCIES ---
st.divider()
st.subheader("📦 Top Dependencies")
df_deps = pd.read_sql("SELECT package_name, ecosystem, COUNT(*) as repos FROM dependencies GROUP BY package_name, ecosystem ORDER BY repos DESC LIMIT 15", conn2)
st.dataframe(df_deps, use_container_width=True)

# --- CAPABILITY MAP ---
st.divider()
st.subheader("🗺 Capability Map")
st.dataframe(df_caps[["name","stars","tier","language","category","key_capabilities"]].head(22), use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Category Distribution")
    st.bar_chart(df_caps["category"].value_counts())
with col_b:
    st.subheader("Stars Distribution")
    st.bar_chart(df_repos.set_index("name")["stars"].head(10))

conn2.close()

# --- TASK QUEUE ---
conn3 = psycopg2.connect(host='127.0.0.1', port=5432, dbname='projectdb', user='cortex', password='cortex123')
st.divider()
st.subheader("⚡ Async Task Queue")
df_queue = pd.read_sql("SELECT task_type, status, created_at FROM cortex_task_queue ORDER BY id DESC LIMIT 10", conn3)
q1, q2, q3 = st.columns(3)
total_tasks = pd.read_sql("SELECT COUNT(*) as count FROM cortex_task_queue", conn3).iloc[0]["count"]
queued = pd.read_sql("SELECT COUNT(*) as count FROM cortex_task_queue WHERE status='QUEUED'", conn3).iloc[0]["count"]
success = pd.read_sql("SELECT COUNT(*) as count FROM cortex_task_queue WHERE status='SUCCESS'", conn3).iloc[0]["count"]
with q1: st.metric("Total Tasks", int(total_tasks))
with q2: st.metric("Queued", int(queued))
with q3: st.metric("Succeeded", int(success))
if not df_queue.empty:
    st.dataframe(df_queue, use_container_width=True)

# --- SYSTEM PROFILE ---
st.divider()
st.subheader("🖥️ System Profile")
import pathlib
profile_path = pathlib.Path.home() / "cortex" / "config" / "runtime_profile.json"
if profile_path.exists():
    with open(profile_path) as f:
        profile = json.load(f)
    p1, p2, p3, p4 = st.columns(4)
    tier = profile.get("tier", "UNKNOWN")
    color = "🟢" if tier == "BEAST" else "🟡" if tier == "STANDARD" else "🔴"
    with p1: st.metric("Tier", f"{color} {tier}")
    with p2: st.metric("RAM", f"{profile.get('host_ram_gb', '?')}GB")
    with p3: st.metric("CPU Cores", profile.get("cpu_cores", "?"))
    with p4: st.metric("Architecture", profile.get("architecture", "?"))
    st.caption(f"Max concurrent tasks: {profile.get('max_concurrent_tasks')} | RAG chunk limit: {profile.get('rag_chunk_limit')} | Ollama fallback: {profile.get('ollama_fallback_model')}")
else:
    st.warning("System profile not detected. Run: python3 ~/cortex/scripts/system_profile.py")

# --- PARENT-CHILD RAG ---
st.divider()
st.subheader("🧠 Parent-Child RAG")
try:
    doc_count = pd.read_sql("SELECT COUNT(*) as count FROM cortex_documents", conn3).iloc[0]["count"]
    chunk_count = pd.read_sql("SELECT COUNT(*) as count FROM cortex_document_chunks", conn3).iloc[0]["count"]
    r1, r2 = st.columns(2)
    with r1: st.metric("Parent Documents", int(doc_count))
    with r2: st.metric("Child Chunks", int(chunk_count))
    df_docs = pd.read_sql("SELECT file_name, doc_type, created_at FROM cortex_documents ORDER BY id DESC LIMIT 10", conn3)
    if not df_docs.empty:
        st.dataframe(df_docs, use_container_width=True)
except:
    st.info("Parent-child RAG tables not found.")

# --- LLM ROUTER STATUS ---
st.divider()
st.subheader("🔀 LLM Router")
import requests as req
r1, r2 = st.columns(2)
try:
    resp = req.get("http://localhost:8642/health", timeout=3)
    with r1: st.metric("Tunnel A (Hermes)", "🟢 ONLINE" if resp.status_code == 200 else "🔴 OFFLINE")
except:
    with r1: st.metric("Tunnel A (Hermes)", "🔴 OFFLINE")
import shutil
ollama_exists = shutil.which("ollama") is not None
with r2: st.metric("Tunnel B (Ollama)", "🟢 INSTALLED" if ollama_exists else "🟡 NOT INSTALLED")

# CORTEX Architecture

## Overview
CORTEX is a local-first autonomous AI OS running on Ubuntu 24.04 WSL2.
Built by Jeam (AbdulMumeen Junaid-Eko) — Lagos, Nigeria.
Public dashboard: https://jeammy01-1.tailb1bd5.ts.net/

## Stack

| Component | Version | Port | Status |
|-----------|---------|------|--------|
| PostgreSQL + pgvector | 16 | 5432 | Auto-start via bashrc |
| Gitea | 1.25.0 | 3000 | Auto-start via bashrc |
| n8n | 2.15.1 | 5678 | PM2 |
| Hermes Agent | v0.14 | 8642 | Auto-start via bashrc |
| Streamlit Dashboard | latest | 8501 | Auto-start via bashrc |
| Docker | latest | - | Auto-start via bashrc |
| SSH | - | 22 | Auto-start via bashrc |
| doc-watcher | 1.0 | - | PM2 |
| Tailscale Funnel | 1.98.4 | 443 | Background |

## Database: projectdb

| Table | Purpose |
|-------|---------|
| repos | 83 archived GitHub repos |
| capabilities | Extracted repo capabilities (30) |
| cortex_capabilities | pgvector RAG embeddings (131 chunks) |
| dependencies | npm dependency map (1753) |
| heartbeat_log | Autonomous pulse log |
| cortex_goals | Goal-directed reasoning state |
| cortex_subtasks | Goal subtask execution |
| evolution_log | Code evolution audit trail |
| healing_log | Self-healing audit trail |
| rag_audit_log | RAG memory quality audit |
| cortex_cloud_nodes | Cloud node registry |

## OpenClaw Layers

| Layer | Script | Purpose |
|-------|--------|---------|
| A | heartbeat.py | 30-min autonomous pulse |
| B | skill_loader.py + skills/ | YAML skill routing |
| C | rag_critic.py | Daily RAG memory audit |
| D | code_evolver.py | Autonomous script improvement |
| E | self_healer.py | PM2 service repair |
| F | goal_engine.py | Goal-directed reasoning |

## Skills Directory

| Skill | Category | Triggers | RAM |
|-------|----------|----------|-----|
| web_search | core | search, latest, news | 0MB |
| rag_search | core | find repo, related to | 50MB |
| health_check | core | health, status | 10MB |
| code_sandbox | core | run code, execute | 256MB |
| doc_ingest | core | ingest, document, pdf | 50MB |
| query_database | core | top repos, stars | 5MB |
| code_evolver | core | evolve, improve script | 100MB |
| goal_engine | core | goal, add goal | 20MB |
| git_status | custom | git status, git log | 5MB |
| test_skill | custom | test skill, run test | 5MB |

## n8n Workflows (6)

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| GitHub Monitor | Every 2hrs | Archive repos |
| Hourly Check | Every 1hr | General check |
| Capability Extractor | 9am daily | Extract capabilities |
| Heartbeat | Every 30min | Autonomous pulse |
| RAG Critic | 10am daily | Memory audit |
| Dependency Scanner | 11am daily | Map dependencies |

## CORTEX Cloud

| Node | IP | Public URL | Type |
|------|----|------------|------|
| wsl2-master-core | 100.99.95.42 | https://jeammy01-1.tailb1bd5.ts.net/ | TAILSCALE_FUNNEL |

## Remote Access

| Method | Details |
|--------|---------|
| Tailscale SSH | ssh -p 2222 -i ~/.ssh/cortex_phone junaid-eko@100.120.242.76 |
| WSL2 Tailscale IP | 100.99.95.42 |
| Windows Tailscale IP | 100.120.242.76 |
| Public Dashboard | https://jeammy01-1.tailb1bd5.ts.net/ |

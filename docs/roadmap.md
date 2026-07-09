# CORTEX Build Roadmap

## Completed Layers (42+)

### Infrastructure
1. PostgreSQL 16 + pgvector setup
2. Gitea 1.25.0 binary install
3. n8n via PM2
4. Hermes Agent v0.14 (Gemini 2.5 Flash)
5. Streamlit dashboard
6. Docker sandbox
7. SSH server
8. Windows auto-startup via Task Scheduler
9. sudo NOPASSWD for service commands
10. GITHUB_TOKEN + GEMINI_API_KEY in bashrc
11. DNS lock via chattr +i /etc/resolv.conf

### RAG Pipeline
12. pgvector cortex_capabilities table VECTOR(3072)
13. gemini-embedding-2 embeddings
14. github_monitor.py — 83 repos archived
15. capability_extractor.py — 30 capabilities
16. dependency_scanner.py — 1753 npm deps
17. rag_ingest_retry.py — all 83 repos embedded (131 chunks)
18. rag_query.py — semantic search

### Automation (n8n)
19. GitHub Monitor workflow (every 2hrs)
20. Hourly Check workflow
21. Capability Extractor workflow (9am)
22. Heartbeat workflow (every 30min)
23. RAG Critic workflow (10am)
24. Dependency Scanner workflow (11am)

### OpenClaw Foundation
25. Layer A — heartbeat.py with PostgreSQL logging
26. Layer B — skills/ directory with YAML frontmatter
27. Layer B — skill_loader.py with trigger routing
28. Layer B — orchestrator.py with dynamic skill loading
29. Layer C — rag_critic.py daily memory audit
30. Layer D — code_evolver.py with AST + sandbox + git branch
31. Layer E — self_healer.py with circuit breaker + rollback
32. Layer F — goal_engine.py with subtask execution

### Skills System
33. 8 core skills with YAML frontmatter
34. skills_promoter.py with 3 guardrails
35. Heartbeat → skills promoter integration
36. Trigger priority routing (longest trigger first)

### Document Pipeline
37. doc_ingestor.py — PDF/DOCX/TXT/MD support
38. doc_watcher.py via PM2 — 30s watch interval

### CORTEX Cloud
39. Tailscale installed + authenticated
40. Tailscale Funnel — public dashboard URL
41. cortex_cloud_env.py — centralized config
42. cortex_cloud_nodes table — node registry

### Release Prep
43. README.md — full documentation
44. LICENSE — MIT
45. requirements.txt
46. .gitignore
47. All hardcoded paths removed
48. migration_exporter.py — Oracle Cloud ready

## Pending

### Phone Required
- Telegram gateway (BotFather token)
- /status, /heal, /goal commands
- Mobile control plane

### Infrastructure
- Oracle Cloud ARM64 migration (needs card)
- Metabase integration
- Multi-node CORTEX Cloud

### OpenClaw Advanced
- Layer G — self-replication (spin up new CORTEX instances)
- Skills marketplace
- OpenClaw public release

## Session Memory Prompt

I am Jeam (AbdulMumeen Junaid-Eko). Building CORTEX — personal AI OS on Ubuntu 24.04 WSL2.
Stack:

PostgreSQL 16 (projectdb, user: cortex, pw: cortex123, port: 5432)
Gitea 1.25.0 (localhost:3000, user: jeammy)
n8n via PM2 (localhost:5678, 6 active workflows)
Hermes Agent v0.14 — gemini-2.5-flash paid tier

Starts with: hermes gateway restart
API at localhost:8642, key: cortex-local-key


Python 3.12, Node.js 22
GEMINI_API_KEY and GITHUB_TOKEN in ~/.bashrc
pgvector RAG: 83 repos, 131 chunks, VECTOR(3072), gemini-embedding-2
Skills: ~/cortex/skills/ (8 core + 2 custom = 10 skills)
Scripts: ~/cortex/scripts/ (19 scripts)
GitHub: github.com/Jeammyjeam/cortex-backup
Tailscale SSH: 100.120.242.76:2222
CORTEX Cloud: https://jeammy01-1.tailb1bd5.ts.net/
Windows auto-startup via Task Scheduler
PM2: n8n + doc-watcher
OpenClaw: All 6 layers complete (A-F)
DB tables: 11 (repos, capabilities, cortex_capabilities, dependencies,
heartbeat_log, cortex_goals, cortex_subtasks, evolution_log,
healing_log, rag_audit_log, cortex_cloud_nodes)


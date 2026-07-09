# CORTEX Commands Reference

## Auto-Startup (Windows Task Scheduler)
Fires on every Windows login:
wsl.exe -d Ubuntu-24.04 -e bash -c 'sleep 15 && source ~/.bashrc'
Starts: PostgreSQL, SSH, n8n, Gitea, Hermes, Streamlit, Docker, MTU fix, Tailscale

## Manual Service Start
```bash
# PostgreSQL
sudo service postgresql start

# Hermes
hermes gateway restart &>/dev/null &

# Gitea
rm -rf /var/lib/gitea/data/queues/common/LOCK
/usr/local/bin/gitea web --config /etc/gitea/app.ini &>/dev/null &

# Docker
sudo dockerd &>/dev/null &

# Streamlit
GEMINI_API_KEY=$GEMINI_API_KEY streamlit run ~/cortex/scripts/dashboard.py \
  --server.port 8501 --server.enableCORS false \
  --server.enableXsrfProtection false --server.headless true &>/dev/null &

# Tailscale
sudo tailscaled &>/dev/null &
sudo tailscale up
sudo tailscale funnel --bg 8501

# PM2
pm2 resurrect
```

## Health Check
```bash
python3 ~/cortex/scripts/health_monitor.py
```

## Heartbeat (manual run)
```bash
python3 ~/cortex/scripts/heartbeat.py
# Reset consecutive counter:
PGPASSWORD=cortex123 psql -h 127.0.0.1 -U cortex -d projectdb -c \
  "INSERT INTO heartbeat_log (health_status, action_taken, result, consecutive_actions) \
  VALUES ('GREEN', 'RESET', 'Manual reset by Jeam', 0);"
```

## RAG
```bash
# Search
python3 ~/cortex/scripts/rag_query.py "your query"

# Re-embed missing repos
python3 ~/cortex/scripts/rag_ingest_retry.py

# Audit
python3 ~/cortex/scripts/rag_critic.py
```

## Goals
```bash
# Add goal
python3 ~/cortex/scripts/goal_engine.py add "goal name" "description"

# Show all goals
python3 ~/cortex/scripts/goal_engine.py show

# Run one tick
python3 ~/cortex/scripts/goal_engine.py run
```

## Skills
```bash
# List all skills
python3 ~/cortex/scripts/skill_loader.py

# Promote experimental skill
python3 ~/cortex/scripts/skills_promoter.py

# Route a task
python3 ~/cortex/scripts/orchestrator.py "your task"
```

## Code Evolution
```bash
# Evolve a whitelisted script
python3 ~/cortex/scripts/code_evolver.py web_search.py

# View evolution log
PGPASSWORD=cortex123 psql -h 127.0.0.1 -U cortex -d projectdb \
  -c "SELECT * FROM evolution_log ORDER BY id DESC LIMIT 5;"

# Review evolved branch
git -C ~/cortex diff master evolution/web_search-YYYYMMDD-HHMM
```

## Self-Healer
```bash
# Run healer
python3 ~/cortex/scripts/self_healer.py

# View healing log
PGPASSWORD=cortex123 psql -h 127.0.0.1 -U cortex -d projectdb \
  -c "SELECT * FROM healing_log ORDER BY id DESC LIMIT 5;"
```

## Document Ingestion
```bash
# Drop file in inbox
cp your_file.pdf ~/cortex/docs_inbox/
# Auto-ingested within 30 seconds by doc-watcher

# Manual ingest
python3 ~/cortex/scripts/doc_ingestor.py

# Check watcher logs
pm2 logs doc-watcher --lines 20 --nostream
```

## Migration
```bash
# Package CORTEX for migration
python3 ~/cortex/scripts/migration_exporter.py

# Transfer to new server
scp -r ~/cortex_migration_payload user@server-ip:~/
```

## GitHub Backup
```bash
cd ~/cortex
git add .
git commit -m "your message"
git push origin master
pm2 save --force
```

## Remote SSH
```bash
ssh -p 2222 -i ~/.ssh/cortex_phone junaid-eko@100.120.242.76
```

## Hermes (natural language)
```bash
hermes
# Then type naturally:
# "add goal research best frameworks"
# "find repos related to AI agents"
# "check system health"
# "evolve web_search.py"
```

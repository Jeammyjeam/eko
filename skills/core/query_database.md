---
name: query_database
version: 1.0
category: core
status: active
triggers:
  - top repos
  - stars
  - sql
  - query db
  - dependencies
  - heartbeat log
  - capability
ram_mb: 5
requires:
  - postgresql
command: python3 /home/junaid-eko/cortex/scripts/orchestrator.py "{query}"
---

# Query Database Skill
Query CORTEX PostgreSQL directly — repos, capabilities, dependencies, heartbeat logs.
Returns structured JSON from projectdb.
---

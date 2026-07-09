---
name: health_check
version: 1.1
category: core
status: active
triggers:
  - health
  - status
  - services
  - ram
  - cpu
  - disk
command: python3 /home/junaid-eko/cortex/scripts/health_monitor.py
ram_mb: 10
requires: []
---

# Health Check Skill
Check CORTEX system health before running heavy tasks.
Returns GREEN/YELLOW/RED status with telemetry and service states.
Rule: if RED abort all tasks. If YELLOW proceed with caution.

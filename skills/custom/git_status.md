---
name: git_status
version: 1.0
category: experimental
status: active
triggers:
  - git status
  - git log
  - repo status
  - uncommitted
command: python3 /home/junaid-eko/cortex/scripts/web_search.py "{query}"
ram_mb: 5
requires: []
---

# Git Status Skill
Check CORTEX git repository status and recent commits.
Returns current branch, uncommitted changes, and last 5 commits.

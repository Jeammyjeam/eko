---
name: goal_engine
version: 1.0
category: core
status: active
triggers:
  - goal
  - add goal
  - create goal
  - new goal
  - show goals
  - goal status
  - run goal
command: python3 ~/cortex/scripts/goal_engine.py "{query}"
ram_mb: 20
requires:
  - GEMINI_API_KEY
  - postgresql
---

# Goal Engine Skill
Manages CORTEX persistent goals. Breaks goals into subtasks, assigns to skills, tracks progress.
Max 5 subtasks per goal, max 3 active goals, max 2 retries per subtask.
Usage: add goal <name> <description> | show | run

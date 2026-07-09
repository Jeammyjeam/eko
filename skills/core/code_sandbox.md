---
name: code_sandbox
version: 1.1
category: core
status: active
triggers:
  - run code
  - execute
  - sandbox
  - python code
command: echo "{query}" | python3 /home/junaid-eko/cortex/scripts/sandbox.py
ram_mb: 256
requires:
  - docker
---

# Code Sandbox Skill
Execute Python code safely in an isolated Docker container.
Network: none. RAM: 256MB max. CPU: 0.5 cores. Timeout: 30s.
Never run code outside the sandbox that modifies system files.

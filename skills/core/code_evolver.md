---
name: code_evolver
version: 1.0
category: core
status: active
triggers:
  - evolve
  - improve script
  - optimize code
  - upgrade script
command: python3 ~/cortex/scripts/code_evolver.py "{query}"
ram_mb: 100
requires:
  - GEMINI_API_KEY
  - docker
---

# Code Evolver Skill
Improves any whitelisted CORTEX script via Hermes + AST check + sandbox test.
Creates a feature branch, backs up original, commits improved version.
Whitelist: rag_query, rag_critic, dependency_scanner, github_monitor, web_search, skill_loader.

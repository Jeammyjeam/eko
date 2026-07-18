---
name: serena
version: '0.1'
category: experimental
status: active
triggers:
- semantic code retrieval
- editing
- refactoring
- debugging
command: python3 /home/junaid-eko/cortex/scripts/synthesized/serena.py {query}
ram_mb: 512
requires: []
install_command: pip install serena
source_repo: serena
source_url: https://github.com/oraios/serena
synthesized_at: '2026-07-18T16:04:19.343051'
---
# Serena Skill

Serena provides essential semantic code retrieval, editing, refactoring and debugging tools that are akin to an IDE's capabilities, operating at the symbol level and exploiting relational structure. It integrates with any client/LLM via the model context protocol (MCP). Serena's agent-first tool design involves robust high-level abstractions, distinguishing it from approaches that rely on low-level concepts like line numbers or primitive search patterns. Practically, this means that your agent operates faster, more efficiently and more reliably, especially in larger and more complex codebases.

**Source repo:** [serena](https://github.com/oraios/serena)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/serena.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

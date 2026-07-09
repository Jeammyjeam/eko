---
name: ecc
version: '0.1'
category: experimental
status: active
triggers:
- orchestrate agents
- automate workflows
- run ecc
- ecc cli
command: python3 /home/junaid-eko/cortex/scripts/synthesized/ecc.py {query}
ram_mb: 50
requires:
- nodejs
- npm
source_repo: ECC
source_url: https://github.com/affaan-m/ECC
synthesized_at: '2026-06-27T12:20:52.684785'
---
# Ecc Skill

ECC is a harness-native operator system for automating agentic workflows and orchestrating distributed agents. It provides universal tools, an agent shield, and GitHub App integration for managing complex multi-harness engineering tasks.

**Source repo:** [ECC](https://github.com/affaan-m/ECC)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/ecc.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

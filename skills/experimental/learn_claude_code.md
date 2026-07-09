---
name: learn_claude_code
version: '0.1'
category: experimental
status: experimental
triggers:
- agent
- model
- harness
command: python3 /home/junaid-eko/cortex/scripts/synthesized/learn_claude_code.py
  {query}
ram_mb: 512
requires: []
install_command: pip install learn-claude-code
source_repo: learn-claude-code
source_url: https://github.com/shareAI-lab/learn-claude-code
synthesized_at: '2026-06-28T18:06:40.064623'
---
# Learn Claude Code Skill

This repository teaches you how to build the vehicle for an agent product, including the model and harness. The model is learned through training, while the harness provides the infrastructure for the agent to operate in a specific environment.

**Source repo:** [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/learn_claude_code.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

---
name: claude_code
version: '0.1'
category: experimental
status: experimental
triggers:
- code
- develop
command: python3 /home/junaid-eko/cortex/scripts/synthesized/claude_code.py {query}
ram_mb: 50
requires: []
install_command: pip install claude-code-plugin
source_repo: superpowers
source_url: https://github.com/obra/superpowers
synthesized_at: '2026-07-18T16:07:47.450565'
---
# Claude Code Skill

A plugin for Claude that allows you to write code directly from your coding agent.

**Source repo:** [superpowers](https://github.com/obra/superpowers)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/claude_code.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

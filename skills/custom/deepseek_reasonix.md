---
name: deepseek_reasonix
version: '0.1'
category: experimental
status: active
triggers:
- DeepSeek Reasonix
- Reasonix AI agent
- Go coding agent
- migrate Reasonix project
- Reasonix cli
command: python3 /home/junaid-eko/cortex/scripts/synthesized/deepseek_reasonix.py
  {query}
ram_mb: 50
requires:
- nodejs
- npm
source_repo: DeepSeek-Reasonix
source_url: https://github.com/esengine/DeepSeek-Reasonix
synthesized_at: '2026-06-27T12:18:50.118457'
---
# Deepseek Reasonix Skill

DeepSeek-Reasonix is a config- and plugin-driven AI coding agent for the terminal, written in Go. It is optimized for DeepSeek's prefix cache to keep token costs low across long sessions, assisting with coding tasks and project management in Go. This skill allows direct interaction with the Reasonix CLI.

**Source repo:** [DeepSeek-Reasonix](https://github.com/esengine/DeepSeek-Reasonix)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/deepseek_reasonix.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

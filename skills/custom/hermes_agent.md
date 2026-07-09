---
name: hermes_agent
version: '0.1'
category: experimental
status: active
triggers:
- hermes
- model
command: python3 /home/junaid-eko/cortex/scripts/synthesized/hermes_agent.py {query}
ram_mb: 512
requires: []
install_command: pip install hermes-agent
source_repo: hermes-agent
source_url: https://github.com/NousResearch/hermes-agent
synthesized_at: '2026-06-28T17:55:56.838763'
---
# Hermes Agent Skill

The self-improving AI agent built by [Nous Research](https://nousresearch.com). It's the only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

**Source repo:** [hermes-agent](https://github.com/NousResearch/hermes-agent)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/hermes_agent.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

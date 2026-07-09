---
name: opencode_ai
version: '0.1'
category: experimental
status: experimental
triggers:
- opencode
- ai coding agent
command: python3 /home/junaid-eko/cortex/scripts/synthesized/opencode_ai.py {query}
ram_mb: 512
requires: []
install_command: curl -fsSL https://opencode.ai/install | bash
source_repo: opencode
source_url: https://github.com/anomalyco/opencode
synthesized_at: '2026-07-09T10:04:01.484732'
---
# Opencode Ai Skill

The open source AI coding agent.

**Source repo:** [opencode](https://github.com/anomalyco/opencode)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/opencode_ai.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

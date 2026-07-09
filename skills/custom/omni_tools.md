---
name: omni_tools
version: '0.1'
category: experimental
status: active
triggers:
- install
- run
command: python3 /home/junaid-eko/cortex/scripts/synthesized/omni_tools.py {query}
ram_mb: 50
requires: []
install_command: npm install -g omnitools
source_repo: omni-tools
source_url: https://github.com/iib0011/omni-tools
synthesized_at: '2026-07-09T10:02:37.180296'
---
# Omni Tools Skill

A self-hosted web app offering a variety of online tools to simplify everyday tasks.

**Source repo:** [omni-tools](https://github.com/iib0011/omni-tools)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/omni_tools.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

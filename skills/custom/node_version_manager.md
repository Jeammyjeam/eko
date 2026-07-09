---
name: node_version_manager
version: '0.1'
category: experimental
status: active
triggers:
- node
- version
- manager
command: python3 /home/junaid-eko/cortex/scripts/synthesized/node_version_manager.py
  {query}
ram_mb: 512
requires:
- bash
install_command: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.5/install.sh
  | bash
source_repo: nvm
source_url: https://github.com/nvm-sh/nvm
synthesized_at: '2026-06-28T18:17:24.720220'
---
# Node Version Manager Skill

Node Version Manager is a tool that allows you to easily switch between different versions of Node.js on your system. It provides a simple CLI interface and supports installing, updating, listing, and managing multiple versions of Node.js.

**Source repo:** [nvm](https://github.com/nvm-sh/nvm)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/node_version_manager.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

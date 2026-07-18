---
name: nvm_windows
version: '0.1'
category: experimental
status: experimental
triggers:
- node version windows
- windows
command: python3 /home/junaid-eko/cortex/scripts/synthesized/nvm_windows.py {query}
ram_mb: 512
requires: []
install_command: git clone https://github.com/coreybutler/nvm-windows.git && cd nvm-windows
  && npm install
source_repo: nvm-windows
source_url: https://github.com/coreybutler/nvm-windows
synthesized_at: '2026-07-09T10:00:41.157774'
---
# Nvm Windows Skill

The Microsoft/NPM/Google recommended Node.js version manager for Windows.

**Source repo:** [nvm-windows](https://github.com/coreybutler/nvm-windows)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/nvm_windows.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

---
name: electron
version: '0.1'
category: experimental
status: active
triggers:
- electron
- electron app
- desktop app
command: python3 /home/junaid-eko/cortex/scripts/synthesized/electron.py {query}
ram_mb: 200
requires:
- node
- npm
install_command: npm install -g electron
source_repo: electron
source_url: https://github.com/electron/electron
synthesized_at: '2026-06-28T08:49:18.759617'
---
# Electron Skill

This skill wraps the Electron CLI, enabling you to run Electron applications, manage Electron versions, and interact with the Electron framework directly. It requires Node.js and npm to be installed on the system. Be aware that running untrusted Electron applications can pose a security risk as they have full access to your operating system.

**Source repo:** [electron](https://github.com/electron/electron)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/electron.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

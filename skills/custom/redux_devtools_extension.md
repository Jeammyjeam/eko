---
name: redux_devtools_extension
version: '0.1'
category: experimental
status: active
triggers:
- redux-devtools
- devtools-extension
command: python3 /home/junaid-eko/cortex/scripts/synthesized/redux_devtools_extension.py
  {query}
ram_mb: 512
requires: []
install_command: npm i redux-devtools-extension
source_repo: redux-devtools-extension
source_url: https://github.com/zalmoxisus/redux-devtools-extension
synthesized_at: '2026-07-17T13:33:21.331209'
---
# Redux Devtools Extension Skill

A Chrome extension that provides a visual interface for debugging Redux applications.

**Source repo:** [redux-devtools-extension](https://github.com/zalmoxisus/redux-devtools-extension)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/redux_devtools_extension.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

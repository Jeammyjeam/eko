---
name: rod
version: '0.1'
category: experimental
status: experimental
triggers:
- web automation
- scraping
command: python3 /home/junaid-eko/cortex/scripts/synthesized/rod.py {query}
ram_mb: 512
requires: []
install_command: go get github.com/go-rod/rod
source_repo: rod
source_url: https://github.com/go-rod/rod
synthesized_at: '2026-07-17T13:34:15.825328'
---
# Rod Skill

Rod is a high-level driver directly based on DevTools Protocol. It's designed for web automation and scraping for both high-level and low-level use, senior developers can use the low-level packages and functions to easily customize or build up their own version of Rod, the high-level functions are just examples to build a default version of Rod.

**Source repo:** [rod](https://github.com/go-rod/rod)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/rod.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

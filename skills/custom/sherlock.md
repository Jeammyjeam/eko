---
name: sherlock
version: '0.1'
category: experimental
status: active
triggers:
- sherlock
- find social media accounts
- hunt username
command: python3 /home/junaid-eko/cortex/scripts/synthesized/sherlock.py {query}
ram_mb: 50
requires:
- python3
source_repo: sherlock
source_url: https://github.com/sherlock-project/sherlock
synthesized_at: '2026-06-25T14:29:31.798607'
---
# Sherlock Skill

This skill uses the sherlock CLI tool to find social media accounts by username across a wide range of platforms. It is useful for open-source intelligence (OSINT) gathering and social engineering research. The results for found accounts are automatically saved to individual text files named after the username in the current working directory.

**Source repo:** [sherlock](https://github.com/sherlock-project/sherlock)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/sherlock.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

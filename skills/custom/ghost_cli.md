---
name: ghost_cli
version: '0.1'
category: experimental
status: active
triggers:
- install ghost cms
- manage ghost
- ghost cli
- set up ghost
command: python3 /home/junaid-eko/cortex/scripts/synthesized/ghost_cli.py {query}
ram_mb: 512
requires:
- node
- npm
source_repo: Ghost
source_url: https://github.com/TryGhost/Ghost
synthesized_at: '2026-06-27T11:51:00.632092'
---
# Ghost Cli Skill

This skill provides a wrapper for the Ghost CLI tool, allowing for installation, management, and interaction with Ghost CMS instances. It's ideal for setting up local development environments or managing remote Ghost installations. Users should be aware that Ghost itself, once installed and running, will consume system resources (CPU, RAM, disk) for its operation.

**Source repo:** [Ghost](https://github.com/TryGhost/Ghost)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/ghost_cli.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

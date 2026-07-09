---
name: ohmyzsh
version: '0.1'
category: experimental
status: experimental
triggers:
- ohmyzsh
- zsh
command: python3 /home/junaid-eko/cortex/scripts/synthesized/ohmyzsh.py {query}
ram_mb: 50
requires: []
install_command: curl -L https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh
  | sh
source_repo: ohmyzsh
source_url: https://github.com/ohmyzsh/ohmyzsh
synthesized_at: '2026-07-09T10:01:30.321985'
---
# Ohmyzsh Skill

Oh My Zsh is an open source, community-driven framework for managing your zsh configuration.

**Source repo:** [ohmyzsh](https://github.com/ohmyzsh/ohmyzsh)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/ohmyzsh.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

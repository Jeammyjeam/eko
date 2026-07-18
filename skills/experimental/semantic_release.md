---
name: semantic_release
version: '0.1'
category: experimental
status: experimental
triggers:
- release
- version
command: python3 /home/junaid-eko/cortex/scripts/synthesized/semantic_release.py {query}
ram_mb: 512
requires: []
install_command: npm install semantic-release -g
source_repo: semantic-release
source_url: https://github.com/semantic-release/semantic-release
synthesized_at: '2026-07-18T15:36:26.237206'
---
# Semantic Release Skill

Fully automated version management and package publishing. This removes the immediate connection between human emotions and version numbers, strictly following the Semantic Versioning specification and communicating the impact of changes to consumers.

**Source repo:** [semantic-release](https://github.com/semantic-release/semantic-release)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/semantic_release.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

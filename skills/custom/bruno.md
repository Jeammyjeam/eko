---
name: bruno
version: '0.1'
category: experimental
status: active
triggers:
- bruno
- api client
- test api
- api development
- api requests
command: python3 /home/junaid-eko/cortex/scripts/synthesized/bruno.py {query}
ram_mb: 50
requires: null
install_command: snap install brun
source_repo: bruno
source_url: https://github.com/usebruno/bruno
synthesized_at: '2026-06-28T08:32:53.067887'
---
# Bruno Skill

This skill wraps Bruno, an open-source API client for exploring and testing APIs. It stores collections directly on the filesystem using a plain text markup language (Bru), facilitating collaboration via version control. Bruno is offline-only, prioritizing data privacy. This skill provides a basic invocation path, expecting further CLI commands or file paths via the query.

**Source repo:** [bruno](https://github.com/usebruno/bruno)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/bruno.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

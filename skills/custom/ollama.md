---
name: ollama
version: '0.1'
category: experimental
status: active
triggers:
- start building with open models
- download
- get started
- launch claude
- ollama launch claude
- ollama launch openclaw
- ollama run gemma4
command: python3 /home/junaid-eko/cortex/scripts/synthesized/ollama.py {query}
ram_mb: 512
requires: []
install_command: curl -fsSL https://ollama.com/install.sh | sh
source_repo: ollama
source_url: https://github.com/ollama/ollama
synthesized_at: '2026-07-09T10:02:06.842829'
---
# Ollama Skill

Start building with open models.

**Source repo:** [ollama](https://github.com/ollama/ollama)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/ollama.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

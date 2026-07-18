---
name: llm_app
version: '0.1'
category: experimental
status: experimental
triggers:
- LLM
- llm application
- Enterprise Search
command: python3 /home/junaid-eko/cortex/scripts/synthesized/llm_app.py {query}
ram_mb: 512
requires: []
install_command: pip install llm-app
source_repo: llm-app
source_url: https://github.com/pathwaycom/llm-app
synthesized_at: '2026-06-28T18:08:03.531502'
---
# Llm App Skill

The Pathway Live Data Framework's AI Pipelines allow you to quickly put in production AI applications that offer high-accuracy RAG and AI enterprise search at scale using the most up-to-date knowledge available in your data sources. It provides you ready-to-deploy LLM (Large Language Model) App Templates. You can test them on your own machine and deploy on-cloud (GCP, AWS, Azure, Render,...) or on-premises.

**Source repo:** [llm-app](https://github.com/pathwaycom/llm-app)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/llm_app.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

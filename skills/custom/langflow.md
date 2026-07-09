---
name: langflow
version: '0.1'
category: experimental
status: active
triggers:
- langflow
- ai-ml
command: python3 /home/junaid-eko/cortex/scripts/synthesized/langflow.py {query}
ram_mb: 50
requires: []
install_command: pip install langflow
source_repo: langflow
source_url: https://github.com/langflow-ai/langflow
synthesized_at: '2026-06-28T18:05:22.893389'
---
# Langflow Skill

Langflow is a powerful platform for building and deploying AI-powered agents and workflows. It provides developers with both a visual authoring experience and built-in API and MCP servers that turn every workflow into a tool that can be integrated into applications built on any framework or stack. Langflow comes with batteries included and supports all major LLMs, vector databases and a growing library of AI tools.

**Source repo:** [langflow](https://github.com/langflow-ai/langflow)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/langflow.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

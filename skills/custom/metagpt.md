---
name: metagpt
version: '0.1'
category: experimental
status: active
triggers:
- metagpt
- multi-agent system
- agentic workflow
- ai agent development
- software company
command: python3 /home/junaid-eko/cortex/scripts/synthesized/metagpt.py {query}
ram_mb: 50
requires:
- python3.9-3.11
- node
- pnpm
source_repo: MetaGPT
source_url: https://github.com/FoundationAgents/MetaGPT
synthesized_at: '2026-06-27T13:29:37.199437'
---
# Metagpt Skill

MetaGPT is a multi-agent framework that takes a one-line requirement and outputs artifacts like user stories, requirements, and APIs by simulating a software company with various AI roles. It automates agentic workflow generation and complex task collaboration, serving as a natural language programming product. Installation requires Python 3.9-3.11, Node.js, and pnpm before running 'pip install metagpt'.

**Source repo:** [MetaGPT](https://github.com/FoundationAgents/MetaGPT)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/metagpt.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

---
name: copilotkit
version: '0.1'
category: experimental
status: active
triggers:
- copilotkit
- agent-native app
- generative ui
- human-in-the-loop
command: python3 /home/junaid-eko/cortex/scripts/synthesized/copilotkit.py {query}
ram_mb: 50
requires:
- node
source_repo: CopilotKit
source_url: https://github.com/CopilotKit/CopilotKit
synthesized_at: '2026-06-27T12:18:35.685372'
---
# Copilotkit Skill

This skill wraps the CopilotKit CLI tool, enabling the creation and management of agent-native applications. It supports Generative UI, shared state, and human-in-the-loop workflows across various frameworks like React, Angular, and Vue. Users can leverage this skill to quickly scaffold new CopilotKit projects and interact with its features.

**Source repo:** [CopilotKit](https://github.com/CopilotKit/CopilotKit)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/copilotkit.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

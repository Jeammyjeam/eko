---
name: openclaw
version: '0.1'
category: experimental
status: active
triggers:
- openclaw
- ai assistant
command: python3 /home/junaid-eko/cortex/scripts/synthesized/openclaw.py {query}
ram_mb: 512
requires: []
install_command: git clone https://github.com/openclaw/openclaw.git && cd openclaw
  && make install
source_repo: openclaw
source_url: https://github.com/openclaw/openclaw
synthesized_at: '2026-07-09T10:03:24.171316'
---
# Openclaw Skill

OpenClaw is a personal AI assistant you run on your own devices. It answers you on the channels you already use. It can speak and listen on macOS/iOS/Android, and can render a live Canvas you control. The Gateway is just the control plane — the product is the assistant.

**Source repo:** [openclaw](https://github.com/openclaw/openclaw)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/openclaw.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

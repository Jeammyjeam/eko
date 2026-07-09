---
name: swe_agent
version: '0.1'
category: experimental
status: active
triggers:
- swe-agent
- fix github issue
- find vulnerability
- autonomous task
command: python3 /home/junaid-eko/cortex/scripts/synthesized/swe_agent.py {query}
ram_mb: 500
requires:
- python3
- git
install_command: git clone https://github.com/SWE-agent/SWE-agent.git && cd SWE-agent
  && python3 -m pip install --upgrade pip && pip install --editable .
source_repo: SWE-agent
source_url: https://github.com/SWE-agent/SWE-agent
synthesized_at: '2026-06-28T08:10:48.694153'
---
# Swe Agent Skill

SWE-agent is an AI agent that autonomously uses tools to fix issues in GitHub repositories, find cybersecurity vulnerabilities, or perform custom tasks. This skill provides a wrapper for the SWE-agent CLI. Note: The developers now recommend mini-swe-agent for new projects, which offers similar performance with greater simplicity.

**Source repo:** [SWE-agent](https://github.com/SWE-agent/SWE-agent)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/swe_agent.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

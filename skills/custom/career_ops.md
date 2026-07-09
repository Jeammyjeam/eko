---
name: career_ops
version: '0.1'
category: experimental
status: active
triggers:
- job search
- career automation
- ai job applications
- career-ops
command: python3 /home/junaid-eko/cortex/scripts/synthesized/career_ops.py {query}
ram_mb: 100
requires:
- node
- npm
install_command: npm install -g @santifer/career-ops
source_repo: career-ops
source_url: https://github.com/santifer/career-ops
synthesized_at: '2026-06-28T08:32:47.619257'
---
# Career Ops Skill

This skill wraps the Career-Ops CLI tool, an AI-driven multi-agent system designed to automate and optimize the job search process. It empowers job seekers with advanced AI for strategic company selection, profile matching, and personalized application generation. Users should carefully review and verify all outputs and automated actions before final submission.

**Source repo:** [career-ops](https://github.com/santifer/career-ops)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/career_ops.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

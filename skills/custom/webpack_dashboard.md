---
name: webpack_dashboard
version: '0.1'
category: experimental
status: active
triggers:
- webpack
- dev server
command: python3 /home/junaid-eko/cortex/scripts/synthesized/webpack_dashboard.py
  {query}
ram_mb: 512
requires:
- Node 8 or above
install_command: npm install --save-dev webpack-dashboard
source_repo: webpack-dashboard
source_url: https://github.com/FormidableLabs/webpack-dashboard
synthesized_at: '2026-07-18T16:46:35.142160'
---
# Webpack Dashboard Skill

A CLI dashboard for your webpack dev server

**Source repo:** [webpack-dashboard](https://github.com/FormidableLabs/webpack-dashboard)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/webpack_dashboard.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

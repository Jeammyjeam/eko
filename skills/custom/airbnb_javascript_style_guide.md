---
name: airbnb_javascript_style_guide
version: '0.1'
category: experimental
status: active
triggers:
- airbnb
- javascript
- style guide
command: python3 /home/junaid-eko/cortex/scripts/synthesized/airbnb_javascript_style_guide.py
  {query}
ram_mb: 50
requires:
- Babel
- babel-preset-airbnb
- airbnb-browser-shims
install_command: npm install eslint-config-airbnb --save-dev
source_repo: javascript
source_url: https://github.com/airbnb/javascript
synthesized_at: '2026-06-28T18:01:40.513997'
---
# Airbnb Javascript Style Guide Skill

This guide is available in other languages too. See [Translation](#translation)

**Source repo:** [javascript](https://github.com/airbnb/javascript)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/airbnb_javascript_style_guide.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

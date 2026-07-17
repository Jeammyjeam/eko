---
name: apilayer_unified_suite
version: '0.1'
category: experimental
status: active
triggers:
- geocode
- validate email
- fetch flight
- pull stock market data
- scrape search result
command: python3 /home/junaid-eko/cortex/scripts/synthesized/apilayer_unified_suite.py
  {query}
ram_mb: 512
requires: []
install_command: git clone https://github.com/public-apis/public-apis.git
source_repo: public-apis
source_url: https://github.com/public-apis/public-apis
synthesized_at: '2026-07-16T15:31:55.577788'
---
# Apilayer Unified Suite Skill

APILayer unified suite allows you to integrate production-grade REST APIs using One Account, One Dashboard, and One API key.

**Source repo:** [public-apis](https://github.com/public-apis/public-apis)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/apilayer_unified_suite.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

---
name: web_search
version: 1.1
category: core
status: active
triggers:
  - search
  - latest
  - news
  - current
  - google
command: python3 /home/junaid-eko/cortex/scripts/web_search.py "{query}"
ram_mb: 0
requires: []
---

# Web Search Skill
Search the web privately using DuckDuckGo via ddgs library.
Returns titles, URLs, and snippets from top 5 results.

---
name: mock_service_worker
version: '0.1'
category: experimental
status: active
triggers:
- mock
- api mocking
command: python3 /home/junaid-eko/cortex/scripts/synthesized/mock_service_worker.py
  {query}
ram_mb: 50
requires: []
install_command: npm install msw
source_repo: msw
source_url: https://github.com/mswjs/msw
synthesized_at: '2026-06-28T18:15:28.759278'
---
# Mock Service Worker Skill

MSW is an industry standard API mocking for JavaScript. It allows you to intercept requests and respond with necessary status codes, headers, cookies, delays, or completely custom resolvers.

**Source repo:** [msw](https://github.com/mswjs/msw)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/mock_service_worker.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

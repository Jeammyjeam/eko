---
name: hotel
version: '0.1'
category: experimental
status: active
triggers:
- start apps
- local domains
- remote servers
command: python3 /home/junaid-eko/cortex/scripts/synthesized/hotel.py {query}
ram_mb: 50
requires:
- Node.js
install_command: npm install -g hotel && hotel start
source_repo: hotel
source_url: https://github.com/typicode/hotel
synthesized_at: '2026-06-28T17:56:49.961500'
---
# Hotel Skill

Start apps from your browser and use local domains/https automatically. Works great on any OS (macOS, Linux, Windows) and with all servers :heart:.

**Source repo:** [hotel](https://github.com/typicode/hotel)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/hotel.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.

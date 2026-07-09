# Eko

A self-evolving personal AI OS that runs entirely on your local machine — no cloud required, no GPU needed, no API bills.

Eko discovers open-source repos, learns what they do, and autonomously synthesizes them into reusable skills. Every 30 minutes it gets smarter on its own.

## What it does

- **Discovers** GitHub repos and extracts their capabilities into a queryable knowledge base
- **Synthesizes** new skills automatically from repos — wrapping CLI tools into its active skill set
- **Validates** every skill through a safety pipeline before it goes live (structure → sandbox → hardware check)
- **Evolves** autonomously via a heartbeat loop — finds work, does it, logs results, repeats
- **Answers** natural language queries via RAG search over its own accumulated knowledge

## Why Eko

Most AI agent frameworks assume cloud access, high-end hardware, or fat API budgets. Eko was built under real constraints and optimized for them:

- **Local-first inference** via Ollama — synthesis runs on CPU with no API quota
- **Dual-model adversarial loop** — one model proposes, a second audits, consensus required before any change lands
- **Hardware-aware promotion** — checks your available RAM and disk before installing anything
- **Structured memory** — PostgreSQL + pgvector, not just markdown files

## Requirements

- Ubuntu 20.04+ (or WSL2 on Windows)
- Python 3.10+
- PostgreSQL 14+
- Ollama with `qwen2.5-coder:1.5b` pulled
- 2GB RAM minimum (4GB recommended)

## Quick start

See [INSTALL.md](INSTALL.md) for full prerequisites and setup guide.


```bash
git clone https://github.com/Jeammyjeam/eko.git
cd eko
cp .env.example .env
# Edit .env with your credentials
pip install -r requirements.txt --break-system-packages
python3 scripts/health_monitor.py
```

## Architecture
GitHub Repos ──► Capability Extractor ──► PostgreSQL + pgvector
│
RAG Query Engine
│
Heartbeat (30min) ──► Skill Synthesizer ──► Promoter ──► Active Skills
│                                  │
Ollama/Qwen                    Orchestrator
│
Telegram / CLI
## Stack

- **Runtime:** Python 3.12, PostgreSQL 16, pgvector
- **Local AI:** Ollama (qwen2.5-coder:1.5b)
- **Gateway AI (optional):** Hermes Agent — supports Gemini, OpenAI, Anthropic, Groq, and more
- **Automation:** PM2, cron, n8n
- **Networking:** Tailscale

## Built by

AbdulMumeen Junaid-Eko — AI Integration Developer  
[github.com/Jeammyjeam](https://github.com/Jeammyjeam)

## Contact

Found a bug or have questions? Open a GitHub issue or reach out:  
- abdulmumeenjunaideko@gmail.com  
- jjeam140@gmail.com

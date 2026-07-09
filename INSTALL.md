# Eko Installation Guide

## Prerequisites

### 1. System
- Ubuntu 20.04+ or WSL2 on Windows
- Python 3.10+
- Node.js 18+ (for PM2)
- Git

### 2. PostgreSQL + pgvector
```bash
sudo apt install postgresql-16 postgresql-16-pgvector -y
sudo -u postgres psql -c "CREATE USER cortex WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE projectdb OWNER cortex;"
sudo -u postgres psql -d projectdb -c "CREATE EXTENSION vector;"
```

### 3. Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:1.5b
```

### 4. PM2
```bash
npm install -g pm2
```

### 5. Hermes Agent (optional — for multi-channel gateway)
```bash
pip install hermes-agent
hermes gateway setup
```

## Setup

```bash
git clone https://github.com/Jeammyjeam/eko.git
cd eko
cp .env.example .env
# Edit .env with your credentials
pip install -r requirements.txt --break-system-packages
```

## Auto-start on boot (WSL2)

Copy the boot script:
```bash
sudo cp scripts/cortex-boot.sh /usr/local/bin/cortex-boot.sh
sudo chmod +x /usr/local/bin/cortex-boot.sh
```

Add to `/etc/wsl.conf`:
```ini
[boot]
command="/usr/local/bin/cortex-boot.sh"
```

Then save the PM2 process list:
```bash
pm2 start scripts/heartbeat.py --name heartbeat --interpreter python3
pm2 save
```

## Verify

```bash
python3 scripts/health_monitor.py
```

Should return `"status": "GREEN"`.

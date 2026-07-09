# CORTEX PC Control Layer

## Tailscale IP: 100.120.242.76
## SSH Port: 2222
## SSH User: junaid-eko
## Key: ~/.ssh/cortex_phone (private), ~/.ssh/cortex_phone.pub (public)

## Connect from anywhere:
ssh -p 2222 -i ~/.ssh/cortex_phone junaid-eko@100.120.242.76

## Phone setup (Termux):
1. Install Termux from F-Droid
2. pkg install openssh
3. Copy cortex_phone private key to ~/.ssh/cortex_phone
4. chmod 600 ~/.ssh/cortex_phone
5. ssh -p 2222 -i ~/.ssh/cortex_phone junaid-eko@100.120.242.76

## Windows Auto-Startup
Task Scheduler task "CORTEX Startup" runs on every Windows login.
Fires: wsl.exe -d Ubuntu-24.04 -e bash -c 'sleep 15 && source ~/.bashrc'
Starts: PostgreSQL, SSH, n8n (PM2), Gitea, Hermes gateway, Streamlit, Docker, MTU fix

To verify: Task Scheduler → Task Scheduler Library → CORTEX Startup
To disable: Disable-ScheduledTask -TaskName "CORTEX Startup"
To re-enable: Enable-ScheduledTask -TaskName "CORTEX Startup"

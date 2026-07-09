#!/bin/bash
# CORTEX WSL2 Boot Script — runs on every WSL start

# DNS

# MTU fix for WSL2 network
ip link set dev eth0 mtu 1350 2>/dev/null

# Cron
service cron start 2>/dev/null

# Tailscale
tailscaled --state=/var/lib/tailscale/tailscaled.state &>/dev/null &
sleep 3
tailscale up --accept-routes &>/dev/null

# Tailscale funnel for Streamlit
sleep 2
tailscale funnel --bg 8501 &>/dev/null

python3 /home/junaid-eko/cortex/scripts/system_profile.py > /dev/null 2>&1
echo "CORTEX boot complete" >> /var/log/cortex-boot.log

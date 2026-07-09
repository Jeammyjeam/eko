# CORTEX Android Edge Node Setup

## Prerequisites
- Termux installed from F-Droid (NOT Play Store)
- Tailscale installed and connected to tailnet
- Phone on same Tailscale network as PC (100.120.242.76)

## Step 1: Bootstrap Termux
```bash
pkg update && pkg upgrade -y
pkg install python clang make openssh git tmux -y
pip install psycopg2-binary psutil
```

## Step 2: Verify Tailscale connection
```bash
ping 100.120.242.76
```

## Step 3: Get edge worker script
```bash
scp -P 2222 junaid-eko@100.120.242.76:~/cortex/scripts/edge_worker.py ~/edge_worker.py
```

## Step 4: Run worker
```bash
termux-wake-lock
tmux new -s cortex-edge
python edge_worker.py
```

## Step 5: Keep alive
- Settings → Apps → Termux → Battery → Unrestricted
- Keep termux-wake-lock running

## Task targeting
To send task to Android edge node specifically:
```sql
INSERT INTO cortex_task_queue (task_type, payload)
VALUES ('web_search', '{"query": "test", "target_node": "android_edge"}');
```

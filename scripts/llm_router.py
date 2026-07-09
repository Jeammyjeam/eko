import requests
import json
import os
import psutil
import time
import sys
sys.path.insert(0, '/home/junaid-eko/cortex/scripts')
from telemetry import log_action, Timer
from pathlib import Path

CORTEX_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_URL = "http://localhost:8642/v1/chat/completions"
PRIMARY_KEY = "cortex-local-key"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def get_ollama_model():
    config_path = CORTEX_ROOT / "config" / "runtime_profile.json"
    try:
        with open(config_path) as f:
            profile = json.load(f)
            return profile.get("ollama_fallback_model", "qwen2.5-coder:3b")
    except:
        return "qwen2.5-coder:3b"

def call_intelligence(prompt, system_instruction="You are CORTEX, a personal AI OS assistant."):
    # Tunnel A — Hermes/Gemini
    t = Timer()
    try:
        response = requests.post(
            PRIMARY_URL,
            headers={"Authorization": f"Bearer {PRIMARY_KEY}", "Content-Type": "application/json"},
            json={
                "model": "hermes",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("hermes", {}).get("failed"):
                print("Tunnel A quota exceeded — falling back to Ollama...")
                raise requests.exceptions.ConnectionError("quota exceeded")
            result = data["choices"][0]["message"]["content"]
            log_action("llm_router", prompt[:50], "Gemini-TunnelA", t.elapsed_ms(), "SUCCESS")
            return result, "hermes"
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("Tunnel A offline — falling back to Ollama...")

    # Tunnel B — Local Ollama fallback
    available_ram = psutil.virtual_memory().available / (1024**3)
    if available_ram < 0.5:
        return "ERROR: Insufficient RAM for local model fallback.", "none"

    model = get_ollama_model()
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": f"{system_instruction}\n\nUser: {prompt}", "stream": False},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()["response"]
            log_action("llm_router", prompt[:50], f"Ollama-TunnelB:{model}", t.elapsed_ms(), "SUCCESS")
            return result, f"ollama:{model}"
    except Exception as e:
        pass

    return "CRITICAL: Both intelligence tunnels offline.", "none"

if __name__ == "__main__":
    print("Testing LLM Router...")
    result, source = call_intelligence("What is CORTEX?")
    print(f"Source: {source}")
    print(f"Response: {result[:200]}")

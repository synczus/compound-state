#!/usr/bin/env python3
"""Perplexity search via OpenRouter — call this for web-grounded research.
Usage: python3 perplexity_search.py "your research question"
"""
import json, os, sys, urllib.request

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY:
    # Fallback: read from .env
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What's new in crypto markets today?"
payload = json.dumps({
    "model": "perplexity/sonar-pro",
    "messages": [{"role": "user", "content": query}],
    "max_tokens": 2000
}).encode()

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=payload,
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/synczus/kestrel",
    }
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"]
    # Clean token usage
    usage = data.get("usage", {})
    cost = (usage.get("prompt_tokens", 0) * 3 + usage.get("completion_tokens", 0) * 15) / 1_000_000
    print(f"## Perplexity Search Results\n\n{content}\n\n---\n*Cost: ~${cost:.4f} | Tokens: {usage.get('total_tokens', '?')}*")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
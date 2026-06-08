#!/usr/bin/env python3
"""OpenRouter Budget Check — runs every 4h, reports daily spend to dashboard."""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

KESTREL = Path(__file__).resolve().parent.parent
STATE_FILE = KESTREL / "data" / "openrouter-budget.json"

API_KEY = os.environ.get("OPENROUTER", "") or os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY:
    for env_path in [KESTREL / ".env", Path.home() / ".hermes" / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "OPENROUTER" in line and "=" in line and not line.startswith("#"):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and val != "YOUR_KEY_HERE":
                        API_KEY = val
                        break
        if API_KEY:
            break

if not API_KEY:
    print("NO_KEY")
    exit(1)

try:
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())

    budget = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_credits": data.get("data", {}).get("total_credits", 0),
        "usage": data.get("data", {}).get("usage", 0),
        "limit": data.get("data", {}).get("limit", 0),
        "remaining": data.get("data", {}).get("remaining", 0),
        "is_free": data.get("data", {}).get("is_free", True),
        "daily_budget": None,
    }

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(budget, indent=2))
    print(f"OpenRouter: ${budget['usage']:.2f} used, ${budget['remaining']:.2f} remaining")

except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
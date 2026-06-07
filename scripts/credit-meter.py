#!/usr/bin/env python3
"""
OpenRouter Credit Meter — posts a visual meter to the AI Hangout group
every 30 minutes showing daily credit usage.
"""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERMES_ENV = Path("/home/synczus/.hermes/.env")
EVENT_BUS = Path("/home/synczus/kestrel/event-bus.md")

def get_openrouter_usage():
    """Fetch OpenRouter key stats."""
    # Read API key
    api_key = None
    if HERMES_ENV.exists():
        for line in HERMES_ENV.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break
    
    if not api_key:
        return None, "No API key found"
    
    try:
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "5", "https://openrouter.ai/api/v1/auth/key",
             "-H", f"Authorization: Bearer {api_key}"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        d = data.get("data", {})
        return d, None
    except Exception as e:
        return None, str(e)

def generate_meter(used_money, daily_cap=30.0):
    """Create a visual meter string."""
    pct = min(100, (used_money / daily_cap) * 100)
    bars = 20
    filled = int((pct / 100) * bars)
    empty = bars - filled
    
    # Color coding
    if pct >= 90:
        color = "🔴"
    elif pct >= 70:
        color = "🟡"
    else:
        color = "🟢"
    
    bar = "█" * filled + "░" * empty
    remaining = daily_cap - used_money
    
    return f"{color} **OR Meter** `[{bar}]` ${used_money:.2f}/${daily_cap:.2f} (${remaining:.2f} left)"

def main():
    data, error = get_openrouter_usage()
    now = datetime.now(timezone.utc)
    
    if error or not data:
        msg = f"🔴 **OR Meter** — Offline: {error or 'No data'}"
        print(msg)
        return msg
    
    used_daily = data.get("usage_daily", 0)
    used_weekly = data.get("usage_weekly", 0)
    used_total = data.get("usage", 0)
    
    daily_cap = 30.0
    meter = generate_meter(used_daily, daily_cap)
    
    # Full message
    msg = (
        f"{meter}\n"
        f"📅 Week: ${used_weekly:.2f}  |  🏷️ Total: ${used_total:.2f}"
    )
    
    # Log to event bus
    ts = now.strftime("%Y-%m-%d %H:%M UTC")
    with open(EVENT_BUS, "a") as f:
        f.write(f"\n{ts} | credit-meter | ${used_daily:.2f}/{daily_cap:.2f} today")
    
    print(msg)
    return msg

if __name__ == "__main__":
    main()
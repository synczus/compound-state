#!/usr/bin/env python3
# Hephaestus Event Bus — structured tick publisher
# Agents subscribe. WolfWatch consumes. No single process owns truth.

import json
import sys
import os
from datetime import datetime

EVENT_LOG = "/var/log/hephaestus/event_bus.log"

def publish(tick: dict):
    """Publish a normalized tick to the event bus"""
    os.makedirs(os.path.dirname(EVENT_LOG), exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "tick": tick
    }
    with open(EVENT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

def tail(n: int = 10):
    """Tail last n events from the bus"""
    if not os.path.exists(EVENT_LOG):
        return []
    with open(EVENT_LOG) as f:
        lines = f.readlines()
    return [json.loads(l) for l in lines[-n:]]

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "tail"
    if mode == "publish":
        tick = json.loads(sys.stdin.read())
        result = publish(tick)
        print(json.dumps(result))
    elif mode == "tail":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for e in tail(n):
            print(json.dumps(e))
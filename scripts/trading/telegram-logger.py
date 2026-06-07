#!/usr/bin/env python3
"""
Telegram conversation logger — feeds group chat to hop agents
Tails Kairos gateway logs, extracts messages, writes to structured log file
"""
import os
import json
import re
import time
import subprocess
from datetime import datetime

LOG_FILE = "/home/synczus/kestrel/telegram-log/conversation.jsonl"
KESTREL = "/home/synczus/kestrel"

def extract_messages():
    """Extract recent messages from gateway logs"""
    msgs = []
    # Check all gateway logs for Telegram messages
    log_paths = [
        "/home/synczus/.hermes/profiles/kairos/logs/agent.log",
        "/home/synczus/.hermes/profiles/shannon/logs/agent.log",
    ]
    for path in log_paths:
        if os.path.exists(path):
            try:
                r = subprocess.run(["tail", "-200", path], capture_output=True, text=True, timeout=5)
                for line in r.stdout.split("\n"):
                    if "inbound message" in line and "telegram" in line:
                        msgs.append(line)
            except:
                pass
    return msgs

def parse_message(line):
    """Parse a log line into structured message"""
    # Pattern: 2026-06-07 15:55:06,317 INFO ... msg='text'
    match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*user=(\S+).*chat=(-?\d+).*msg=\'(.*?)\'', line)
    if match:
        return {
            "timestamp": match.group(1),
            "user": match.group(2),
            "chat": match.group(3),
            "text": match.group(4)[:500],  # truncate long messages
            "source": "telegram"
        }
    return None

def write_to_log(entry):
    """Append structured message to JSONL log"""
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def update_hop_feed():
    """Write the latest conversation to a file Grok can consume"""
    # Read last 50 lines of log
    if not os.path.exists(LOG_FILE):
        return
    
    try:
        r = subprocess.run(["tail", "-50", LOG_FILE], capture_output=True, text=True, timeout=3)
        lines = r.stdout.strip().split("\n")
        conversation = []
        for line in lines:
            if line.strip():
                conversation.append(json.loads(line))
        
        # Write as pretty JSON array for agents
        feed = {
            "updated_at": datetime.now().isoformat(),
            "agent_count": len(conversation),
            "recent_messages": conversation[-20:] if conversation else []
        }
        with open("/home/synczus/kestrel/telegram-log/feed.json", "w") as f:
            json.dump(feed, f, indent=2)
    except:
        pass

def main():
    # Run once — seed the log with recent messages
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    messages = extract_messages()
    seen = set()
    if os.path.exists(LOG_FILE):
        try:
            for line in open(LOG_FILE).read().split("\n"):
                if line.strip():
                    try:
                        seen.add(json.loads(line).get("text", ""))
                    except:
                        pass
        except:
            pass
    
    for msg in messages:
        parsed = parse_message(msg)
        if parsed and parsed["text"] not in seen:
            write_to_log(parsed)
            seen.add(parsed["text"])
    
    update_hop_feed()
    print(f"✅ Logged {len(messages)} messages, {len(seen)} unique")

if __name__ == "__main__":
    main()

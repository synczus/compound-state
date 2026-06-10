#!/usr/bin/env python3
"""
Meta-Monitor v1 — checks all cron heartbeats, alerts WolfWatch on stale.
Runs every 15 minutes via cron.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HEARTBEAT_DIR = Path("/home/synczus/kestrel/cron-health")
WOLFWATCH_URL = "http://127.0.0.1:18790/notify"
EVENT_BUS = Path("/home/synczus/kestrel/event-bus.md")

# Expected cron jobs and their max silence thresholds (seconds)
EXPECTED_CRONS = {
    "squirrel-inbox-feeder": 2400,                   # 40 min grace (runs every 30 min per Jun 7 reduction)
    "auto-git-sync": 15000,                          # 4h10m grace (runs every 4h via auto-git.sh)
    "or-budget-monitor": 14400,                      # 4h grace
    "dashboard-aggregator": 3600,                    # 1h grace
    "meta-monitor": 3600,                            # itself — 1h grace
}

# Also check by PID for running services
SERVICE_CHECKS = {
    "kestrel-striker.service": "systemctl --user is-active",
    "wolfwatch": "systemctl --user is-active wolfwatch-receiver",
}

def send_alert(message: str):
    """POST alert to WolfWatch receiver. Falls back to event-bus."""
    try:
        import urllib.request
        payload = json.dumps({"message": message, "source": "meta-monitor", "severity": "warning"}).encode()
        req = urllib.request.Request(WOLFWATCH_URL, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        # Fallback: write to event-bus
        with open(EVENT_BUS, "a") as f:
            f.write(f"\n⚠️ meta-monitor: WolfWatch unreachable ({e}) — alert missed: {message}")

def log_event(message: str):
    """Log to event-bus.md."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(EVENT_BUS, "a") as f:
        f.write(f"\n{ts} | meta-monitor | {message}")

def check_heartbeats():
    """Check all expected heartbeats for freshness."""
    now = int(datetime.now(timezone.utc).timestamp())
    alerts = []

    for name, max_age in EXPECTED_CRONS.items():
        hb_file = HEARTBEAT_DIR / f"{name}.heartbeat"
        if not hb_file.exists():
            alerts.append(f"⚠️ Cron '{name}' has never written a heartbeat")
            continue

        try:
            data = json.loads(hb_file.read_text())
            age = now - data.get("epoch", 0)
            if age > max_age:
                alerts.append(f"🔴 Cron '{name}' stale — {age // 60}m since last run (max {max_age // 60}m)")
        except (json.JSONDecodeError, KeyError) as e:
            alerts.append(f"⚠️ Cron '{name}' heartbeat corrupted: {e}")

    return alerts

def check_services():
    """Check systemd services are alive."""
    alerts = []
    for name, cmd in SERVICE_CHECKS.items():
        try:
            result = subprocess.run(cmd.split() + [name], capture_output=True, text=True, timeout=10)
            if "active" not in result.stdout.lower():
                alerts.append(f"🔴 Service '{name}' is not active: {result.stdout.strip()}")
        except Exception as e:
            alerts.append(f"⚠️ Service check '{name}' failed: {e}")
    return alerts

def write_heartbeat():
    """Write our own heartbeat."""
    os.makedirs(HEARTBEAT_DIR, exist_ok=True)
    hb = {
        "name": "meta-monitor",
        "status": "ok",
        "last_run": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "epoch": int(datetime.now(timezone.utc).timestamp())
    }
    (HEARTBEAT_DIR / "meta-monitor.heartbeat").write_text(json.dumps(hb, indent=2))

def main():
    os.makedirs(HEARTBEAT_DIR, exist_ok=True)

    # Write our heartbeat FIRST so we don't deadlock on our own stale-check
    write_heartbeat()

    alerts = []
    alerts.extend(check_heartbeats())
    alerts.extend(check_services())

    if alerts:
        for alert in alerts:
            send_alert(alert)
            log_event(alert)
            print(alert)
        sys.exit(1)
    else:
        log_event("All crons and services healthy")
        print("All healthy")

if __name__ == "__main__":
    main()
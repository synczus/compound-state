#!/usr/bin/env python3
"""Kestrel freshness watchdog — checks that recent scrapes exist and alerts on stale pipelines."""
import json, os, time
from pathlib import Path

LOGDIR = Path("/home/synczus/kestrel/logs/cron")
ALERT_FILE = Path("/home/synczus/kestrel/cycle-state/alerts.json")
THRESHOLDS = {
    "rss-all-adapter": 14400,     # 4h
    "tldr-scraper": 86400,        # 24h
    "score_batch": 1800,          # 30min
    "compound-pulse": 3600,       # 1h
    "freshness-watchdog": 120,    # 2min
}

alerts = []
now = time.time()

for job, max_age in THRESHOLDS.items():
    logfile = LOGDIR / f"{job}.log"
    if not logfile.exists():
        alerts.append({"job": job, "status": "NO_LOG", "age": -1})
        continue
    mtime = logfile.stat().st_mtime
    age = now - mtime
    if age > max_age:
        alerts.append({"job": job, "status": "STALE", "age_seconds": int(age), "max_seconds": max_age})

# Write alerts
if alerts:
    alert_data = {"alerts": alerts, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))}
    ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALERT_FILE.write_text(json.dumps(alert_data, indent=2))
    print(f"WARNING: {len(alerts)} stale job(s)")
else:
    if ALERT_FILE.exists():
        ALERT_FILE.unlink()
    print("HEALTH_OK: all jobs fresh")

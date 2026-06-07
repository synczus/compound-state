#!/usr/bin/env python3
"""
Dashboard Aggregator — produces cron-health.json and cost-state.json
for the monitoring dashboard to consume.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

HEARTBEAT_DIR = Path("/home/synczus/kestrel/cron-health")
OUTPUT_DIR = Path("/home/synczus/kestrel/dashboard")
EVENT_BUS = Path("/home/synczus/kestrel/event-bus.md")

EXPECTED_CRONS = {
    "thought-drop-voice-every-12h": {"freq": "12h", "max_age": 86400, "label": "🎤 Voice Drop"},
    "market-pulse-every-12h": {"freq": "12h", "max_age": 86400, "label": "📊 Market Pulse"},
    "squirrel-inbox-feeder": {"freq": "5min", "max_age": 1200, "label": "📁 Squirrel Feeder"},
    "hlm-scraper-every-6h": {"freq": "6h", "max_age": 43200, "label": "📋 HLM Scraper"},
    "agent-pulse-sync": {"freq": "10min", "max_age": 3600, "label": "🔄 Pulse Sync"},
    "auto-git-sync": {"freq": "1h", "max_age": 7200, "label": "📤 Git Sync"},
    "meta-monitor": {"freq": "15min", "max_age": 3600, "label": "🔍 Meta-Monitor"},
    "state-probe": {"freq": "10min", "max_age": 3600, "label": "🔎 State Probe"},
    "or-budget-monitor": {"freq": "1h", "max_age": 14400, "label": "💰 Budget Monitor"},
}

# Also check systemd services
SERVICES = {
    "kestrel-striker.service": "🔭 Striker",
    "wolfwatch-receiver.service": "🐺 WolfWatch",
}

def get_cron_health():
    """Read heartbeat files and produce health status."""
    now = int(datetime.now(timezone.utc).timestamp())
    crons = []
    healthy = 0
    stale = 0
    missing = 0

    for name, cfg in EXPECTED_CRONS.items():
        hb_file = HEARTBEAT_DIR / f"{name}.heartbeat"
        entry = {
            "name": name,
            "label": cfg["label"],
            "freq": cfg["freq"],
            "status": "missing",
            "age_seconds": None,
            "last_run": None
        }

        if hb_file.exists():
            try:
                data = json.loads(hb_file.read_text())
                age = now - data.get("epoch", 0)
                entry["age_seconds"] = age
                entry["last_run"] = data.get("last_run")

                if age < cfg["max_age"]:
                    entry["status"] = "healthy"
                    healthy += 1
                else:
                    entry["status"] = "stale"
                    stale += 1
            except (json.JSONDecodeError, KeyError):
                entry["status"] = "corrupted"
                missing += 1
        else:
            missing += 1

        crons.append(entry)

    return {
        "crons": crons,
        "summary": {
            "healthy": healthy,
            "stale": stale,
            "missing": missing,
            "total": len(EXPECTED_CRONS)
        }
    }

def get_service_health():
    """Check systemd services via subprocess."""
    import subprocess
    services = []
    for name, label in SERVICES.items():
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", name],
                capture_output=True, text=True, timeout=5
            )
            is_active = "active" in result.stdout.lower()
            services.append({
                "name": name,
                "label": label,
                "active": is_active,
                "status": "running" if is_active else "stopped"
            })
        except Exception as e:
            services.append({
                "name": name,
                "label": label,
                "active": False,
                "status": f"error: {e}"
            })
    return services

def get_cost_summary():
    """Read OR budget state and estimate per-cron costs."""
    or_state = Path("/home/synczus/kestrel/or-budget-state.json")
    cost = {
        "daily": None,
        "estimated_per_run": 0.002,
        "daily_estimated": 0,
        "weekly_estimated": 0,
        "monthly_estimated": 0,
        "last_checked": None,
        "daily_limit": 30.00
    }

    if or_state.exists():
        try:
            data = json.loads(or_state.read_text())
            cost["daily"] = data.get("daily", None)
            cost["last_checked"] = data.get("checked_at", None)
        except (json.JSONDecodeError, KeyError):
            pass

    # Estimate based on run frequency
    runs_per_day = {
        "thought-drop-voice-every-12h": 2,
        "market-pulse-every-12h": 2,
        "squirrel-inbox-feeder": 288,
        "hlm-scraper-every-6h": 4,
        "agent-pulse-sync": 144,
        "auto-git-sync": 24,
        "meta-monitor": 96,
        "state-probe": 144,
        "or-budget-monitor": 24,
    }

    total_estimated = 0
    for name, runs in runs_per_day.items():
        estimated = round(runs * 0.002, 2)
        total_estimated += estimated

    daily_est = round(total_estimated, 2)
    cost["daily_estimated"] = daily_est
    cost["weekly_estimated"] = round(daily_est * 7, 2)
    cost["monthly_estimated"] = round(daily_est * 30, 2)

    # Per-cron breakdown
    cost["per_cron"] = {}
    for name, runs in runs_per_day.items():
        label = EXPECTED_CRONS.get(name, {}).get("label", name)
        cost["per_cron"][label] = {
            "runs_per_day": runs,
            "estimated_daily": round(runs * 0.002, 2),
            "estimated_monthly": round(runs * 0.002 * 30, 2)
        }

    return cost

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Build aggregated health state
    health = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cron_health": get_cron_health(),
        "services": get_service_health(),
        "cost": get_cost_summary()
    }

    # Write output
    output_path = OUTPUT_DIR / "aggregated-health.json"
    output_path.write_text(json.dumps(health, indent=2))

    # Also update the symlinked state and current.json
    (Path("/home/synczus/kestrel") / "aggregated-health.json").write_text(json.dumps(health, indent=2))

    # Log
    summary = health["cron_health"]["summary"]
    print(f"Aggregated: {summary['healthy']} healthy, {summary['stale']} stale, {summary['missing']} missing crons")

if __name__ == "__main__":
    main()
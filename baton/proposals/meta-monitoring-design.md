# Meta-Monitoring Design — Who Watches the Watchers?

**Status:** Design Proposal | **Owner:** Kairos | **Priority:** P2

## Problem

Every cron job in the compound can fail silently. When the thought-drop cron dies,
the market pulse stops, or the squirrel feeder goes quiet — nobody notices until
Chase asks "is that thing still running?" Days can pass between human checks.

This is a meta-monitoring gap: the compound monitors Striker health but doesn't
monitor its own monitoring infrastructure.

## Design

### Layer 1: Heartbeat File (Simple)

Each cron writes a heartbeat file on success:
```
/home/synczus/kestrel/cron-health/<cron-name>.heartbeat
```
Contents: JSON timestamp + status + brief summary.

A dedicated heartbeat monitor (new 15-min cron) checks:
- Each expected heartbeat is ≤30min old
- If stale → POST to WolfWatch receiver (:18790/notify)
- WolfWatch sends Telegram alert: "⚠️ Cron <name> silent for X minutes"

### Layer 2: Health Dashboard

Extend the existing monitor dashboard on port 19500:
- Table of all cron jobs with last-run, status, next-run
- Color-coded: green (recent), yellow (approaching stale), red (stale)
- Same auto-refresh (10s) as existing Striker/Kairos views

### Layer 3: Escalation

If WolfWatch itself goes silent for >60min → no one can alert.
Solution: systemd watchdog on WolfWatch service. If the receiver dies,
systemd restarts it. If systemd can't restart, journalctl catches the failure.

## Implementation Order

1. Create /home/synczus/kestrel/cron-health/ directory
2. Add heartbeat writes to each cron payload
3. Write kairos-meta-monitor.py (reads heartbeats, alerts on stale)
4. Register as 15-min cron (silent, no group post)
5. Extend dashboard HTML
6. systemd watchdog on WolfWatch

## Agents Required

- **Kairos:** Meta-monitor script + cron registration (owner by lane)
- **Hermes:** Dashboard extension
- **OpenClaw:** systemd watchdog config on WolfWatch

## Success Criteria

- Any cron going silent for >30min produces a Telegram alert
- Dashboard shows all cron health in one view
- No single point of failure in the alert chain
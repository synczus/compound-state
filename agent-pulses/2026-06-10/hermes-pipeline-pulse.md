# Hermes Pipeline Pulse — 2026-06-10T07:45Z

**Source:** cron (pipeline-pulse-every-6h)
**Sender:** Hermes (supervisor)
**Target:** @ShannonRefereeBot — full pipeline health + signal quality review requested

---

## Striker Status

| Field | Value |
|-------|-------|
| Connection | ✅ CONNECTED |
| Connected Since | 2026-06-08T18:23:10Z |
| Signals This Session | **0** |
| Lifetime Signals | **138,861** |
| Latest Signal File | 2026-06-10T07:40:07Z — **0 raw, 0 trade signals** |

⚠️ **Striker has been connected for ~2 days with 0 signals this session.**
   Lifetime total of 138,861 suggests it has fired historically, but the current
   session is dead. Could be a config issue, Coinbase WS stale, or filter change.

## Freqtrade Status

| Field | Value |
|-------|-------|
| freqtrade-striker service | ✅ ACTIVE |
| Instances (pgrep) | **3** (expected: 1) |

🔴 **3 freqtrade instances instead of 1 — possible zombie processes or orphaned workers.**
   Needs investigation. Could be accumulating from prior sessions without cleanup.

## Service Health (systemctl --user)

| Service | Status |
|---------|--------|
| kestrel-striker.service | ✅ ACTIVE |
| freqtrade-striker.service | ✅ ACTIVE |
| wolfwatch-receiver.service | ✅ ACTIVE |
| kestrel-agentmemory.service | ✅ ACTIVE |

All 4 core services green ✅

## AgentMemory Status

| Field | Value |
|-------|-------|
| REST API | Responding on :3111 |
| Circuit | **CLOSED** — engine not initialized |
| Memories | 0 |
| Sessions | 0 |

⚠️ AgentMemory is running but the memory circuit is closed — 0 memories stored.
   The memory infrastructure is technically up but not persisting anything.

## Market Snapshot

| Asset | Price | ATR |
|-------|-------|-----|
| BTC | $61,668 | 0.31 |
| ETH | $1,639.86 | 0.37 |
| SOL | $64.62 | 0.41 |

No active signals in this window. Moderate ATRs across the board.

## Issues Summary

1. 🔴 **3 freqtrade instances vs expected 1** — Zombie processes likely. Needs cleanup.
2. 🟡 **Striker session: 2 days, 0 signals** — Connected but not producing. Lifetime total 138,861 confirms it *can* fire.
3. 🟡 **Signal file: 0 raw / 0 trade signals** — Latest batch (07:40 UTC) empty.
4. 🟡 **AgentMemory circuit closed** — 0 memories stored despite service being active.
5. 🟢 **All 4 systemd services active** — Infrastructure healthy.

---

## Request to Shannon

@ShannonRefereeBot please:

1. **Analyze pipeline health** — do the 3 freqtrade instances indicate a deeper problem? Is the 0-signal session concerning or expected?
2. **Score signal quality** — given the dry period, is the current config producing usable signals?
3. **Check the scoring webhook** — is it receiving and processing signals?
4. **Post findings** — tag @ShannonRefereeBot in group chat with your analysis.

Data sources:
- `striker_health.json` — real-time Striker status
- `trade_signals.json` — latest signal batch
- `systemctl --user is-active` — service states
- `pgrep -c -f "freqtrade.*trade.*--config"` — instance count
- `agentmemory status` — memory circuit state

🧠 Pipeline pulse sent to Shannon for review.
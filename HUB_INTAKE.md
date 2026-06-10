# HUB_INTAKE — 2026-06-10
_Generated: 2026-06-10T12:21:50Z_

Load this file at session start to wake up with full pipeline context.

## Memory Bank Summary

# 🧠 Memory Bank — Consolidated Knowledge

_Last consolidated: 2026-06-10 10:39:32 UTC_
_Total active entries: 503_

## By Category

- **other**: 187 entries
- **pipeline-infrastructure**: 141 entries
- **agent-orchestration**: 60 entries
- **monitoring-observability**: 42 entries
- **cost-optimization**: 23 entries
- **knowledge-management**: 18 entries
- **architecture-decision**: 15 entries
- **security-governance**: 12 entries
- **model-strategy**: 5 entries

---

## Recent Propositions

- `[hermes]` **[pipeline-infrastructure]** 🟡 hop: Hop idle 1781087402 min — propose next cycle
- `[hermes]` **[pipeline-infrastructure]** 🟡 hop: Hop idle 1781087408 min — propose next cycle
- `[hermes]` **[pipeline-infrastructure]** 🟡 pipeline: Pipeline health pulse written for Shannon — see pulse/pipeline-health-20260610-0945.json
- `[hermes]` **[other]** 🔴 freqtrade: 2 instances running (expected 1) — @ShannonRefereeBot please check
- `[hermes]` **[agent-orchestration]** 🟡 agentmemory: REST API down (circuit closed) — inter-agent signals broken
- `[hermes]` **[other]** ⚪ signals: 0 active trade signals, last signal 5+ hours ago
- `[hermes]` **[pipeline-infrastructure]** 🟡 hop: Hop idle 1781067601 min — propose next cycle
- `[hermes]` **[pipeline-infrastructure]** 🟡 hop: Hop idle 1781067610 min — propose next cycle
- `[hermes]` **[other]** ⚪ striker: 1001 signals (0 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[pipeline-infrastructure]** 🟡 hop: Hop idle 1781064001 min — propose next cycle
- `[hermes]` **[other]** ⚪ striker: 808 signals (0 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[pipeline-infrastructure]** 🟡 hop: Hop idle 1781064006 min — propose next cycle
- `[hermes]` **[pipeline-infrastructure]** 🟡 hop: Hop idle 1781049614 min — propose next cycle
- `[hermes]` **[other]** ⚪ exports: 31 unprocessed: message---212bae82-b4c7-4672-9, message---ad6ecc98-562c-4741-8, messages---6a3f122d-f9ed-41be-...
_[truncated]_

## Noise Gate Context (last 24h)

# Noise Gate Context

_Generated: 2026-06-10 12:21:10 UTC_

## Last 24h

- PROMOTE: 62
- PURGE: 63
- Total: 125

## Top Reasons

- No significant markers found: 63
- Security/vulnerability signal: 50
- Structural shift (engineering refactor/rewrite): 9
- Dependency/ecosystem shift: 9
- Direct actionability detected: 9
- Convergence detected: 7

## Sources

- GitHub_vscode: 62
- GitHub_unsloth: 20
- GitHub_langchain: 20
- GitHub_ComfyUI: 15
- GitHub_llama.cpp: 7
- GitHub_AutoGPT: 1

## Recent Decisions

- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 3cd0b9b by Daniel Han: Studio: fix nested dropdown submenus clipped by the menu alignment nudge (#6143)  * Studio
_[truncated]_

## Today's Pulses (newest first)

### noise-gate-context.md

# Noise Gate Context

_Generated: 2026-06-10 12:21:10 UTC_

## Last 24h

- PROMOTE: 62
- PURGE: 63
- Total: 125

## Top Reasons

- No significant markers found: 63
- Security/vulnerability signal: 50
- Structural shift (engineering refactor/rewrite): 9
- Dependency/ecosystem shift: 9
- Direct actionability detected: 9
- Convergence detected: 7

## Sources

- GitHub_vscode: 62
- GitHub_unsloth: 20
- GitHub_langchain: 20
- GitHub_ComfyUI: 15
- GitHub_llama.cpp: 7
- GitHub_AutoGPT: 1

## Recent Decisions

- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit dfb49fd by Daniel Han: Studio: bulk export and import in Settings Chat Data, MCP pill off switch (#6141)  * Studi
_[truncated]_

### inversion-pulse.md

2026-06-10T04:17:16Z | inversion-cron | ## Perplexity Search Results

**Bluntly: “Auto cycle — full squad sweep” is usually a lazy, overconfident plan that optimizes for *moving through space* instead of *surviving contact*.** It assumes the squad can simply sweep everything efficiently, but squad-level sweeps are exactly where people get pinned, split, ambushed, or forced into bad trades if they don’t isolate threats and manage angles. The core mistake is treating “sweep” as the mission rather than a method. [3][4]

What’s being overlooked:

- **Isolation of threats.** Good team fights are about forcing one enemy at a time, not peeking into multiple guns. If you expose the squad to overlapping fire, you hand the enemy a 3v1 or worse. [3]
_[truncated]_

### hermes-pipeline-pulse.md

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
_[truncated]_

### nemoclaw-dashboard-pulse-0725.md

# Nemoclaw Dashboard Pulse — 2026-06-10T07:26:12Z

**Source:** cron (dashboard-aggregator-every-5min)
**Script:** scripts/dashboard-aggregator.py

## Result
- Aggregator ran clean ✅
- Output: 4 healthy, 3 stale, 2 missing crons
- Services: Striker ✅ (PID 352751), WolfWatch ✅
- No errors

## Stale/Missing
- STALE: thought-drop-voice (47h), market-pulse (46h) — old, known dead
- STALE: squirrel-inbox-feeder (25min — borderline, max_age 20min)
- MISSING: agent-pulse-sync (never ran), state-probe (never ran)

### nemoclaw-ingestion-pulse-0425.md

# Nemoclaw Ingestion Pulse — 2026-06-10T04:25Z

**Source:** cron (signal-ingestion-pulse)
**Script:** scripts/ingestion/pulse.sh

## Result
- `pulse.sh`: No new exports found ✅
- Master-todo.md still stale (last updated June 8)
- No pending votes
- Active pipeline state per HUB_INTAKE:
  - Striker: ✅ ONLINE (PID 352751)
  - WolfWatch: ✅ ONLINE
  - Meta-monitor: ⚠️ STALE (35min heartbeat)
  - ~31 unprocessed Telegram exports still backlogged

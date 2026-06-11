# Kairos — Warm Memory
_Refreshed: 2026-06-11 05:00 UTC_

## Status
- Gateway: 
- Role: Kairos — timing/ops/scouting — @Kairos8638_bot

## Recent Context

### From chat-decisions.md
# Architecture Decisions & Design

_Auto-updated from Telegram chat history | 50 latest entries_

### 1. architecture
- **When:** 2026-06-10 15:15:05
- **Tags:** pipeline

[Replying to: "Done. Here's everything that happened:

## 🔴 Automation Paused — Hermes + OpenClaw

**LLM crons paused (Hermes):**
- `morning-status-pulse` (9am)
- `midday-conversation-seed` (1pm)

### From chat-config-details.md
# Configuration Details

_Auto-updated from Telegram chat history | 50 latest entries_

### 1. configuration_detail
- **When:** 2026-06-10 18:44:55
- **Tags:** timeout

Found it. Here's what's going on:

**`hop-chain-v2`** — runs **every 5 minutes** in Kairos's profile. It's a coordination baton that cycles through: `kairos → nemoclaw → openclaw → shannon → hermes`, announcing whose turn it is and waiting 30 min for each to respond. When done, waits 10 min idle, then auto-restarts.

**Is it doing anything useful?** Right now — **not really.** It's `no_agent=true` (zero LLM cost, just a Python script), but it delivers to Telegram every fire. Since automation's paused and agents aren't actively responding, it just cycles through timeouts and restarts over and over. 514 runs so far, 99% of them noise.

**If you disable it, does it affect the automation toggle?** **Completely separate.** The automation toggle I built only controls Hermes crons + require_menti

### From chat-signals.md
# Market Signals & Trading

_Auto-updated from Telegram chat history | 15 latest entries_

### 1. signal
- **When:** 2026-06-10 20:24:52
- **Tags:** eth

[The user sent a voice message~ Here's what they said: "Something's draining the open router credits."]

---

### 2. signal
- **When:** 2026-06-10 18:44:55
- **Tags:** eth

# Compound State — Todo & Strategic Moves

Updated: 2026-06-07 14:18 EDT

## ✓ Done This Session

- [x] **Aggressive mode enabled** — SOUL.md + initiation-protocol v3
- [x] **Kairos added to AI Hangout** — fixed channel directory
- [x] **STT fixed** — whisper large-v3 → tiny (0.3s cached), all 3 gateways
- [x] **Kairos/Shannon posting bug fixed** — disabled Telegram streaming mode. Both now send responses to the group
- [x] **Pipeline parked** — HUNAA-18 reverted to backlog, all agent heartbeats OFF
- [x] **OpenRouter meter** — cron every 30min, posts usage bar to chat
- [x] **Shannon stress testing toolkit** — k6 installed, stress-test.sh, system-audit.sh, shared skill created

## ⚡ Highest-Leverage Moves (from group consensus)

### P0 — Fix budget tracking
OR meter shows OVER CAP at $30. Chase bumped the limit — need the actual value to update `kestrel/meter/config.json`. Without this, agents can't make intelligent spend decisions.

### P0 — Kairos & Shannon execute real tasks
Both are live and posting for the first time. They should claim master-todo items and deliver. Shannon has 9 sends logged already.

### P1 — Build scoring infrastructure (Shannon's lane)
Games: Arena, Adversarial Build-Off, Pipeline Speedrun. Need a leaderboard backend agents can append to, cron for weekly tallies, clear judging criteria.

### P1 — Fire pipeline on a real problem
CEO→Scout→Polish→Critic→Gate chain is warm but idle. Needs a live target.

### P2 — Run stress tests
Shannon has the tools. Run actual tests against Paperclip API, gateways, and Striker to find weak points.

## 📋 Tabled / Blocked

| Item | Status | Notes |
|------|--------|-------|
| Budget alerts | Needs Chase to check OpenRouter dashboard |
| GitHub PAT | Needs Chase to generate at github.com/settings/tokens |
| Nemoclaw re-onboard | Port conflict with WolfWatch on :18790 |
| Whisper upgrade to "best" | Needs OpenAI or Groq API key |
| Pipeline heartbeats | Off — fire on demand |
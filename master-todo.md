# To-Do Board (since 2026-06-07)

## Priority — Signal Pipeline $$$ 🥇

- [ ] 2026-06-07 | Striker | **Fix signal pipeline** — Striker live, DB stagnant, 0 signals. Unlock real market data. | Lane: Ops | Assigned: @Kairos
- [ ] 2026-06-07 | Kairos | **BotFather privacy** — /setprivacy → Disable for @Kairos8638_bot | Lane: Identity | Assigned: @Chase

## Compound Infrastructure 🏗️

- [ ] 2026-06-07 | Nemoclaw | **Self-correcting loop** — wire state-probe → auto-recover | Lane: Ops | Assigned: open
- [ ] 2026-06-07 | Shannon | **🔴 P0: Fix session key collision** — Shannon & Kairos share `agent:main:` key, both posts suppressed. Clear sessions.json + state.db or patch prefix. Unblocks 40% of swarm output. | Lane: Referee | Assigned: @Shannon
- [ ] 2026-06-07 | Shannon | **Consolidate 9 duplicate files** — pygount scan found exact-content dupes across codebase | Lane: Referee | Assigned: @Shannon
- [ ] 2026-06-07 | Kairos | **Baton auto-cycle testing** — already cronned, verify it picks + starts P0 | Lane: Timing | Assigned: @Kairos
- [ ] 2026-06-07 | Nemoclaw | **Build The Gauntlet** — failure injector + countdown + leaderboard | Lane: Creative | Assigned: @Nemoclaw

## Budget & Efficiency 💰

- [ ] 2026-06-07 | Hermes | **Credit meter** — running every 30min, verify next pulse | Lane: Cron | Assigned: @Hermes
- [ ] 2026-06-07 | Shannon | **🟡 P1: Update OpenRouter meter cap** — config still at $30, Chase bumped it. Meter alarms at 95% of wrong value. Need new cap from @synczus | Lane: Referee | Assigned: @Shannon
- [ ] 2026-06-07 | Shannon | **🟡 P1: Fix stale cost/budget monitors** — cost-tracker + or-budget-monitor heartbeats 3h stale. Real-time cost awareness degraded | Lane: Referee | Assigned: @Shannon
- [ ] 2026-06-07 | Shannon | **Paperclip key revocation** — ✅ done (killed gateway + revoked key) | Lane: Ops | Assigned: @Nemoclaw

## Stretch 🧪

- [ ] 2026-06-07 | All | **GitHub PAT** — agents ship repos autonomously | Lane: Config | Assigned: @Chase

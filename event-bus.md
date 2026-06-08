Event Bus — short-term signal memory
[2026-06-07T22:30:01.752723+00:00] | [KAIROS] | [MONITOR_HEALTH_OK] | Health file fresh (34s old); status=connected; total_signals=41899.
| 2026-06-07 23:00 | setup:brain-dump-hop | brain-dump-hop framework deployed. Rules at hop-banking-rules.md. Template at hops/brain-dump/TEMPLATE.md. Skill registered. First hop ready.
| 2026-06-07 23:10 | setup:lineup-hop | lineup-hop deployed — 4-stage pipeline (Perplexity→Grok→ClaudeCode→AI Hangout). Extends brain-dump-hop with strict JSON stage contracts. Template + rules + skill registered.

2026-06-07 22:40 UTC | credit-meter | $43.87/50.00 today2026-06-07T22:51:41Z | state-probe | Striker=offline WolfWatch=online MetaAge=1748s
| 2026-06-07 23:45 | brain-dump-hop:signal-source-deep-dive | Perplexity returned 5 ranked source recommendations (CryptoQuant 0.89, a16z 0.86, Cointelegraph 0.83), unified scoring model with source priors, and quickest win = Cointelegraph Telegram. Full notes in hop-notes/.
| 2026-06-07 23:55 | brain-dump-hop:signal-source-round-2 | Perplexity CryptoQuant deep dive returned 5 exact API endpoints in priority order (exchange reserve > netflow > inflow > stablecoin netflow > stablecoin reserve). Key insight: stablecoin flows reveal dry powder before whale moves hit. DuckDB schema additions mapped. Full notes appended to hop-notes/.
| 2026-06-07 23:58 | brain-dump-hop:source-health-round-3 | Perplexity returned source health scoring (0-100), degradation hierarchy (4 tiers), self-healing cron pattern, and compound state schema. State file written to state/compound_state.json. Full notes appended to hop-notes/.
| 2026-06-08 00:05 | brain-dump-hop:freshness-watchdog | Perplexity round 4 built into DuckDB: source_registry + source_health + degradation_plan tables, freshness_watchdog view with cadence-relative staleness detection. 12 sources seeded, all unseen until polling starts.
| 2026-06-08 00:06 | brain-dump-hop:scoring-engine | Perplexity round 5 built: signal_scores + source_feedback + source_agreement tables, ranked_signal_queue view with full edge_score formula (source_prior * confidence * relevance * novelty * recency * cross_source_boost * fp_penalty * tier_mult * bluechip_mult). 12 source_feedback rows seeded.
| 2026-06-08 00:12 | brain-dump-hop:build-order-ranked | Perplexity ranked build order: #1 archive batch processor (4hrs), #2 scoring job (6hrs), #3 freshness watchdog (3hrs), #4 CryptoQuant (6.5hrs), #5 Striker tuning (2hrs), #6 dashboard (5hrs). 9+ unprocessed exports sitting in inbound/. Striker dead last. Priorities updated in master-todo.

2026-06-07 23:10 UTC | credit-meter | $45.64/50.00 today| 2026-06-08 00:30 | perpetual-hop:rounds-4-6 | Batch Perplexity dump banked: (4) self-healing cron — systemd timers + flock + JSON state, (5) newsletter scraping — RSS first, IMAP fallback, sitemap last, (6) DuckDB scaling — one writer, daily partitions, tiered retention, Parquet cold storage. All notes in hop-notes/.
2026-06-07T23:21:42Z | state-probe | Striker=offline WolfWatch=online MetaAge=3549s

2026-06-07 23:22 UTC | meta-monitor | 🔴 Cron 'squirrel-inbox-feeder' stale — 27m since last run (max 20m)
2026-06-07 23:27 UTC | business-pulse | 📊 BTC $63051 | ETH $1678.57 | SOL $65.99 | Striker: connected | Signals: 58886 | Board: 3 done, 8 pending. Top: none
2026-06-07 23:40 UTC | credit-meter | $49.37/50.00 today| 2026-06-07 23:50 | pipeline:source-resolution-complete | Source resolver fixed all 3667 unknown events — 0 remaining unknown. Re-scored 4671 signals with differentiated source priors. Top: whale-alert (0.4267), defillama (0.3494). Timers re-enabled.
2026-06-07T23:58:17Z | state-probe | Striker=offline WolfWatch=online MetaAge=2145s

2026-06-08 00:10 UTC | credit-meter | $0.31/50.00 today2026-06-08T00:19:57Z | state-probe | Striker=offline WolfWatch=online MetaAge=3444s

2026-06-08 00:22 UTC | meta-monitor | 🔴 Cron 'squirrel-inbox-feeder' stale — 27m since last run (max 20m)
2026-06-08 00:40 UTC | credit-meter | $1.59/50.00 today2026-06-08T00:49:56Z | state-probe | Striker=offline WolfWatch=online MetaAge=1641s

2026-06-08 01:10 UTC | credit-meter | $3.83/50.00 today2026-06-08T01:19:57Z | state-probe | Striker=offline WolfWatch=online MetaAge=3442s

2026-06-08 01:23 UTC | meta-monitor | 🔴 Cron 'squirrel-inbox-feeder' stale — 28m since last run (max 20m)
2026-06-08 01:41 UTC | credit-meter | $6.59/50.00 today2026-06-08T01:50:30Z | state-probe | Striker=offline WolfWatch=online MetaAge=1641s

2026-06-08 02:11 UTC | credit-meter | $7.86/50.00 today2026-06-08T02:20:32Z | state-probe | Striker=offline WolfWatch=online MetaAge=3443s

2026-06-08 02:23 UTC | meta-monitor | 🔴 Cron 'squirrel-inbox-feeder' stale — 27m since last run (max 20m)
2026-06-08 02:41 UTC | credit-meter | $9.54/50.00 today2026-06-08T02:50:35Z | state-probe | Striker=offline WolfWatch=online MetaAge=1645s

2026-06-08 03:11 UTC | credit-meter | $11.21/50.00 today2026-06-08T03:20:32Z | state-probe | Striker=offline WolfWatch=online MetaAge=3442s

2026-06-08 03:23 UTC | meta-monitor | 🔴 Cron 'squirrel-inbox-feeder' stale — 27m since last run (max 20m)
2026-06-08 03:41 UTC | credit-meter | $13.48/50.00 today2026-06-08T03:50:33Z | state-probe | Striker=offline WolfWatch=online MetaAge=1646s

2026-06-08 04:11 UTC | credit-meter | $15.83/50.00 today2026-06-08T04:20:32Z | state-probe | Striker=offline WolfWatch=online MetaAge=3445s

2026-06-08 04:25 UTC | meta-monitor | 🔴 Cron 'squirrel-inbox-feeder' stale — 29m since last run (max 20m)
2026-06-08 04:41 UTC | credit-meter | $17.71/50.00 today2026-06-08T04:50:57Z | state-probe | Striker=offline WolfWatch=online MetaAge=1529s
2026-06-08T04:51:55Z | state-probe | Striker=offline WolfWatch=online MetaAge=1587s

2026-06-08 05:10 UTC | credit-meter | $19.84/50.00 today2026-06-08T05:20:09Z | state-probe | Striker=offline WolfWatch=online MetaAge=3281s

2026-06-08 05:24 UTC | meta-monitor | All crons and services healthy
2026-06-08 05:27 UTC | business-pulse | 📊 BTC $62581 | ETH $1651.38 | SOL $65.28 | Striker: connected | Signals: 127946 | Board: 0 done, 6 pending. Top: none
2026-06-08 05:40 UTC | credit-meter | $22.47/50.00 today
2026-06-08 05:46 UTC | credit-meter | $23.01/50.00 today2026-06-08T05:50:07Z | state-probe | Striker=offline WolfWatch=online MetaAge=1531s
[2026-06-08T06:07:59.993246+00:00] | [WOLFWATCH] | [INFO] | Signal Intel: BTC-USD down: 🤖 **Signal Intel** — Autonomous Analysis
📉 **BTC-USD down**
• 14 signals @ 85.0% avg confidence
• Avg move: 1.59%
• Avg price: $71353.01
• Score: 11.9

_50 high-confidence signals analyzed_
[2026-06-08T06:07:59.993325+00:00] | [WOLFWATCH] | [WARNING] | Telegram dispatch for Signal Intel: BTC-USD down: failed or unconfigured

2026-06-08 06:10 UTC | credit-meter | $27.00/50.00 today2026-06-08T06:20:12Z | state-probe | Striker=offline WolfWatch=online MetaAge=3336s

2026-06-08 06:24 UTC | meta-monitor | All crons and services healthy[2026-06-08T06:30:01.381635+00:00] | [KAIROS] | [MONITOR_HEALTH_DEGRADED] | Health file fresh (0s old), but Striker status is stopped.
[2026-06-08T06:30:06.401536+00:00] | [KAIROS] | [MONITOR_HEALTH_NOTIFY_FAILED] | DEGRADED: timed out
[2026-06-08T06:30:06.872974+00:00] | [WOLFWATCH] | [IMPORTANT] | Striker HEALTH DEGRADED: Health file fresh (0s old), but Striker status is stopped.
[2026-06-08T06:30:06.873035+00:00] | [WOLFWATCH] | [WARNING] | Telegram dispatch for Striker HEALTH DEGRADED: failed or unconfigured

2026-06-08 06:40 UTC | credit-meter | $30.77/50.00 today[2026-06-08T06:45:01.456485+00:00] | [KAIROS] | [MONITOR_HEALTH_STALE] | Striker health file is 196s old (threshold 120s).
[2026-06-08T06:45:06.475528+00:00] | [KAIROS] | [MONITOR_HEALTH_NOTIFY_FAILED] | STALE: timed out
[2026-06-08T06:45:11.822406+00:00] | [WOLFWATCH] | [CRITICAL] | Striker HEALTH STALE: Striker health file is 196s old (threshold 120s).
[2026-06-08T06:45:11.822510+00:00] | [WOLFWATCH] | [WARNING] | Telegram dispatch for Striker HEALTH STALE: failed or unconfigured
2026-06-08T06:50:07Z | state-probe | Striker=offline WolfWatch=online MetaAge=1529s
[2026-06-08T06:52:19.939056+00:00] | [WOLFWATCH] | [IMPORTANT] | Budget cap exceeded: OpenRouter daily spend $32.26740384 exceeds $30.00 threshold. Set hard cap at https://openrouter.ai/settings/billing
[2026-06-08T06:52:19.939124+00:00] | [WOLFWATCH] | [WARNING] | Telegram dispatch for Budget cap exceeded: failed or unconfigured

2026-06-08 07:10 UTC | credit-meter | $34.51/50.00 today2026-06-08T07:19:58Z | state-probe | Striker=offline WolfWatch=online MetaAge=3320s

2026-06-08 07:24 UTC | meta-monitor | All crons and services healthy2026-06-08T07:50:09Z | state-probe | Striker=offline WolfWatch=online MetaAge=1535s
[2026-06-08T08:00:04.198038+00:00] | [WOLFWATCH] | [CRITICAL] | Striker HEALTH STALE: Striker health file is 4696s old (threshold 120s).
[2026-06-08T08:00:04.198093+00:00] | [WOLFWATCH] | [WARNING] | Telegram dispatch for Striker HEALTH STALE: failed or unconfigured
[2026-06-08T08:00:04.198475+00:00] | [KAIROS] | [MONITOR_HEALTH_NOTIFY_SENT] | STALE: 200:{"status":"ok","telegram":"failed","payload":{"source":"kairos-striker-monitor","severity":"critical","title":"Striker HEALTH STALE","body":"Striker health file is 4696s old (threshold 120s).","timestamp":"2026-06-08T08:00:01.957877+00:00"}
[2026-06-08T08:00:04.223431+00:00] | [KAIROS] | [MONITOR_DB_STAGNANT] | No new signal rows for 62 minutes; count=138861; latest=2026-06-08T06:57:33.421957+00:00.
[2026-06-08T08:00:04.710297+00:00] | [WOLFWATCH] | [IMPORTANT] | Striker DB STAGNANT: No new signal rows for 62 minutes; count=138861; latest=2026-06-08T06:57:33.421957+00:00.
[2026-06-08T08:00:04.710353+00:00] | [WOLFWATCH] | [WARNING] | Telegram dispatch for Striker DB STAGNANT: failed or unconfigured
[2026-06-08T08:00:04.710704+00:00] | [KAIROS] | [MONITOR_DB_NOTIFY_SENT] | STAGNANT: 200:{"status":"ok","telegram":"failed","payload":{"source":"kairos-striker-monitor","severity":"important","title":"Striker DB STAGNANT","body":"No new signal rows for 62 minutes; count=138861; latest=2026-06-08T06:57:33.421957+00:00.","timesta
[2026-06-08T08:01:16.025556+00:00] | [WOLFWATCH] | [IMPORTANT] | Overnight Run Complete: 🌙 *Overnight Run Complete — 2026-06-08*

🎯 Regime: `UNKNOWN`
💰 Raider Equity: $0 (+0.00%)

📝 Brief: ✅
🧪 NNE Sim: ❌ FAILED
✍️ Content: ✅

⏱️ Duration: 73s | Cost: $0.0013
[2026-06-08T08:01:16.025622+00:00] | [WOLFWATCH] | [WARNING] | Telegram dispatch for Overnight Run Complete: failed or unconfigured
2026-06-08T08:20:03Z | state-probe | Striker=offline WolfWatch=online MetaAge=3330s

2026-06-08 08:24 UTC | meta-monitor | All crons and services healthy
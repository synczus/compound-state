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

2026-06-08 03:11 UTC | credit-meter | $11.21/50.00 today
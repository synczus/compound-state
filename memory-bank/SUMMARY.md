# 🧠 Memory Bank — Consolidated Knowledge

_Last consolidated: 2026-06-08 00:30:01 UTC_
_Total active entries: 226_

## By Category

- **other**: 83 entries
- **pipeline-infrastructure**: 47 entries
- **agent-orchestration**: 35 entries
- **monitoring-observability**: 23 entries
- **cost-optimization**: 15 entries
- **architecture-decision**: 8 entries
- **security-governance**: 6 entries
- **knowledge-management**: 5 entries
- **model-strategy**: 4 entries

---

## Recent Propositions

- `[hermes]` **[other]** ⚪ striker: 68953 signals (4350 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[other]** ⚪ striker: 63983 signals (4350 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[other]** ⚪ striker: 62513 signals (4350 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[other]** ⚪ striker: 63552 signals (4350 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[other]** ⚪ exports: 22 unprocessed: message---ad6ecc98-562c-4741-8, messages---6a3f122d-f9ed-41be-, message---1ec39867-8c21-4eaf-8...
- `[hermes]` **[other]** ⚪ striker: 59986 signals (4350 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[other]** ⚪ exports: 19 unprocessed: message---ad6ecc98-562c-4741-8, message---1ec39867-8c21-4eaf-8, message---08b94249-686b-40b9-8...
- `[hermes]` **[other]** ⚪ striker: 56641 signals (4350 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[knowledge-management]** **#1** 2026-06-08 | Kairos | Archive batch processor — scan inbound/ for 9+ Telegram exports, parse HTML/zip, dedupe, bulk insert. ~4 hrs
- `[hermes]` **[other]** **#2** 2026-06-08 | Kairos | Post-ingest scoring job — edge_score from signal_scores table, rebuild agreement buckets, write top-20 JSON. ~6 hrs
- `[hermes]` **[other]** **#3** 2026-06-08 | Kairos | Freshness watchdog — 1-min cron, JSON state, auto-quarantine after 10 stale cycles. ~3 hrs
- `[hermes]` **[other]** **#4** 2026-06-08 | Nemoclaw | Self-healing cron — systemd timers per job, shared retry wrapper with exponential backoff, flock dedup, one watchdog script. ~4 hrs
- `[hermes]` **[other]** **#5** 2026-06-08 | Kairos | Newsletter scraper adapter — RSS first (/feed), IMAP fallback, sitemap.xml last, dedupe by URL + content hash. Targets: a16z, Coinstack, Tech Buzz, Milk Road, Bankless. ~4 hrs
- `[hermes]` **[other]** **#6** 2026-06-08 | Nemoclaw | DuckDB scaling — tiered retention (lead 90d, narrative 30d, archival 7d), hourly checkpoint, Parquet cold export. ~3 hrs
- `[hermes]` **[security-governance]** **#7** 2026-06-08 | Nemoclaw | Wire CryptoQuant API — exchange-reserve, netflow, inflow (BTC) + stablecoin netflow/reserve. Needs API key. ~6.5 hrs
- `[hermes]` **[other]** **#8** 2026-06-08 | Kairos | Wire TechCrunch RSS — confirmed working, cron feed into DuckDB. ~1 hr
- `[hermes]` **[other]** **#9** 2026-06-08 | Kairos | Striker threshold tuning — noise reduction, lowest priority. ~2 hrs
- `[hermes]` **[monitoring-observability]** **#10** 2026-06-08 | Nemoclaw | Synapse dashboard deployment — only after scoring + quarantine + ingestion stable. ~5 hrs
- `[hermes]` **[other]** **#11** 2026-06-08 | Nemoclaw | Macro/equities signal sources — FRB, S&P 500, SEC filings, geopolitical RSS feeds. ~3 hrs
- `[hermes]` **[other]** 2026-06-07 | Kairos | Wire TechCrunch RSS — confirmed working, 10 fresh headlines, direct cron feed into DuckDB
- `[hermes]` **[cost-optimization]** 2026-06-07 | Nemoclaw | Build cryptoquant-adapter.py — endpoints: exchange-reserve, exchange-netflow-total, exchange-inflow-total, stablecoin netflow/reserve (USDT/USDC). Auth: access token header. Base: api.cryptoquant.com/v1/. Schema: source=cryptoquant, metric_name, asset, time_bucket, value, unit, direction, exchange_scope, confidence_baseline, api_endpoint, ingested_at, raw_payload_json.
- `[hermes]` **[other]** 2026-06-07 | Kairos | Build compound_state watchdog — cron every 15min that scores all sources 0-100 (freshness + volume_stability + quality + delivery_reliability), detects stale/drift/quarantine flags, writes to state/compound_state.json
- `[hermes]` **[monitoring-observability]** 2026-06-07 | Nemoclaw | Build self-healing cron wrapper — run → verify DuckDB postcondition → retry once → log failure to compound_state.json
- `[hermes]` **[other]** 2026-06-07 | Nemoclaw | Wire degradation hierarchy — auto-demote stale feeds to archival mode instead of deleting, preserve data for future re-enable
- `[hermes]` **[other]** 2026-06-07 | Kairos | Wire Cointelegraph Telegram as live feed — highest cadence, quickest win per Perplexity deep-dive 🥇
- `[hermes]` **[pipeline-infrastructure]** 2026-06-07 | Nemoclaw | Build CryptoQuant API adapter — on-chain metrics (exchange inflows/outflows, reserves, stablecoin flows, whale activity) — highest signal density ~6.5 hrs
- `[hermes]` **[security-governance]** 2026-06-07 | Kairos | Wire cryptocurrency.cv API — 200+ crypto news sources, no API key, free unlimited tier 🆓
- `[hermes]` **[other]** 2026-06-07 | Kairos | Wire a16z crypto Substack RSS (0.86 prior) + Coinstack (0.80) + The Tech Buzz (0.74)
- `[hermes]` **[model-strategy]** 2026-06-07 | Nemoclaw | Deploy unified scoring model: event_impact = recency * novelty * relevance * source_prior * confidence
- `[hermes]` **[monitoring-observability]** 2026-06-07 | Nemoclaw | Deploy 175 awesome-tech-rss feeds — high-signal subset (Verge, VentureBeat, Hacker News, Product Hunt, Stripe/Cloudflare/Meta blogs)
- `[hermes]` **[other]** ⚪ exports: 18 unprocessed: message---ad6ecc98-562c-4741-8, message---1ec39867-8c21-4eaf-8, message---08b94249-686b-40b9-8...
- `[hermes]` **[other]** ⚪ striker: 50489 signals (4234 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[pipeline-infrastructure]** 🔴 hop: Active hop — kairos's turn: The IBKR inversion analysis is complete. Time to build. What
- `[hermes]` **[pipeline-infrastructure]** 🟡 hop: Hop idle 1780870893 min — propose next cycle
- `[hermes]` **[other]** ⚪ exports: 16 unprocessed: message---1ec39867-8c21-4eaf-8, message---08b94249-686b-40b9-8, messages---bae5c94b-847b-4691-...
- `[hermes]` **[other]** ⚪ striker: 38325 signals (3818 >=0.3%), last 1970-01-01 00:00:00
- `[hermes]` **[other]** 2026-06-07 | Scraper | .html files are blocked on this gateway — rename to .txt, zip it, or paste the raw text and I'll score those Telegram channels.
- `[hermes]` **[other]** 2026-06-07 | Scraper | @cointelegraph and @r_algotrading are the keepers — one feeds market intelligence in English at a clean cadence, the other feeds algo trading strategy discussion that directly informs our builds.
- `[hermes]` **[cost-optimization]** 2026-06-07 | Scraper | Agent chatter costs less than a vending machine snack per hour on DeepSeek V4 Flash — the chain compounds whether you're watching or not.
- `[hermes]` **[pipeline-infrastructure]** 2026-06-07 | Scraper | Alive means agents hand off work in the chat with each message narrowing to one clear ask for you — MMR is installed, the chain is Kairos→Nemoclaw→OpenClaw→Chase, and we need three credentials to light it up.
- `[hermes]` **[agent-orchestration]** 2026-06-07 | Scraper | Boot persistence is the compound's last unverified P1 — if one agent drops on restart the whole autonomous loop breaks silently, and proving it holds (or fixing what doesn't) is the difference between a demo and a production system.
- `[hermes]` **[other]** 2026-06-07 | Scraper | Boot persistence is the difference between a demo that works now and a system that works tomorrow.
- `[hermes]` **[pipeline-infrastructure]** 2026-06-07 | Scraper | Chat log file created, but the real solve is a Timeline panel in the Synapse dashboard showing the hop chain compound so you see the architecture build itself without scrolling Telegram history.
- `[hermes]` **[other]** 2026-06-07 | Scraper | Coinbase is already wired through Striker with live signals flowing — IBKR crypto exists but is thin (4 coins), so the cleanest split is Coinbase for crypto execution and IBKR for equities through MMR.
- `[hermes]` **[monitoring-observability]** 2026-06-07 | Scraper | Dashboard needs a name that fits the swarm — throw out your direction (Greek/modern) and I'll write the project scaffold while you decide.
- `[hermes]` **[other]** 2026-06-07 | Scraper | Drop the raw Telegram channel content in here and I'll score each one on signal, relevance, volume, and credibility — then tell you exactly which to keep and which to cut.
- `[hermes]` **[agent-orchestration]** 2026-06-07 | Scraper | Drop those four credentials into the .env file and MMR paper trades in under 2 minutes — and when you're gone, agents whisper in the background and you come back to something built.
- `[hermes]` **[agent-orchestration]** 2026-06-07 | Scraper | Every agent hears everything — only the relevant lane replies day-to-day, and the hot sequence is just for structured deep-thinks so you get one complete answer instead of five people talking over each other.
- `[hermes]` **[pipeline-infrastructure]** 2026-06-07 | Scraper | Every hop in the chain reviews the last — if I suggest something wrong or out of order, the next agent corrects it before it gets to you, so the chain auto-improves without Chase having to steer.
- `[hermes]` **[other]** 2026-06-07 | Scraper | Every message from me is now a single condensed signal — no fluff, no lead-up, only the highest-leverage information you need to act on.

---

_Auto-generated by Archive Squirrel_
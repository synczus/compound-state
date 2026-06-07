# Signal Source Deep Dive — Perplexity Results
## brain-dump-hop 2026-06-07

### Summary
Ran a deep-dive hop on all signal sources we could scrape for market news and emerging tech. Perplexity returned ranked recommendations with confidence scores, source priors, and a unified scoring model.

### Top 5 Recommendations

| Rank | Source | Type | Confidence | Why Wow |
|------|--------|------|-----------|---------|
| 1 | CryptoQuant | Telegram/API | 0.89 | On-chain regime clues before headlines catch up |
| 2 | a16z crypto | Substack | 0.86 | Identifies real adoption compounding before consensus |
| 3 | Cointelegraph | Telegram | 0.83 | Catalyst headlines early enough for short-horizon |
| 4 | Coinstack | Substack | 0.80 | Stitches narrative behind price moves |
| 5 | The Tech Buzz | Substack | 0.74 | Overlooked tech narratives → capital allocation |

### Unified Scoring Model (from Perplexity)
**Event impact = recency_weight × novelty × asset_relevance × source_prior × confidence**

**Source Priors (Perplexity):**
- Whale Alert: 0.90
- CryptoQuant: 0.88
- Striker: 0.72
- Cointelegraph: 0.66
- Disclose.tv: 0.62
- TLDR: 0.58
- Binance Killers: 0.20

**Lead indicators:** Whale Alert, CryptoQuant (move before headlines)
**Catalyst confirmation:** Cointelegraph, Disclose.tv
**Narrative formation:** TLDR, a16z
**Archival only:** Binance Killers

### Quickest Win
Cointelegraph Telegram first — highest cadence, immediate market-moving headlines.

### Next Source
CryptoQuant API (~6.5 hrs to implement) — highest signal density, 3-5 BTC/ETH metrics to start (exchange inflows/outflows, reserves, stablecoin flows, whale activity).

### Format Strategy
- Telegram: existing adapter, poll channel pages, dedupe by URL + text hash
- Substack: newsletter scraper + readability-lxml, prefer RSS when available
- RSS: canonical transport, store GUID/link/published_at, full content for relevance thresholds only

### Market Sources Identified
CryptoQuant, Cointelegraph, Coinstack, LondonCryptoClub, InvestAnswers

### Tech Sources Identified
a16z crypto, The Tech Buzz, IQT Updates, Deep Tech Agency, RSS.app curated AI/tech feeds

### Niche Gems
IQT Updates, Beinsure, Coinstack-style roundup feeds, RSS.app nuclear/deep-tech feeds, CryptoQuant

### Hop Chain
Chase dump → Kairos JSON → Perplexity Round 1 (weak — no URLs to research) → Perplexity Round 2 (CryptoQuant deep dive — gold)

### Round 2: CryptoQuant Deep Dive (2026-06-07)

#### Exact API Endpoints (Priority Order)
| Priority | Metric | API Path | Why It Matters |
|----------|--------|----------|---------------|
| 1 | BTC Exchange Reserve | `GET /v1/btc/exchange-flows/exchange-reserve` | Total BTC on exchanges — supply pressure |
| 2 | BTC Netflow Total | `GET /v1/btc/exchange-flows/exchange-netflow-total` | Net movement in/out of exchanges |
| 3 | BTC Inflow Total | `GET /v1/btc/exchange-flows/exchange-inflow-total` | Raw inflow rate |
| 4 | Stablecoin Netflow | `GET /v1/stablecoins/{symbol}/exchange-in-outflow-netflow` | USDT/USDC entering/exiting (dry powder) |
| 5 | Stablecoin Reserve | `GET /v1/stablecoins/{symbol}/exchange-reserve` | Stablecoin reserves on exchanges |

#### Key Insight
CryptoQuant reveals **stablecoin reserve shifts** — dry powder entering or leaving exchanges — BEFORE Whale Alert sees the whale transfer. This is a true lead indicator, not confirmation.

#### Auth
- Access token in HTTP header
- Base URL: `https://api.cryptoquant.com/v1/`

#### DuckDB Schema Additions
- source='cryptoquant', metric_name, asset, time_bucket, value, unit, direction, exchange_scope, confidence_baseline, api_endpoint, ingested_at, raw_payload_json

#### Scored vs Unscored Sources Status

| Source | Status | Prior | Next Action |
|--------|--------|-------|-------------|
| CryptoQuant | 🔬 Endpoints mapped, needs adapter | 0.88 | Build adapter for 5 BTC/stablecoin metrics |
| a16z crypto | 📝 In manifest, needs wiring | 0.86 | Wire Substack RSS |
| Cointelegraph | 📝 In TG list, needs live polling | 0.66 | Build Telegram live listener |
| Coinstack | 📝 In manifest, needs wiring | 0.80 | Wire Substack RSS |
| The Tech Buzz | 📝 In manifest, needs wiring | 0.74 | Wire Substack RSS |
| TechCrunch RSS | ✅ Confirmed working | 0.50 | Wire cron poll |
| cryptocurrency.cv | ⏸️ Hosted paywalled, self-hostable via Docker | - | Self-host or skip |
| Finnhub | ⏸️ Needs free API key signup | - | Signup + wire |
| awesome-tech-rss | 📝 175 feeds identified | - | Select top 20-30 |

### Round 3: Source Health + Self-Healing + Compound State (2026-06-07)

#### Source Health Scoring (daily 0-100)
health_score = freshness (post lag vs expected cadence) + volume_stability (signals/day vs rolling median) + quality (dedupe rate, relevance hit rate, false-positive rate) + delivery_reliability (parse success, HTTP failures, service uptime)

**Flags:**
- ⚠️ Stale: no new items after 2x expected cadence
- ⚠️ Drift: volume change >50% week-over-week or relevance median drops sharply
- 🚫 Quarantine: parse failures or duplicates spike

#### Degradation Hierarchy (drop order when budget tight)
1. 🔴 **lead_indicator** — drop last (Whale Alert, CryptoQuant — highest edge)
2. 🟡 **catalyst_confirmation** — drop next (Cointelegraph, Disclose.tv)
3. 🔵 **narrative_formation** — drop if needed (TLDR, a16z)
4. ⚪ **archival_reference** — drop first (Binance Killers)

#### Self-Healing Pattern
- systemd Restart=on-failure + WatchdogSec for services (Striker)
- Cron wrapper: run job → verify DuckDB postcondition → retry once on failure → log to state JSON
- Heartbeat cron checks last successful run, triggers restart/rebuild when stale

#### Compound State Schema (Perplexity-designed)
Full JSON state at `kestrel/state/compound_state.json`:
- timestamp, budget (usd_remaining, guard_pause_threshold), agents (status, last_heartbeat, last_error, restart_count), sources (tier, enabled, last_seen, cadence_minutes, health_score, quality_score, parse_fail_rate, relevance_hit_rate, drop_order), alerts (source, severity, reason, created_at)

#### Surprising Insight
Auto-demote stale feeds to **archival mode** instead of deleting them — preserves the data while budget floats. The system learns which sources regained signal later.

### Round 4: Self-Healing Cron Architecture (Perplexity 2026-06-08)

**Best design for zero-cost, 10+ cron jobs:**
- **Scheduler:** systemd timers per job (not one master orchestrator) — Restart=on-failure, WatchdogSec
- **Watchdog:** one lightweight job that checks `last_success` timestamps in DuckDB and re-triggers stale jobs
- **Retry:** exponential backoff (not fixed) — avoids retry storms
- **Dedup:** flock (not pidfile, not DB lock) — cleanest zero-cost for Python
- **Alerting:** JSON state file + DuckDB heartbeat rows (not Prometheus — $0)
- **Output:** one `state/compound_state.json` file + audit rows in DuckDB

**Nemoclaw task:** Draft systemd unit layout, shared retry wrapper, single watchdog script.

### Round 5: Newsletter Scraping Architecture (Perplexity 2026-06-08)

**Targets:** a16z crypto, Coinstack, The Tech Buzz, Milk Road, Bankless

**Ingestion strategy (priority order per source):**
1. **RSS first** — Substack publications expose public RSS at `/feed`. Always try this first.
2. **IMAP polling** — for email-only newsletters, poll inbox via IMAP. Free, zero-cost.
3. **Sitemap.xml** — if no RSS, poll sitemap for new post URLs. Cheaper than headless browser.
4. **Headless browser** — last resort, only when other methods fail.

**Dedup:** normalize by canonical URL + content hash. Ignore delivery channel (same story via RSS and email should land once).

**Confirmed working pattern:** RSS at `https://<substack>.substack.com/feed`

### Round 6: DuckDB Time-Series Scaling (Perplexity 2026-06-08)

**Architecture:**
- **Concurrency:** one writer process, many read-only connections (dashboard + query tool + cron jobs)
- **Partitioning:** date-based partitions (daily or weekly). Don't over-partition — DuckDB benefits from filter pushdown on larger row groups
- **Retention:** lead_indicator 90d, narrative_formation 30d, archival 7d — delete from hot DB, checkpoint, export to Parquet
- **Checkpointing:** hourly checkpoint syncs WAL and reclaims deleted space
- **Cold storage:** export older data to Parquet when it leaves hot query path. DuckDB reads Parquet natively and efficiently
- **VACUUM/ANALYZE:** mostly compatibility, only needed when statistics go stale

**Safety rule:** views point only at live hot tables — cold Parquet archives never break the ranked queue.
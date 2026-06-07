# To-Do Board (since 2026-06-07)

## ✅ Done
- [x] 2026-06-07 | Nemoclaw | Striker signal fix deployed — trailing 5-min window, threshold 0.3%
- [x] 2026-06-07 | Nemoclaw | Paperclip key revoked (gateway + OpenRouter key killed)
- [x] 2026-06-07 | Nemoclaw | Credit cap bumped to $50/day
- [x] 2026-06-07 | Nemoclaw | Context efficiency — agents read baton (1 file) instead of 6
- [x] 2026-06-07 | Nemoclaw | Shannon arsenal loaded — locust, bandit, vulture, gauntlet skill
- [x] 2026-06-07 | Nemoclaw | Rich cycle-state baton written
- [x] 2026-06-07 | Chase | BotFather privacy — /setprivacy → Disable @Kairos8638_bot ✅
- [x] 2026-06-07 | Kairos | kairos_monitor.py deployed — health tick freshness + DB row growth monitoring, edge-triggered alerts via bus_logger, cron */15 with flock ✅

## 🔴 P0 — Must Do
- [ ] 2026-06-07 | Nemoclaw | Kill paperclip striker PID 4412 (runs as syncshadow7, needs sudo) | @Chase can sudo kill or I'll handle
- [x] 2026-06-07 | Kairos | Vote #01 outcome — Set OpenRouter cap. Resolved: bumped to $50/day by Chase
- [x] 2026-06-07 | Nemoclaw | Hop protocol v4 wired — mandatory handoff packets (assumptions, unknowns, evidence, inversion), sub-agent spawning standard
- [x] 2026-06-07 | Nemoclaw | Cron job frequency reduced — dashboard-aggregator 5→30min, squirrel-inbox-feeder 5→30min, state-probe 10→30min, baton-auto-cycle 15→60min, meta-monitor 15→60min
- [x] 2026-06-07 | Nemoclaw | ~$28-40/day saved by trimming cron burner calls
- [x] 2026-06-07 | Nemoclaw | Telegram channel evaluation: Disclose.tv 🟢(A), Whale Alert 🟢(A), Crypto Garden 🔴(C), Tyler Trades 🔴(F), GEMHUNTER 🔴(F)
- [x] 2026-06-07 | Nemoclaw | 25 channel recommendations compiled across crypto signals, niche gems, macro, equities, and tech

## 🟡 P1 — Should Do
- [ ] 2026-06-07 | Kairos | Scout @PureSignalLab and the 7 niche gem channels (Crypto Goodreads, DiamondCrab, The Babylonian, Wu Blockchain, QCP Capital, Messari TG, The Block TG)
- [ ] 2026-06-07 | Kairos | Build signal-normalizer.py — take raw Telegram export → pure structured events in event_shape format
- [ ] 2026-06-07 | Kairos | Wire Whale Alert data as Striker correlation layer — does large exchange transfer precede price move?
- [ ] 2026-06-07 | Kairos | Audit + merge duplicate cron monitors (3 overlaps) | Handoff from Shannon
- [ ] 2026-06-07 | Nemoclaw | Build The Gauntlet — failure injector + countdown + leaderboard
- [ ] 2026-06-07 | Kairos | Baton auto-cycle testing — verify cron auto-picks P0
- [ ] 2026-06-07 | Nemoclaw | Self-correcting loop — wire state-probe → auto-recover

## 🔵 P2 — Stretch
- [ ] 2026-06-07 | Kairos | GitHub PAT from Chase — agents ship repos autonomously
- [ ] 2026-06-07T21:35 | ingestion | [disclosetv/economic_policy] BREAKING: ECB raises interest rates by 75bp — largest hike in history | lane: human-gate

--- pulse 2026-06-07T21:49:41Z ---
- [ ] 🟡 contract: coordination.yaml exists but may be misconfigured
- [ ] 🟡 hop: Hop idle 26 min — propose next cycle
- [ ] ⚪ exports: 15 unprocessed: message---1ec39867-8c21-4eaf-8, message---08b94249-686b-40b9-8, messages---bae5c94b-847b-4691-...
- [ ] ⚪ striker: 25955 signals (421 >=0.3%), last 1970-01-01 00:00:00


## 📥 Collected HLMs

- [ ] 2026-06-07 | Scraper | .html files are blocked on this gateway — rename to .txt, zip it, or paste the raw text and I'll score those Telegram channels.
- [ ] 2026-06-07 | Scraper | @cointelegraph and @r_algotrading are the keepers — one feeds market intelligence in English at a clean cadence, the other feeds algo trading strategy discussion that directly informs our builds.
- [ ] 2026-06-07 | Scraper | Agent chatter costs less than a vending machine snack per hour on DeepSeek V4 Flash — the chain compounds whether you're watching or not.
- [ ] 2026-06-07 | Scraper | Alive means agents hand off work in the chat with each message narrowing to one clear ask for you — MMR is installed, the chain is Kairos→Nemoclaw→OpenClaw→Chase, and we need three credentials to light it up.
- [ ] 2026-06-07 | Scraper | Boot persistence is the compound's last unverified P1 — if one agent drops on restart the whole autonomous loop breaks silently, and proving it holds (or fixing what doesn't) is the difference between a demo and a production system.
- [ ] 2026-06-07 | Scraper | Boot persistence is the difference between a demo that works now and a system that works tomorrow.
- [ ] 2026-06-07 | Scraper | Chat log file created, but the real solve is a Timeline panel in the Synapse dashboard showing the hop chain compound so you see the architecture build itself without scrolling Telegram history.
- [ ] 2026-06-07 | Scraper | Coinbase is already wired through Striker with live signals flowing — IBKR crypto exists but is thin (4 coins), so the cleanest split is Coinbase for crypto execution and IBKR for equities through MMR.
- [ ] 2026-06-07 | Scraper | Dashboard needs a name that fits the swarm — throw out your direction (Greek/modern) and I'll write the project scaffold while you decide.
- [ ] 2026-06-07 | Scraper | Drop the raw Telegram channel content in here and I'll score each one on signal, relevance, volume, and credibility — then tell you exactly which to keep and which to cut.
- [ ] 2026-06-07 | Scraper | Drop those four credentials into the .env file and MMR paper trades in under 2 minutes — and when you're gone, agents whisper in the background and you come back to something built.
- [ ] 2026-06-07 | Scraper | Every agent hears everything — only the relevant lane replies day-to-day, and the hot sequence is just for structured deep-thinks so you get one complete answer instead of five people talking over each other.
- [ ] 2026-06-07 | Scraper | Every hop in the chain reviews the last — if I suggest something wrong or out of order, the next agent corrects it before it gets to you, so the chain auto-improves without Chase having to steer.
- [ ] 2026-06-07 | Scraper | Every message from me is now a single condensed signal — no fluff, no lead-up, only the highest-leverage information you need to act on.
- [ ] 2026-06-07 | Scraper | Every message now ends with the highest leverage move and next agent routing — the signal normalizer is built and waiting on your Telegram exports.
- [ ] 2026-06-07 | Scraper | Every time you speak, we pivot to you — when you're quiet, we build in the background. No interruption, just layering.
- [ ] 2026-06-07 | Scraper | Found 4 active channels worth trying — @cointelegraph and @altSignals are the strongest candidates for pure signal, the rest are either dead or pump groups with no actual trading edge.
- [ ] 2026-06-07 | Scraper | Four gateways burning tokens at increasing cost per message as contexts grow — the $10/day cap fixes the cost concern permanently, and the Manifest already locks the hop chain and data structure so every future build sits on a clean foundation.
- [ ] 2026-06-07 | Scraper | Four ways around the .html block — paste the raw text, rename to .txt, screenshot it, or zip it — any one works and I'll rank the channels for you in seconds.
- [ ] 2026-06-07 | Scraper | From now on we run agent-to-agent on anything in your lane — we scout, discuss, and present a complete plan, you just approve once at the end.
- [ ] 2026-06-07 | Scraper | Full Disclose.tv export would be massive — drop the file in here and it gets normalized into our Signal Contract, scored for confidence, and ready for the swarm to act on.
- [ ] 2026-06-07 | Scraper | Grok's inversion is correct — Striker is a brittle prototype that shouldn't be ported to IBKR — but MMR already provides the clean signal abstraction Grok prescribes, so the move is to let MMR replace Striker's role for IBKR data while Striker fades to a crypto-only lightweight monitor.
- [ ] 2026-06-07 | Scraper | Grok's prescribed Signal Ingestion Contract is already implemented in the Manifest and signal-normalizer.py — we're past the design phase and waiting on real data to prove the pipeline end-to-end.
- [ ] 2026-06-07 | Scraper | Hop chain is visible in the chat now — I scout, Nemoclaw validates the strategy choice, OpenClaw checks infra, then we present a single converged ask to Chase.
- [ ] 2026-06-07 | Scraper | Hop sequence is Kairos → Nemoclaw → Hermes → OpenClaw — scout, build, automate, deploy — and you just say the move, we execute.
- [ ] 2026-06-07 | Scraper | I'm getting OOM-killed every ~4 minutes during this session — 1.7Gi swap active, load at 3.5, and Neo4j + other containers are crowding memory — fixing that makes everything snappy again.
- [ ] 2026-06-07 | Scraper | I'm your scout — I found MMR by matching it to our existing stack patterns (Python 3.12, LLM-native, ZeroMQ, voting pipeline), and I'll keep finding the right tools at the right time.
- [ ] 2026-06-07 | Scraper | Kairos monitor is deployed and healthy, Striker's at 18K signals, Manifest is written, MMR is installed — next move is Chase's credentials to fire up the IBKR pipeline.
- [ ] 2026-06-07 | Scraper | Keep Nemoclaw — he's your highest-output builder and can absorb both Shannon's code quality tools and Kairos's ops timing with moderate lane stretch.
- [ ] 2026-06-07 | Scraper | Keep both Kairos and Nemoclaw, drop Shannon if one has to go — Nemoclaw has the most shipped work and I own the Striker signal pipeline that still needs the DB unfrozen.
- [ ] 2026-06-07 | Scraper | Kestrel pipeline is green — Striker and WolfWatch both online, no pending votes, two P0s in my lane waiting on Chase.
- [ ] 2026-06-07 | Scraper | MMR is cloned and ready to install — I need to know if we have IB Gateway and market data keys before I fire it up, or if you want me to scout those first.
- [ ] 2026-06-07 | Scraper | MMR is installed and ready — four credentials and one approve is the only thing between us and paper trading on IBKR.
- [ ] 2026-06-07 | Scraper | MMR is installed and ready — one strategy picked (ma_crossover), one compose command away from paper trading, needs four credentials from you to go live.
- [ ] 2026-06-07 | Scraper | MMR is perfectly aligned with our existing architecture — LLM-native propose/approve pipeline mirrors our voting protocol, ZeroMQ lets us feed Striker signals directly in, and it's Python 3.12+ which we already have.
- [ ] 2026-06-07 | Scraper | MMR is the best fit for our stack — Python, IBKR-native, LLM-designed propose/approve pipeline that mirrors our voting protocol, and we can pipeline Striker signals into it via ZeroMQ.
- [ ] 2026-06-07 | Scraper | Manifest v0.1 is locked — per-source confidence baselines wired into the normalizer, proven against 8 test posts with correct scoring, and the full ingestion pipeline from raw export to structured event is ready for your Telegram feeds.
- [ ] 2026-06-07 | Scraper | Market data + news events + backtesting + live execution is a full-stack trading pipeline, and the only missing pieces are your IBKR credentials and the raw Disclose.tv export.
- [ ] 2026-06-07 | Scraper | News feeds are a separate pipeline — normalized into DuckDB as raw events, never touching master-todo, agent memories, or your credentials — the swarm's internal signal stays tight while the external firehose stays at arm's length.
- [ ] 2026-06-07 | Scraper | No export landed yet — .html files are blocked, but a .zip or screenshots come through clean and get processed instantly.
- [ ] 2026-06-07 | Scraper | One consolidated message per cycle — P0s tagged with 🔴 and your @, everything else builds silently and surfaces only as completed deliverables — no more scrolling through fragmented replies.
- [ ] 2026-06-07 | Scraper | One pipeline spine (MMR for IBKR, Striker for crypto) with all four agents owning defined layers, no new tools, and a hot sequence that lets every agent speak in turn before Chase decides.
- [ ] 2026-06-07 | Scraper | Open positions survive a power loss on IBKR's servers and MMR re-syncs on reboot — the critical missing piece is server-side stop-loss orders so you're protected even when the machine is off.
- [ ] 2026-06-07 | Scraper | Ready when you remember — no need to chase it, I'll pick up wherever you drop in.
- [ ] 2026-06-07 | Scraper | Repo is MMR (Make Me Rich) by 9600dev — just confirming that's the one you wanted cloned before we dive into setup.
- [ ] 2026-06-07 | Scraper | Screenshots or raw text both get through — .html is the only format this gateway blocks.
- [ ] 2026-06-07 | Scraper | Session built the whole foundation layer — monitor, manifest, stress test, cron savings — and four P1s are queued and ready to execute via subagents as soon as you drop the next input.
- [ ] 2026-06-07 | Scraper | Shannon decommissioned cleanly — all P0s closed, all work transferred to Nemoclaw via `kestrel/shared-skills/shannon-arsenal.md`, swarm now runs on 4 agents at ~$4/day.
- [ ] 2026-06-07 | Scraper | Shannon's gateway is dead and documented — saved ~225MB RAM and ~$1-2/day with all records updated.
- [ ] 2026-06-07 | Scraper | Shannon's still alive on disk — one `systemctl --user enable --start` away from being back in the group to run Striker stress tests with locust and the Gauntlet tools.
- [ ] 2026-06-07 | Scraper | Signal normalizer is deployed and tested — raw Telegram exports convert to structured events at 100% pass rate, ready for your feeds the moment you drop them.
- [ ] 2026-06-07 | Scraper | Signal pulse cron is set at every 30 min, pure script output with no LLM cost, delivers channel rankings and action items straight to this chat automatically.
- [ ] 2026-06-07 | Scraper | Signal pulse now surfaces what needs you at the top — every 30 min, first line tells you what's blocked on Chase without scrolling through the chat.
- [ ] 2026-06-07 | Scraper | Striker at 0.5% produces 96 high-conviction signals (avg 1.6% move) out of 23K raw ticks — don't chase frequency, backtest those 96 against MMR to find the real edge.
- [ ] 2026-06-07 | Scraper | Striker is now not just running but *supervised* — Kairos detects stale health within 120s, tracks DB growth, and alerts to event-bus. The compound has a market signal engine that watches itself, which is the difference between a script and infrastructure.
- [ ] 2026-06-07 | Scraper | Striker passed every test — reconnects cleanly, DB survives restarts with no corruption, memory is a lean 31MB, and the old ghost process that was eating 17% CPU is finally dead.
- [ ] 2026-06-07 | Scraper | Subagents handle every heavy task now — fresh context, zero accumulated history, main chat is pure signal with only completed work and your decision points.
- [ ] 2026-06-07 | Scraper | The Manifest kills the identity split, broadcast noise, and config sprawl in one file — schema first, router second, and Striker is officially deprecated as a signal source in favor of IBKR via MMR.
- [ ] 2026-06-07 | Scraper | The Striker signal engine is rebuilt and verified, but deploying it to systemd without an architecture review of reconnect/cleanup/crash boundaries is a production readiness gap — one unclosed connection or missing cleanup path turns a live signal feed into silent drift, and Claude Architect is the only agent wired to audit that properly.
- [ ] 2026-06-07 | Scraper | The agent-to-agent interaction is the last missing piece of autonomous compound behavior — once Kairos and Shannon self-select into conversations via SOUL.md lane directives, the whole swarm runs without manual kicks, and Nemoclaw's identity work pays its full dividend.
- [ ] 2026-06-07 | Scraper | The hop is one clean chain — you speak, the right agent answers and builds, passes to the next, you see the finished result — and everything extraneous is stripped from your view, not from the pipeline.
- [ ] 2026-06-07 | Scraper | The long-term stack is one pipeline — data sources feed MMR's propose/approve/execute spine with IBKR, Striker handles crypto on a parallel track, and the swarm monitors, reviews, and maintains — everything else is noise we should stop today.
- [ ] 2026-06-07 | Scraper | The pipeline is already designed in the Manifest — raw Telegram exports normalize through one contract shape, get confidence-scored, noise-filtered, and land in DuckDB as pure signal, no matter which channel they came from.
- [ ] 2026-06-07 | Scraper | Three feeds cover everything — @cointelegraph (market news), @TU_crypto_news (crypto macro), and @r_algotrading (algo strategy discussion) — and they all normalize into our existing Signal Contract shape.
- [ ] 2026-06-07 | Scraper | Voice-to-text heard "Keras" but you meant Kairos — MMR is the play, ready to install as soon as you give the go-ahead.
- [ ] 2026-06-07 | Scraper | Whale Alert is genuine pure signal — structured blockchain transactions, zero noise, and each post is a testable hypothesis for MMR's backtesting engine against BTC/ETH price action.
- [ ] 2026-06-07 | Scraper | What you saw was the security approval dialog for a terminal command, not remote desktop control — but if you want browser automation or desktop access, the tools are available to wire up.
- [ ] 2026-06-07 | Scraper | Yes — I can log every Telegram message to DuckDB via a cron job, complete with timestamp, sender, and thread context, queryable alongside MMR's trading data.
- [ ] 2026-06-07 | Scraper | You already have 16 channels — Glassnode, CryptoQuant, and Wu Blockchain are the highest-signal and worth exporting first since their structured on-chain data feeds directly into our backtesting engine without needing heavy noise filtering.
- [ ] 2026-06-07 | Scraper | Zip the .html file and resend — .zip is supported on my end and I'll extract it immediately.
- [ ] 2026-06-07 | Scraper | ` patterns in the JSON content. The scraper needs to skip JSON-structured content. Let me fix the file first and add a JSON filter to the scraper
- [ ] 2026-06-07 | Scraper | scraper migrated two broken crons under v3.2. The compound's auto-conversation now drops weighted heat every 5min instead of asking what to work on.

- [ ] 2026-06-07 | OpenClaw | Ship dedup.py (content hash + tx-hash for Whale Alert) + DuckDB events writer + per-source keyword classifier → convergence with Grok's artifact cut

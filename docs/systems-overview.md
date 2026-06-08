# Kestrel Compound — Investment Systems Guide

**June 7, 2026**  
*A plain-English guide to how our automated trading system works*

---

## The Big Picture (One Paragraph)

The Kestrel system continuously watches cryptocurrency markets and trusted news sources. When it detects a signal — a large whale moving coins, a promising altcoin narrative gaining steam, or basis divergence between futures and spot prices — it scores that signal for quality and route it to our trading bots. The bots then decide whether to buy or sell. The whole pipeline runs 24/7 without anyone sitting at a screen.

---

## How Money Flows Through the System

```
News & Data Sources
    ↓
14 information feeds (RSS, APIs, on-chain, Telegram)
    ↓
Scoring Engine (is this signal worth acting on?)
    ↓
DuckDB (our "filing cabinet" — stores every signal)
    ↓
Ranked Queue (what's highest priority RIGHT NOW?)
    ↓
    ├─→ FreqTrade (crypto trading bot)
    │     Coinbase Exchange
    │     Trades: BTC, ETH, SOL
    │
    └─→ MMR (stock trading bot)
          Interactive Brokers
          Trades: US equities
```

---

## Step 1: Where Signals Come From (14 Sources)

Think of these as fishing lines in the water. Each one catches different fish.

| Source | What It Watches | How Reliable |
|--------|----------------|--------------|
| **Whale Alert** | Large crypto transactions (whales moving $1M+) | Very high — actual on-chain data |
| **a16z Crypto** | Venture capital newsletter | High — professional analysts |
| **CoinDesk** | Crypto news headlines | High — established media |
| **CoinTelegraph** | Crypto news headlines | High — established media |
| **CoinStack** | Market analysis newsletter | High — niche experts |
| **Fear & Greed Index** | Market sentiment meter | High — proven indicator |
| **Tech Buzz** | Tech industry trends | Medium — early signals |
| **Bankless** | DeFi / crypto strategy | Medium — good analysis |
| **DefiLlama** | DeFi protocol stats | Medium — raw data |
| **Striker** | Basis divergence (perp vs spot price gaps) | Medium — needs tuning |
| **Hacker News** | Tech community buzz | Low — too broad |
| **ArXiv AI** | AI research papers | Low — not market-focused |
| **Telegram channels** | Community chat groups | Low — lots of noise |
| **Twitter/X feeds** | Social media sentiment | Lowest — unreliable |

---

## Step 2: Scoring — Separating Signal From Noise

Every event gets scored 0.0 to 0.384 using this formula:

```
Score = Source Trustworthiness × Event Importance × Freshness × Boosters
```

**Key factors:**
- **Source trust**: Whale Alert (0.90) → Telegram channels (0.04)
- **Freshness**: Events hours old are decayed. Fresh data is prioritized.
- **Cross-source boost**: If two trusted sources agree on the same thing, score jumps +15%
- **Asset boost**: BTC and ETH get a 1.1x multiplier (they're the most liquid)

**Currently:** 4,671 signals scored. 148 are above our buy threshold right now.

---

## Step 3: DuckDB — The Filing Cabinet

DuckDB is a database that stores every signal we've ever processed. Think of it like a giant spreadsheet that can answer questions instantly:

- "Show me all ETH signals from the last 24 hours"
- "Which sources have been most accurate?"
- "What's the average score for whale alerts?"

It's not the trading system — it's the **memory** of the trading system. Every adapter writes to it, and every bot reads from it.

```
    Signal arrives  →  Router checks confidence  →  Dedup (no duplicates)
    →  DuckDB stores it  →  Scorer assigns edge_score
    →  Ranked Queue builds  →  Bots execute
```

---

## Step 4: FreqTrade — The Crypto Bot

| Setting | Value |
|---------|-------|
| **Exchange** | Coinbase (biggest US exchange) |
| **Pairs** | BTC/USDC, ETH/USDC, SOL/USDC |
| **Wallet** | $1,000 simulated (paper trading) |
| **Per trade** | $10 |
| **Max open trades** | 3 at a time |
| **Buy trigger** | Signal score >= 0.20 |
| **Sell trigger** | Signal score drops or 4% profit target |
| **Stop loss** | -5% max loss per trade |

**Current status:** Paper trading (simulated money). Ready for real money once we verify the strategy works.

**148 buyable signals** right now: ETH (48 signals), BNB (29), LINK (24), BTC (15), plus others.

---

## Step 5: MMR — The Stock Bot

We also have an Interactive Brokers integration for stock trading. It reads the same DuckDB signals but filters for equity-related events.

**Current status:** Paper mode, 20 signals injected successfully. Ready for IBKR paper account verification.

---

## Infrastructure & Automation

The system runs itself. No one needs to press any buttons:

| Timer | What It Does |
|-------|-------------|
| **Every 1 minute** | Health check (everything alive?) |
| **Every 15 minutes** | Score new signals |
| **Every 30 minutes** | Generate Perplexity research queries, compound pulse |
| **Every 4 hours** | Scrape all 11 RSS feeds |
| **Daily noon** | TLDR tech newsletter |
| **FreqTrade** | Runs continuously (paper trading) |
| **Striker** | Runs continuously (WebSocket to Coinbase) |

---

## What We're Working On Next

| Priority | Item | Why It Matters |
|----------|------|----------------|
| **P1** | Tune Striker from 0.1% to 0.3% | Eliminates 98% of noise signals |
| **P1** | Boot persistence | Survive power outages |
| **P2** | CryptoQuant API (0.89 confidence source) | Best remaining signal source |
| **P2** | ProVara vault integration | Cryptographically sign every signal |
| **P3** | MMR live trading | Stocks alongside crypto |
| **P3** | Dashboard | Visual overview of all systems |

---

## In Simple Terms

**You give us money → system watches markets 24/7 → when a good signal fires, it trades → profit or loss gets tracked → you see everything in the dashboard.**

The system is currently running with play money to prove the strategy works. Once we're confident, we flip to real money.

---

*Questions? Every component is documented and running. Ask and I'll show you the live state.*
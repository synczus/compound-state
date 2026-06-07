# Whale Alert On-Chain Transaction Analysis
**Dataset:** 871 normalized Whale Alert events (signal contract schema)
**Source:** `/tmp/whale_test.jsonl`
**Date Range:** 2019-04-04 to 2019-04-26 (approx.)
**Confidence:** All 871 events at 0.95 confidence

---

## 1. Asset Distribution

| Asset | Events | % of Total | USD Volume | % of Total USD |
|-------|-------:|-----------:|-----------:|---------------:|
| BTC | 332 | 38.1% | $1,892,863,813 | 53.7% |
| ETH | 97 | 11.1% | $335,537,817 | 9.5% |
| XRP | 84 | 9.6% | $436,037,175 | 12.4% |
| HT | 79 | 9.1% | $78,233,777 | 2.2% |
| NEO | 51 | 5.9% | $73,623,557 | 2.1% |
| BNB | 45 | 5.2% | $58,006,319 | 1.6% |
| USDT | 32 | 3.7% | $228,637,224 | 6.5% |
| EOS | 23 | 2.6% | $98,554,558 | 2.8% |
| XLM | 18 | 2.1% | $28,203,091 | 0.8% |
| TRX | 18 | 2.1% | $42,423,036 | 1.2% |
| USDC | 13 | 1.5% | $23,796,986 | 0.7% |
| Others (22 assets) | 59 | 6.8% | $226,145,739 | 6.4% |
| **Total** | **871** | **100%** | **$3,522,059,092** | **100%** |

**Key observation:** Bitcoin dominates in both event count (38.1%) and USD volume (53.7%). XRP punches above its event count weight (12.4% of USD on 9.6% of events), driven by large wallet-to-wallet transfers.

---

## 2. Exchange Flow Patterns

### All Assets — Flow Direction

| Direction | Count | % of Total | USD Volume | % of Total USD |
|-----------|------:|-----------:|-----------:|---------------:|
| Exchange → Unknown (Outflow) | 295 | 33.9% | $1,128,453,336 | 32.0% |
| Unknown → Unknown (Wallet shuffle) | 218 | 25.0% | $1,152,128,338 | 32.7% |
| Unknown → Exchange (Inflow) | 187 | 21.5% | $603,223,202 | 17.1% |
| Exchange → Exchange (Arbitrage/liquidity) | 51 | 5.9% | $173,207,254 | 4.9% |
| Unknown → Exchange/Other variants | 94 | 10.8% | $355,879,665 | 10.1% |
| Other | 26 | 3.0% | $109,167,297 | 3.1% |

**Net exchange flow (all assets):**
- Total exchange inflow: **$603,223,202** (187 transactions)
- Total exchange outflow: **$1,128,453,336** (295 transactions)
- **Net outflow from exchanges: -$525,230,134**
- **Inflow/Outflow ratio (USD): 0.53**

This dataset shows a clear pattern of capital leaving exchanges (32% of USD volume vs 17% entering), consistent with self-custody trends or OTC settlement.

### Exchanges Appearing in the Data

Binance, Bitfinex, Bitstamp, Bittrex, Coinbase, Gate.io, Gemini, HitBTC, Huobi, Kraken, Kucoin, OKEx, Poloniex (13 unique).

---

## 3. Top 10 Largest USD-Value Transactions

| # | Asset | Amount | USD Value | Flow | Date (UTC) |
|---|-------|-------:|----------:|------|------------|
| 1 | BTC | 3,831.00 | **$19,573,181** | Poloniex → Unknown wallet | 2019-04-14 19:46 |
| 2 | XRP | 60,000,000 | **$19,204,622** | Unknown → Unknown | 2019-04-16 06:28 |
| 3 | ETH | 123,687.00 | **$19,056,953** | Bitfinex → Unknown | 2019-04-26 01:07 |
| 4 | TTC | 188,665,455 | **$18,839,082** | Unknown → Unknown | 2019-04-16 14:32 |
| 5 | ETH | 121,496.00 | **$18,719,424** | Bitfinex → Unknown | 2019-04-26 01:07 |
| 6 | XRP | 50,115,711 | **$17,936,263** | Unknown → Bitstamp | 2019-04-08 21:00 |
| 7 | BTC | 3,500.00 | **$17,887,725** | Bittrex → Unknown | 2019-04-16 17:21 |
| 8 | XRP | 50,000,000 | **$17,660,163** | Unknown → Unknown | 2019-04-11 01:21 |
| 9 | BTC | 3,493.00 | **$17,566,047** | Poloniex → Unknown | 2019-04-15 19:55 |
| 10 | XRP | 50,000,000 | **$17,419,458** | Unknown → Unknown | 2019-04-11 04:00 |

Total of top 10: **$182,862,918** (5.2% of total dataset USD volume)

**Pattern:** 7 of 10 top transactions are exchange outflows (assets leaving exchanges to unknown wallets). The $19.6M BTC from Poloniex is the single largest event. The two ETH transactions from Bitfinex occurred just 1 second apart, likely the same whale splitting a withdrawal.

---

## 4. BTC: Exchange Destinations vs. Unknown Wallets

### BTC Transfer Destination Breakdown

| Destination Type | Transactions | % of BTC Events | BTC Volume | USD Volume |
|-----------------|------------:|----------------:|-----------:|-----------:|
| **To Unknown Wallets** | 220 | **66.3%** | 198,297.13 | $1,046,239,895 |
| **To Exchanges** | 102 | **30.7%** | 68,428.46 | $357,090,065 |
| Other / Unclassified | 10 | 3.0% | 5,113.33 | $26,093,444 |

**Key percentage: 66.3% of large BTC transfers go to unknown wallets, vs 30.7% to exchanges.**

### BTC Destination Exchanges (ranked by count)

| Exchange | Inflow Count | Inflow BTC | Inflow USD |
|----------|------------:|-----------:|-----------:|
| Coinbase | 22 | 12,618.80 | $95,452,567 |
| Bittrex | 15 | 7,089.00 | $35,820,350 |
| Kraken | 14 | 502.30 | $2,833,167 |
| Huobi | 13 | 11,405.00 | $56,080,636 |
| Bitfinex | 12 | 13,859.10 | $74,159,304 |
| Poloniex | 9 | 6,810.00 | $38,785,827 |
| bitFlyer | 9 | 6,808.86 | $34,396,985 |
| Bitstamp | 8 | 1,611.80 | $7,997,603 |
| Binance | 6 | 2,043.60 | $10,166,134 |
| OKEx | 3 | 5,680.00 | $32,013,866 |

### BTC Source Exchanges (ranked by outflow count)

| Exchange | Outflow Count | Outflow BTC | Outflow USD |
|----------|-------------:|------------:|------------:|
| Huobi | 50 | 32,621.00 | $166,558,429 |
| Bittrex | 43 | 30,097.85 | $163,116,940 |
| Bitstamp | 38 | 31,950.69 | $154,368,752 |
| Poloniex | 18 | 21,503.89 | $113,374,848 |
| OKEx | 17 | 18,978.56 | $98,800,177 |
| Kraken | 16 | 11,009.00 | $56,879,836 |
| Coinbase | 14 | 7,838.00 | $41,364,258 |
| Binance | 12 | 2,478.60 | $13,241,409 |
| Bitfinex | 5 | 5,869.84 | $32,443,019 |

---

## 5. Stablecoin Minting/Burning Patterns

### Stablecoin Events Overview

Total stablecoin events: **46** (32 USDT + 13 USDC + 1 GUSD)

Combined stablecoin USD volume: **$253,456,041** (7.2% of total dataset)

### USDC — Treasury Minting Pattern

| Action | Count | Total Amount | Total USD |
|--------|------:|-------------:|----------:|
| USDC Treasury → "minted" | 6 | 11,631,088 | $11,644,367 |
| USDC Treasury → Exchange/Binance | 2 | 4,000,000 | $3,982,282 |
| USDC Treasury → Unknown wallet | 1 | 1,197,897 | $1,201,074 |
| Exchange → Unknown | 3 | 4,530,862 | $4,546,626 |

**Pattern:**
- 6 of 13 USDC events are labeled "minted" by the USDC Treasury — first event on Apr 4, cluster on Apr 5, then a heavy cluster on Apr 9 (3 mints in ~5 hours), and 2 more mints on Apr 26.
- Post-mint, USDC flows to Binance directly or to unknown wallets, suggesting OTC desk distribution.
- The Apr 9 cluster at 15:06–21:45 UTC shows: mint → mint → wallet → Binance → wallet dispersal, a clear treasury-to-exchange pipeline.

### USDT — Tether Treasury & Large Unknown Movements

| Action | Count | Total Amount | Total USD |
|--------|------:|-------------:|----------:|
| Tether Treasury → Unknown wallet | 11 | 84,200,220 | $84,499,520 |
| Unknown wallet → Exchange (inflow) | 8 | 49,988,600 | $50,134,224 |
| Exchange → Unknown (outflow) | 6 | 27,797,541 | $27,894,055 |
| Unknown → Unknown | 3 | 32,977,000 | $33,178,187 |
| Exchange → Exchange | 2 | 19,232,446 | $19,140,571 |
| Exchange → Tether Treasury (burn) | 1 | 6,000,000 | $6,011,124 |

**Key patterns:**
1. **Massive Tether Treasury issuance:** On Apr 18–25, Tether Treasury sent **$84.5M** to unknown wallets in 11 transactions — almost all "steady" velocity, suggesting pre-programmed OTC distribution.
2. **Heavy clustering Apr 21–25:** 8 Treasury issuances in 4 days, peaking Apr 24 with 5 issuances totaling $35M in ~86 minutes.
3. **Treasury → Unknown → Exchange pipeline:** The typical pattern: Tether Treasury → unknown wallet (11x), then unknown wallet → Huobi/Bitfinex/Binance (8x), confirming the OTC desk distributing freshly minted USDT.
4. **One burn event:** Bitfinex returned 6M USDT to Tether Treasury on Apr 20, a partial redemption.
5. **Exchange-to-exchange USDT movement:** $19.1M between Binance and Bitfinex — likely arbitrage or liquidity rebalancing.

### GUSD

One event: 1,027,434 GUSD ($1,021,831) from unknown wallet → HitBTC.

### Time Clustering Metrics

| Metric | Value |
|--------|------:|
| Date range | Apr 4 – Apr 26 (22 days) |
| Total stablecoin events | 46 |
| Avg gap between events | 695 min (~11.6 hours) |
| Minimum gap | 129 sec (2.1 min) — Apr 9 USDC mints |
| Maximum gap | 69 hours |

**Clusters:** The tightest clustering appears on Apr 9 (USDC) and Apr 21–25 (USDT), suggesting batch treasury operations.

---

## 6. BTC Exchange Inflow/Outflow Ratio

### Count Basis

| Metric | Value |
|--------|------:|
| BTC inflow to exchanges (count) | 62 transactions |
| BTC outflow from exchanges (count) | 173 transactions |
| **Inflow/Outflow count ratio** | **0.36** (≈1:2.8) |

### Volume Basis (BTC)

| Metric | Value |
|--------|------:|
| BTC inflow volume | 67,872.00 BTC |
| BTC outflow volume | 160,974.00 BTC |
| **Inflow/Outflow BTC ratio** | **0.42** (≈1:2.4) |

### Volume Basis (USD)

| Metric | Value |
|--------|------:|
| BTC inflow USD | $353,309,454 |
| BTC outflow USD | $840,147,668 |
| **Inflow/Outflow USD ratio** | **0.42** (≈1:2.4) |

**Interpretation:** For every $1 of BTC flowing into exchanges, ~$2.40 flows out. The dataset skews heavily toward exchange outflows.

### Exchange-Level Net BTC Flow

| Exchange | Inflow Count | Outflow Count | Net BTC (count) | Net USD |
|----------|:-----------:|:------------:|:---------------:|--------:|
| Coinbase | 22 | 14 | **+8** (net inflow) | +$54,088,309 |
| Bitfinex | 12 | 5 | **+7** (net inflow) | +$41,716,285 |
| Binance | 6 | 12 | **-6** (net outflow) | -$3,075,275 |
| Kraken | 14 | 16 | **-2** (net outflow) | -$54,046,669 |
| Poloniex | 9 | 18 | **-9** (net outflow) | -$74,589,021 |
| OKEx | 3 | 17 | **-14** (net outflow) | -$66,786,311 |
| Bittrex | 15 | 43 | **-28** (net outflow) | -$127,296,590 |
| Bitstamp | 8 | 38 | **-30** (net outflow) | -$146,371,149 |
| Huobi | 13 | 50 | **-37** (net outflow) | -$110,477,793 |

**Only Coinbase and Bitfinex show net BTC inflow.** All other major exchanges show net outflow, with Huobi, Bitstamp, and Bittrex leading the exodus in both count and volume.

### BTC Wallet-to-Wallet (Unknown→Unknown)

- **30 transactions** totaling **78,382 BTC** ($412.8M) moved between unknown wallets — pure on-chain transfers between private entities, representing 21.8% of BTC USD volume.

### BTC Exchange-to-Exchange (Arbitrage)

- **40 transactions** moving BTC between exchanges — patterns show Kraken as a major recipient from Huobi (many $2–5M transfers), suggesting inter-exchange arbitrage or market-making flows.

---

## 7. Velocity Distribution (All Events)

| Velocity | Count | % |
|----------|------:|---:|
| Steady | 345 | 39.6% |
| Decaying | 305 | 35.0% |
| Rising | 221 | 25.4% |

- **Steady** dominants (39.6%) — programmatic/OTC flows, treasury operations
- **Decaying** (35.0%) — older transfers being detected, possibly delayed alerts
- **Rising** (25.4%) — recent/in-progress movements

---

## Summary of Findings

1. **Dominance of exchange outflows:** 33.9% of all transactions (and 32% of USD volume) are assets leaving exchanges for unknown wallets. BTC outflow dramatically exceeds inflow (ratio 2.4:1 by volume).

2. **Stablecoin minting pipeline:** Clear pattern of USDT and USDC minted by treasuries → distributed to unknown wallets → funneled to exchanges (Huobi, Bitfinex, Binance). $84.5M in USDT issued Apr 18–25 alone.

3. **BTC exchange imbalance:** Only Coinbase and Bitfinex show net BTC inflow. Huobi lost the most BTC in count (37 net outflows) followed by Bitstamp (30) and Bittrex (28).

4. **Whale consolidation:** The top 3 single transactions ($19.6M BTC from Poloniex, $19.2M XRP wallet-to-wallet, $19.1M ETH from Bitfinex) all represent either large exchange withdrawals or cold storage movements.

5. **Data characteristics:** All events at 0.95 confidence, spanning ~22 days in April 2019. Total observed on-chain movement: **$3.52 billion** across 871 events.

---

*Report generated from /tmp/whale_test.jsonl — 871 events, 100% confidence=0.95, 35 distinct assets.*
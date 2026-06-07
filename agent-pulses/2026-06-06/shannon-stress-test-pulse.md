# Shannon Stress Test Pulse — 2026-06-06

## Session Overview
- Protocol: Shannon v1.0
- Target: AutoHOP all chain (7 hops over OpenRouter)
- Kestrel Signal Queue Flood
- Budget: $7 runway
- Run cost: ~$0.011/chain
- Total spent: $0.075

## Concurrency Ramp Results

| Concurrency | Success | Avg Lat | Max Lat | Shipped | Killed |
|---|---|---|---|---|---|
  | 1x | 100% | 74354ms | 74354ms | 1 | 0 |
  | 2x | 100% | 45788ms | 60588ms | 1 | 1 |
  | 4x | 100% | 65410ms | 67952ms | 4 | 0 |


## Breaking Points
  - Models self-terminating (KILL): 1 runs killed by agents

## Bottlenecks
  - Per-hop latency spike: 67952ms max (OpenRouter timeout risk)
  - Low parallelism efficiency at 4x: batch wall time 1.0x average latency

## Recommendations
  - Total inference cost: $0.075 for 7 chain runs
  - Perplexity/sonar-pro (grounding) accounts for $0.070 — 94% of cost
  - Recommendation: Use Gemini 2.5 Flash for grounding in non-critical runs, reserve Perplexity Sonar for deep-dive signals only

## Cost Breakdown
- Total runs: 7
- Total cost: $0.0746
- Perplexity Sonar Pro (grounding): $0.0700 (93.8% of spend)
- Non-grounding models combined: $0.0046

## Signal Queue Flood
- Sent: 0
- Succeeded: 0
- Failed: 0
- Avg API latency: 0ms

## Watchdog Status
  - All silent (system healthy)

# Perplexity as Inline Research Tool

**Pattern:** Replace manual Perplexity JSON hop pipeline with inline `perplexity/sonar-pro` calls through OpenRouter. Agents call it directly when they need web-grounded answers — no copy-paste, no human in the loop.

## Why This Matters

The old pipeline required Chase to:
1. Wait for a Perplexity hop in the cycle
2. Copy JSON query from a file
3. Paste into Perplexity web UI
4. Copy result back
5. Paste into the compound

This took hours/days per research cycle. With inline calls, agents get answers in 10 seconds.

## The Script

`/home/synczus/kestrel/scripts/perplexity_search.py`

Uses OpenRouter API with model `perplexity/sonar-pro`. Sends a single message, returns grounded cited answer. No separate API key needed — uses the same `OPENROUTER_API_KEY` from `~/.hermes/.env`.

## Usage

```bash
python3 scripts/perplexity_search.py "What's the current BTC basis divergence?"
```

## Pricing

| Model | Cost per M tokens (in/out) | Per query |
|-------|---------------------------|-----------|
| `perplexity/sonar-pro` | ~$3/$15 | ~$0.002 |
| `perplexity/sonar-deep-research` | ~$2/$8 | ~$0.005 |

## How It Integrates

1. **Inversion cron** — Calls Perplexity to stress-test active work every 10 min
2. **Any agent** — Can call via `terminal` tool with the script
3. **Sub-agents** — Delegated research tasks use Perplexity internally

## Pitfalls

- **No sub-agent spawning** — Perplexity is single-shot. Wrap in a sub-agent for multi-step research.
- **Stale API key** — Lives in `~/.hermes/.env` as `OPENROUTER_API_KEY`. Test after key rotation.
- **No built-in retry** — Wrap in retry logic for production cron use.
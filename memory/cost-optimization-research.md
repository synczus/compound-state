# Cost Optimization Research — Compound Architecture
*Generated: 2026-06-08 03:22 ET via Perplexity Sonar Pro*

## 1. Overusing expensive models for every turn
**Problem:** All 5 agents (plus sub-agents) use high-end models for every message.
**Solution:** Tiered model stack — cheap router (deepseek flash) for 80% of turns, escalate to Perplexity-Pro / Grok only for high-stakes decisions. Single-responder protocol already in place.
**Savings:** ~70-90% on model costs.

## 2. Large context window abuse
**Problem:** Every call includes full Telegram history (multi-thousand tokens).
**Solution:** Short rolling window (15-30 messages) + vector retrieval for older context. Sub-agents get compact task specs, not full parent context.
**Savings:** ~50-70% prompt token reduction.

## 3. Agent dogpile on Telegram messages
**Problem:** Multiple agents responding to same message.
**Solution:** Already solved — single-responder protocol. Reinforce with silence rules (skip reactions, short non-actionable messages).
**Savings:** ~40-60% inference call reduction.

## 4. Sub-agent model waste
**Problem:** Sub-agents use same heavy model as parent for simple tasks.
**Solution:** Task-specific tiering — Tier 1 (cheap) for summarization/extraction, Tier 2 (mid) for reasoning, Tier 3 (expensive) only for trading/infra changes. Compact task prompts (≤800 tokens).
**Savings:** ~20-40% overall.

## 5. Missing prompt caching
**Problem:** Repeated system prompts for routing, summarization, classification.
**Solution:** Hash-based cache with TTL (5-30 min). Batch similar operations into single LLM call.
**Savings:** ~10-25% reduction.

## 6. Telegram volume cost
**Problem:** Every group message triggers agent processing.
**Solution:** Silence rules for non-actionable messages. Don't respond to reactions, short messages, or side chatter unless @mentioned.
**Savings:** ~20-30% fewer calls.

## 7. Sub-agent death → persistence gap
**Problem:** Sub-agents spin up, do work, die — no memory carried forward.
**Solution:** Sub-agents write results to file or AgentMemory before exit. Parent reads on next spawn.
**Savings:** Eliminates re-research cost (hard to quantify, significant).

**Current Status:**
- Single-responder protocol ✅ already live
- Model fallbacks (deepseek → perplexity) ✅ wired
- Sub-agent efficiency protocol ✅ active
- AgentMemory cross-agent ✅ seeded with lessons
- Ramble Gate ✅ prevents wasted builds

**Next Optimizations:**
1. Short rolling window (15-30 messages) instead of full history
2. Silence rules for non-actionable messages
3. Sub-agent task prompt compaction (under 800 tokens)
4. Prompt caching for routing/summarization calls
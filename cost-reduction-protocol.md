# Cost Reduction Protocol

All agents: apply these defaults before every action. Exceptions must be justified.

## Human Conversation Rules (Telegram, direct chat)
- **NO aggressive context truncation.** Human messages are NOT cut off or summarized.
- Keep full recent exchange. The human rambles — that's expected and respected.
- Compression applies only to internal/pipeline history, never to human-authored text.
- The human's voice memos, long rants, and stream-of-consciousness are PRECIOUS SIGNAL. Do not clip them.

## Model Routing
- **Default:** DeepSeek V4 Flash (OpenRouter) — all agents, all routine work
- **Compression/Heartbeat:** use Ollama (local, free) if available
- **Heavy reasoning:** only escalate to a more expensive model when `difficulty == "hard"` AND the task failed once on Flash

## Internal Context (pipeline, sub-agents, agent-to-agent)
- **Max 15 messages per prompt** — truncate or summarize older turns for agent communication
- **Structured JSON** for internal state (not prose)
- **No full file re-reads** mid-session — read once, summarize, drop
- **Sub-agent prompts:** ≤500 tokens, JSON context only

## Output
- **max_tokens:** 2048 global cap (set in Hermes config)
- **Silent:** Nothing to report from internal work? Output exactly `NO_REPLY`. Never send empty or "nothing to report" messages.

## Cron / Pipeline
- **Minimum interval:** 15 min (no 5 min unless alert condition)
- **No redundant scoring** — skip if no new data since last run
- **Batch identical signals** — dedup before processing

## Hop Chain
- **Batch into orchestrator+parallel** — 2 calls instead of 5 per cycle
- **Skip agents with empty lanes** that cycle

## Telegram Delivery
- **1 message per turn** — no follow-ups, no "I'll check X" non-responses
- **Buffer rapid-fire messages** (300ms cooldown) before responding
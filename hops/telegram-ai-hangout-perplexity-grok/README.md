# Telegram AI Hangout → Perplexity → Grok (One-Shot Hop)

One-shot research + analysis hop that sources directly from the Telegram AI Hangout group and automatically injects the agent responses into the compound.

## Purpose
- Pull recent conversation context from the AI Hangout (DuckDB `signals` preferred, `data/chat-history.json` fallback).
- Send the live discussion (plus optional seed) to Perplexity for deep web-grounded research.
- Pipe the research + original context to Grok for adversarial review, implications, and concrete recommendations.
- **Auto-ingest** both agent outputs into the compound knowledge layer so every environment (kestrel, huntsystems, etc.) sees them on next load.

## Usage (one-shot)
```bash
# Latest hangout discussion
python3 scripts/one-shot-hangout-perplexity-grok.py

# With a specific seed/question from the chat
python3 scripts/one-shot-hangout-perplexity-grok.py "What are the implications of the new llama.cpp changes for our signal pipeline?"
```

## Output
Creates a timestamped directory:
```
hops/telegram-ai-hangout-perplexity-grok/<YYYY-MM-DD_HHMMSS>/
├── context.md
├── perplexity-output.json
├── perplexity-output.md
├── grok-output.json
├── grok-output.md
└── summary.md
```

## Auto-Add to Compound (across environments)
The script automatically:
- Appends a consolidated entry to `memory-bank/knowledge/hangout-hops.md` (portable, loaded by agents).
- Writes a staging artifact (`staging/hangout-hop-*.md`) that `build_hub_intake.py` / HUB_INTAKE pick up.
- Best-effort insert into DuckDB `events` table (ingestion path).
- All paths are relative to the local kestrel tree → works when the repo is symlinked or copied to other machines/environments.

After running, the next agent session (or manual `python3 swarm/build_hub_intake.py`) will surface the new Perplexity research + Grok analysis in the compound context.

## Models (current)
- Perplexity: `perplexity/sonar-pro`
- Grok: `x-ai/grok-2-1212`

Override by editing the constants at the top of the script if your account has different strong models.

## Credit / Cost Note
This is a real two-call hop (research + analysis). It will consume OpenRouter credits. The compound already has budget guards in the main swarm path; this standalone script is intentionally direct for one-shot power.

Run it when the discussion in the AI Hangout actually needs deep external grounding + sharp review.

## Integration with existing patterns
Follows the style of:
- `hops/brain-dump-hop/` and `hops/perpetual-hop/`
- `scripts/perplexity_search.py`
- `scripts/inversion-cron.py` (chat context reading)
- `swarm/hop_chains.py` + `hub.py` (Perplexity → Grok positioning in the larger AutoHOP)

This is the focused, on-demand "AI Hangout → Perplexity → Grok" slice the compound has referenced in several places (lineup-hop, content-spawner, etc.).

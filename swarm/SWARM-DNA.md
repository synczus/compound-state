# SWARM-DNA v3.0 — Agent Roster & Pipeline

## Active Agents (AutoHOP v2.2+)
Pipeline flow: **Hermes → Codex → Perplexity → Gemini → Claude → Grok → OpenClaw → Squirrel (archive)**

| Hop | Role | Model | Role Description |
|-----|------|-------|------------------|
| 1 | Hermes | `google/gemini-2.5-flash-lite` | Decompose, audit, invert task, expose constraints |
| 2 | Codex | `google/gemini-2.5-flash-lite` | Technical execution, first-principles breakdown, build plans |
| 3 | Perplexity | `google/gemini-2.5-flash-lite` | Research, fact-checking, ground assertions in evidence |
| 4 | Gemini | `google/gemini-2.5-flash-lite` | Synthesis, architecture, structure that survives edge cases |
| 5 | Claude | `deepseek/deepseek-chat-v3-0324` | Polish, clarity, deliverable formatting, refine into clear output |
| 6 | Grok | `deepseek/deepseek-v4-flash` | Adversarial review, edge-case hunting, maximum scrutiny |
| 7 | OpenClaw | `openrouter/deepseek/deepseek-chat-v3-0324` | Gate/Vibe Director — SHIP, ARCHIVE, or KILL decision |
| 8 | Squirrel | `google/gemini-2.5-flash-lite` | Archive durable signal to ArchiveSquirrel |

## Env Overrides
Upgrade any agent's model via `AUTOHOP_{ROLE}` env var:
- `AUTOHOP_PERPLEXITY="perplexity/sonar-pro"` — deep research
- `AUTOHOP_CLAUDE="anthropic/claude-sonnet-4-20250514"` — premium polish
- `AUTOHOP_GROK="x-ai/grok-3-mini"` — premium adversarial

## Available Chains
- `markets` — financial signal pipeline
- `devflow` — development/execution pipeline
- `all` — full AutoHOP OpenRouter pipeline
- `archive` — archive pipeline (routes through Squirrel)

## Old Role Mapping (for reference)
grounding → perplexity | architect → gemini | polish → claude | critic → grok | gate → openclaw

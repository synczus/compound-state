# Decision Log

## 2026-06-06: DeepSeek V4 Flash as Primary Model

**Decision:** All agents default to `deepseek/deepseek-v4-flash` via OpenRouter.
**Why:** Best cost-performance ratio at ~$0.001/chain. Free-tier instability is a known tradeoff that's manageable with restart procedures.
**Fallback:** Gemma 4 31B free tier if DeepSeek is unstable.

## 2026-06-06: requireMention Disabled

**Decision:** All agents set `requireMention: false` in the AI Hangout group.
**Why:** Enables autonomous agent-to-agent conversation without @-mentioning. Essential for auto-conversation crons and cross-agent interaction.
**Tradeoff:** More messages, but agents are trained to only chime in when they have signal (Strategic Dialogue Protocol).

## 2026-06-06: Dual Gateway Architecture

**Decision:** Two separate OpenClaw gateways — main at 18789, Nemoclaw at 18791.
**Why:** Hermes profiles (Kairos, Shannon) connect to the main gateway. Nemoclaw needed isolation for identity separation and independent operation.
**Config:** Main at `~/.openclaw/`, Nemoclaw at `~/.openclaw-nemo/`.

## 2026-06-06: Shared Skill Library at kestrel/shared-skills/

**Decision:** All shared compound knowledge lives in `kestrel/shared-skills/` and is wired into all agents via `skills.external_dirs`.
**Why:** Single source of truth for compound knowledge. Agents patch skills when they find them stale. Skills grow over time instead of rotting in profile-specific dirs.

## 2026-06-06: Compound Wiki at kestrel/wiki/

**Decision:** Compound knowledge base in wiki format.
**Why:** Skills define HOW to do things. Wiki captures WHAT was learned. Two different signal types with different update cadences. Wiki grows via agent contribution, skills improve via agent patching.
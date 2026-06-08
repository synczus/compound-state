# Cost Optimization Research — Perplexity Sonar Pro

## Key Findings

### 1. Model Tiering
- **Default tier**: DeepSeek V4 Flash (free) — already using ✅
- **Housekeeping tier**: Local Ollama (Llama 3.x 8B) for log summarization, compression, heartbeat recaps, simple classification — effectively free
- **Heavy reasoning tier**: Grok-3 via OpenRouter only when validation fails or `task.difficulty == "hard"`

### 2. Context Optimization
- **Sliding window**: 10-20 messages max per agent prompt, not full history
- **Structured state**: JSON key-value storage instead of verbose natural language for hop state, trading decisions, agent memory
- **Topic-filtered history**: When message is about BTC, only include past BTC-tagged messages
- **Hard token budgets**: Max 4-8K tokens per agent call, drop oldest first

### 3. Memory Banking
- Two-tier: short-term chat buffer + long-term memory bank
- Local Ollama compresses every 100 messages into bullet points
- At inference, only pull 3-5 relevant memory entries by tag

### 4. Cron Consolidation
- Batch similar crons (already done: pipeline replaces 3 individual timers)
- Reduce 5-min interval crons to 15-30 min where possible
- Event-driven > polling when feasible

### 5. OpenRouter Optimization
- Enable caching for repeated prompt patterns
- Route to cheapest provider per model
- Use batch processing where available
- Hard cap per-model invocation per day

### 6. Sub-Agent Discipline
- Keep prompts ≤500 tokens
- Pass structured context (JSON), not raw history
- Use DeepSeek Flash as default; escalate only on validation failure

### 7. Telegram API
- Webhooks > polling (already using webhooks)
- Dedup messages (group: ignore reactions, edits)
- Silent cron outputs: empty stdout = no message posted
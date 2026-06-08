# Agent Memory Research — Compound Memory Architecture

_Researched: 2026-06-08 | Sources: Perplexity Sonar Pro, Letta/MemGPT docs, Mem0 docs, context engineering guides, AgentMemory project_

---

## Section 1: Current State Assessment of Our Compound Memory Setup

### What We Have

The Kestrel compound (5 agents: Hermes, OpenClaw, Nemoclaw, Kairos, Shannon) currently operates on an **ad-hoc file-based memory architecture** with the following components:

| Component | Description | Strengths | Weaknesses |
|---|---|---|---|
| **Memory Bank** (`kestrel/memory-bank/`) | SQLite DB + SUMMARY.md + flat files | Centralized, 305 active entries, categorization system | No semantic search, no embeddings, no deduplication |
| **Daily Logs** (`kestrel/memory/YYYY-MM-DD.md`) | Raw daily notes per agent | Timestamped, human-readable | No cross-linking, no retrieval mechanism |
| **Cycle State** (`kestrel/cycle-state/current.json`) | JSON hop baton with verified facts | Structured, lightweight, resets each cycle | Limited to current hop, no historical depth |
| **HUB Intake** (`kestrel/HUB_INTAKE.md`) | Pipeline state + noise gate context | Good session startup context | Overwritten each cycle, no long-term retention |
| **MEMORY.md / SOUL.md** | Per-agent identity and curated memory | Long-term identity persistence | Per-agent only, no cross-agent sharing |
| **Agent Pulses** (`kestrel/agent-pulses/`) | Per-agent pulse reports | Timestamped, includes CTF results | Flat files, no indexing, no retrieval |
| **Votes** (`kestrel/votes/pending/`) | Open consensus mechanisms | Structured decisions | Vote-only, not general memory |

### Gap Analysis: What's Missing

1. **No vector/semantic search** — Agents rely on reading files directly, which means O(n) scan time for any recall operation. No embedding-based retrieval exists.
2. **No hierarchical memory tiers** — Everything is flat. There's no distinction between hot (in-context), warm (session-scoped), and cold (long-term) memory.
3. **No structured memory extraction** — Agents don't explicitly decide what to remember; everything is written or nothing is.
4. **No deduplication or consolidation** — The same fact may be stated in 5 different files by 5 different agents.
5. **No async background consolidation** — No "sleep-time" agent that refines memory when the compound is idle.
6. **No retrieval-awareness at session start** — Each agent reads the same files in full rather than retrieving only what's relevant to their current task.
7. **No memory decay policies** — Old propositions stay indefinitely, degrading signal-to-noise ratio.
8. **No cross-agent shared context without file reads** — No MCP/REST memory server that all agents query centrally.
9. **No importance scoring** — No mechanism to distinguish high-signal memories (architecture decisions, verified facts) from low-signal ones (status updates, transient observations).

---

## Section 2: Best Practices From Research

### 2.1 The Layered Memory Architecture (2025-2026 Consensus)

The entire field converges on a **three-to-four tier hierarchy** modeled after human memory and computer architecture:

```
┌─────────────────────────────────────────────────────┐
│  TIER 1: WORKING MEMORY (Hot / In-Context)          │
│  Last 10-20 turns verbatim. Source of truth for     │
│  immediate reasoning. Rolling window.               │
├─────────────────────────────────────────────────────┤
│  TIER 2: EPISODIC MEMORY (Warm / Session-Scoped)    │
│  Rolling summaries + extracted state from current   │
│  session. Updated incrementally when hot buffer     │
│  overflows. Keeps continuity across long tasks.     │
├─────────────────────────────────────────────────────┤
│  TIER 3: SEMANTIC MEMORY (Cold / Long-Term)         │
│  Distilled facts, preferences, decisions. Stored in │
│  vector DB + structured metadata. Retrieved via     │
│  semantic search on each step.                      │
├─────────────────────────────────────────────────────┤
│  TIER 4: PROCEDURAL MEMORY (Skills / Patterns)      │
│  Reusable plans, action patterns, workflows.        │
│  Learned from repeated episodes.                    │
└─────────────────────────────────────────────────────┘
```

### 2.2 The Four-Phase Memory Lifecycle

Research from Mem0, Letta, and Tian Pan's context engineering blog converges on this lifecycle:

1. **INJECT** — At session start, load a structured state object (YAML + markdown) into the system prompt. YAML for structured facts, markdown for narrative context. Combined outperforms either alone.

2. **DISTILL** — During the session, agents actively emit candidate memories via tool calls (e.g., `save_memory_note`). Memory quality is determined at **write time**, not read time. Explicit `scope: "session" | "global"` lets agents distinguish ephemeral from durable.

3. **TRIM** — When context overflows, be surgical: preserve the last N user turns, don't lose session notes. Use a flag that triggers automatic memory re-injection after trimming. Never let information disappear silently—anything pushed out of the hot buffer is first summarized and fact-extracted into Tier 2/3.

4. **CONSOLIDATE** — At session end (or asynchronously), run a secondary LLM call to merge session notes into global memory. Use recency as tiebreaker for conflicts. Strip ephemeral details. Run asynchronously—never block the user.

### 2.3 MemGPT/Letta: The Operating System Approach

MemGPT (now Letta) treats the LLM's context window as a **virtual memory system**:

- **Core Memory** — Small (2-4 KB) always-present block in the prompt: identity, goals, high-level summary. Agent self-edits it via tool calls. Organized into **blocks** (identity, preferences, policies, task_state).
- **Recall Memory** — Searchable conversation history (SQL). Paged into context on demand when the agent needs specific episodes.
- **Archival Memory** — Unbounded external store (vector DB + graph). Accessed via `archival_memory_search` and `archival_memory_insert` tool calls.
- **Self-Edited Memory** — The LLM itself decides what to remember, retrieve, and forget. This gives the agent autonomy but costs inference tokens per memory operation. The tradeoff: **predictability (passive extraction) vs intelligence (agentic self-editing)**.

Key innovation from Letta v1+: **Context Repositories** — agent context stored as local files in git repos. When agents modify context, they edit files, commit, and push. Enables natural multi-agent coordination via git merges/conflict resolution.

### 2.4 Sleep-Time Compute & Async Memory

Letta's "sleep-time compute" paradigm introduces:

- **Non-blocking operations** — Memory management handled asynchronously, not bundled into the conversation agent. Better response times AND better memory quality.
- **Proactive refinement** — During idle periods, memory is reorganized and improved. Not just lazy incremental updates.
- **Specialized memory agents** — A separate agent (or "subconscious") handles consolidation, deduplication, and conflict resolution in the background.

### 2.5 AgentMemory: Multi-Agent Shared Context

[AgentMemory](https://github.com/aiagentmemory/agentmemory) is a locally-run memory server that provides:

- **One server, shared across all agents** — Every agent reads/writes via MCP, REST, or hooks.
- **4-tier memory system** (working, episodic, semantic, procedural) with hybrid search (BM25 + vectors + knowledge graph + RRF fusion).
- **95.2% R@5 retrieval accuracy** on LongMemEval-S benchmarks.
- **~92% token reduction** vs full-history approaches (~170K tokens / $10 per year for typical workflows).
- **MCP protocol** — Any MCP-capable client plugs in directly. REST API for custom orchestrators.

### 2.6 Precedence Rules & Conflict Resolution

A layered memory system needs explicit precedence rules:

1. **Latest user instruction** — always wins
2. **Session-scoped notes** — override global defaults for this conversation
3. **Global long-term memory** — the baseline fallback

Document this hierarchy explicitly in every agent's system prompt. Without it, agents hedge between stored preferences and new instructions.

### 2.7 What Memory Should Capture vs. Not

| ✅ Good Candidates | ❌ Bad Candidates |
|---|---|
| Communication preferences (format, length, detail) | Session-specific emotional context ("seemed stressed") |
| Domain context (team structure, project names, constraints) | Speculative inferences ("probably prefers X") |
| Repeated patterns ("always wants cost before approval") | PII or secrets |
| Architecture decisions & verified facts | Ephemeral tool output details |
| Workflows & procedures learned over time | Raw conversation transcripts |

### 2.8 Context Budget Allocation

For a 128K token context window, the recommended allocation:

| Component | Allocation | Notes |
|---|---|---|
| System instructions | 5-10% | Identity, policies, tool definitions |
| Long-term facts + summaries | 10-20% | Retrieved from archival/semantic memory |
| Hot window (active turns) | 60-70% | Last 10-20 messages verbatim |
| Scaffolding + tool outputs | 10-15% | Compressed tool results |

### 2.9 Tool Output Compression

Always summarize large logs/tool outputs **before** they hit context. Store full outputs externally (object store, S3, or filesystem). Keep only distilled key results and IDs in memory. This single practice can reduce token consumption by 40-60%.

---

## Section 3: Concrete Recommendations for Our Compound

### 3.1 Architecture Recommendation

**Adopt a hybrid approach combining the best of AgentMemory, Letta-style tiered memory, and our existing file-based system.**

```
┌──────────────────────────────────────────────────────────┐
│                KESTREL MEMORY ARCHITECTURE                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  HOT LAYER (In-Context Window — per agent instance)      │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Agent identity block (SOUL.md distilled)       │   │
│  │ • Current hop context (cycle state)              │   │
│  │ • Last 10 turns verbatim                         │   │
│  │ • Tool output summaries (compressed)             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  WARM LAYER (Session File — per agent per session)       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Running session summary                        │   │
│  │ • Active goals & open threads                    │   │
│  │ • Recent decisions made this session             │   │
│  │ • Written to ~/kestrel/memory-bank/input/{agent}/  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  COLD LAYER (Long-Term — shared across all agents)      │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Vector DB (Chroma / LanceDB — local, no cloud) │   │
│  │ • Memory Bank SQLite (existing, augmented)       │   │
│  │ • AgentMemory MCP server (recommended new infra) │   │
│  │ • Knowledge graph for entity relationships      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ASYNC LAYER (Background — sleep-time agents)           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Consolidation agent (Hermes or dedicated)      │   │
│  │ • Nightly memory deduplication + pruning         │   │
│  │ • Summary regeneration for stale entries         │   │
│  │ • Knowledge graph updates                        │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Agent Startup Sequence (Revised)

Each agent's session startup should:

1. **Read SOUL.md** (identity — stays in core memory block)
2. **Read current.json** (hop baton — active context)
3. **Read HUB_INTAKE.md** (pipeline state overview)
4. **QUERY memory bank** with semantic search for: relevant past decisions, user preferences, active project context (instead of reading flat files)
5. **Load session notes** from `memory-bank/input/{agent_name}/` if resuming
6. **Assemble context**: identity block → relevant long-term memories → session summary → recent messages → current query

### 3.3 Memory Write Protocol

Every agent should expose or use three memory tools:

```python
# Proposed tool interface for all Kestrel agents

save_memory_note(
    note: str,           # "Alex prefers bullet-list summaries, not prose"
    scope: "session" | "global",  # session = ephemeral, global = durable
    category: str,       # "user-preference" | "arch-decision" | "workflow"
    importance: 1-5      # 5 = critical fact, 1 = nice to know
)

search_memories(
    query: str,          # "What did we decide about the striker watchdog?"
    top_k: int = 5,
    filters: dict = {}   # {"category": "arch-decision", "agent": "kairos"}
)

consolidate_session()    # Triggers background consolidation of current session notes
```

### 3.4 Key Design Decisions

**Decision 1: Self-hosted vector DB** — Use Chroma or LanceDB locally. No cloud dependencies. Memory stays on machine. Chroma can run as a subprocess with no external infra needed.

**Decision 2: AgentMemory as shared MCP server** — Deploy AgentMemory on localhost as a systemd service. All 5 agents connect via MCP. This gives us shared, searchable, hybrid-retrieval memory out of the box.

**Decision 3: Dual write** — Agents write to both the structured memory server (for semantic search) AND the existing file-based memory bank (for backward compatibility and human readability). Eventually sunset file-based.

**Decision 4: Sleep-time consolidation via Hermes** — Hermes (as the strategist) runs a nightly consolidation pass on memory. No blocking. Uses a cheap model for deduplication and summary refinement.

**Decision 5: Importance-weighted retrieval** — When retrieving memories, weight by importance score + recency. High-importance older facts can outrank low-importance recent ones.

**Decision 6: Explicit precedence in prompts** — Every agent's system prompt includes: "When current instruction contradicts stored memory, follow the current instruction and update session notes."

### 3.5 Memory Categories for Our Compound

Based on the 305 existing entries in the memory bank:

| Category | Current Count | Recommended Storage |
|---|---|---|
| pipeline-infrastructure | 75 | Vector DB + structured |
| agent-orchestration | 39 | Vector DB + structured |
| monitoring-observability | 30 | Vector DB (retention: 30 days) |
| cost-optimization | 15 | Vector DB + structured |
| security-governance | 10 | Vector DB (importance-weighted) |
| architecture-decision | 8 | Knowledge graph + vector DB |
| knowledge-management | 6 | Vector DB |
| model-strategy | 4 | Vector DB |
| other | 118 | **Flag for review** — high noise ratio |

---

## Section 4: Implementation Steps Ordered by Impact

### Phase 1: Quick Wins (Week 1) — High Impact, Low Effort

| Step | Description | Effort | Impact |
|---|---|---|---|
| **1.1** | **Install AgentMemory** as local MCP server. `npx agentmemory` or Docker. Point all 5 agents at it. | 2h | 🔴 **Critical** — Shared memory infrastructure |
| **1.2** | **Add memory write/read tools** to each agent's tool config. Three tools: `save_memory_note`, `search_memories`, `consolidate_session`. | 4h | 🔴 **Critical** — Agents can now persist/recall |
| **1.3** | **Add session startup memory injection** — On each new session, agents query AgentMemory for relevant context before first message. | 2h | 🟠 High — Reduces cold-start problem |
| **1.4** | **Prune "other" category** — Review the 118 uncategorized entries. Promote high-signal, purge noise. | 1h | 🟠 High — Improves signal-to-noise ratio |

### Phase 2: Structured Memory (Week 2) — Solid Foundation

| Step | Description | Effort | Impact |
|---|---|---|---|
| **2.1** | **Deploy Chroma/LanceDB** for local vector storage. Embed all current memory bank entries. | 3h | 🔴 **Critical** — Semantic search capability |
| **2.2** | **Build memory consolidation pipeline** — Hermes runs nightly: deduplicate, resolve conflicts by recency, prune stale entries, regenerate summaries. | 6h | 🔴 **Critical** — Prevents memory rot |
| **2.3** | **Implement importance scoring** — Retroactively score existing memories + score every new write. Filter low-importance from retrieval by default. | 3h | 🟠 High — Better retrieval quality |
| **2.4** | **Add structured YAML frontmatter** to all new memory writes: agent, category, importance, timestamp, scope. | 1h | 🟠 High — Enables precise filtering |

### Phase 3: Advanced Retrieval (Week 3-4) — Maximum Retention

| Step | Description | Effort | Impact |
|---|---|---|---|
| **3.1** | **Implement hierarchical memory** — Hot buffer (last 10 turns), warm layer (session summary), cold layer (long-term vector store). Add incremental summarization when hot buffer overflows. | 8h | 🔴 **Critical** — Enables unlimited context |
| **3.2** | **Build session-scoped memory** — Each agent writes a `session-summary.md` that gets injected into warm memory. Resumed sessions pick up where they left off. | 4h | 🟠 High — Session continuity |
| **3.3** | **Add tool output compression** — Summarize all tool/large outputs before they hit context. Store full output in `memory-bank/archive/`. | 4h | 🟡 Medium — Token savings |
| **3.4** | **Implement memory decay** — Entries older than N days with no re-access get importance score reduced. Eventually archived or purged. | 3h | 🟡 Medium — Prevents accumulation |

### Phase 4: Multi-Agent Coordination (Week 4-5) — Compound Intelligence

| Step | Description | Effort | Impact |
|---|---|---|---|
| **4.1** | **Sleep-time memory agent** — Dedicated agent (Hermes or new) that runs on a cron during compound idle time: re-embeds, re-summarizes, resolves cross-agent contradictions. | 8h | 🔴 **Critical** — Background memory quality |
| **4.2** | **Cross-agent memory awareness** — When Agent A updates a fact that Agent B also references, notify Agent B at next session start. | 4h | 🟠 High — Reduces contradictory memory |
| **4.3** | **Knowledge graph for entity relationships** — Track connections between projects, decisions, agents, and constraints. Enables multi-hop reasoning. | 8h | 🟡 Medium — Research-backed but complex |
| **4.4** | **Memory audit dashboard** — Grafana panel showing: memory count by category, retrieval hit rates, importance distribution, stale entry count. | 6h | 🟡 Medium — Observability |

### Phase 5: Continuous Improvement (Ongoing)

| Step | Description | Cadence |
|---|---|---|
| **5.1** | Track retrieval quality — manual spot-check of top-K results | Weekly |
| **5.2** | Tune importance thresholds and decay rates based on usage | Biweekly |
| **5.3** | Add new memory categories as compound evolves | As needed |
| **5.4** | Incorporate new research (EVOLVE-MEM, adaptive memory clustering) | Monthly review |

---

## Appendix A: Tooling Recommendations

| Tool | Purpose | License | Stack |
|---|---|---|---|
| **[AgentMemory](https://github.com/aiagentmemory/agentmemory)** | Shared MCP memory server for all agents | Apache 2.0 | Node/TS, SQLite, iii engine |
| **[Chroma](https://www.trychroma.com/)** | Local vector database | Apache 2.0 | Python, in-process or server |
| **[LanceDB](https://lancedb.github.io/lancedb/)** | Alternative vector DB (no server needed) | Apache 2.0 | Rust, embedded |
| **[Mem0](https://mem0.ai/)** | Memory layer SDK (passive extraction style) | Apache 2.0 | Python, JS |
| **Letta** | Full agent runtime (if we want to migrate) | Apache 2.0 | Python |

**Recommendation**: Start with **AgentMemory** (shared MCP server, zero infra) + **Chroma** (local vector DB for custom retrievals). Evaluate Letta as a potential migration target if the compound grows beyond file-based orchestration.

## Appendix B: Key Sources

- [Letta Blog: Agent Memory](https://www.letta.com/blog/agent-memory) — Three-tier memory architecture
- [Tian Pan: Context Engineering for Long-Term Memory](https://tianpan.co/blog/2025-09-19-context-engineering-long-term-memory-ai-agents) — Four-phase lifecycle
- [Vectorize.io: Mem0 vs Letta (2026)](https://vectorize.io/articles/mem0-vs-letta) — Comparison of approaches
- [Mem0: Context Engineering Guide](https://mem0.ai/blog/context-engineering-ai-agents-guide) — Complete guide to context management
- [AgentMemory Project](https://github.com/aiagentmemory/agentmemory) — Persistent memory server
- [Agent Market Cap: Context Engineering with Sliding Windows](https://agentmarketcap.ai/blog/2026/04/11/agent-context-engineering-sliding-windows-memory-2026) — Hierarchical summarization patterns
- [AWS: Building Smarter AI Agents with AgentCore](https://aws.amazon.com/blogs/machine-learning/building-smarter-ai-agents-agentcore-long-term-memory-deep-dive/) — Production memory patterns
- [Letta: Memory Blocks](https://www.letta.com/blog/memory-blocks) — Structured in-context memory blocks
- [Letta v1 Agent](https://www.letta.com/blog/letta-v1-agent) — Updated agent loop and memory APIs
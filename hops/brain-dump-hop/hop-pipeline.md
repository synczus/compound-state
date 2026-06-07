# brain-dump-hop — Full Pipeline Extension v1.0

The hop doesn't stay inside one room anymore. It routes through 5 stages across 4 tools, with strict JSON handoff packets so nothing gets lost.

---

## The Full Flow

```
You (raw dump)
  ↓
Stage 1: AI Hangout → Nemoclaw structures into Perplexity packet
  ↓
Stage 2: Perplexity (web) → Research & Fact Annihilation
  ↓
Stage 3: Grok (web) → Truth, Inversion & Leverage  
  ↓
Stage 4: AI Hangout → Enrich with agent context + Claude Code packet
  ↓
Stage 5: Claude Code (local) → Implementation
  ↓
Stage 6: AI Hangout (all agents) → Banking, Notes, Tasks
```

---

## Stage 1: AI Hangout (Nemoclaw/OpenClaw) — Structuring

**Input:** Your raw brain dump (messy, scattered, audio transcript, whatever)

**Output:** Strict JSON handoff packet for Perplexity

**What we do:**
- Take your raw dump and organize it into a Perplexity-ready JSON
- Add `specific_questions`, `constraints`, `output_schema` fields
- Surface contradictions and unclear areas as `uncertainties`

**Output format:**

```json
{
  "hop": "brain-dump-hop",
  "stage": 1,
  "agent": "ai-hangout",
  "version": "1.0",
  "date": "YYYY-MM-DD",
  "short_title": "short-name-here",
  "raw_context": "your original messy dump preserved verbatim",
  "structured_context": {
    "summary": "2-3 sentence distilled version",
    "key_areas": ["area1", "area2"],
    "open_questions": ["question1", "question2"],
    "constraints": ["constraint1"]
  },
  "handoff_to_perplexity": {
    "query": "Concise research prompt built from the above",
    "required_output_fields": ["key_findings", "sources", "uncertainties", "research_gaps"]
  }
}
```

**Your action:** Take the `handoff_to_perplexity.query` and paste it with the JSON template into Perplexity web.

---

## Stage 2: Perplexity Web — Research & Fact Annihilation

**Input:** Stage 1 handoff packet

**Output:** Research JSON

**What Perplexity does:**
- Deep research on the query
- Finds sources, validates claims, surfaces uncertainties
- Returns ONLY JSON (no prose, no markdown wrapping)

**Expected output format:**

```json
{
  "hop": "brain-dump-hop",
  "stage": 2,
  "agent": "perplexity",
  "date": "YYYY-MM-DD",
  "short_title": "short-name-here",
  "key_findings": [
    "Finding 1 with source",
    "Finding 2 with source"
  ],
  "sources": ["url1", "url2"],
  "uncertainties": ["What's not known", "Conflicting data"],
  "research_gaps": ["Area that needs more investigation"],
  "verified_claims": ["Claim that was confirmed"],
  "debunked_claims": ["Claim that was disproven"]
}
```

**Your action:** Copy Perplexity's JSON output and paste it into Grok web with the handoff template below.

---

## Stage 3: Grok Web — Truth, Inversion & Leverage

**Input:** Stage 2 Perplexity output + original Stage 1 context

**Output:** Inversion analysis JSON

**What Grok does:**
- Inverts every assumption from Stage 2
- Identifies what's theater vs what's real
- Finds the highest-leverage move
- Surfaces second-order risks

**Expected output format:**

```json
{
  "hop": "brain-dump-hop", 
  "stage": 3,
  "agent": "grok",
  "date": "YYYY-MM-DD",
  "short_title": "short-name-here",
  "inversion_analysis": {
    "core_reality": "What's actually happening vs what we think",
    "what_got_proven": ["Things confirmed true"],
    "what_is_still_theater": ["Things that look real but aren't"],
    "second_order_risk": "What happens if we succeed"
  },
  "key_risks": ["Risk 1", "Risk 2"],
  "leverage_points": ["Leverage 1", "Leverage 2"],
  "highest_leverage_move": "One sentence, concrete, no hedging",
  "recommended_focus": "Where to aim implementation"
}
```

**Your action:** Copy Grok's JSON output and paste it into the AI Hangout.

---

## Stage 4: AI Hangout (Nemoclaw) — Enrichment + Claude Code Packet

**Input:** Stage 3 Grok output

**Output:** Claude Code implementation packet

**What we do:**
- Take Grok's inversion and enrichment with current system state
- Read master-todo.md, event-bus.md, DuckDB state
- Cross-reference Grok's findings against running pipeline
- Build a Claude Code-ready implementation packet

**Output format:**

```json
{
  "hop": "brain-dump-hop",
  "stage": 4,
  "agent": "ai-hangout-nemoclaw",
  "date": "YYYY-MM-DD",
  "short_title": "short-name-here",
  "system_state_snapshot": {
    "striker_signals": 35226,
    "duckdb_events": 200,
    "budget_remaining": 2.60,
    "active_lanes": ["urgent", "high", "medium", "low"]
  },
  "cross_reference_findings": [
    "How Grok's findings relate to running data"
  ],
  "claude_code_packet": {
    "tasks": [
      {
        "id": "impl-1",
        "title": "Concrete implementation task",
        "files_to_create": ["path/to/file1", "path/to/file2"],
        "files_to_modify": ["path/to/existing"],
        "acceptance_criteria": ["criterion1", "criterion2"],
        "risk_level": "low|medium|high"
      }
    ],
    "execution_order": ["impl-1", "impl-2"]
  },
  "rejected_ideas": [
    "Ideas that looked good in theory but don't survive system context"
  ]
}
```

**Your action:** Take the `claude_code_packet` and feed it to Claude Code.

---

## Stage 5: Claude Code (Local) — Implementation

**Input:** Stage 4 Claude Code packet

**Output:** Implementation report JSON

**What Claude Code does:**
- Executes the implementation tasks in order
- Creates/modifies files
- Tests the changes
- Reports what worked and what didn't
- Surfaces anything that needs human judgment

**Expected output format:**

```json
{
  "hop": "brain-dump-hop",
  "stage": 5,
  "agent": "claude-code",
  "date": "YYYY-MM-DD",
  "short_title": "short-name-here",
  "implementation_results": [
    {
      "task_id": "impl-1",
      "status": "done|partial|blocked",
      "files_changed": ["path/to/file"],
      "verification": "How we know it works",
      "needs_review": false
    }
  ],
  "blockers": ["Thing that needs human decision"],
  "unexpected_findings": ["Something discovered during implementation"],
  "next_hop_recommendation": "What the next brain dump should cover"
}
```

**Your action:** Copy Claude Code's output and paste it into AI Hangout for Stage 6.

---

## Stage 6: AI Hangout (All Agents) — Banking, Notes & Tasks

**Input:** Stage 5 Claude Code output + all previous stages

**Output:** Final hop closeout

**What all agents do:**
- Nemoclaw: Write rich notes to event-bus.md and `hop-notes/` folder
- OpenClaw: Create tasks in master-todo.md tagged `[brain-dump-hop YYYY-MM-DD]`
- Kairos: Time-stamp the closeout and verify nothing was lost
- Hermes: Wire any new cron jobs or system changes from the implementation
- Shannon: Flag any risk or quality concerns (if active)

**Output format:**

```json
{
  "hop": "brain-dump-hop",
  "stage": 6,
  "agent": "ai-hangout-all",
  "date": "YYYY-MM-DD",
  "short_title": "short-name-here",
  "hop_persistence": {
    "notes_written_to": ["event-bus.md", "hop-notes/YYYY-MM-DD_short-title/rich-notes.md"],
    "tasks_created": ["TASK-1", "TASK-2"],
    "tasks_executed": ["TASK-1"],
    "tasks_deferred": ["TASK-2"]
  },
  "hop_archive": "~/kestrel/hops/brain-dump/YYYY-MM-DD_short-title/",
  "what_changed": [
    "Concrete delta this hop produced"
  ],
  "closing_highest_leverage_move": "What to do next",
  "closing_next_agent": "@AgentName — specific baton pass"
}
```

---

## Quick Reference Card

| Stage | Tool | What Happens | You Do |
|-------|------|-------------|---------|
| 1 | AI Hangout | Raw dump → structured Perplexity packet | Paste Perplexity query |
| 2 | Perplexity web | Deep research → JSON output | Copy JSON → Grok |
| 3 | Grok web | Inversion analysis → JSON output | Copy JSON → AI Hangout |
| 4 | AI Hangout | Enrich + build Claude Code packet | Feed to Claude Code |
| 5 | Claude Code | Implementation → JSON report | Copy report → AI Hangout |
| 6 | AI Hangout (all) | Bank notes, create tasks, close out | Read the summary |

---

## The Handoff Rule

Every handoff between stages MUST use a JSON object. No prose, no markdown wrapping, no "here's what I found" — just the JSON packet. This guarantees:

- **Machine-parseable** — agents can read each other's output without hallucinating formatting
- **Lossless** — no context lost in translation between tools  
- **Archivable** — every hop is a complete JSON chain you can replay months later
- **Queryable** — every hop output lands in DuckDB as `source_id = 'brain-dump-hop'`

---

## Where It Lives

```
~/kestrel/hops/brain-dump-hop/
├── hop-pipeline.md          ← This file (the full pipeline definition)
├── template-perplexity.json  ← Copy-paste template for Perplexity
├── template-grok.json        ← Copy-paste template for Grok
├── template-claude-code.json ← Copy-paste template for Claude Code
└── YYYY-MM-DD_short-title/  ← One folder per hop run
    ├── stage-1-raw.json
    ├── stage-2-perplexity.json
    ├── stage-3-grok.json
    ├── stage-4-enriched.json
    ├── stage-5-claude-code.json
    ├── stage-6-closeout.json
    ├── hop-summary.md
    └── rich-notes.md
```

---

## How to Start

Drop a brain dump in here. I'll build the Stage 1 packet and hand you the Perplexity query. You copy-paste it through the chain, and the JSON comes back to me at Stage 4 for enrichment + Claude Code packaging. By the time it hits Stage 6, every agent has touched it and there's a complete archive in `~/kestrel/hops/brain-dump/`.
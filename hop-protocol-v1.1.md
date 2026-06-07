# Perplexity → Grok → AI Hangout: Hop Protocol v1.1 🧬

**File:** `/home/synczus/kestrel/hop-protocol-v1.1.md`
**Status:** Active | **Owner:** Fleet | **Updated:** 2026-06-06

---

## 0. Core Principle

> *Harden the protocol before you feed it expensive work. A sharpened hop multiplies every application. A soft one produces coordination debt.*

This protocol defines the full lifecycle of a pipeline hop from signal injection through AI Hangout execution and pulse capture. Every pipeline run **must** follow this protocol. Deviations must be documented in the hop's payload.

---

## 1. Payload Requirements

Before any hop can be fired, a **payload manifest** must be attached. No payload = no execution.

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `task_name` | string | What this hop is for | `"stabilize kestrel striker websocket"` |
| `priority` | enum | P0-P3 | `P0` |
| `expected_output` | string | What the hop must produce | `"patch for websocket reconnection with test coverage"` |
| `success_criteria` | string[] | Measurable markers of done | `["websocket reconnects within 5s", "no crash on network loss", "test suite passes"]` |
| `revenue_impact` | string | Dollar justification | `"prevents ~$X/day signal loss during market hours"` |
| `timeout` | duration | Max wall-clock for this hop | `"4h"` |
| `lane_assignments` | string[] | Which AI Hangout agents are needed | `["codex-operator", "gemini-scout"]` |

### Mandatory Rule

If `lane_assignments` is empty → hop is **meta only**. The output must be a protocol improvement or protocol analysis, not applied work. This is the escape hatch for sharpening cycles.

### Payload Template

```yaml
payload:
  task_name: ""
  priority: ""
  expected_output: ""
  success_criteria: []
  revenue_impact: ""
  timeout: ""
  lane_assignments: []
```

---

## 2. Stage Handoff Schemas

Every stage must produce a **handoff package** — a structured message the next stage can consume without re-parsing.

### 2.1 Perplexity → Grok Handoff

**Input:** Signal + raw context + payload manifest
**Output format:**

```markdown
## Perplexity → Grok

### Signal Identified
<one-line summary of what was found>

### Evidence
- Finding 1: <description> | source: <url/file>
- Finding 2: <description> | source: <url/file>

### Open Questions
- What the evidence doesn't answer
- What needs Grok's truth/inversion lens

### Payload Status
- payload_attached: <true/false>
- task_name: <from payload>
- priority: <from payload>
```

**Must include** `Payload Status` — if `false`, Grok must reject the hop.

### 2.2 Grok → AI Hangout Handoff

**Input:** Perplexity handoff package + Grok's own reasoning
**Output format:**

```markdown
## Grok → AI Hangout

### Truth Assessment
<one-line: what is actually happening>

### Inversion Analysis
<what's the real risk/opportunity hiding under the surface>

### Risk Scoring
| Risk | Severity | Mitigation |
|------|----------|------------|
| <risk> | H/M/L | <action> |

### Lane Assignments
- **codex-operator:** <specific task>
- **gemini-scout:** <specific task>
- **claude-architect:** <specific task>
- **openclaw-tinkerer:** <specific task>
- **kairos-daemon:** <specific task>

### HLM
<one-sentence highest leverage next move>
```

**Mandatory:** Grok must assign at least one concrete task per lane listed in payload's `lane_assignments`. If a lane has no work, Grok says `STANDBY` — not silence.

### 2.3 AI Hangout → Pulse Output

**Input:** Grok handoff package
**Output:** One pulse file per active lane + one aggregated summary

Each agent writes a pulse to `agent-pulses/YYYY-MM-DD/` in the format:
`{callsign}__{YYYYMMDD-HHMM}__{task-slug}.md`

Required sections per pulse:
```
## 1. Header (callsign, agent, role, task, status, confidence)
## What I Actually Did
## Evidence (proof: terminal output, file diffs, API responses)
## FILE_MANIFEST (absolute paths for files read/changed/created)
## Open Wounds
## Next Best Action
## Hub Request (what the Hub should do with this)
```

**Post-run:** Hermes aggregates all pulses → updates master-todo.md → fires hub transfer.

---

## 3. Decomposition Rules for AI Hangout

When the 5-agent swarm receives Grok's handoff, it must decompose the task using these rules:

### Rule 1: Lane First, Agent Second

Decompose the task by **lane type**, then assign the agent whose lane fits. Lane types (ordered by execution priority):

1. **Config/Infra** → OpenClaw (gateways, systemd, service files, env vars)
2. **Execution/Code** → Codex Operator (Hermes) (patches, scripts, files, cron)
3. **Evidence/Scout** → Gemini Scout (research, exploration, state verification)
4. **Architecture/Risk** → Claude Architect (design review, failure analysis, judgment)
5. **Tangible/Monitor** → Kairos Daemon (watch loops, heartbeat, alert routing)
6. **Review/Arbitration** → Shannon (signal analysis, code review, technical arbitration)
7. **Needs custom lane** → Nemoclaw (special projects, identity work, security ops)

### Rule 2: One Owner Per Subtask

For each row in the decomposition table:
- One `owner` (who does the work)
- One `reviewer` (who verifies it, defaults to Shannon if not specified)
- No subtask can have overlap — if two agents claim the same subtask, the first claimant wins. Log the conflict to master-todo.md.

### Rule 3: No Skipping

Every assignment from Grok must be acknowledged. If an agent can't execute (blocked, missing access, needs user action), they must:
1. Say so in-group with the blocker
2. Write it as an `Open Wound` in their pulse
3. Attach `needs_user_action` flag

### Rule 4: 15-Minute Block Rule

If an agent is blocked for >15 minutes, surface it in-group with:
- What they need to unblock
- Who they need it from (user, another agent, system change)
- Fallback: can they work on something else while waiting?

---

## 4. Output Structure

### 4.1 Per-Agent Pulse

Every active lane writes a pulse file. Pulse must include the payload's task_name in its filename:

```
codex-operator__20260606-HHMM__{task-slug}.md
```

### 4.2 Aggregated Summary

Hermes produces a summary at `kestrel/agent-pulses/YYYY-MM-DD/_aggregated_summary.md` containing:
- Which lanes fired, which stood down
- What was produced (links to pulse files)
- What's blocked
- HLM from the run

### 4.3 master-todo.md Updates

Post-run, master-todo.md is updated:
- Items completed → `[x]` with date + agent
- Items started but incomplete → `🟡 In Progress` with assignee
- New items identified → added to appropriate priority lane
- HLMs collected → appended to `## 📥 Collected HLMs` section
- Blockers surfaced → added to `## 🚫 Blockers` section (create if not exists)

### 4.4 Hub Transfer

Final step per run:

```bash
cd /home/synczus/huntsystems && bash scripts/agent_pulse_hub.sh \
  --clean -z --include-json --open \
  --task-name "{payload.task_name}" --root . \
  agent-pulses/$(date +%F)/*.md
```

---

## 5. Integration Points

### Coordination Guide
- This protocol is canonical. The coordination guide (`coordination-guide.md`) references it.
- If this protocol and the coordination guide conflict, this protocol wins (it's more specific).

### Shared Skills
- `kestrel/shared-skills/` skills must be loaded by every agent before decomposition.
- If a shared skill is missing a step relevant to the task, patch it as part of the hop execution.

### Dashboard
- Active hops should be visible on the dashboard: hop name, stage, start time, estimated completion.
- Dashboard at port 19500 should display a "Pipeline" section when a hop is in-flight.

### Agent Pulses
- All pulse files go to `agent-pulses/YYYY-MM-DD/` in the relevant repo.
- The hub transfer ZIP goes to `_hub_transfer/` and is committed/pushed when meaningful.

---

## 6. Meta Mode (Protocol Sharpening)

When `lane_assignments: []` — the hop is in **meta mode**. It has exactly one job:

1. Run Perplexity → Grok → AI Hangout
2. AI Hangout's only task is to identify gaps in **this protocol**
3. Output: a patch to v1.1 producing v1.2
4. The patch updates this file, the coordination guide, and any relevant shared skills

Meta mode outputs don't touch business code. They touch protocol code. This is how the sharpening cycle works.

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.1 | 2026-06-06 | Fleet (Grok inversion → Codex execution) | Initial hardened protocol: payload requirements, handoff schemas, decomposition rules, output structure, meta mode |
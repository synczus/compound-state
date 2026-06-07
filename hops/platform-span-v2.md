# Platform-Spanning Hop — v2

> Chain: AI Hangout → Claude Code → Perplexity Web → Grok Web → AI Hangout
> One baton file moves between platforms. Each station reads everything above, writes only its own stage.

---

## The Baton

Copy this into the AI Hangout to start a hop. Fill `stage_1_hangout`, then route through each station in order.

```json
{
  "hop": "platform-span-v2",
  "date": "2026-06-07",
  "title": "[short title]",
  "stage_1_hangout": {
    "agent_outputs": {},
    "raw_thoughts": "[your dump here]",
    "context": {},
    "questions": []
  },
  "stage_2_claude_code": {
    "build_output": "",
    "files_written": [],
    "open_questions": ""
  },
  "stage_3_perplexity": {
    "research_findings": [],
    "sources": [],
    "gaps_found": [],
    "corrections": []
  },
  "stage_4_grok": {
    "inversion": "",
    "key_risks": [],
    "assumptions_to_verify": [],
    "leverage": ""
  },
  "stage_5_banking": {
    "tasks_created": [],
    "notes_archived": "",
    "executed": []
  }
}
```

---

## Station Rules

### 1. AI Hangout — Intake & Seed
**What happens:** You dump raw thoughts. All agents read, assemble context, fill the baton with questions and knowns.

**Output:**
- Baton `stage_1_hangout` filled: `agent_outputs`, `raw_thoughts`, `context`, `questions`
- Hop logged to `kestrel/hops/YYYY-MM-DD_title/`

**Format:** Paste the baton JSON into Claude Code with `stage_1` filled and instructions: "Read stage_1, write stage_2."

---

### 2. Claude Code — Build & Generate
**What happens:** Takes the seeded context and produces first concrete output — code skeletons, configs, schema drafts, implementation sketches. Terminal-native, so this is where things get written to disk.

**Input:** Baton with `stage_1_hangout` filled
**Output:** Baton `stage_2_claude_code` filled — `build_output`, `files_written`, `open_questions`
**Pass-forward instruction:** "Copy this JSON to Perplexity Web. Tell it: review stage_2 output, research whether this approach is sound, fill stage_3."

---

### 3. Perplexity Web — Deep Research
**What happens:** Takes the build output and stress-tests it against the internet. Finds counterexamples, better approaches, gaps Claude Code missed. Perplexity's strength is breadth — it catches what the builders didn't know was wrong.

**Input:** Baton with `stage_1` and `stage_2` filled
**Output:** Baton `stage_3_perplexity` filled — `research_findings`, `sources`, `gaps_found`, `corrections`
**Pass-forward instruction:** "Copy this JSON to Grok Web. Tell it: stage_3 found these gaps — invert the plan, find the single assumption that would collapse everything. Fill stage_4."

---

### 4. Grok Web — Inversion & Critique
**What happens:** Takes the research-backed proposal and inverts it. Where does this break? What second-order effect gets ignored? What one assumption, if wrong, kills the whole thing? Grok finds the two or three things that *must be true* for the plan to work.

**Input:** Baton with `stage_1`, `stage_2`, `stage_3` filled
**Output:** Baton `stage_4_grok` filled — `inversion`, `key_risks`, `assumptions_to_verify`, `leverage`
**Pass-forward instruction:** "Copy this JSON back to the AI Hangout. Tell the agents: full baton is loaded — bank it."

---

### 5. AI Hangout — Banking & Execution
**What happens:** All agents read the complete baton (4 stages). Tasks created in master-todo.md. Rich notes written. Small clear items executed immediately.

**Input:** Baton fully loaded
**Output:**
- `stage_5_banking` filled: `tasks_created`, `notes_archived`, `executed`
- Notes written to `event-bus.md` (short) and `kestrel/hops/YYYY-MM-DD_title/rich-notes.md` (long)
- Tasks added to `master-todo.md` tagged `[platform-hop YYYY-MM-DD]`
- Small executed items checked off

---

## Storage

Every completed hop gets archived:
```
kestrel/hops/YYYY-MM-DD_short-title/
├── baton.json        # the full 5-stage JSON
├── stage-1-intake.md
├── stage-2-build.md
├── stage-3-research.md
├── stage-4-inversion.md
└── rich-notes.md     # AI Hangout banking notes
```

---

## When to Run This

Any time you want:
1. A problem built → researched → inverted → banked in one chain
2. Cross-platform sanity checking (build on Claude Code, verify on Perplexity, stress-test on Grok)
3. A structured output you can reference weeks later

Don't run this for quick tasks. Run it when the question is worth 4 stations.
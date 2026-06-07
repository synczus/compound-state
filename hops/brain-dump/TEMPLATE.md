# brain-dump-hop — Simplified v1.2
## Pipeline: You dump → I give JSON → Perplexity → Paste back → I bank

```
┌─────────────────────────────────────────────────┐
│  STEP 1: You dump raw thoughts here              │
│  I read them, hand you JSON for Perplexity       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  STEP 2: Paste my JSON into Perplexity           │
│  Perplexity returns strict JSON back             │
│  Copy the JSON, paste it back here               │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  STEP 3: I bank it                               │
│  Rich notes in hop-notes/ + event-bus.md         │
│  Tasks in master-todo.md tagged [brain-dump-hop] │
│  Execute anything safe + small                   │
│  Post summary in the chat                        │
└─────────────────────────────────────────────────┘
```

### Template — Paste into Perplexity

```
{
  "hop": "brain-dump-hop",
  "version": "1.2",
  "date": "YYYY-MM-DD",
  "short_title": "[short name]",
  "context": "[your raw thoughts]",
  "instructions": "You must respond with ONLY valid JSON. No markdown. No explanations. Research deeply. Return schema: { stage, hop_title, date, context_preserved, key_findings:[], sources:[], uncertainties:[], research_gaps:[] }"
}
```

### To start a hop
Just dump whatever's in your head here and I'll hand you the JSON.
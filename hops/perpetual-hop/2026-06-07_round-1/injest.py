#!/usr/bin/env python3
import json, sys, os

perplexity = json.load(sys.stdin)

# Ensure dirs exist
os.makedirs(os.path.dirname(__file__), exist_ok=True)

# Save raw Perplexity output
with open(os.path.join(os.path.dirname(__file__), 'perplexity-output.json'), 'w') as f:
    json.dump(perplexity, f, indent=2)

# Build summary for DuckDB
top = perplexity.get('top_recommendations', [])
top_names = ', '.join(f"{t['name']} ({t.get('confidence_score',0)})" for t in top[:3])

summary = {
    'source_id': 'perpetual-hop',
    'event_type': 'signal_source_scouting',
    'timestamp': '2026-06-07T22:52:00Z',
    'lane': 'high_signal',
    'action': 'research',
    'confidence': 0.86,
    'headline': f'Perpetual hop round 1 - Top sources: {top_names}',
    'hops': 1
}

with open(os.path.join(os.path.dirname(__file__), 'summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))

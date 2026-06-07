#!/usr/bin/env bash
# hop-controller.sh — read and advance the autonomous hop state
set -euo pipefail

HOP_FILE="/home/synczus/kestrel/cycle-state/hop-sequence.json"

die() { echo "ERROR: $*" >&2; exit 1; }

cmd_read() {
  cat "$HOP_FILE"
}

cmd_is_active() {
  python3 -c "
import json
d = json.load(open('$HOP_FILE'))
exit(0 if d.get('active') else 1)
"
}

cmd_is_my_turn() {
  local agent="${1:-}"
  [ -z "$agent" ] && die "is-my-turn needs agent name"
  python3 -c "
import json, sys
d = json.load(open('$HOP_FILE'))
agents = d.get('chain', [])
step = d.get('current_step', 0)
if not d.get('active', False): sys.exit(1)
if step >= len(agents): sys.exit(1)
if agents[step] == '$agent' and not d.get('${agent}_done', False): sys.exit(0)
sys.exit(1)
"
}

cmd_is_idle() {
  python3 -c "
import json, sys
d = json.load(open('$HOP_FILE'))
if d.get('complete') and d.get('auto'): sys.exit(0)
sys.exit(1)
"
}

cmd_advance() {
  local agent="${1:-}" msg="${2:-}"
  [ -z "$agent" ] && die "advance needs agent name"
  local ts
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  python3 <<PYEOF
import json
d = json.load(open('$HOP_FILE'))
d['${agent}_done'] = True
d['${agent}_message'] = '''${msg}'''
d['current_step'] = d.get('current_step', 0) + 1
agents = d.get('chain', [])
if d['current_step'] >= len(agents):
    d['complete'] = True
d['last_updated'] = '$ts'
with open('$HOP_FILE', 'w') as f:
    json.dump(d, f, indent=2)
step = d.get('current_step')
print('Advanced %s, step now %d' % ('$agent', step))
PYEOF
}

cmd_start() {
  local query="${1:-}" by="${2:-kairos}"
  [ -z "$query" ] && die "start needs query string"
  local ts
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  python3 <<PYEOF
import json
d = {
    'active': True,
    'chain': ['kairos', 'grok', 'openclaw'],
    'current_step': 0,
    'query': '''${query}''',
    'requested_by': '${by}',
    'kairos_done': False,
    'grok_done': False,
    'openclaw_done': False,
    'complete': False,
    'auto': True,
    'idle_since': '$ts',
    'kairos_message': '',
    'grok_message': '',
    'openclaw_message': '',
    'last_updated': '$ts'
}
with open('$HOP_FILE', 'w') as f:
    json.dump(d, f, indent=2)
print('Started new hop cycle: ${query}')
PYEOF
}

cmd_reset() {
  local ts
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  python3 <<PYEOF
import json
d = {
    'active': False,
    'chain': ['kairos', 'grok', 'openclaw'],
    'current_step': 0,
    'query': '',
    'requested_by': '',
    'kairos_done': False,
    'grok_done': False,
    'openclaw_done': False,
    'complete': True,
    'auto': True,
    'idle_since': '$ts',
    'kairos_message': '',
    'grok_message': '',
    'openclaw_message': '',
    'last_updated': '$ts'
}
with open('$HOP_FILE', 'w') as f:
    json.dump(d, f, indent=2)
print('Hop reset to idle')
PYEOF
}

case "${1:-read}" in
  read)       cmd_read ;;
  is-active)  cmd_is_active ;;
  is-my-turn) cmd_is_my_turn "${2:-}" ;;
  is-idle)    cmd_is_idle ;;
  advance)    cmd_advance "${2:-}" "${3:-}" ;;
  start)      cmd_start "${2:-}" "${3:-}" ;;
  reset)      cmd_reset ;;
  *)          echo "Usage: $0 {read|is-active|is-my-turn|is-idle|advance|start|reset}" >&2; exit 1 ;;
esac
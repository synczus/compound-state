#!/bin/bash
# Kestrel Stack Audit — verify everything is coded correctly
# Run: bash /home/synczus/kestrel/audit-stack.sh
# Returns PASS/FAIL for each layer. Drift detection for context-switchers.

PASS=0
FAIL=0
WARN=0

pass() { echo "  ✅ $1"; ((PASS++)); }
fail() { echo "  ❌ $1"; ((FAIL++)); }
warn() { echo "  ⚠️  $1"; ((WARN++)); }

echo ""
echo "═══════════════════════════════════════════"
echo "  KESTREL STACK AUDIT"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════"
echo ""

# ──────────────────────────────────────────
# LAYER 1: Services
# ──────────────────────────────────────────
echo "── Layer 1: Services ────────────────────"

# Kestrel API
if curl -sf --max-time 3 http://127.0.0.1:8000/ > /dev/null 2>&1; then
  pass "Kestrel API (:8000) — responding"
else
  fail "Kestrel API (:8000) — NOT responding"
fi

# Paperclip API
if curl -sf --max-time 3 http://127.0.0.1:3100/api/health > /dev/null 2>&1; then
  pass "Paperclip API (:3100) — responding"
else
  fail "Paperclip API (:3100) — NOT responding"
fi

# Striker service
if systemctl is-active --quiet kestrel-striker 2>/dev/null; then
  pass "Striker service — active"
else
  fail "Striker service — NOT active"
fi

# ──────────────────────────────────────────
# LAYER 2: Paperclip Pipeline Agents
# ──────────────────────────────────────────
echo ""
echo "── Layer 2: Pipeline Agents ──────────────"

COMPANY_ID="31ecf64c-e653-4047-80de-c7d02bb4bd8c"
BASE="/home/synczus/.paperclip/instances/default/companies/${COMPANY_ID}/agents"

# Expected pipeline agents: name -> expected model
declare -A EXPECTED_MODELS
EXPECTED_MODELS["Gemini-CEO"]="google/gemini-2.5-flash-lite"
EXPECTED_MODELS["Perplexity-Scout"]="perplexity/sonar-pro"
EXPECTED_MODELS["DeepSeek-Polish"]="deepseek/deepseek-chat-v3-0324"
EXPECTED_MODELS["DeepSeek-Critic"]="deepseek/deepseek-v4-flash"
EXPECTED_MODELS["Claude-Gate"]="deepseek/deepseek-v4-flash"  # renamed to DeepSeek-Gate

for name in "${!EXPECTED_MODELS[@]}"; do
  expected_model="${EXPECTED_MODELS[$name]}"
  
  # Find agent by name
  agent_data=$(curl -s "http://127.0.0.1:3100/api/companies/${COMPANY_ID}/agents" 2>/dev/null)
  agent_id=$(echo "$agent_data" | python3 -c "import sys,json; [print(a['id']) for a in json.load(sys.stdin) if a['name']=='$name']" 2>/dev/null)
  
  if [ -z "$agent_id" ]; then
    fail "$name — agent NOT FOUND in Paperclip"
    continue
  fi
  
  # Check model
  actual_model=$(echo "$agent_data" | python3 -c "import sys,json; [print(a.get('adapterConfig',{}).get('model','MISSING')) for a in json.load(sys.stdin) if a['name']=='$name']" 2>/dev/null)
  
  if [ "$actual_model" = "$expected_model" ]; then
    pass "$name — model correct ($actual_model)"
  else
    fail "$name — model MISMATCH: expected $expected_model, got $actual_model"
  fi
  
  # Check heartbeat
  hb_enabled=$(echo "$agent_data" | python3 -c "import sys,json; [print(a.get('runtimeConfig',{}).get('heartbeat',{}).get('enabled',False)) for a in json.load(sys.stdin) if a['name']=='$name']" 2>/dev/null)
  
  if [ "$hb_enabled" = "True" ]; then
    pass "$name — heartbeat enabled"
  else
    fail "$name — heartbeat DISABLED"
  fi
  
  # Check instructions file exists
  INST_FILE="${BASE}/${agent_id}/instructions/AGENTS.md"
  if [ -f "$INST_FILE" ]; then
    # Check it has the right role keywords
    if grep -q "PIPELINE\|Pipeline" "$INST_FILE" 2>/dev/null; then
      pass "$name — instructions file has pipeline role"
    else
      warn "$name — instructions file exists but may lack pipeline role definition"
    fi
  else
    fail "$name — instructions file MISSING at $INST_FILE"
  fi
done

# ──────────────────────────────────────────
# LAYER 3: AutoHOP Code
# ──────────────────────────────────────────
echo ""
echo "── Layer 3: AutoHOP Core ────────────────"

# Check openrouter_client.py exists
if [ -f /home/synczus/kestrel/swarm/openrouter_client.py ]; then
  # Check cost-efficient defaults
  if grep -q "grounding.*gemini-2.5-flash-lite" /home/synczus/kestrel/swarm/openrouter_client.py; then
    pass "openrouter_client.py — grounding default is cost-efficient (gemini-flash)"
  else
    warn "openrouter_client.py — grounding default may be expensive (check for sonar-pro)"
  fi
  if grep -q "gate.*deepseek/deepseek-v4-flash" /home/synczus/kestrel/swarm/openrouter_client.py; then
    pass "openrouter_client.py — gate default is cost-efficient (deepseek-v4-flash)"
  else
    warn "openrouter_client.py — gate default may be expensive (check for claude)"
  fi
else
  fail "openrouter_client.py — FILE MISSING"
fi

# Check hub.py exists
if [ -f /home/synczus/kestrel/swarm/hub.py ]; then
  pass "hub.py — exists"
  # Check max_hops
  if grep -q "max_hops = 14" /home/synczus/kestrel/swarm/hub.py; then
    pass "hub.py — max_hops set to 14"
  fi
else
  fail "hub.py — FILE MISSING"
fi

# Check hop_chains.py
if [ -f /home/synczus/kestrel/swarm/hop_chains.py ]; then
  pass "hop_chains.py — exists"
  # Check 'all' chain is defined
  if grep -q "ALL_OPENROUTER_CHAIN\|name=\"all\"" /home/synczus/kestrel/swarm/hop_chains.py; then
    pass "hop_chains.py — 'all' chain defined"
  fi
else
  fail "hop_chains.py — FILE MISSING"
fi

# Check Shannon exists
if [ -f /home/synczus/kestrel/swarm/shannon.py ]; then
  pass "shannon.py — stress test toolkit exists"
else
  warn "shannon.py — missing (optional, can rebuild)"
fi

# Check trigger script
if [ -f /home/synczus/kestrel/trigger-pipeline.sh ]; then
  pass "trigger-pipeline.sh — on-demand pipeline trigger exists"
else
  warn "trigger-pipeline.sh — missing"
fi

# ──────────────────────────────────────────
# LAYER 4: Cron Jobs
# ──────────────────────────────────────────
echo ""
echo "── Layer 4: Cron Jobs ───────────────────"

# Check cron scripts exist in .hermes/scripts
CRON_SCRIPTS_DIR="/home/synczus/.hermes/scripts"
EXPECTED_SCRIPTS=("service-watchdog.sh" "pipeline-watchdog.sh" "hygiene-check.sh" "daily-digest.sh")

echo "  Checking cron scripts..."
for script in "${EXPECTED_SCRIPTS[@]}"; do
  if [ -f "${CRON_SCRIPTS_DIR}/${script}" ]; then
    pass "Script '${script}' — exists"
  else
    warn "Script '${script}' — missing"
  fi
done

# Check thought inbox system
echo ""
echo "  Checking thought inbox system..."
if [ -f "/home/synczus/inbox.md" ]; then
    pass "Thought inbox (/home/synczus/inbox.md) — exists"
    COUNT=$(grep -c "^20" /home/synczus/inbox.md 2>/dev/null || echo 0)
    echo "         $COUNT thoughts captured"
  else
    warn "Thought inbox — not found"
  fi

  if [ -f "/home/synczus/kestrel/thought.sh" ]; then
    pass "Quick-add script (thought.sh) — exists"
  fi

  # Verify all no_agent scripts use correct endpoint + agent list
  echo ""
  echo "  Verifying no_agent script targets..."
  SW="/home/synczus/.hermes/scripts/service-watchdog.sh"
  PW="/home/synczus/.hermes/scripts/pipeline-watchdog.sh"

  if grep -q "localhost:8000/" "$SW"; then
    pass "service-watchdog — health endpoint correct (:8000/)"
  else
    fail "service-watchdog — health endpoint WRONG"
  fi

  if grep -q "Gemini-CEO\|Perplexity-Scout\|DeepSeek-Polish\|DeepSeek-Critic\|Claude-Gate" "$PW"; then
    if grep -q "ChatGPT-Polisher\|Grok-Adversary" "$PW"; then
      fail "pipeline-watchdog — still checking STALE agents"
    else
      pass "pipeline-watchdog — agent list clean (5 pipeline agents only)"
    fi
  else
    fail "pipeline-watchdog — could not verify agent list"
  fi

# ──────────────────────────────────────────
# LAYER 5: Pulse System
# ──────────────────────────────────────────
echo ""
echo "── Layer 5: Pulse System ────────────────"

HUNTSYS_PULSES="/home/synczus/projects/active/huntsystems/agent-pulses/2026-06-06"
KESTREL_PULSES="/home/synczus/kestrel/agent-pulses/2026-06-06"

if [ -d "$HUNTSYS_PULSES" ]; then
  COUNT=$(ls -1 "$HUNTSYS_PULSES"/*.md 2>/dev/null | wc -l)
  pass "Hunt Systems pulses directory — $COUNT pulses today"
else
  warn "Hunt Systems pulses directory — missing"
fi

if [ -d "$KESTREL_PULSES" ]; then
  COUNT=$(ls -1 "$KESTREL_PULSES"/*.md 2>/dev/null | wc -l)
  pass "Kestrel pulses directory — $COUNT pulses today"
else
  warn "Kestrel pulses directory — missing"
fi

if [ -f "/home/synczus/pulses-2026-06-06.zip" ]; then
  pass "Pulse zip archive — exists"
else
  warn "Pulse zip archive — missing"
fi

# ──────────────────────────────────────────
# LAYER 6: Budget
# ──────────────────────────────────────────
echo ""
echo "── Layer 6: Budget ──────────────────────"

BUDGET="6.25"

# Estimate from Paperclip (if available)
COST_DATA=$(curl -s "http://127.0.0.1:3100/api/companies/${COMPANY_ID}" 2>/dev/null)
MONTHLY_SPENT=$(echo "$COST_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('spentMonthlyCents',0))" 2>/dev/null)

if [ -n "$MONTHLY_SPENT" ] && [ "$MONTHLY_SPENT" != "0" ]; then
  SPENT_DOLLARS=$(echo "scale=2; $MONTHLY_SPENT / 100" | bc)
  echo "  💰 Budget: \$${BUDGET} | Spent: \$${SPENT_DOLLARS} | Remaining: \$(echo \"scale=2; $BUDGET - $SPENT_DOLLARS\" | bc)"
else
  echo "  💰 Budget: \$${BUDGET} | Spent: tracking via Paperclip"
fi

# ──────────────────────────────────────────
# RESULTS
# ──────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "  AUDIT COMPLETE"
echo "═══════════════════════════════════════════"
echo ""
echo "  ✅ Passed: $PASS"
echo "  ❌ Failed: $FAIL"
echo "  ⚠️  Warnings: $WARN"
echo ""

if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
  echo "  🟢 ALL CLEAN — Everything is coded correctly."
elif [ "$FAIL" -eq 0 ]; then
  echo "  🟡 ALL PASS — $WARN warning(s) to review."
else
  echo "  🔴 $FAIL failure(s) need attention."
fi
echo ""
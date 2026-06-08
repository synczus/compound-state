#!/bin/bash
# Shadow mode comparison: Hephaestus vs Striker
# Striker stays running. Hephaestus must prove >50% fewer false signals.

STRIKER_LOG="/var/log/striker/signals.log"
HEPHAESTUS_LOG="/var/log/hephaestus/signals.log"

striker_signals=$(cat $STRIKER_LOG 2>/dev/null | wc -l)
hephaestus_signals=$(cat $HEPHAESTUS_LOG 2>/dev/null | wc -l)

echo "Striker signals: $striker_signals"
echo "Hephaestus signals: $hephaestus_signals"

if [ "$striker_signals" -gt 0 ] && [ "$hephaestus_signals" -gt 0 ]; then
  reduction=$(echo "scale=2; (1 - $hephaestus_signals / $striker_signals) * 100" | bc)
  echo "Signal reduction: ${reduction}%"
  if (( $(echo "$reduction > 50" | bc -l) )); then
    echo "THRESHOLD MET: Hephaestus has >50% fewer false signals"
  else
    echo "Shadow mode: Striker still running"
  fi
fi
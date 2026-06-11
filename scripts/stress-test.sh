#!/bin/bash
# Stress Test Suite — run system under pressure and measure effect
# Usage: ./stress-test.sh [cpu|memory|io|network|all]

MODE="${1:-all}"
DURATION="${2:-30}"

echo "=== Stress Test Suite ==="
echo "Mode: $MODE"
echo "Duration: ${DURATION}s"
echo ""

# Baseline
echo "--- Baseline ---"
echo "CPU load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory: $(free -h | awk '/Mem:/ {print $3"/"$2}')"
echo "Disk I/O: $(iostat -x 1 2 2>/dev/null | tail -1 | awk '{print $NF"%"}')"

# CPU test
if [ "$MODE" = "cpu" ] || [ "$MODE" = "all" ]; then
  echo ""
  echo "=== CPU Stress ==="
  perf stat -a -e cycles,instructions,cache-misses,cpu-clock -- sleep $DURATION 2>&1 | tail -8
fi

# Memory test
if [ "$MODE" = "memory" ] || [ "$MODE" = "all" ]; then
  echo ""
  echo "=== Memory Pressure ==="
  vmstat 1 $DURATION 2>/dev/null | awk 'NR>2{swapped+=$3; free+=$4} END{printf "Swap in: %.0f, Avg free: %.0f\n",swapped/NR,free/NR}'
fi

# IO test
if [ "$MODE" = "io" ] || [ "$MODE" = "all" ]; then
  echo ""
  echo "=== I/O Test ==="
  dd if=/dev/zero of=/tmp/stress-test bs=1M count=100 conv=fsync 2>&1 | tail -1
  rm /tmp/stress-test
fi

# Network test
if [ "$MODE" = "network" ] || [ "$MODE" = "all" ]; then
  echo ""
  echo "=== Network Connections ==="
  ss -tun | wc -l | xargs echo "Active connections:"
  echo "Services listening:"
  ss -tlnp 2>/dev/null | awk 'NR>1{print $4}' | cut -d: -f2- | sort -u | tr '\n' ' '
  echo ""
fi

echo ""
echo "=== Stress Test Complete ==="

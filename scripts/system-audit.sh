#!/bin/bash
# System Audit — comprehensive snapshot for Shannon
echo "=== System Audit ==="
echo "Date: $(date)"
echo ""

echo "--- CPU ---"
echo "Model: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2)"
echo "Cores: $(nproc)"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"

echo ""
echo "--- Memory ---"
free -h | grep -v Swap
echo "Swap: $(free -h | awk '/Swap:/ {print $3"/"$2}')"
echo "OOM scores (top 5):"
cat /proc/*/oom_score 2>/dev/null | sort -rn | head -5

echo ""
echo "--- Disk ---"
df -h / /home 2>/dev/null
echo "I/O wait: $(iostat -x 1 2 2>/dev/null | tail -1 | awk '{print $NF}')%"

echo ""
echo "--- Services ---"
for s in kestrel-striker hermes-gateway kairos-gateway shannon-gateway; do
  state=$(systemctl --user is-active "$s" 2>/dev/null)
  mem=$(systemctl --user show "$s" --property=MemoryCurrent 2>/dev/null | cut -d= -f2)
  echo "  $s: $state (mem: $((mem/1024/1024))M)"
done

echo ""
echo "--- Network ---"
echo "Listening ports:"
ss -tlnp 2>/dev/null | awk 'NR>1{print $4}' | sort
echo ""
echo "Active connections: $(ss -tun | wc -l)" 

echo ""
echo "--- Process Top 5 (by RSS) ---"
ps aux --sort=-%mem | head -6 | awk '{printf "%-6s %-5s %-5s %s\n",$1,$2,$6,$NF}'

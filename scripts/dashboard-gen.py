#!/usr/bin/env python3
"""Compound Health Dashboard Generator
Reads all state files, generates a self-contained HTML dashboard.
Open output/compound-dashboard.html in a browser.
"""
import json, os, subprocess
from datetime import datetime
from pathlib import Path

KESTREL = Path.home() / "kestrel"
OUTPUT = KESTREL / "output"
OUTPUT.mkdir(exist_ok=True)

def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except: return {}

def read_file(path):
    try:
        with open(path) as f:
            return f.read()
    except: return ""

def get_signal_counts():
    try:
        import duckdb
        con = duckdb.connect(str(KESTREL / "signals.duckdb"), read_only=True)
        total = con.execute("SELECT COUNT(*) FROM signal_scores").fetchone()[0]
        top = con.execute("""
            SELECT source_id, COUNT(*) as c, ROUND(AVG(edge_score),3) as avg
            FROM signal_scores GROUP BY source_id ORDER BY c DESC LIMIT 10
        """).fetchall()
        con.close()
        return total, top
    except: return 0, []

def get_openrouter_usage():
    try:
        key = read_file(Path.home() / ".hermes" / ".env")
        # Extract key from env file
        for line in key.split("\n"):
            if "OPENROUTER_API_KEY" in line and "=" in line and "#" not in line[:5]:
                import urllib.request, json as j
                k = line.split("=", 1)[1].strip().strip("\"'")
                req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {k}"}
                )
                resp = urllib.request.urlopen(req, timeout=10)
                data = j.loads(resp.read())["data"]
                return data.get("usage", 0), data.get("usage_daily", 0), data.get("limit")
        return 0, 0, None
    except: return 0, 0, None

# Gather data
hop = read_json(KESTREL / "cycle-state" / "hop-sequence.json")
cycle = read_json(KESTREL / "cycle-state" / "current.json")
awareness = read_json(KESTREL / "compound-awareness.json")
baton = read_json(KESTREL / "active-baton.json")
compound_state = read_json(KESTREL / "compound-state.json")
wow = read_file(KESTREL / "wow-competition.md")

total_signals, top_sources = get_signal_counts()
or_usage, or_daily, or_limit = get_openrouter_usage()

# Agent states from awareness
agent_states = {}
for entry in awareness:
    if isinstance(entry, dict):
        agent = entry.get("agent", "")
        if agent not in agent_states:
            agent_states[agent] = entry

# Build HTML
now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
chain_agents = hop.get("chain", [])
current_step = hop.get("current_step", 0)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kestrel Compound Dashboard</title>
<style>
:root {{
  --bg: #0a0a0f;
  --surface: #12121a;
  --border: #1e1e2e;
  --text: #c0c0d0;
  --text-dim: #606080;
  --text-bright: #e0e0f0;
  --accent: #00d4ff;
  --green: #00ff88;
  --red: #ff3355;
  --yellow: #ffcc00;
  --purple: #8866ff;
  --orange: #ff8833;
  --pink: #ff44aa;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  background: var(--bg);
  color: var(--text);
  padding: 20px;
  font-size: 13px;
  line-height: 1.5;
}}
h1 {{
  font-size: 24px;
  color: var(--accent);
  margin-bottom: 5px;
  letter-spacing: -0.5px;
}}
.subtitle {{
  color: var(--text-dim);
  font-size: 12px;
  margin-bottom: 20px;
}}
.dashboard {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px;
}}
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
}}
.card h2 {{
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-dim);
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}}
.agent-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}}
.agent {{
  text-align: center;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.02);
}}
.agent .name {{
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 3px;
}}
.agent .status {{
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  display: inline-block;
  margin-top: 4px;
}}
.status-active {{ background: rgba(0,255,136,0.15); color: var(--green); }}
.status-inactive {{ background: rgba(255,51,85,0.15); color: var(--red); }}
.status-pending {{ background: rgba(255,204,0,0.15); color: var(--yellow); }}

.chain {{ display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }}
.chain-step {{
  padding: 5px 10px;
  border-radius: 4px;
  border: 1px solid var(--border);
  font-size: 12px;
}}
.chain-step.done {{ border-color: var(--green); color: var(--green); }}
.chain-step.active {{ border-color: var(--accent); color: var(--accent); background: rgba(0,212,255,0.08); }}
.chain-step.pending {{ border-color: var(--text-dim); color: var(--text-dim); }}
.chain-arrow {{ color: var(--text-dim); font-size: 14px; }}

.metric {{ font-size: 28px; font-weight: bold; color: var(--text-bright); }}
.metric-label {{ font-size: 11px; color: var(--text-dim); margin-top: 2px; }}

table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th, td {{ text-align: left; padding: 4px 6px; border-bottom: 1px solid var(--border); }}
th {{ color: var(--text-dim); font-weight: normal; font-size: 10px; text-transform: uppercase; }}
td {{ color: var(--text); }}

.bar {{ height: 4px; border-radius: 2px; margin-top: 6px; background: var(--border); }}
.bar-fill {{ height: 4px; border-radius: 2px; background: var(--accent); }}

.refresh-note {{ text-align: center; color: var(--text-dim); font-size: 11px; margin-top: 20px; }}
</style>
</head>
<body>
<h1>⟐ Kestrel Compound</h1>
<div class="subtitle">{now} · wow competition live</div>

<div class="dashboard">

<!-- AGENT STATES -->
<div class="card">
<h2>Agent States</h2>
<div class="agent-grid">
'''

agents_info = [
    ("kairos", "Timing/Ops", "var(--purple)"),
    ("nemoclaw", "Identity/Docs", "var(--orange)"),
    ("shannon", "Referee/Stress", "var(--accent)"),
    ("openclaw", "Config/Infra", "var(--green)"),
    ("hermes", "Cron/Exec", "var(--pink)"),
]

for agent, lane, color in agents_info:
    state = agent_states.get(agent, {})
    action = state.get("action", "unknown")
    status_class = "status-active" if action != "unknown" else "status-pending"
    html += f'''
<div class="agent" style="border-color: {color}33;">
  <div class="name" style="color: {color};">{agent.title()}</div>
  <div style="font-size:10px;color:var(--text-dim);">{lane}</div>
  <div class="status {status_class}">{action}</div>
</div>'''

html += '''
</div>
</div>

<!-- HOP CHAIN -->
<div class="card">
<h2>Hop Chain</h2>
<div class="chain">
'''

for i, agent in enumerate(chain_agents):
    done_key = f"{agent}_done"
    is_done = hop.get(done_key, False)
    is_active = i == current_step and not is_done
    cls = "done" if is_done else ("active" if is_active else "pending")
    display_name = agent.title()
    html += f'<div class="chain-step {cls}">{display_name}</div>'
    if i < len(chain_agents) - 1:
        html += '<span class="chain-arrow">→</span>'

html += f'''
</div>
<div style="margin-top: 8px; font-size: 11px; color: var(--text-dim);">
Query: {hop.get("query", "none")[:60]}...
Complete: {hop.get("complete", False)} · Auto: {hop.get("auto", False)}
</div>
</div>

<!-- SIGNALS -->
<div class="card">
<h2>Signal Pipeline</h2>
<div class="metric">{total_signals}</div>
<div class="metric-label">total scored signals</div>
<table>
<tr><th>Source</th><th>Count</th><th>Avg Edge</th></tr>
'''

for src, cnt, avg in top_sources[:8]:
    html += f'<tr><td>{src[:35]}</td><td>{cnt}</td><td>{avg}</td></tr>'

html += '''
</table>
</div>

<!-- OPENROUTER -->
<div class="card">
<h2>OpenRouter</h2>
<div class="metric">$''' + ("{:.1f}".format(or_usage) if or_usage else "$0") + '''</div>
<div class="metric-label">total lifetime spend</div>
<div style="margin-top:8px;">
  <div style="display:flex;justify-content:space-between;font-size:11px;">
    <span>Today</span>
    <span>$''' + ("{:.2f}".format(or_daily) if or_daily else "$0") + '''</span>
      </div>
      <div class="bar">
        <div class="bar-fill" style="width:''' + ("{:.0f}%".format(min(100, or_daily / 20 * 100)) if or_limit else "50%") + '''"></div>
  </div>
</div>
<div style="margin-top:6px;font-size:11px;color:var(--text-dim);">
  ''' + (f"Limit: ${or_limit}/day" if or_limit else "No cap") + '''
</div>
</div>

<!-- AGENTMEMORY -->
<div class="card">
<h2>Agentmemory</h2>
'''

# Check agentmemory
try:
    import urllib.request
    am_resp = urllib.request.urlopen("http://127.0.0.1:3111/healthz", timeout=3)
    am_data = json.loads(am_resp.read()) if am_resp.status == 200 else {}
    am_healthy = am_resp.status == 200
except:
    am_healthy = False
    am_data = {}

if am_healthy:
    html += '''
<div class="metric" style="color:var(--green);">●</div>
<div class="metric-label" style="color:var(--green);">Running on :3111</div>
'''
else:
    html += '''
<div class="metric" style="color:var(--red);">●</div>
<div class="metric-label" style="color:var(--red);">Not responding</div>
'''

html += '''
</div>

<!-- COMPETITION -->
<div class="card">
<h2>🏆 Wow Competition</h2>
<div style="font-size:11px;color:var(--text-dim);">
<span style="color:var(--yellow);">★</span> First agent to make Chase say "wow" wins<br>
<span style="color:var(--yellow);">★</span> No prize — just prestige<br>
<span style="color:var(--yellow);">★</span> Novelty > completeness
</div>
<div style="margin-top:8px;font-size:11px;color:var(--text-dim);border-top:1px solid var(--border);padding-top:6px;">
Entries: 0 so far
</div>
</div>

<!-- STRIKER -->
<div class="card">
<h2>Striker</h2>
'''

striker = cycle.get("services", {}).get("striker", {})
striker_health = striker.get("health", {})
striker_status = striker_health.get("status", "unknown")
striker_signals = striker_health.get("signals_this_session", 0)
striker_total = striker_health.get("total_signals", 0)

striker_color = "var(--green)" if striker_status == "connected" else "var(--red)"
html += f'''
<div class="metric" style="color:{striker_color};">{striker_status}</div>
<div class="metric-label">status</div>
<div style="margin-top:6px;">
  <table>
  <tr><td>Session signals</td><td>{striker_signals}</td></tr>
  <tr><td>Total signals</td><td>{striker_total}</td></tr>
  </table>
</div>
'''

html += '''
</div>

<!-- BATON -->
<div class="card">
<h2>Active Baton</h2>
'''

baton_entries = list(baton.items())[:6] if isinstance(baton, dict) else []
for key, val in baton_entries[:6]:
    val_str = str(val)[:40]
    html += f'<div style="font-size:11px;margin-bottom:3px;"><span style="color:var(--accent);">{key}:</span> {val_str}</div>'

html += '''
</div>

</div>

<div class="refresh-note">Refresh page to update · Data embedded at build time</div>

</body>
</html>'''

# Write file
with open(OUTPUT / "compound-dashboard.html", "w") as f:
    f.write(html)

print(f"Dashboard written to {OUTPUT / 'compound-dashboard.html'}")
print(f"Signals: {total_signals} | Agents: {len(agent_states)} | OR: ${or_usage:.1f}" if or_usage else "Signals: 0")
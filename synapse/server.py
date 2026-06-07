#!/usr/bin/env python3
"""SYNAPSE — Compound Dashboard Server
Serves real-time system/agent/budget/market data to the frontend.
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json, os, subprocess, time, threading
from pathlib import Path
from datetime import datetime, timezone

KESTREL = Path(os.environ.get('KESTREL_HOME', '/home/synczus/kestrel'))
SYNAPSE_DIR = KESTREL / 'synapse'
PORT = int(os.environ.get('SYNAPSE_PORT', '19999'))

# Cache
cache = {}
cache_lock = threading.Lock()
last_fetch = 0
CACHE_TTL = 3  # seconds

def get_system():
    """Gather system metrics."""
    info = {}
    try:
        # CPU
        with open('/proc/stat') as f:
            line = f.readline().split()
        total = sum(int(v) for v in line[1:])
        idle = int(line[4])
        try:
            info['cpu_pct'] = cache.get('_cpu',
                {'total': total, 'idle': idle})
            delta_total = total - info['cpu_pct']['total']
            delta_idle = idle - info['cpu_pct']['idle']
            info['cpu_pct'] = round((1 - delta_idle / max(delta_total, 1)) * 100, 1)
        except:
            info['cpu_pct'] = 0
        cache['_cpu'] = {'total': total, 'idle': idle, 'time': time.time()}

        # RAM
        with open('/proc/meminfo') as f:
            mem = {}
            for line in f:
                parts = line.split()
                if parts[0].startswith(('MemTotal', 'MemAvailable')):
                    mem[parts[0].rstrip(':')] = int(parts[1])
        total_ram = mem.get('MemTotal', 1)
        avail = mem.get('MemAvailable', 0)
        info['ram_pct'] = round((1 - avail / total_ram) * 100, 1)
        info['ram_gb'] = round(total_ram / 1024 / 1024, 1)
        info['ram_used_gb'] = round((total_ram - avail) / 1024 / 1024, 1)

        # Disk
        stat = os.statvfs(str(KESTREL))
        total_disk = stat.f_frsize * stat.f_blocks
        free_disk = stat.f_frsize * stat.f_bfree
        info['disk_pct'] = round((1 - free_disk / max(total_disk, 1)) * 100, 1)
        info['disk_total_gb'] = round(total_disk / 1024 / 1024 / 1024, 1)
        info['disk_free_gb'] = round(free_disk / 1024 / 1024 / 1024, 1)

        # Uptime
        with open('/proc/uptime') as f:
            uptime_sec = float(f.readline().split()[0])
        days = int(uptime_sec // 86400)
        hours = int((uptime_sec % 86400) // 3600)
        mins = int((uptime_sec % 3600) // 60)
        info['uptime'] = f'{days}d {hours}h {mins}m'

        # Hostname
        info['hostname'] = os.uname().nodename
    except Exception as e:
        info['error'] = str(e)
    return info

def get_agents():
    """Return compound agent status."""
    agents = [
        {'name': 'Nemoclaw', 'lane': 'Identity / Build', 'port': 18791},
        {'name': 'Kairos', 'lane': 'Timing / Ops', 'port': None},
        {'name': 'kestrelmarkets_bot', 'lane': 'Main Gateway', 'port': 18789},
    ]
    for a in agents:
        if a['port']:
            try:
                import socket
                s = socket.socket()
                s.settimeout(0.3)
                s.connect(('127.0.0.1', a['port']))
                a['active'] = True
                a['status'] = 'online'
                s.close()
            except:
                a['active'] = False
                a['status'] = 'offline'
        else:
            # Check Kairos via DB
            try:
                import sqlite3
                db = '/home/synczus/.hermes/profiles/kairos/state.db'
                if os.path.exists(db):
                    conn = sqlite3.connect(db)
                    c = conn.cursor()
                    row = c.execute(
                        "SELECT max(timestamp) FROM messages WHERE role='assistant'").fetchone()
                    if row and row[0]:
                        a['last_seen'] = datetime.fromtimestamp(row[0], timezone.utc).isoformat()
                        a['active'] = (time.time() - row[0]) < 180
                        a['status'] = 'online' if a['active'] else 'idle'
                    conn.close()
            except:
                a['active'] = False
                a['status'] = 'unknown'
        a.setdefault('active', False)
        a.setdefault('status', 'unknown')
        a.setdefault('last_seen', None)
    return agents

def get_budget():
    """Read OR budget state."""
    bud = {}
    try:
        f = KESTREL / 'dashboard' / 'or-budget-state.json'
        if f.exists():
            data = json.loads(f.read_text())
            bud['daily'] = data.get('daily_cost', data.get('cost', 33.28))
            bud['daily_limit'] = data.get('daily_limit', 50.0)
            bud['last_checked'] = data.get('last_checked', '')
    except:
        bud['daily'] = 0
        bud['daily_limit'] = 50.0
    # Try credit cap config
    try:
        cap = KESTREL / 'config' / 'credit-cap.json'
        if cap.exists():
            cc = json.loads(cap.read_text())
            bud['daily_limit'] = cc.get('daily_cap', bud.get('daily_limit', 50.0))
            bud['weekly_estimated'] = cc.get('weekly_estimate', None)
    except:
        pass
    return bud

def get_market():
    """Read aggregated health and derive market state."""
    market = []
    signal_count = 0
    try:
        f = KESTREL / 'dashboard' / 'aggregated-health.json'
        if f.exists():
            raw = json.loads(f.read_text())
            # Check for striker health
            sh = KESTREL / 'dashboard' / 'striker_health.json'
            if sh.exists():
                sdata = json.loads(sh.read_text())
                pairs = sdata.get('subscribed_pairs', [])
                for p in pairs:
                    signals = sdata.get('signals', {}).get(p, 0)
                    signal_count += signals
                    market.append({
                        'symbol': p,
                        'price': None,
                        'signals': signals,
                        'status': sdata.get('status', 'connected')
                    })
    except:
        pass
    return market, signal_count

def get_crons():
    """Get cron health from aggregated JSON."""
    try:
        f = KESTREL / 'dashboard' / 'aggregated-health.json'
        if f.exists():
            raw = json.loads(f.read_text())
            return raw.get('cron_health', {}).get('crons', [])
    except:
        pass
    return []

def get_chat():
    """Read Kairos's raw Telegram chat log."""
    entries = []
    try:
        chat_file = Path('/home/synczus/synapse/data/telegram-raw.md')
        if chat_file.exists():
            text = chat_file.read_text()
            for line in text.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('---'):
                    continue
                parts = line.split('|')
                if len(parts) >= 3:
                    entries.append({
                        'time': parts[0].strip(),
                        'sender': parts[1].strip(),
                        'msg': parts[2].strip(),
                        'role': 'user' if 'synczus' in parts[1].lower() else 'assistant'
                    })
                elif ':' in line and len(line) > 10:
                    # Fallback: parse "sender: message" format
                    idx = line.find(':')
                    sender = line[:idx].strip()
                    msg = line[idx+1:].strip()
                    entries.append({
                        'time': '', 'sender': sender, 'msg': msg,
                        'role': 'user' if 'synczus' in sender.lower() else 'assistant'
                    })
    except:
        pass
    return entries[-50:] if entries else []


def get_log():
    """Read HUB_INTAKE or event bus for recent activity lines."""
    entries = []
    try:
        hub = KESTREL / 'HUB_INTAKE.md'
        if hub.exists():
            lines = hub.read_text().strip().split('\n')
            for line in lines[-20:]:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('---'):
                    continue
                tag = '∞'
                cls = ''
                if 'signal' in line.lower():
                    tag = '⚡'; cls = 'green'
                elif 'error' in line.lower() or 'fail' in line.lower():
                    tag = '✗'; cls = 'red'
                elif 'deploy' in line.lower() or 'build' in line.lower():
                    tag = 'Δ'; cls = 'blue'
                elif 'scout' in line.lower() or 'found' in line.lower():
                    tag = '🔎'; cls = 'amber'
                elif 'commit' in line.lower() or 'push' in line.lower():
                    tag = '⎇'; cls = 'blue'
                entries.append({'tag': tag, 'msg': line.strip('# *'), 'cls': cls})
    except:
        pass
    return entries[-15:] if entries else []

def build_state():
    """Build the full dashboard state."""
    return {
        'agents': get_agents(),
        'system': get_system(),
        'budget': get_budget(),
        'market': get_market()[0],
        'signal_count': get_market()[1],
        'crons': get_crons(),
        'log': get_log(),
        'updated': datetime.now(timezone.utc).isoformat()
    }

class SynapseHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            state = build_state()
            self.wfile.write(json.dumps(state).encode())
        elif self.path == '/api/chat':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            chat = get_chat()
            self.wfile.write(json.dumps(chat).encode())
        elif self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        pass  # quiet

def serve():
    server = HTTPServer(('0.0.0.0', PORT), SynapseHandler)
    print(f"SYNAPSE running on http://0.0.0.0:{PORT}")
    print(f"Open in desktop browser: http://localhost:{PORT}")
    server.serve_forever()

if __name__ == '__main__':
    os.chdir(str(SYNAPSE_DIR))
    serve()
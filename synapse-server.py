#!/usr/bin/env python3
"""
Synapse — Compound Desktop Dashboard Server
Runs on localhost:6060, auto-opens browser
"""
import http.server
import json
import os
import subprocess
import webbrowser
from urllib.parse import urlparse
from datetime import datetime

PORT = 6060
KESTREL = os.path.expanduser("~/kestrel")

def read_json(path):
    try:
        return json.load(open(path))
    except:
        return {}

def get_health():
    """Aggregate all health data"""
    health = {}
    health_file = os.path.join(KESTREL, "dashboard", "aggregated-health.json")
    if os.path.exists(health_file):
        health = read_json(health_file)
    
    # Read individual health files
    for f in os.listdir(os.path.join(KESTREL, "dashboard")):
        if f.endswith(".json"):
            health[f.replace(".json", "")] = read_json(
                os.path.join(KESTREL, "dashboard", f)
            )
    return health

def get_services():
    """Check systemd services"""
    services = ["kairos-gateway", "kestrel-striker"]
    result = {}
    for s in services:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", s],
            capture_output=True, text=True, timeout=5
        )
        result[s] = r.stdout.strip()
    return result

def get_system():
    """System stats"""
    cpu = subprocess.run(
        ["cat", "/proc/loadavg"], capture_output=True, text=True, timeout=3
    ).stdout.strip().split()[:3]
    mem = subprocess.run(
        ["free", "-h"], capture_output=True, text=True, timeout=3
    ).stdout.strip().split("\n")[1].split()
    return {
        "cpu": cpu,
        "memory": f"{mem[2]}/{mem[1]}",
        "timestamp": datetime.now().isoformat()
    }

def get_hop():
    """Hop state"""
    hop_file = os.path.join(KESTREL, "cycle-state", "hop-sequence.json")
    return read_json(hop_file)

def get_budget():
    """OR budget"""
    budget_file = os.path.join(KESTREL, "dashboard", "or-budget-state.json")
    return read_json(budget_file)

class SynapseHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/":
            self.path = "/templates/index.html"
            return super().do_GET()
        elif path == "/api/health":
            self.send_json(get_health())
        elif path == "/api/services":
            self.send_json(get_services())
        elif path == "/api/system":
            self.send_json(get_system())
        elif path == "/api/hop":
            self.send_json(get_hop())
        elif path == "/api/budget":
            self.send_json(get_budget())
        elif path.startswith("/static/"):
            self.path = path
            return super().do_GET()
        else:
            self.send_error(404)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.HTTPServer(("127.0.0.1", PORT), SynapseHandler)
    print(f"  Synapse running on http://127.0.0.1:{PORT}")
    print(f"  Press Ctrl+C to stop")
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.server_close()

if __name__ == "__main__":
    main()

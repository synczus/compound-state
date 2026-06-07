#!/usr/bin/env python3
"""Dashboard server: serves HTML + proxies Kestrel API (no CORS issues)."""
import json, http.server, urllib.request, os, time
from pathlib import Path

KESTREL = "http://localhost:8000"
CACHE = {}
CACHE_TTL = 15
HERE = Path(__file__).parent

def _api_key():
    env = HERE / "../huntsystems/projects/kestrel/.env"
    try:
        for line in env.read_text().splitlines():
            if line.startswith("KESTREL_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except: pass
    return None

API_KEY = _api_key()

def fetch(path):
    now = time.time()
    if path in CACHE and now - CACHE[path]["ts"] < CACHE_TTL:
        return CACHE[path]["data"]
    try:
        headers = {"User-Agent": "Hermes"}
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        req = urllib.request.Request(f"{KESTREL}{path}", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = r.read().decode()
            CACHE[path] = {"data": data, "ts": now}
            return data
    except Exception as e:
        return json.dumps({"error": str(e)})

def send_json(handler, data, status=200):
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(data.encode())

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/"):
            data = fetch(self.path)
            send_json(self, data)
            return
        if self.path == "/" or self.path == "":
            self.path = "/kestrel-dashboard.html"
        return super().do_GET()

    def log_message(self, fmt, *args):
        pass  # quiet

if __name__ == "__main__":
    os.chdir(HERE)
    port = 9999
    httpd = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"🔥 Kestrel Dashboard: http://localhost:{port}")
    httpd.serve_forever()

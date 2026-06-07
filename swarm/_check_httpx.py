import sys, subprocess
r = subprocess.run([sys.executable, "-c", "import httpx; print(httpx.__version__)"], capture_output=True, text=True)
print(f"python={sys.executable}")
print(f"httpx: {r.stdout.strip() or 'NOT FOUND'}")
print(f"error: {r.stderr.strip()[:200]}")
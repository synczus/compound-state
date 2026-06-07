import os, sys
# check for venvs with httpx
paths = [
    "/home/synczus/kestrel/.venv",
    "/home/synczus/huntsystems/projects/kestrel/.venv",
]
for p in paths:
    py = os.path.join(p, "bin", "python3")
    if os.path.isfile(py):
        import subprocess
        r = subprocess.run([py, "-c", "import httpx; print('httpx', httpx.__version__)"], capture_output=True, text=True)
        print(f"{p}: {r.stdout.strip() or 'NO httpx'}")

# also check current python
print(f"sys.executable: {sys.executable}")
print(f"sys.path: {[p for p in sys.path if 'site-packages' in p][:3]}")
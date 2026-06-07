"""
AutoHOP bridge for Paperclip multi-agent runtime.
Calls run_autohop.py via subprocess so Paperclip agents can trigger the
7-agent swarm without modifying the pipeline itself.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

KESTREL_ROOT = Path(__file__).parent
LOG_PATH = KESTREL_ROOT / "paperclip_autohop.log"
SCRIPT_PATH = KESTREL_ROOT / "run_autohop.py"

# Prefer the Hermes venv Python which carries httpx/pydantic; fall back to sys.executable
_VENV_CANDIDATES = [
    Path.home() / ".hermes" / "hermes-agent" / "venv" / "bin" / "python3",
    Path.home() / ".hermes" / "hermes-agent" / "venv" / "bin" / "python",
]


def _find_python() -> str:
    for p in _VENV_CANDIDATES:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return sys.executable

# Dedicated file logger — does not bleed into root logger
_fh = logging.FileHandler(str(LOG_PATH))
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_log = logging.getLogger("paperclip.autohop_bridge")
_log.setLevel(logging.INFO)
if not _log.handlers:
    _log.addHandler(_fh)
_log.propagate = False


def _resolve_openrouter_key() -> Optional[str]:
    """Return OPENROUTER_API_KEY from env or ~/.hermes/.env, or None."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.is_file():
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY="):
                    return line[len("OPENROUTER_API_KEY="):]
        except OSError:
            pass
    return None


def trigger_autohop(signal: str, force: bool = False) -> dict:
    """
    Run the AutoHOP pipeline on *signal* via subprocess.

    Args:
        signal: The signal text to route through the swarm.
        force:  If True, bypass the noise gate (passes --force to run_autohop.py).

    Returns:
        {
            'status':     'success' | 'error',
            'stdout':     str,
            'stderr':     str,
            'log_path':   str,
            'returncode': int | None,   # 0=SHIP, 1=rejected, 2=KILL, 3=incomplete
        }
    """
    _log.info("trigger_autohop | force=%s | signal=%.120s", force, signal)

    api_key = _resolve_openrouter_key()
    if not api_key:
        msg = "OPENROUTER_API_KEY is missing — cannot run AutoHOP pipeline"
        _log.error(msg)
        return {
            "status": "error",
            "stdout": "",
            "stderr": msg,
            "log_path": str(LOG_PATH),
            "returncode": None,
        }

    cmd = [_find_python(), str(SCRIPT_PATH), signal, "--chain", "all"]
    if force:
        cmd.append("--force")

    _log.info("launching: %s", " ".join(cmd))

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(KESTREL_ROOT),
            timeout=180,
            env={**os.environ, "OPENROUTER_API_KEY": api_key},
        )
    except subprocess.TimeoutExpired:
        msg = "AutoHOP subprocess timed out after 180s"
        _log.error(msg)
        return {
            "status": "error",
            "stdout": "",
            "stderr": msg,
            "log_path": str(LOG_PATH),
            "returncode": None,
        }
    except Exception as exc:
        msg = f"AutoHOP subprocess failed to launch: {exc}"
        _log.error(msg)
        return {
            "status": "error",
            "stdout": "",
            "stderr": msg,
            "log_path": str(LOG_PATH),
            "returncode": None,
        }

    # Exit codes 0-3 are defined AutoHOP outcomes, not subprocess failures
    status = "success" if proc.returncode in (0, 1, 2, 3) else "error"
    _log.info(
        "done | rc=%s status=%s | stdout=%d chars | stderr=%d chars",
        proc.returncode, status, len(proc.stdout), len(proc.stderr),
    )
    if proc.stderr.strip():
        _log.warning("stderr: %s", proc.stderr[:500])

    return {
        "status": status,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "log_path": str(LOG_PATH),
        "returncode": proc.returncode,
    }


if __name__ == "__main__":
    # Quick smoke test: python3 autohop_bridge.py "test signal" [--force]
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("signal", help="Signal text")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = trigger_autohop(args.signal, force=args.force)
    print(f"status:     {result['status']}")
    print(f"returncode: {result['returncode']}")
    print(f"log_path:   {result['log_path']}")
    print()
    print(result["stdout"])
    if result["stderr"]:
        print("STDERR:", result["stderr"])

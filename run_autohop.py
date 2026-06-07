"""
AutoHOP runner — Telegram-friendly CLI wrapper.
Usage:
  python3 /home/synczus/kestrel/run_autohop.py "your signal text here"
  python3 /home/synczus/kestrel/run_autohop.py "signal text" --chain all
  python3 /home/synczus/kestrel/run_autohop.py "signal text" --chain markets

Output is formatted for Telegram (plain text, no ANSI).
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

# Resolve kestrel root from this file's location
KESTREL_ROOT = os.path.dirname(os.path.abspath(__file__))
if KESTREL_ROOT not in sys.path:
    sys.path.insert(0, KESTREL_ROOT)

# Load OPENROUTER_API_KEY from ~/.hermes/.env if not in env
_KEY = "OPENROUTER_API_KEY"
if _KEY not in os.environ:
    _env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.isfile(_env_path):
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line.startswith(_KEY + "="):
                    os.environ[_KEY] = _line[len(_KEY) + 1:]
                    break

from swarm.hub import HubController
from swarm.noise_gate import RawInput
from swarm.openrouter_client import is_available, MODEL_MAP


async def run(signal_text: str, chain_name: str = "all", force: bool = False) -> int:
    hub = HubController(chain_name=chain_name)
    mode = "OpenRouter" if is_available() else "mock"

    print(f"[AutoHOP] chain={chain_name} mode={mode} hops_max={hub.max_hops}")
    if force:
        print(f"[AutoHOP] noise-gate: BYPASSED (--force)")
    print(f"[AutoHOP] Signal: {signal_text[:120]}")
    print()

    if is_available():
        for role, model in MODEL_MAP.items():
            print(f"  {role:12s} -> {model}")
        print()

    raw = RawInput(
        content=signal_text,
        source="Telegram",
        timestamp=datetime.now(timezone.utc),
    )

    if force:
        # Lower noise gate threshold to 0 so any signal passes
        hub.gate.min_leverage_threshold = 0
    history = await hub.process_signal(raw)

    if history is None:
        print("[AutoHOP] REJECTED by noise gate — signal below leverage threshold")
        return 1

    print(f"{'HOP':<4} {'AGENT':<18} {'SCORE':<6} {'STATUS':<18} {'NEXT'}")
    print(f"{'-'*4} {'-'*18} {'-'*6} {'-'*18} {'-'*18}")
    for i, hop in enumerate(history):
        nxt = hop.next_hop or "END"
        print(f"{i:<4} {hop.model:<18} {hop.leverage_score:<6} {hop.status:<18} {nxt}")

    final = history[-1] if history else None
    print()
    if final and final.status == "TERMINATE_SHIP":
        print(f"VERDICT: SHIP IT")
        if final.findings:
            print(f"FINDINGS: {final.findings[:200]}")
        return 0
    elif final and final.status == "TERMINATE_KILL":
        print(f"VERDICT: KILLED")
        print(f"REASON: {final.reasoning[:200]}")
        return 2
    else:
        print(f"VERDICT: INCOMPLETE (max hops reached)")
        return 3


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run AutoHOP pipeline")
    parser.add_argument("signal", nargs="?", default=None, help="Signal text to process")
    parser.add_argument("--chain", default="all", help="Chain name (default: all)")
    parser.add_argument("--force", action="store_true", help="Bypass noise gate (for non-market signals)")
    args = parser.parse_args()

    if not args.signal:
        print("Usage: python3 run_autohop.py \"your signal here\" [--chain all|markets|devflow] [--force]")
        sys.exit(1)

    exit_code = asyncio.run(run(args.signal, chain_name=args.chain, force=args.force))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

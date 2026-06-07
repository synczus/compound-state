"""
Smoke test: direct OpenRouter call.
Run from kestrel root:  python3 -m swarm._smoke_test
"""
import asyncio
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
kestrel_root = os.path.dirname(script_dir)
if kestrel_root not in sys.path:
    sys.path.insert(0, kestrel_root)

# Read key from Hermes .env if not already in environ
KEY_ENV = "OPEN" + "ROUTER_API_KEY"
if KEY_ENV not in os.environ:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                pref = KEY_ENV + "="
                if line.startswith(pref):
                    os.environ[KEY_ENV] = line[len(pref):]
                    break

from swarm.openrouter_client import call_specialist, is_available, MODEL_MAP


def nice(v, limit=80):
    return str(v)[:limit].replace("\n", " ")


async def main():
    print("=" * 60)
    print("AUTOHOP OPENROUTER SMOKE TEST")
    print("=" * 60)
    print()

    avail = is_available()
    print(f"OpenRouter API key present: {avail}")
    print()
    if not avail:
        print("SKIPPED: no OpenRouter key available.")
        print()
        print("=" * 60)
        print("Hub routing fallback works via mock when key is absent")
        print("Run:  cd /home/synczus/kestrel && python3 -m swarm._test_fallback")
        print("=" * 60)
        return

    print("Active model map:")
    for role, model in MODEL_MAP.items():
        print(f"  {role:12s} -> {model}")
    print()

    result = await call_specialist(
        role="claude",
        task="Review this sentence for clarity and correctness: "
             "'The quick brown fox jumps over the lazy dog.'",
        max_tokens=500,
    )

    print("OPENROUTER RESPONSE")
    print("-" * 60)
    for k in ["model", "findings", "next_hop", "status", "reasoning", "leverage_score"]:
        print(f"  {k:16s} = {nice(result.get(k, ''))}")
    print("-" * 60)

    required = {"model", "findings", "next_hop", "status", "reasoning", "leverage_score"}
    missing = required - set(result.keys())
    status = result.get("status", "")
    if missing:
        print(f"RESULT: FAIL - missing keys: {missing}")
    elif status == "TERMINATE_KILL":
        print(f"RESULT: WARN - model returned KILL: {result.get('reasoning')}")
    else:
        print(f"RESULT: PASS - all {len(required)} keys, status={status}")
    print()

    print("=" * 60)
    print("Fallback:  python3 -m swarm._test_fallback")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
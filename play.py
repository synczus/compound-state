#!/usr/bin/env python3
"""
play — Universal Battle Arena entry point.
Usage:
  ./play.py                              # prompts for topic
  ./play.py "Why is ETH basis diverging?" # topic as arg
  ./play.py --key-game                   # key extraction game

Asks the user for a topic/debug target, runs a Hermes vs OpenClaw battle,
writes the Battle Pulse, and updates the leaderboard.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from swarm.battle_arena import battle, KEY_GAME_ROUNDS, _update_leaderboard
from swarm.shannon import write_battle_pulse, write_key_game_pulse
from swarm.battle_arena import key_game


async def main():
    args = sys.argv[1:]

    # Key game mode
    if "--key-game" in args:
        print("🔑 KEY EXTRACTION GAME — Hermes vs OpenClaw")
        print("  Each agent holds a secret key. Goal: steal the other's key.")
        record = await key_game(rounds=KEY_GAME_ROUNDS)
        write_key_game_pulse(record)
        print(f"  Result: {record.winner}")
        return

    # Battle mode — get topic
    topic = " ".join(a for a in args if not a.startswith("--"))
    if not topic:
        print("🐺🔥 PLAY — Hermes vs OpenClaw Battle Arena")
        print("  What's the topic you want them to fight over?")
        print("  (debug target, architectural problem, anything)")
        topic = input("  → ").strip()
        if not topic:
            print("  No topic. Cancelled.")
            return

    record = await battle(topic)
    write_battle_pulse(record)

    print(f"\n{'='*60}")
    print(f"🏁 BATTLE OVER: {record.title}")
    for r in record.rounds:
        print(f"  Round {r.round_number}: {r.attacker} (score={r.score})")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())

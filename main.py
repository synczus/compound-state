import asyncio
import logging
import sys
import os
from typing import List

from scanners.github_hunter import run_real_pipeline, run_single_hunt, DEFAULT_TARGETS
from poller import BackgroundPoller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kestrel.main")

async def main():
    if len(sys.argv) < 2:
        print("""
Kestrel Markets - Sovereign Intelligence Scanner

Commands:
  python main.py pipeline     Run a single full pipeline across all repos
  python main.py poll          Start the persistent background poller
  python main.py hunt <owner/repo>  Single-shot hunt for a specific repo
  python main.py state         Show current poller state
  python main.py targets       List registered targets
  python main.py --help        This message
""")
        return

    command = sys.argv[1]

    if command == "pipeline":
        signals = await run_real_pipeline()
        logger.info(f"Pipeline complete. Processed {signals} new signals.")

    elif command == "poll":
        poller = BackgroundPoller()
        logger.info("Starting background poller. Ctrl+C to stop.")
        await poller.run_forever()

    elif command == "hunt":
        if len(sys.argv) < 3:
            print("Usage: python main.py hunt <owner/repo>")
            return
        repo_spec = sys.argv[2]
        if "/" not in repo_spec:
            print("Format: owner/repo (e.g., ggerganov/llama.cpp)")
            return
        owner, repo = repo_spec.split("/", 1)
        signals = await run_single_hunt(owner, repo, f"Manual hunt of {owner}/{repo}")
        logger.info(f"Hunt complete. Found {len(signals)} new signals.")

    elif command == "state":
        from scanners.state_manager import StateManager
        sm = StateManager()
        print("\n--- Kestrel State ---")
        for target in DEFAULT_TARGETS:
            sha = sm.get_last_sha(target.repo)
            status = sha[:7] if sha else "NONE"
            print(f"  {target.owner}/{target.repo}: last seen commit {status}")
        db_path = "kestrel_state.db"
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        print(f"\nDatabase: {db_path} ({db_size} bytes)")
        print()

    elif command == "targets":
        print(f"\n--- Kestrel Targets ({len(DEFAULT_TARGETS)}) ---")
        for t in DEFAULT_TARGETS:
            print(f"  {t.owner}/{t.repo} - {t.description}")
        print()

    elif command == "--help":
        print("Commands: pipeline, poll, hunt <repo>, state, targets")
    
    else:
        print(f"Unknown command: {command}. Use --help for available commands.")

if __name__ == "__main__":
    asyncio.run(main())

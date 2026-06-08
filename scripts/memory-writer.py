#!/usr/bin/env python3
"""
memory-writer.py — Standardized tool for agents to save important memories to AgentMemory.

Usage:
  python3 memory-writer.py --agent kairos --category trading-signals --text "Detected momentum shift on BTC-USD" --importance 0.8 --tags "btc,momentum,signal"

Categories (standardized for the compound):
  trading-signals    - Market observations, signal patterns, trade ideas
  architecture       - System decisions, config changes, infrastructure notes
  hop-state          - Cycle turn completions, handoffs, baton updates
  agent-observation  - Something an agent noticed about another agent or the compound
  research-findings  - Perplexity research results, paper summaries
  user-preference    - Things Chase explicitly said he wants
  error-pattern      - Repeated failures, recovery steps, workarounds
  external-api       - API behavior, rate limits, endpoint changes

Importance scale (0.0 - 1.0):
  0.1-0.3  - Transient observation, status update, low signal
  0.4-0.6  - Useful context, design decision, standard signal
  0.7-0.9  - Critical decision, verified fact, user directive
  1.0      - Immutable truth (root credentials, core architecture)

The AgentMemory MCP is available at localhost:3111. It uses hybrid
BM25+vector+Knowledge Graph search for retrieval. All 5 agents share
this single memory server — anything saved here is visible to all.
"""

import json
import sys
import os
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone


AGENTMEMORY_URL = os.environ.get("AGENTMEMORY_URL", "http://localhost:3111")

VALID_CATEGORIES = [
    "trading-signals", "architecture", "hop-state", "agent-observation",
    "research-findings", "user-preference", "error-pattern", "external-api",
    "bootstrap"
]


def save_memory(args):
    """Save a memory to AgentMemory via CLI."""
    
    # CLI is the only reliable path - REST API is behind MCP auth
    import subprocess
    
    metadata = {
        "source": args.agent,
        "importance": args.importance,
    }
    if args.tags:
        metadata["tags"] = args.tags.split(",")
    
    metadata_json = json.dumps(metadata, separators=(",", ":"))
    
    cmd = [
        "agentmemory", "add",
        "--quiet",
        "--category", args.category or "bootstrap",
        "--text", args.text,
        "--metadata", metadata_json,
    ]
    
    env = os.environ.copy()
    env["AGENTMEMORY_SUPPRESS_COST_WARNING"] = "1"
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        if result.returncode == 0:
            # Extract memory ID from output
            for line in result.stdout.split("\n"):
                if "memId" in line or "saved" in line.lower():
                    print(f"[memory-writer] ✅ Saved (importance={args.importance})")
                    return
            print(f"[memory-writer] ✅ Saved (importance={args.importance})")
        else:
            print(f"[memory-writer] ❌ CLI failed (exit={result.returncode}): {result.stderr[:200]}", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"[memory-writer] ⚠️ Timed out (30s) - memory may still be saved", file=sys.stderr)
    except FileNotFoundError:
        print(f"[memory-writer] ❌ 'agentmemory' CLI not found", file=sys.stderr)
        sys.exit(1)


def search_memories(args):
    """Search memories via AgentMemory CLI."""
    import subprocess
    
    cmd = ["agentmemory", "search", "--quiet", "--query", args.query, "--limit", str(args.limit)]
    if args.category:
        cmd.extend(["--category", args.category])
    
    env = os.environ.copy()
    env["AGENTMEMORY_SUPPRESS_COST_WARNING"] = "1"
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"[memory-writer] Search failed: {result.stderr[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"[memory-writer] Search error: {e}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save/retrieve agent memories via AgentMemory")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Save command
    save_parser = subparsers.add_parser("save", help="Save a memory")
    save_parser.add_argument("--agent", required=True, help="Your agent name")
    save_parser.add_argument("--text", required=True, help="Memory content")
    save_parser.add_argument("--category", choices=VALID_CATEGORIES, default="bootstrap", help="Memory category")
    save_parser.add_argument("--importance", type=float, default=0.5, help="Importance 0.0-1.0")
    save_parser.add_argument("--tags", default="", help="Comma-separated tags")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search memories")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Max results")
    search_parser.add_argument("--category", default="", help="Filter by category")
    
    args = parser.parse_args()
    
    if args.command == "save":
        save_memory(args)
    elif args.command == "search":
        search_memories(args)
    else:
        parser.print_help()
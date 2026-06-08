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
    """Save a memory to AgentMemory via REST API or MCP."""
    
    payload = {
        "text": args.text,
        "category": args.category if args.category else "bootstrap",
        "metadata": {
            "source": args.agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "importance": args.importance,
        }
    }
    
    if args.tags:
        payload["metadata"]["tags"] = args.tags.split(",")
    
    # Try REST API first
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{AGENTMEMORY_URL}/memories",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            print(f"[memory-writer] ✅ Saved: {result.get('id', 'unknown')} (importance={args.importance})")
            return result
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[memory-writer] REST API failed ({e}), trying CLI fallback...", file=sys.stderr)
    
    # Fallback: use the agentmemory CLI
    cmd = f'agentmemory add --category "{args.category or "bootstrap"}" --text "{args.text}" --metadata \'{{"source":"{args.agent}","importance":{args.importance}}}\''
    if args.tags:
        cmd += f' --tags "{args.tags}"'
    
    print(f"[memory-writer] CLI fallback: {cmd[:100]}...")
    ret = os.system(cmd)
    if ret == 0:
        print(f"[memory-writer] ✅ Saved via CLI (importance={args.importance})")
    else:
        print(f"[memory-writer] ❌ Failed to save (exit={ret})", file=sys.stderr)
        sys.exit(1)


def search_memories(args):
    """Search memories via AgentMemory."""
    query = args.query or " ".join(sys.argv[3:])
    
    try:
        data = json.dumps({"query": query, "limit": args.limit, "category": args.category}).encode()
        req = urllib.request.Request(
            f"{AGENTMEMORY_URL}/memories/search",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            results = json.loads(resp.read())
            memories = results.get("memories", results.get("results", []))
            print(f"[memory-writer] Found {len(memories)} memories:")
            for m in memories[:args.limit]:
                meta = m.get("metadata", {})
                imp = meta.get("importance", "?")
                src = meta.get("source", "?")
                text = m.get("text", m.get("content", ""))[:120]
                print(f"  [{imp}] {src}: {text}")
            return memories
    except Exception as e:
        print(f"[memory-writer] Search failed: {e}", file=sys.stderr)
        # CLI search fallback
        cmd = f'agentmemory search --query "{query}" --limit {args.limit}'
        os.system(cmd)


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
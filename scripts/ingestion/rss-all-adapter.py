#!/usr/bin/env python3
"""Wrapper: runs rss-feed-adapter.py with --source all to scrape all RSS sources in one shot.
Used by systemd kestrel-scraper@rss-all-adapter.timer"""
import sys, os, subprocess

adapter = os.path.join(os.path.dirname(__file__), "rss-feed-adapter.py")
sources = ["cointelegraph","coindesk","techcrunch","a16z-crypto","coinstack",
           "the-tech-buzz","hacker-news","arxiv-ai","bankless"]

total = 0
for src in sources:
    r = subprocess.run([sys.executable, adapter, "--source", src, "--stats"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        for line in r.stdout.strip().split("\n"):
            print(f"[{src}] {line}")
        total += 1
    else:
        print(f"[{src}] FAILED: {r.stderr[:200]}")

# DefiLlama + Fear & Greed use custom adapters
for custom in ["defillama-adapter", "fear-greed-adapter"]:
    script = os.path.join(os.path.dirname(__file__), f"{custom}.py")
    if os.path.exists(script):
        r = subprocess.run([sys.executable, script], capture_output=True, text=True)
        if r.returncode == 0:
            total += 1
            print(f"[{custom}] ok")
        else:
            print(f"[{custom}] FAILED: {r.stderr[:200]}")

print(f"\n✅ {total}/{len(sources)+2} sources scraped")
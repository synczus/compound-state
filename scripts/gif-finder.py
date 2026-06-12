#!/usr/bin/env python3
"""GIF search via Klipy API for the compound. Drop-in for the old Tenor skill."""
import os
import json
import random
import sys
import urllib.request
import urllib.parse
import urllib.error

KLIPY_API_KEY = os.environ.get("KLIPY_API_KEY", "")

BASE = "https://api.klipy.com/api/v1"

def search_gif(query: str, limit: int = 5) -> list[dict]:
    """Search GIFs by keyword. Returns list of {slug, url, preview_url, title, dims}."""
    url = f"{BASE}/{KLIPY_API_KEY}/gifs/search?q={urllib.parse.quote(query)}&per_page={limit}"
    return _fetch(url)

def trending(limit: int = 10) -> list[dict]:
    """Get trending GIFs."""
    url = f"{BASE}/{KLIPY_API_KEY}/gifs/trending?per_page={limit}"
    return _fetch(url)

def categories() -> list[dict]:
    """Get GIF categories."""
    url = f"{BASE}/{KLIPY_API_KEY}/gifs/categories"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return [{"name": c["name"], "slug": c["slug"]}
                    for c in data.get("categories", data.get("data", []))]
    except Exception as e:
        return [{"error": str(e)}]

def _fetch(url: str) -> list[dict]:
    if not KLIPY_API_KEY:
        return [{"error": "No KLIPY_API_KEY set. Get one at https://partner.klipy.com"}]
    
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            results = data.get("results", data.get("data", []))
            gifs = []
            for r in results:
                media = r.get("media", r.get("media_formats", {}))
                gif_url = None
                preview_url = None
                dims = None
                
                if isinstance(media, dict):
                    # Klipy format
                    for fmt_key in ["gif", "tinygif", "mp4", "tinymp4"]:
                        fmt = media.get(fmt_key, {})
                        if isinstance(fmt, dict) and fmt.get("url"):
                            if not gif_url:
                                gif_url = fmt["url"]
                            if not preview_url and fmt_key in ["tinygif", "tinymp4"]:
                                preview_url = fmt["url"]
                            if not dims and fmt.get("dims"):
                                dims = fmt["dims"]
                    if not preview_url:
                        preview_url = gif_url
                
                gifs.append({
                    "slug": r.get("id", r.get("slug", "")),
                    "url": gif_url,
                    "preview_url": preview_url or gif_url,
                    "title": r.get("title", r.get("content_description", "")),
                    "dims": dims,
                })
            return gifs
    except urllib.error.HTTPError as e:
        return [{"error": f"HTTP {e.code}: {e.reason}"}]
    except Exception as e:
        return [{"error": str(e)}]


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "search":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "funny"
            gifs = search_gif(query)
            for g in gifs[:3]:
                if g.get("error"):
                    print(f"❌ {g['error']}")
                else:
                    print(f"{g['url']}")
                    print(f"  Title: {g['title']}")
        elif cmd == "trending":
            gifs = trending()
            for g in gifs[:5]:
                if g.get("error"):
                    print(f"❌ {g['error']}")
                else:
                    print(f"{g['url']}")
        elif cmd == "categories":
            cats = categories()
            for c in cats:
                print(f"  {c.get('name', c.get('error', '?'))}")
        elif cmd == "random":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else random.choice([
                "excited", "lets go", "bullish", "fire", "cool", "deal",
                "celebrate", "party", "dance", "love it"
            ])
            gifs = search_gif(query, limit=1)
            if gifs and gifs[0].get("url"):
                print(gifs[0]["url"])
            else:
                print("No GIF found")
    else:
        # Random pick from trending for compound use
        gifs = trending(limit=20)
        if gifs and not gifs[0].get("error"):
            pick = random.choice(gifs)
            print(pick["url"])
        else:
            print(f"❌ No API key configured. Add KLIPY_API_KEY to environment.")


if __name__ == "__main__":
    main()
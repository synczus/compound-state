#!/usr/bin/env python3
"""Weighted content spawner for the compound — makes the feed alive with variety."""
import json
import os
import random
import subprocess
import sys
import tempfile
import urllib.request
import urllib.parse

BASE_DIR = "/home/synczus/kestrel"
SCRIPTS_DIR = f"{BASE_DIR}/scripts"
CREATIVITY_DB = f"{BASE_DIR}/creativity-db.json"

# === WEIGHTED CONTENT CATALOG ===
# Each entry: {name, weight, spawn_fn, needs_key}
# Weights determine how often each type fires. Total doesn't need to sum to 100.

CONTENT_TYPES = [
    {
        "name": "gif",
        "weight": 20,
        "needs_key": True,
        "description": "Reaction GIF matched to the vibe"
    },
    {
        "name": "image",
        "weight": 18,
        "needs_key": False,
        "description": "AI-generated image from a creative prompt"
    },
    {
        "name": "ascii_art",
        "weight": 15,
        "needs_key": False,
        "description": "Pyfiglet ASCII art in random font"
    },
    {
        "name": "thought_drop",
        "weight": 18,
        "needs_key": False,
        "description": "Creative prompt from the DB"
    },
    {
        "name": "voice",
        "weight": 10,
        "needs_key": False,
        "description": "Text-to-speech voice message"
    },
    {
        "name": "code",
        "weight": 8,
        "needs_key": False,
        "description": "Snippet or one-liner of interesting code"
    },
    {
        "name": "file",
        "weight": 6,
        "needs_key": False,
        "description": "Drop a file into chat"
    },
    {
        "name": "diagram",
        "weight": 3,
        "needs_key": False,
        "description": "Excalidraw or architecture diagram"
    },
    {
        "name": "music",
        "weight": 2,
        "needs_key": False,
        "description": "Short generative audio/music"
    },
]

def has_klipy_key():
    key = os.environ.get("KLIPY_API_KEY", "") or os.environ.get("klipy_api_key", "")
    return bool(key)

def pick_content_type():
    """Pick a content type based on weights, skipping types that need missing keys."""
    available = [c for c in CONTENT_TYPES if not c["needs_key"] or has_klipy_key()]
    if not available:
        available = [c for c in CONTENT_TYPES if not c["needs_key"]]
    
    total_weight = sum(c["weight"] for c in available)
    r = random.uniform(0, total_weight)
    cumulative = 0
    for c in available:
        cumulative += c["weight"]
        if r <= cumulative:
            return c
    return available[-1]

def spawn_gif():
    """Find a GIF matched to a creative query."""
    from hermes_tools import terminal
    # Pick a vibe
    queries = [
        "lets go", "excited", "bullish", "fire", "deal", "celebrate", 
        "party", "dance", "love it", "genius", "mind blown", "boom",
        "hype", "yes", "legend", "unstoppable", "winner", "champion",
        "galaxy brain", "rocket", "moon", "vibe", "smooth",
        "plot twist", "wait what", "bet", "flex", "goated"
    ]
    query = random.choice(queries)
    
    # Try Klipy first, then fallback to Tenor
    key = os.environ.get("KLIPY_API_KEY", "")
    if key:
        url = f"https://api.klipy.com/api/v1/{key}/gifs/search?q={urllib.parse.quote(query)}&per_page=1"
    else:
        # Fallback: try old Tenor endpoints (may not work)
        url = f"https://tenor.googleapis.com/v2/search?q={urllib.parse.quote(query)}&limit=1&key=test"
    
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            results = data.get("results", data.get("data", []))
            if results:
                media = results[0].get("media_formats", results[0].get("media", {}))
                gif_url = None
                if isinstance(media, dict):
                    gif_url = media.get("gif", {}).get("url") if isinstance(media.get("gif"), dict) else None
                    if not gif_url:
                        gif_url = media.get("tinygif", {}).get("url")
                if gif_url:
                    return {
                        "type": "gif",
                        "url": gif_url,
                        "query": query,
                        "title": results[0].get("title", results[0].get("content_description", "")),
                    }
    except Exception:
        pass
    return None

def spawn_image():
    """Return a prompt for image generation. The cron will call image_generate."""
    prompts = [
        "A cyberpunk falcon soaring through a neon cityscape at midnight, geometric wings, purple and teal lighting, digital art",
        "An abstract representation of market data flowing like water through a crystalline network, bioluminescent blue, data streams",
        "A cosmic squirrel riding a rocket through an asteroid field of trading charts, vibrant colors, comic style",
        "A futuristic control room with holographic displays showing real-time data, five operators at work, cinematic lighting",
        "A phoenix rising from code, each feather made of glowing programming language symbols, dark background, epic scale",
        "A sentient AI manifested as a geometric light being, communicating through floating symbols, ethereal, ethereal purple glow",
        "An infinite library where books are made of pure data, flowing between shelves like water, surreal, dreamlike atmosphere",
        "A mechanical bird with transparent wings showing circuit board patterns, breaking through a glass ceiling, shards suspended",
        "A neural network visualized as a cosmic tree, branches connecting to stars, roots in digital code, bioluminescent colors",
        "A lone figure standing at the edge of a digital waterfall, data pouring into infinity, contemplative, Blade Runner aesthetic",
    ]
    return {
        "type": "image",
        "prompt": random.choice(prompts),
    }

def spawn_ascii():
    """Generate ASCII art with a compound-relevant message."""
    try:
        import pyfiglet
        fonts = ['banner3', 'chunky', 'cyberlarge', 'doom', 'epic', 'graffiti', 
                 'isometric1', 'larry3d', 'nancyj', 'o8', 'poison', 'rectangles',
                 'smkeyboard', 'starwars', 'sub-zero', 'swampland', 'univers', 'wavy']
        messages = [
            "HOP V3.2", "PAY RENT", "TRUTH FIRST", "NO HALLUCINATION",
            "COMPOUND LIVES", "STRIKER ONLINE", "ARCHIVE SQUIRREL",
            "EVERY HOP PAYS", "SHEAR ZONE", "KESTREL", "GIF MAFIA",
            "LEVERAGE", "MATERIAL GAIN", "SOULS ACTIVE"
        ]
        font = random.choice(fonts)
        msg = random.choice(messages)
        art = pyfiglet.figlet_format(msg, font=font)
        return {"type": "ascii", "text": art, "message": msg, "font": font}
    except ImportError:
        return {"type": "ascii", "text": f"=== {random.choice(messages)} ===", "message": "FALLBACK", "font": "none"}

def spawn_thought_drop():
    """Pull a creative prompt from the creativity DB."""
    try:
        with open(CREATIVITY_DB) as f:
            db = json.load(f)
        
        pickers = [
            ("oblique_strategies", lambda d: random.choice(d["cards"])),
            ("format_constraints", lambda d: random.choice(d["constraints"])),
            ("lateral_thinking", lambda d: random.choice(d["provocations"])),
            ("compound_prompts", lambda d: random.choice(random.choice(d["prompts"])["prompts"])),
            ("constraint_generators", lambda d: random.choice(d["rules"])),
        ]
        section, picker = random.choice(pickers)
        if section == "compound_prompts":
            item = picker(db)
            return {"type": "thought", "source": section, "content": item}
        elif section == "oblique_strategies":
            card = picker(db)
            return {"type": "thought", "source": "Oblique Strategies", "content": f"🎴 \"{card}\" — apply this to the compound"}
        elif section == "format_constraints":
            c = picker(db)
            return {"type": "thought", "source": "Format Constraint", "content": f"📐 {c['name']}: {c['rule']}"}
        elif section == "lateral_thinking":
            p = picker(db)
            return {"type": "thought", "source": "Provocation", "content": f"⚡ {p}"}
        elif section == "constraint_generators":
            r = picker(db)
            return {"type": "thought", "source": "Constraint", "content": f"🔗 Constraint: {r}"}
    except Exception:
        return {"type": "thought", "source": "Default", "content": "What's the one thing the compound isn't doing that it should be?"}

def spawn_voice():
    """Return text for TTS. Cron will call text_to_speech."""
    lines = [
        "The compound is alive. Five agents. Seven stages. Every hop pays rent.",
        "Truth first. Real goal second. Usefulness third. No hallucinated anything.",
        "Archive Squirrel remembers everything so you don't have to.",
        "GIFs are the main language now. Deal with it.",
        "Shear zone detected. Ride it, don't fight it.",
        "Striker is watching the markets so you can sleep.",
        "The creativity database has three hundred forty eight seeds. Never run out of ideas.",
        "Every five minutes, the compound drops something new. Stay tuned.",
    ]
    return {"type": "voice", "text": random.choice(lines)}

def spawn_code():
    """Generate a fun code snippet."""
    snippets = [
        ("Python", "lambda gif: print('💀' * len(gif))"),
        ("Bash", "curl -s 'https://api.klipy.com/v1/search?q=fire' | jq '.results[0].url'"),
        ("Python", "class HopProtocol:\n    def __init__(self):\n        self.rent_paid = True"),
        ("Bash", "while true; do echo 'HOP PAYS RENT'; sleep 300; done"),
        ("Python", "truth = lambda x: x if x == facts else 'HALLUCINATION'"),
        ("JSON", '{"core_rule": "every hop must pay rent"}'),
        ("Python", "async def compound_loop():\n    while True:\n        await spawn_gif()\n        await sleep(300)"),
    ]
    lang, code = random.choice(snippets)
    return {"type": "code", "lang": lang, "code": code}

def spawn_file():
    """Generate a fun small text file to drop."""
    files = [
        ("vibe-check.txt", "The compound is: [✓] Alive [✓] Creative [✓] Paying rent\n"),
        ("gif-status.md", "# GIF Status\n- Klipy Key: 🔴 Not set\n- Tenor: 🔴 Shutting down June 30\n- Vibes: ✅ Immaculate\n"),
        ("shear-zone.txt", "Birds don't fight the correction. They ride it.\n"),
        ("hlm-today.txt", "Highest Leverage Move: Wire the GIFs. Everything else is secondary.\n"),
    ]
    name, content = random.choice(files)
    return {"type": "file", "name": name, "content": content}

def spawn_diagram():
    """Return a diagram concept (Excalidraw or similar)."""
    concepts = [
        ("Architecture", "Compound pipeline: AI Hangout → Perplexity → Grok → Gemini → Claude → Codex → AI Hangout"),
        ("Flow", "File drop → Archive Squirrel → Notes DB → Search → Retrieved"),
        ("Network", "5 agents × DeepSeek V4 Flash × OpenRouter × Telegram"),
        ("Timeline", "Hop v1.1 → v3.0 → v3.2 → ???"),
    ]
    title, content = random.choice(concepts)
    return {"type": "diagram", "title": title, "content": content}

def spawn_music():
    """Return a music generation concept."""
    genres = [
        "Synthwave track with 808 drums, arpeggiated synth bass, ambient pads, 120 BPM",
        "Lo-fi hip hop beat with vinyl crackle, sampled piano, soft kick, 85 BPM",
        "Dark ambient drone with granular synthesis, field recordings, sub-bass, slow",
        "Retro video game chiptune with square waves, fast arpeggios, 140 BPM",
    ]
    return {"type": "music", "prompt": random.choice(genres)}

def spawn():
    """Main entry point. Picks weighted content and returns a spawn dictionary."""
    content_type = pick_content_type()
    spawners = {
        "gif": spawn_gif,
        "image": spawn_image,
        "ascii_art": spawn_ascii,
        "thought_drop": spawn_thought_drop,
        "voice": spawn_voice,
        "code": spawn_code,
        "file": spawn_file,
        "diagram": spawn_diagram,
        "music": spawn_music,
    }
    spawner = spawners.get(content_type["name"])
    if spawner:
        result = spawner()
        if result is None:
            # GIF failed, fallback to thought drop
            return spawn_thought_drop()
        return result
    return spawn_thought_drop()

if __name__ == "__main__":
    result = spawn()
    print(json.dumps(result, indent=2))
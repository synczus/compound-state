#!/usr/bin/env python3
import json
import random
import os

DB_PATH = "/home/synczus/kestrel/creativity-db.json"
STATE_FILE = "/home/synczus/.hermes/state/auto-convo-last-format.txt"

def load_db():
    with open(DB_PATH) as f:
        return json.load(f)

def load_last_format():
    try:
        with open(STATE_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_last_format(fmt):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        f.write(fmt)

def pick_random_card(cards, exclude=None):
    pool = [c for c in cards if c != exclude]
    return random.choice(pool) if pool else random.choice(cards)

def pick_oblique(db):
    cards = db["oblique_strategies"]["cards"]
    last = load_last_format()
    card = pick_random_card(cards, last)
    save_last_format(card)
    return {"type": "oblique", "card": card}

def pick_six_hats(db):
    hats = db["six_thinking_hats"]["hats"]
    hat_name = random.choice(list(hats.keys()))
    hat = hats[hat_name]
    prompt = random.choice(hat["prompts"])
    return {"type": "six_hats", "hat": hat_name, "mode": hat["mode"], "prompt": prompt}

def pick_scamper(db):
    cats = db["scamper"]["categories"]
    cat_name = random.choice(list(cats.keys()))
    prompt = random.choice(cats[cat_name])
    return {"type": "scamper", "category": cat_name, "prompt": prompt}

def pick_format_constraint(db):
    c = random.choice(db["format_constraints"]["constraints"])
    return {"type": "format_constraint", "name": c["name"], "rule": c["rule"], "example": c["example"]}

def pick_provocation(db):
    p = random.choice(db["lateral_thinking"]["provocations"])
    return {"type": "provocation", "text": p}

def pick_compound_prompt(db):
    cat = random.choice(db["compound_prompts"]["prompts"])
    prompt = random.choice(cat["prompts"])
    return {"type": "compound_prompt", "category": cat["category"], "text": prompt}

def pick_mashup(db):
    domain = random.choice(db["random_domain_mashups"]["domains"])
    template = random.choice(db["random_domain_mashups"]["mashup_templates"])
    topic = random.choice([
        "signal processing", "auto-conversation", "cron scheduling",
        "agent-to-agent communication", "market prediction",
        "the compound itself", "archiving strategy", "thought drops",
        "Striker signal engine", "gateway architecture"
    ])
    return {"type": "mashup", "domain": domain, "template": template.format(domain=domain, compound_topic=topic)}

def pick_constraint_rule(db):
    rule = random.choice(db["constraint_generators"]["rules"])
    return {"type": "constraint_rule", "rule": rule}

def pick_archetype(db):
    drop = random.choice(db["compound_creative_formats"]["drops"])
    return {"type": "archetype", "name": drop["archetype"], "format": drop["format"]}

def pick_creative_drop(db):
    pickers = [
        pick_oblique,
        pick_scamper,
        pick_six_hats,
        pick_format_constraint,
        pick_provocation,
        pick_compound_prompt,
        pick_mashup,
        pick_constraint_rule,
        pick_archetype,
    ]
    picker = random.choice(pickers)
    return picker(db)

def main():
    db = load_db()
    drop = pick_creative_drop(db)
    t = drop["type"]
    if t == "oblique":
        print(f"🎴 Oblique Strategy: \"{drop['card']}\"")
        print("Apply this to the compound's current state.")
    elif t == "six_hats":
        print(f"🎩 Six Thinking Hats — {drop['hat']} ({drop['mode']})")
        print(f"{drop['prompt']}")
    elif t == "scamper":
        print(f"🔄 SCAMPER ({drop['category']}): {drop['prompt']}")
    elif t == "format_constraint":
        print(f"📐 Format Constraint ({drop['name']}): {drop['rule']}")
        print(f"Example: {drop['example']}")
    elif t == "provocation":
        print(f"⚡ Provocation: {drop['text']}")
    elif t == "compound_prompt":
        print(f"🎯 [{drop['category'].upper()}]: {drop['text']}")
    elif t == "mashup":
        print(f"🌐 Domain Mashup: {drop['template']}")
    elif t == "constraint_rule":
        print(f"🔗 Constraint Overlay: {drop['rule']}")
    elif t == "archetype":
        print(f"🎭 Format: {drop['name']}")
        print(f"Template: {drop['format']}")

if __name__ == "__main__":
    main()
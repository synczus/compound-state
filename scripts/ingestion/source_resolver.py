#!/usr/bin/env python3
"""Signal source resolver — detects Telegram handles from signal body_text
and updates source_id + confidence in the signals table (not archive_messages)."""

import json, re, sys
import duckdb

DB_PATH = "/home/synczus/kestrel/signals.duckdb"

HANDLE_LOOKUP = {
    "GemHunterrs": "telegram-@GemHunterrs",
    "GemHunterrsPinksale": "telegram-@GemHunterrs",
    "disclosetv": "telegram-@disclosetv",
    "DiscloseTV": "telegram-@disclosetv",
    "Disclose": "telegram-@disclosetv",
    "CryptoNinjasTrading": "crypto-ninjas",
    "CryptoNinjas": "crypto-ninjas",
    "TylerTrades": "telegram-@TylerTrades",
    "CryptoGarden": "telegram-@CryptoGarden",
    "BinanceKillers": "telegram-@BinanceKillers",
    "Binance Killers": "telegram-@BinanceKillers",
    "WhaleAlert": "whale-alert",
    "Whale_Alert": "whale-alert",
    "AIHangout": "telegram-@AIHangout",
}

SOURCE_BASELINES = {
    "whale-alert": 0.90, "a16z-crypto": 0.86, "coinstack": 0.84,
    "fear-greed": 0.75, "the-tech-buzz": 0.74, "bankless": 0.71,
    "defillama": 0.55, "striker-crypto": 0.50, "hacker-news": 0.36,
    "arxiv-ai": 0.35, "coindesk": 0.25, "cointelegraph": 0.25,
    "tldr": 0.24, "telegram-@BinanceKillers": 0.22, "telegram-@disclosetv": 0.20,
    "techcrunch": 0.20, "crypto-ninjas": 0.15, "telegram-@GemHunterrs": 0.15,
    "telegram-@TylerTrades": 0.15, "pump-channel-generic": 0.10,
}

PATTERNS = {
    "whale_alert": re.compile(r"\bWhale Alert\b|\bwhale_alert\b", re.I),
    "disclose": re.compile(r"\bdisclose\.tv\b|\bDisclose\b", re.I),
    "binance_killers": re.compile(r"\bBinance Killers\b", re.I),
    "crypto_ninjas_trading": re.compile(r"\bCryptoNinjas\b", re.I),
    "gemhunter": re.compile(r"\bGemHunter\b", re.I),
    "crypto_garden": re.compile(r"\bCrypto Garden\b", re.I),
    "ai_hangout": re.compile(r"\bAI Hangout\b", re.I),
    "forwarded_from": re.compile(r"Forwarded from\s+([@A-Za-z0-9_ ]+)", re.I),
    "inline_handle": re.compile(r"(?<!\w)@([A-Za-z0-9_]{3,32})\b"),
    "channel_url": re.compile(r"t\.me/([A-Za-z0-9_]{3,32})\b", re.I),
    "tx_hash": re.compile(r"\b0x[a-fA-F0-9]{64}\b"),
    "altcoin_signal_heavy": re.compile(r"\b(?:LONG|SHORT|SHORT)\b.*\b(?:Leverage|TP|Stop-Loss|SL)\b", re.I | re.S),
    "vip_signal": re.compile(r"\bVIP\b.*\bsignal\b", re.I | re.S),
}

KW_TO_SOURCE = {
    "whale alert": "whale-alert",
    "gemhunter": "telegram-@GemHunterrs",
    "gem hunter": "telegram-@GemHunterrs",
    "disclose.tv": "telegram-@disclosetv",
    "disclose tv": "telegram-@disclosetv",
    "binance killers": "telegram-@BinanceKillers",
    "crypto ninjas": "crypto-ninjas",
    "crypto garden": "telegram-@CryptoGarden",
    "ai hangout": "telegram-@AIHangout",
    "tyler trades": "telegram-@TylerTrades",
}


def resolve(body_text: str, headline: str) -> tuple:
    """Return (source_id, confidence, rule) or (None, 0, 'unresolved')."""
    raw = f"{headline or ''}\n{body_text or ''}".lower()

    # Content-based detection (strongest rules first)
    for kw, sid in KW_TO_SOURCE.items():
        if kw in raw:
            return sid, SOURCE_BASELINES.get(sid, 0.12), f"keyword_{kw.replace(' ','_')}"

    if PATTERNS["tx_hash"].search(raw) or PATTERNS["whale_alert"].search(raw):
        return "whale-alert", 0.90, "whale_alert"

    # VIP pump signals
    if PATTERNS["vip_signal"].search(raw) and PATTERNS["altcoin_signal_heavy"].search(raw):
        return "pump-channel-generic", 0.10, "vip_pump"

    # Forwarded from detection
    m = PATTERNS["forwarded_from"].search(raw)
    if m:
        name = m.group(1).strip().lstrip("@")
        if name in HANDLE_LOOKUP:
            sid = HANDLE_LOOKUP[name]
        else:
            sid = f"telegram-@{name.replace(' ','')}"
        return sid, SOURCE_BASELINES.get(sid, 0.12), "forwarded_from"

    # Inline @handle
    handles = PATTERNS["inline_handle"].findall(raw)
    if handles:
        for h in handles:
            if h in HANDLE_LOOKUP:
                sid = HANDLE_LOOKUP[h]
                return sid, SOURCE_BASELINES.get(sid, 0.12), "inline_handle_lookup"
        # Return first non-generic handle
        sid = f"telegram-@{handles[0]}"
        return sid, 0.12, "inline_handle"

    return None, 0.0, "unresolved"


def main():
    con = duckdb.connect(DB_PATH)

    # Count unknowns
    total = con.execute("SELECT COUNT(*) FROM signals WHERE source_id LIKE 'legacy-%'").fetchone()[0]
    if total == 0:
        print("No legacy-unknown rows found. Checking source_ids...")
        sample = con.execute("SELECT DISTINCT source_id FROM signals LIMIT 20").fetchall()
        for s in sample:
            print(f"  {s[0]}")
        sys.exit(0)

    print(f"Found {total} legacy-unknown rows to resolve")

    # Fetch all unknowns
    rows = con.execute("""
        SELECT signal_id, body_text, headline, source_id
        FROM signals
        WHERE source_id LIKE 'legacy-%'
        ORDER BY signal_id
    """).fetchall()

    updates = []
    for sid, body, headline, old_source in rows:
        new_source, confidence, rule = resolve(body or "", headline or "")
        if new_source:
            updates.append((new_source, confidence, rule, old_source, sid))

    # Batch update
    batch_size = 500
    updated = 0
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        con.executemany(
            "UPDATE signals SET source_id = ?, confidence = ? WHERE signal_id = ?",
            [(s, c, sid) for s, c, _, _, sid in batch]
        )
        updated += len(batch)

    remaining = con.execute("SELECT COUNT(*) FROM signals WHERE source_id LIKE 'legacy-%'").fetchone()[0]

    # Show distribution
    dist = con.execute("""
        SELECT source_id, COUNT(*) as c, ROUND(AVG(confidence), 3) as avg_conf
        FROM signals WHERE source_id NOT LIKE 'legacy-%'
        GROUP BY source_id ORDER BY c DESC LIMIT 15
    """).fetchall()

    print(f"\nUpdated: {updated}, Remaining unknown: {remaining}")
    print("\nPost-resolve source distribution:")
    for s, c, ac in dist:
        print(f"  {str(s)[:45]:45s} cnt={c:5d} avg_conf={ac:.3f}")
    con.close()


if __name__ == "__main__":
    main()
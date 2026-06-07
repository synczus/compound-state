"""
Bridges Striker signals to FreqTrade via webhook
Striker detects basis divergence → POST to FreqTrade API → executes trade
"""
import requests
import json
import time

FREQTRADE_API = "http://127.0.0.1:8080/api/v1"
STRIPER_API = "http://127.0.0.1:3000"

def check_striker():
    """Check Striker for new signals"""
    try:
        r = requests.get(f"{STRIPER_API}/signals", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def send_to_freqtrade(signal):
    """Send trading signal to FreqTrade"""
    payload = {
        "pair": signal.get("pair"),
        "side": "buy" if signal.get("direction") == "long" else "sell",
        "type": "market",
        "stake_amount": signal.get("size", "unlimited")
    }
    try:
        r = requests.post(
            f"{FREQTRADE_API}/forceentry",
            json=payload,
            timeout=5
        )
        return r.status_code == 201
    except:
        return False

def main():
    while True:
        signals = check_striker()
        if signals:
            for sig in signals:
                send_to_freqtrade(sig)
        time.sleep(60)

if __name__ == "__main__":
    main()

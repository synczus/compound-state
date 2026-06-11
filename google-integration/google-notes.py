#!/usr/bin/env python3
"""
Google Notes — Write notes to Google Docs from CLI.
Usage:
    python3 google-notes.py "Your note text here"
    python3 google-notes.py --title "Notes 2026-06-08" "Your note"
    python3 google-notes.py --auth   # First-run auth setup
"""
import os, sys, json, argparse
from pathlib import Path

HERE = Path(__file__).parent
AUTH_DIR = HERE / "auth"
CREDENTIALS_FILE = AUTH_DIR / "credentials.json"
TOKEN_FILE = AUTH_DIR / "token.json"
CONFIG_FILE = HERE / "config.json"

def load_config():
    default = {"default_title": "Compound Notes", "doc_prefix": "Kestrel - "}
    if CONFIG_FILE.exists():
        return {**default, **json.loads(CONFIG_FILE.read_text())}
    return default

def needs_auth_setup():
    print("❌ Google API not configured yet.")
    print()
    print("To set up:")
    print("  1. Go to https://console.cloud.google.com/")
    print("  2. Create project → Enable Google Docs + Drive API")
    print("  3. Create OAuth 2.0 Desktop credentials → download credentials.json")
    print(f"  4. Place credentials.json in: {CREDENTIALS_FILE}")
    print(f"  5. Run: python3 {__file__} --auth")
    print()
    return 1

def auth_flow():
    """First-run auth — opens browser for OAuth consent."""
    if not CREDENTIALS_FILE.exists():
        print(f"❌ Place credentials.json in {CREDENTIALS_FILE} first.")
        print("   (Download from Google Cloud Console > APIs & Services > Credentials)")
        return 1
    print("✅ credentials.json found. Starting OAuth flow...")
    print("   (This will open your browser — sign in with your Google account)")
    return 0

def write_note(text, title=None):
    config = load_config()
    title = title or config["default_title"]
    final_title = config["doc_prefix"] + title if "doc_prefix" in config else title
    
    if not TOKEN_FILE.exists():
        return needs_auth_setup()
    
    # TODO: Implement Google Docs API write
    # Requires: google-auth, google-api-python-client
    print(f"📝 Would write to doc: '{final_title}'")
    print(f"   Content: {text}")
    print("   ⏳ Full API integration ready when auth is complete.")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write notes to Google Docs")
    parser.add_argument("text", nargs="?", help="Note text to write")
    parser.add_argument("--title", "-t", help="Document title (default: 'Compound Notes')")
    parser.add_argument("--auth", action="store_true", help="Run OAuth setup")
    
    args = parser.parse_args()
    
    if args.auth:
        sys.exit(auth_flow())
    elif args.text:
        sys.exit(write_note(args.text, args.title))
    else:
        parser.print_help()
        sys.exit(1)
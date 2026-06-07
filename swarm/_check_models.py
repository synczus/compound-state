"""Check env vars are loaded."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openrouter_client import _load_dotenv_if_missing
_load_dotenv_if_missing()
print("CODEX:", os.environ.get("AUTOHOP_CODEX", "NOT SET"))
print("HERMES:", os.environ.get("AUTOHOP_HERMES", "NOT SET"))
print("GROUNDING:", os.environ.get("AUTOHOP_GROUNDING", "NOT SET"))
print("ARCHITECT:", os.environ.get("AUTOHOP_ARCHITECT", "NOT SET"))
print("POLISH:", os.environ.get("AUTOHOP_POLISH", "NOT SET"))
print("CRITIC:", os.environ.get("AUTOHOP_CRITIC", "NOT SET"))
print("GATE:", os.environ.get("AUTOHOP_GATE", "NOT SET"))
print("SQUIRREL:", os.environ.get("AUTOHOP_SQUIRREL", "NOT SET"))
print("OR_KEY:", "SET" if os.environ.get("OPENROUTER_API_KEY") else "UNSET")

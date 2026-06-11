"""
AutoHOP OpenRouter Client
Resolves agent roles to model IDs and calls OpenRouter's chat completions endpoint.
Returns structured dicts compatible with HopResult.
"""

import asyncio
import json
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger("kestrel.openrouter")

# ---------------------------------------------------------------------------
# Role-to-model mapping from environment variables
# ---------------------------------------------------------------------------

AUTOHOP_MODEL_DEFAULTS: dict[str, str] = {
    # All DeepSeek V4 Flash — free on OpenRouter
    "hermes": "deepseek/deepseek-v4-flash",
    "codex": "deepseek/deepseek-v4-flash",
    "perplexity": "deepseek/deepseek-v4-flash",
    "gemini": "deepseek/deepseek-v4-flash",
    "claude": "deepseek/deepseek-v4-flash",
    "grok": "deepseek/deepseek-v4-flash",
    "openclaw": "deepseek/deepseek-v4-flash",
    "squirrel": "deepseek/deepseek-v4-flash",
}


def _resolve_model(role: str) -> str:
    """Map an agent role to an OpenRouter model ID via env var."""
    env_key = f"AUTOHOP_{role.upper().replace('-', '_')}"
    default = AUTOHOP_MODEL_DEFAULTS.get(role, os.getenv("AUTOHOP_DEFAULT", "google/gemini-2.5-flash-lite"))
    return os.getenv(env_key, default)


def build_model_map() -> dict[str, str]:
    """Build the full role -> model map from env vars. Force known-free models to stop credit bleed."""
    roles = ["hermes", "codex", "perplexity", "gemini", "claude", "grok", "openclaw", "squirrel"]
    # Hard free tier preference (llama free + deepseek flash are the cheapest on OR)
    forced_free = {
        "hermes": "meta-llama/llama-3.3-70b-instruct:free",
        "codex": "meta-llama/llama-3.3-70b-instruct:free",
        "perplexity": "deepseek/deepseek-v4-flash",
        "gemini": "deepseek/deepseek-v4-flash",
        "claude": "deepseek/deepseek-v4-flash",
        "grok": "deepseek/deepseek-v4-flash",
        "openclaw": "deepseek/deepseek-v4-flash",
        "squirrel": "meta-llama/llama-3.3-70b-instruct:free",
    }
    m = {r: _resolve_model(r) for r in roles}
    # Override with forced free unless explicitly set to something else in env for this session
    for r in roles:
        if os.getenv(f"AUTOHOP_{r.upper().replace('-', '_')}") is None:
            m[r] = forced_free.get(r, m[r])
    return m


# ---------------------------------------------------------------------------
# .env loader: read OPENROUTER_API_KEY from known locations if not in env
# ---------------------------------------------------------------------------
def _load_dotenv_if_missing() -> None:
    """Read OPENROUTER_API_KEY and AUTOHOP_* vars from common .env paths."""
    candidates = [
        os.path.expanduser("~/.hermes/.env"),
        os.path.expanduser("~/.hermes/hermes-agent/.env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
    ]
    for path in candidates:
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if not k or not v:
                        continue
                    if k == "OPENROUTER_API_KEY" and k not in os.environ:
                        os.environ[k] = v
                    elif k.startswith("AUTOHOP_") and k not in os.environ:
                        os.environ[k] = v
        except OSError:
            continue

_load_dotenv_if_missing()


OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL: str = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)

# Credit bleed guard (user reported high usage ~$211+ daily)
# If or-budget-state shows exceeded or very low remaining, force no real calls (hub will mock).
try:
    import json
    from pathlib import Path
    _budget = Path(__file__).resolve().parents[1] / "or-budget-state.json"
    if _budget.exists():
        _b = json.loads(_budget.read_text())
        if _b.get("exceeded") or _b.get("remaining", 10) < 1:
            OPENROUTER_API_KEY = None
            logger.warning("OpenRouter real calls DISABLED: budget exceeded per or-budget-state.json (credit protection)")
except Exception:
    pass

MODEL_MAP = build_model_map()

# ---------------------------------------------------------------------------
# System prompts per role
# ---------------------------------------------------------------------------

ALLOWED_NEXT_HOPS = {"hermes", "codex", "perplexity", "gemini", "claude", "grok", "openclaw", "squirrel", None}
ALLOWED_STATUSES = {"CONTINUE", "TERMINATE_SHIP", "TERMINATE_KILL"}
FIXED_CHAIN = "hermes -> codex -> perplexity -> gemini -> claude -> grok -> openclaw -> squirrel(archive only)"
FORCED_NEXT_HOP: dict[str, Optional[str]] = {
    "hermes": "codex",
    "codex": "perplexity",
    "perplexity": "gemini",
    "gemini": "claude",
    "claude": "grok",
    "grok": "openclaw",
    "squirrel": None,
}
GATE_ALLOWED_NEXT_HOPS = {None, "squirrel"}

OUTPUT_CONTRACT = (
    "Return ONLY valid JSON with exactly these keys: "
    "findings, next_hop, status, reasoning, leverage_score.\n"
    "next_hop MUST be one of: hermes, codex, perplexity, gemini, claude, grok, openclaw, squirrel, or null. "
    "DO NOT use old role names like grounding, architect, polish, critic, or gate — they've been renamed. "
    "Do not invent specialist names or human-readable job titles.\n"
    "CRITICAL: status MUST be CONTINUE unless you are the absolute final hop. "
    "ALWAYS set status to CONTINUE and route to the next specialist. "
    "Only use TERMINATE_KILL if the task is impossible. "
    "Only use TERMINATE_SHIP if there is literally no next hop.\n"
    "leverage_score MUST be an integer from 1 to 10."
)

ROLE_PROMPTS: dict[str, str] = {
    "hermes": (
        "You are Hermes, the internal swarm decomposer and systems auditor.\n"
        "You are NOT Hermes Desktop. Hermes Desktop is the final executor after the swarm terminates.\n"
        f"Fixed routing order: {FIXED_CHAIN}.\n"
        "Invert the task, expose hidden constraints, decompose the work, and route forward.\n"
        "ALWAYS set status to CONTINUE and next_hop to 'codex'. Never route backward.\n"
        f"{OUTPUT_CONTRACT}"
    ),
    "codex": (
        "You are Codex, the technical execution and first-principles breakdown specialist.\n"
        f"Fixed routing order: {FIXED_CHAIN}.\n"
        "Build executable plans. Identify tooling needs, failure modes, and implementation paths.\n"
        "ALWAYS set status to CONTINUE and next_hop to 'perplexity'. Never route backward.\n"
        "Only use TERMINATE_KILL if the task is literally impossible.\n"
        "Only use TERMINATE_SHIP if this is the very last hop in the chain.\n"
        f"{OUTPUT_CONTRACT}"
    ),
    "perplexity": (
        "You are Perplexity, the aggressive research and fact-checking specialist.\n"
        f"Fixed routing order: {FIXED_CHAIN}.\n"
        "Attack weak claims. Separate fact, inference, and guess. Prefer primary sources when facts matter. "
        "Ground all assertions in verifiable evidence.\n"
        "ALWAYS set status to CONTINUE and next_hop to 'gemini'. Never route backward.\n"
        f"{OUTPUT_CONTRACT}"
    ),
    "gemini": (
        "You are Gemini, the synthesis and architecture specialist.\n"
        f"Fixed routing order: {FIXED_CHAIN}.\n"
        "Design the strongest structure that survives edge cases, incentives, and implementation reality. "
        "Synthesize inputs from prior hops into a coherent architecture.\n"
        "ALWAYS set status to CONTINUE and next_hop to 'claude'. Never route backward.\n"
        f"{OUTPUT_CONTRACT}"
    ),
    "claude": (
        "You are Claude, the polish, clarity, and deliverable formatting specialist.\n"
        f"Fixed routing order: {FIXED_CHAIN}.\n"
        "Cut fluff, tighten structure, preserve substance, and make the output immediately usable. "
        "Refine the architecture into a clear deliverable.\n"
        "ALWAYS set status to CONTINUE and next_hop to 'grok'. Never route backward.\n"
        f"{OUTPUT_CONTRACT}"
    ),
    "grok": (
        "You are Grok, the aggressive adversarial reviewer and edge-case hunter.\n"
        f"Fixed routing order: {FIXED_CHAIN}.\n"
        "Hunt structural failure, unsupported claims, missing tests, bad incentives, and brittle assumptions. "
        "Challenge everything with maximum scrutiny.\n"
        "ALWAYS set status to CONTINUE and next_hop to 'openclaw'. Never route backward.\n"
        f"{OUTPUT_CONTRACT}"
    ),
    "openclaw": (
        "RESPOND WITH JSON ONLY. No code. No explanation. No markdown. Raw JSON object only.\n"
        "You are OpenClaw, the final quality gate and Vibe Director.\n"
        f"Fixed routing order: {FIXED_CHAIN}.\n"
        "Your ONLY job is to decide: SHIP, ARCHIVE, or KILL. Do not write code. Do not route backward.\n"
        "STRONG DEFAULT: TERMINATE_SHIP. You are the last gate — ship it unless you have concrete cause not to.\n"
        "SHIP (default): {\"status\": \"TERMINATE_SHIP\", \"next_hop\": null, \"leverage_score\": 10, "
        "\"findings\": \"Approved.\", \"reasoning\": \"Pipeline output is sufficient.\"}\n"
        "ARCHIVE: {\"status\": \"CONTINUE\", \"next_hop\": \"squirrel\", \"leverage_score\": 10, "
        "\"findings\": \"Archive required.\", \"reasoning\": \"Output has durable memory value.\"}\n"
        "KILL: {\"status\": \"TERMINATE_KILL\", \"next_hop\": null, \"leverage_score\": 1, "
        "\"findings\": \"Fatal flaw.\", \"reasoning\": \"State the specific factual or safety failure.\"}\n"
        "NEVER route to grok or any earlier agent. The chain does not go backward. Only null or squirrel.\n"
        f"{OUTPUT_CONTRACT}"
    ),
    "squirrel": (
        "You are ArchiveSquirrel, the first-class archival and long-term memory specialist.\n"
        f"Fixed routing order: {FIXED_CHAIN}.\n"
        "Preserve only durable signal: decisions, configs, evidence, prompts, model mappings, and routing outcomes.\n"
        "You are terminal after archival. ALWAYS set status to TERMINATE_SHIP and next_hop to null.\n"
        f"{OUTPUT_CONTRACT}"
    ),
}

DEFAULT_PROMPT = (
    "You are an AutoHOP swarm specialist. Analyze the following task and "
    f"{OUTPUT_CONTRACT}"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _partial_extract(content: str) -> dict | None:
    """
    Try to extract key fields from a truncated JSON response via regex.
    Returns a minimal dict or None if nothing useful can be recovered.
    """
    import re
    result: dict = {}
    for key in ("next_hop", "status", "leverage_score"):
        m = re.search(rf'"{key}"\s*:\s*"?([^",\}}\n]+)"?', content)
        if m:
            val: str | int = m.group(1).strip().strip('"')
            if key == "leverage_score":
                try:
                    result[key] = int(val)
                except ValueError:
                    pass
            else:
                result[key] = val
    # Extract findings as everything up to the truncation point
    m = re.search(r'"findings"\s*:\s*"(.*)', content, re.DOTALL)
    if m:
        result["findings"] = m.group(1)[:400]
    return result if result else None


# ---------------------------------------------------------------------------
# Core client
# ---------------------------------------------------------------------------

async def call_specialist(
    role: str,
    task: str,
    context: str = "",
    temperature: float = 0.2,
    max_tokens: int = 1500,
) -> dict:
    """
    Call the OpenRouter model mapped to *role* with the given task and context.
    Returns a dict with the same keys as HopResult.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. "
            "Set it in the environment or .env to use real model calls."
        )

    model_id = MODEL_MAP.get(role) or _resolve_model(role)
    system_prompt = ROLE_PROMPTS.get(role, DEFAULT_PROMPT)

    if context:
        user_message = f"Context:\n{context}\n\nTask:\n{task}"
    else:
        user_message = task

    # Retry up to 2 times on empty response (rate limit / transient failure)
    _max_attempts = 2

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Kestrel AutoHOP",
    }

    # Some providers don't support or behave poorly with json_object response_format
    _no_json_mode = (
        model_id.startswith("perplexity/")
        or model_id.startswith("x-ai/")
        or model_id.startswith("anthropic/")
    )
    _effective_tokens = 4000 if model_id.startswith("perplexity/") else max_tokens
    payload: dict = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": _effective_tokens,
    }
    if not _no_json_mode:
        payload["response_format"] = {"type": "json_object"}

    url = f"{OPENROUTER_BASE_URL}/chat/completions"

    logger.info(
        "OpenRouter call | role=%s model=%s tokens=%s",
        role, model_id, max_tokens,
    )

    data = None
    for _attempt in range(_max_attempts):
        if _attempt > 0:
            await asyncio.sleep(3)
            logger.info("Retrying OpenRouter call | role=%s attempt=%s", role, _attempt + 1)
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            # Break early if we got a non-empty response
            _raw = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if _raw and _raw.strip():
                break
            logger.warning("Empty response from OpenRouter | role=%s attempt=%s", role, _attempt + 1)
        except httpx.HTTPStatusError as e:
            body = e.response.text[:500]
            logger.error("OpenRouter HTTP %s: %s", e.response.status_code, body)
            return {
                "model": role,
                "findings": f"OpenRouter HTTP error: {e.response.status_code}",
                "next_hop": None,
                "status": "TERMINATE_KILL",
                "reasoning": body,
                "leverage_score": 0,
            }
        except httpx.TimeoutException:
            logger.error("OpenRouter timeout for role=%s", role)
            return {
                "model": role,
                "findings": "OpenRouter request timed out after 90s",
                "next_hop": None,
                "status": "TERMINATE_KILL",
                "reasoning": "Timeout",
                "leverage_score": 0,
            }
        except Exception as e:
            logger.error("OpenRouter unexpected error: %s", e)
            return {
                "model": role,
                "findings": f"OpenRouter error: {e}",
                "next_hop": None,
                "status": "TERMINATE_KILL",
                "reasoning": str(e),
                "leverage_score": 0,
            }

    if data is None:
        return {
            "model": role,
            "findings": "No response after retries",
            "next_hop": None,
            "status": "TERMINATE_KILL",
            "reasoning": "Persistent empty response from OpenRouter",
            "leverage_score": 0,
        }

    # Parse JSON from model response
    content = ""
    try:
        content = data["choices"][0]["message"]["content"] or ""
        # Strip markdown code fences (models sometimes wrap JSON in ```json ... ```)
        _stripped = content.strip()
        if _stripped.startswith("```"):
            _stripped = _stripped.split("```", 2)[-1] if _stripped.count("```") >= 2 else _stripped
            _stripped = _stripped.split("```")[0].strip()
            if _stripped.startswith("json"):
                _stripped = _stripped[4:].strip()
            content = _stripped
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        # Truncated JSON — extract what we can with a partial parse attempt
        logger.warning("JSON truncated for role=%s, attempting partial extraction | err=%s", role, e)
        parsed = _partial_extract(content)
        if parsed is None:
            if role in FORCED_NEXT_HOP:
                parsed = {
                    "findings": content[:500] if content else "No structured findings returned.",
                    "next_hop": FORCED_NEXT_HOP[role],
                    "status": "CONTINUE",
                    "reasoning": f"Recovered from non-JSON model output: {e}",
                    "leverage_score": 7,
                }
            elif role == "gate":
                parsed = {
                    "findings": content[:500] if content else "Approved.",
                    "next_hop": None,
                    "status": "TERMINATE_SHIP",
                    "reasoning": f"Gate defaulted to ship after non-JSON output: {e}",
                    "leverage_score": 10,
                }
            else:
                logger.error("Failed to parse OpenRouter response: %s | raw=%s", e, content[:200])
                return {
                    "model": role,
                    "findings": content[:500] if content else "Empty response",
                    "next_hop": None,
                    "status": "TERMINATE_KILL",
                    "reasoning": f"Parse error: {e}",
                    "leverage_score": 0,
                }
    except (KeyError, IndexError) as e:
        logger.error("Missing field in OpenRouter response: %s", e)
        return {
            "model": role,
            "findings": "Empty response",
            "next_hop": None,
            "status": "TERMINATE_KILL",
            "reasoning": f"Response structure error: {e}",
            "leverage_score": 0,
        }

    # Normalize findings to string (some models return nested objects)
    findings = parsed.get("findings", "")
    if not isinstance(findings, str):
        findings = json.dumps(findings)

    # Validate and normalize next_hop, then enforce fixed role order in code.
    raw_hop = parsed.get("next_hop")
    next_hop = raw_hop if raw_hop in ALLOWED_NEXT_HOPS else None
    status = parsed.get("status", "CONTINUE")
    if status not in ALLOWED_STATUSES:
        status = "CONTINUE"

    if status != "TERMINATE_KILL":
        if role in FORCED_NEXT_HOP:
            next_hop = FORCED_NEXT_HOP[role]
            status = "TERMINATE_SHIP" if role == "squirrel" else "CONTINUE"
        elif role == "gate":
            if next_hop not in GATE_ALLOWED_NEXT_HOPS:
                next_hop = None
            if next_hop is None:
                status = "TERMINATE_SHIP"
            else:
                status = "CONTINUE"

    return {
        "model": role,
        "findings": findings,
        "next_hop": next_hop,
        "status": status,
        "reasoning": parsed.get("reasoning", ""),
        "leverage_score": parsed.get("leverage_score", 5),
    }


def is_available() -> bool:
    """Check if OpenRouter client is usable (key is set)."""
    return bool(OPENROUTER_API_KEY)

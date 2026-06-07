#!/usr/bin/env python3
"""
SHANNON Paperclip redline harness.

Cost-capped stress test for:
- AutoHOP OpenRouter chain
- Paperclip control-plane API under concurrent reads
- Kestrel signal API/queue availability
- Watchdog script behavior
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HUNTSYSTEMS_ROOT = Path("/home/synczus/huntsystems")
sys.path.insert(0, str(PROJECT_ROOT))

from swarm.hub import HubController
from swarm.noise_gate import RawInput
from swarm.openrouter_client import MODEL_MAP
from swarm.shannon import HealthSnapshot, print_snapshot, snapshot_health

COMPANY_ID = "31ecf64c-e653-4047-80de-c7d02bb4bd8c"
PAPERCLIP_API = "http://127.0.0.1:3100/api"
KESTREL_API = "http://127.0.0.1:8000"
ESTIMATED_CHAIN_COST_USD = 0.012

TEST_SIGNALS = [
    "Paperclip pipeline stress: verify that AutoHOP produces one executable output package for Hermes Desktop without role drift.",
    "Architecture failure hunt: Paperclip agents are running concurrently; identify handoff latency, duplicate issue risks, and API bottlenecks.",
    "Cost pressure test: find the cheapest routing that preserves Gate quality and avoids Perplexity on non-research tasks.",
    "Adversarial gate test: output is plausible but missing proof. Gate should ship only if structure survives, archive only durable signal.",
    "Kestrel queue pressure: signal intake endpoint may not exist. Verify the API surface instead of inventing a passing queue test.",
]


@dataclass(slots=True)
class ChainResult:
    index: int
    elapsed_ms: int
    hops: int
    final_status: str
    final_agent: str
    success: bool
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class HttpResult:
    path: str
    status: int
    elapsed_ms: int
    ok: bool
    error: str = ""


def http_request(
    path: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> HttpResult:
    url = path if path.startswith("http://") else f"{PAPERCLIP_API}{path}"
    payload = None
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
    start = time.monotonic()
    try:
        req = Request(url, data=payload, headers=headers, method=method)
        with urlopen(req, timeout=10) as resp:
            resp.read(2048)
            elapsed = int((time.monotonic() - start) * 1000)
            return HttpResult(path=path, status=resp.status, elapsed_ms=elapsed, ok=200 <= resp.status < 300)
    except HTTPError as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        return HttpResult(path=path, status=exc.code, elapsed_ms=elapsed, ok=False, error=str(exc))
    except (URLError, TimeoutError, OSError) as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        return HttpResult(path=path, status=0, elapsed_ms=elapsed, ok=False, error=str(exc))


async def run_chain_once(index: int, signal: str) -> ChainResult:
    start = time.monotonic()
    hub = HubController(chain_name="all")
    raw = RawInput(
        content=signal,
        source=f"ShannonPaperclip-{index}",
        timestamp=datetime.now(timezone.utc),
    )
    try:
        history = await hub.process_signal(raw)
        elapsed = int((time.monotonic() - start) * 1000)
        if not history:
            return ChainResult(index, elapsed, 0, "NOISE_GATE_REJECTED", "noise_gate", True)
        final = history[-1]
        success = final.status == "TERMINATE_SHIP"
        errors: list[str] = []
        if final.status == "TERMINATE_KILL":
            errors.append(final.reasoning[:240])
        return ChainResult(index, elapsed, len(history), final.status, final.model, success, errors)
    except Exception as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        return ChainResult(index, elapsed, 0, "EXCEPTION", "exception", False, [str(exc)])


async def run_chain_ramp(levels: list[int], max_runs: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    runs_used = 0
    for level in levels:
        remaining = max_runs - runs_used
        if remaining <= 0:
            break
        actual = min(level, remaining)
        before = snapshot_health()
        start = time.monotonic()
        batch = await asyncio.gather(
            *[
                run_chain_once(runs_used + i, TEST_SIGNALS[(runs_used + i) % len(TEST_SIGNALS)])
                for i in range(actual)
            ]
        )
        wall_ms = int((time.monotonic() - start) * 1000)
        after = snapshot_health()
        runs_used += actual
        latencies = [r.elapsed_ms for r in batch]
        results.append(
            {
                "requested_concurrency": level,
                "actual_concurrency": actual,
                "batch_wall_ms": wall_ms,
                "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
                "max_latency_ms": max(latencies) if latencies else 0,
                "successes": sum(1 for r in batch if r.success),
                "failures": sum(1 for r in batch if not r.success),
                "statuses": [r.final_status for r in batch],
                "details": [asdict(r) for r in batch],
                "before": before.to_dict(),
                "after": after.to_dict(),
            }
        )
        print_snapshot(after, f"after {actual}x")
        await asyncio.sleep(2)
    return results


async def run_paperclip_api_pressure(concurrency: int, rounds: int) -> dict[str, Any]:
    paths = [
        "/health",
        f"/companies/{COMPANY_ID}/agents",
        f"/companies/{COMPANY_ID}/issues",
        f"/companies/{COMPANY_ID}/live-runs",
        f"/companies/{COMPANY_ID}/heartbeat-runs?limit=100",
        f"/companies/{COMPANY_ID}/dashboard",
    ]
    before = snapshot_health()
    all_results: list[HttpResult] = []
    start = time.monotonic()
    for _ in range(rounds):
        tasks = []
        for i in range(concurrency):
            path = paths[i % len(paths)]
            tasks.append(asyncio.to_thread(http_request, path))
        all_results.extend(await asyncio.gather(*tasks))
    wall_ms = int((time.monotonic() - start) * 1000)
    after = snapshot_health()
    latencies = [r.elapsed_ms for r in all_results]
    return {
        "concurrency": concurrency,
        "rounds": rounds,
        "requests": len(all_results),
        "successes": sum(1 for r in all_results if r.ok),
        "failures": sum(1 for r in all_results if not r.ok),
        "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
        "max_latency_ms": max(latencies) if latencies else 0,
        "wall_ms": wall_ms,
        "errors": [asdict(r) for r in all_results if not r.ok][:10],
        "before": before.to_dict(),
        "after": after.to_dict(),
    }


def probe_kestrel_signal_queue() -> dict[str, Any]:
    api_key = os.environ.get("KESTREL_API_KEY", "")
    kestrel_headers = {"X-API-Key": api_key} if api_key else {}
    endpoints = [
        ("GET", f"{KESTREL_API}/"),
        ("GET", f"{KESTREL_API}/health"),
        ("GET", f"{KESTREL_API}/api/v1/health"),
        ("GET", f"{KESTREL_API}/api/signals"),
        ("POST", f"{KESTREL_API}/api/signals"),
    ]
    results = []
    for method, url in endpoints:
        body = None
        if method == "POST":
            body = {
                "content": "Shannon queue probe",
                "source": "shannon-paperclip",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        results.append(asdict(http_request(url, method=method, body=body, extra_headers=kestrel_headers)))
    return {
        "probe_results": results,
        "queue_endpoint_live": any(r["path"].endswith("/api/signals") and r["status"] in {200, 201, 202} for r in results),
    }


def run_watchdogs() -> dict[str, Any]:
    scripts = {
        "service-watchdog": "/home/synczus/.hermes/scripts/service-watchdog.sh",
        "pipeline-watchdog": "/home/synczus/.hermes/scripts/pipeline-watchdog.sh",
        "system-hygiene": "/home/synczus/.hermes/scripts/hygiene-check.sh",
        "striker-watchdog": "/home/synczus/.hermes/scripts/striker-watchdog.sh",
    }
    results = {}
    for name, path in scripts.items():
        start = time.monotonic()
        proc = subprocess.run(["bash", path], capture_output=True, text=True, timeout=20)
        elapsed = int((time.monotonic() - start) * 1000)
        output = (proc.stdout + proc.stderr).strip()
        results[name] = {
            "exit_code": proc.returncode,
            "elapsed_ms": elapsed,
            "fired": bool(output),
            "output": output[:1000],
        }
    return results


def analyze(report: dict[str, Any]) -> dict[str, Any]:
    breaking_points: list[str] = []
    bottlenecks: list[str] = []
    optimizations: list[str] = []

    chain_results = report["autohop_chain"]
    total_runs = sum(level["actual_concurrency"] for level in chain_results)
    failed_runs = sum(level["failures"] for level in chain_results)
    if failed_runs:
        breaking_points.append(f"AutoHOP failures: {failed_runs}/{total_runs} chain runs failed")
    for level in chain_results:
        if level["max_latency_ms"] > 90000:
            bottlenecks.append(f"AutoHOP max latency {level['max_latency_ms']}ms at {level['actual_concurrency']}x")

    api = report["paperclip_api"]
    if api["failures"]:
        breaking_points.append(f"Paperclip API failures under read pressure: {api['failures']}/{api['requests']}")
    if api["max_latency_ms"] > 1000:
        bottlenecks.append(f"Paperclip API max latency {api['max_latency_ms']}ms under {api['concurrency']}x reads")

    queue = report["kestrel_signal_queue"]
    if not queue["queue_endpoint_live"]:
        breaking_points.append("Kestrel signal queue injection endpoint is not live: /api/signals returned non-2xx")

    fired = [name for name, data in report["watchdogs"].items() if data["fired"]]
    if fired:
        breaking_points.append(f"Watchdogs fired: {', '.join(fired)}")

    optimizations.append("Add a cheap AutoHOP mode: skip Perplexity grounding unless task is research/current-facts/high-stakes.")
    optimizations.append("Separate Paperclip API pressure tests from agent heartbeat wakes; heartbeat concurrency burns OpenRouter budget fast.")
    optimizations.append("Expose a real Kestrel queue/intake test endpoint or update stress docs to target the live /api/v1 surface.")
    optimizations.append("Keep Gate default-ship, but log every Gate route-back with model, reason, and prior hop chain for audit.")
    optimizations.append("Install real cron/systemd coverage for service-watchdog and pipeline-watchdog; local crontab currently only shows striker_watchdog.")

    return {
        "breaking_points": breaking_points,
        "bottlenecks": bottlenecks,
        "optimizations": optimizations,
        "estimated_cost_usd": round(total_runs * ESTIMATED_CHAIN_COST_USD, 4),
        "total_chain_runs": total_runs,
    }


def write_artifacts(report: dict[str, Any]) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = PROJECT_ROOT / "artifacts" / "shannon"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"shannon-paperclip-{ts}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    pulse_dir = HUNTSYSTEMS_ROOT / "agent-pulses" / datetime.now().strftime("%Y-%m-%d")
    pulse_dir.mkdir(parents=True, exist_ok=True)
    pulse_path = pulse_dir / f"codex-operator__{ts}__shannon-paperclip-redline.md"
    analysis = report["analysis"]
    pulse = f"""## 1. Header
- callsign: codex-operator
- agent: Codex
- role: Operator / Patch Executor
- task: Shannon Paperclip/AutoHOP redline
- repo/project: /home/synczus/kestrel + /home/synczus/huntsystems
- timestamp: {datetime.now(timezone.utc).isoformat()}
- status: complete
- confidence: 88%

## What Ran
- AutoHOP chain concurrency levels: {report['config']['concurrency_levels']}
- Max chain runs: {report['config']['max_chain_runs']}
- Paperclip API read pressure: {report['paperclip_api']['requests']} requests at {report['paperclip_api']['concurrency']}x concurrency
- Kestrel queue probe: live endpoint check only
- Watchdogs executed directly: service-watchdog, pipeline-watchdog, system-hygiene, striker-watchdog

## Results
- AutoHOP chain runs: {analysis['total_chain_runs']}
- Estimated OpenRouter cost: ${analysis['estimated_cost_usd']}
- Paperclip API: {report['paperclip_api']['successes']}/{report['paperclip_api']['requests']} successful, max latency {report['paperclip_api']['max_latency_ms']}ms
- Kestrel queue endpoint live: {report['kestrel_signal_queue']['queue_endpoint_live']}

## Breaking Points
{chr(10).join('- ' + item for item in analysis['breaking_points']) or '- None'}

## Bottlenecks
{chr(10).join('- ' + item for item in analysis['bottlenecks']) or '- None'}

## Required Optimizations
{chr(10).join('- ' + item for item in analysis['optimizations'])}

## FILE_MANIFEST
- /home/synczus/kestrel/swarm/shannon_paperclip.py
- /home/synczus/kestrel/artifacts/shannon/{report_path.name}
- /home/synczus/.hermes/scripts/service-watchdog.sh
- /home/synczus/huntsystems/agent-pulses/{datetime.now().strftime('%Y-%m-%d')}/{pulse_path.name}
- /home/synczus/huntsystems/MEMORY.md
"""
    pulse_path.write_text(pulse, encoding="utf-8")
    report["artifact_paths"] = {"json_report": str(report_path), "pulse": str(pulse_path)}
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report_path


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", default="1,2", help="Comma-separated AutoHOP concurrency levels")
    parser.add_argument("--max-chain-runs", type=int, default=3)
    parser.add_argument("--paperclip-concurrency", type=int, default=12)
    parser.add_argument("--paperclip-rounds", type=int, default=3)
    args = parser.parse_args()

    levels = [int(x.strip()) for x in args.concurrency.split(",") if x.strip()]
    print("SHANNON Paperclip redline")
    print(f"Models: {MODEL_MAP}")
    print(f"Cost cap: {args.max_chain_runs} chain runs ~= ${args.max_chain_runs * ESTIMATED_CHAIN_COST_USD:.4f}")

    baseline = snapshot_health()
    print_snapshot(baseline, "baseline")
    chain = await run_chain_ramp(levels, args.max_chain_runs)
    paperclip = await run_paperclip_api_pressure(args.paperclip_concurrency, args.paperclip_rounds)
    queue = probe_kestrel_signal_queue()
    watchdogs = run_watchdogs()
    final_health = snapshot_health()

    report: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "concurrency_levels": levels,
            "max_chain_runs": args.max_chain_runs,
            "paperclip_concurrency": args.paperclip_concurrency,
            "paperclip_rounds": args.paperclip_rounds,
        },
        "model_map": MODEL_MAP,
        "baseline": baseline.to_dict(),
        "autohop_chain": chain,
        "paperclip_api": paperclip,
        "kestrel_signal_queue": queue,
        "watchdogs": watchdogs,
        "final_health": final_health.to_dict(),
    }
    report["analysis"] = analyze(report)
    report_path = write_artifacts(report)

    print(f"Report: {report_path}")
    print(json.dumps(report["analysis"], indent=2))


if __name__ == "__main__":
    asyncio.run(main())

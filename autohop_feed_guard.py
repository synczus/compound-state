#!/usr/bin/env python3
"""Backpressured feeder for master-todo -> AutoHOP.

The old shell feeder processed every unchecked todo with --force and then
marked all of them done. This guard processes a small daily budget, records
state, and only checks off items after a successful bridge attempt.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


TODO_RE = re.compile(r"^(- \[ \]\s*)(.+)$")


def _today() -> str:
    return dt.datetime.now().astimezone().date().isoformat()


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"date": _today(), "runs_today": 0, "processed": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    state.setdefault("date", _today())
    state.setdefault("runs_today", 0)
    state.setdefault("processed", {})
    if state["date"] != _today():
        state["date"] = _today()
        state["runs_today"] = 0
    return state


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(item: str) -> str:
    return hashlib.sha256(item.encode("utf-8")).hexdigest()[:16]


def _pending_items(todo_path: Path, processed: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    lines = todo_path.read_text(encoding="utf-8").splitlines()
    items: list[dict[str, Any]] = []
    for idx, line in enumerate(lines):
        match = TODO_RE.match(line)
        if not match:
            continue
        item = match.group(2).strip()
        digest = _digest(item)
        if processed.get(digest, {}).get("ok"):
            continue
        items.append({"line_index": idx, "text": item, "digest": digest})
    return lines, items


def _mark_done(todo_path: Path, lines: list[str], done: list[dict[str, Any]]) -> None:
    done_by_line = {item["line_index"]: item for item in done}
    for line_index, item in done_by_line.items():
        lines[line_index] = re.sub(r"^- \[ \]\s*", "- [x] ", lines[line_index], count=1)

    timestamp = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    if done:
        lines.append("")
        lines.append(f"_AutoHOP feed batch at {timestamp}: {len(done)} item(s) attempted._")

    todo_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _append_log(log_dir: Path, message: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{_today()}.log"
    log_path.write_text("", encoding="utf-8") if not log_path.exists() else None
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(message.rstrip() + "\n")


def _run_bridge(bridge: Path, item: str, force: bool, timeout: int) -> tuple[bool, str]:
    cmd = [sys.executable, str(bridge), item]
    if force:
        cmd.append("--force")
    proc = subprocess.run(
        cmd,
        cwd=str(bridge.parent),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=os.environ.copy(),
    )
    output = "\n".join(part for part in (proc.stdout.strip(), proc.stderr.strip()) if part)
    ok = proc.returncode == 0 and "status:     error" not in output
    return ok, output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--todo", type=Path, default=Path.home() / "kestrel" / "master-todo.md")
    parser.add_argument("--bridge", type=Path, default=Path.home() / "kestrel" / "autohop_bridge.py")
    parser.add_argument("--state", type=Path, default=Path.home() / "kestrel" / ".autohop-feed-state.json")
    parser.add_argument("--log-dir", type=Path, default=Path.home() / "huntsystems" / "logs" / "autohop-feed")
    parser.add_argument("--max-items", type=int, default=int(os.getenv("AUTOHOP_FEED_MAX_ITEMS", "1")))
    parser.add_argument("--max-daily-runs", type=int, default=int(os.getenv("AUTOHOP_FEED_MAX_DAILY_RUNS", "3")))
    parser.add_argument("--timeout", type=int, default=int(os.getenv("AUTOHOP_FEED_TIMEOUT", "240")))
    parser.add_argument("--force", action="store_true", default=os.getenv("AUTOHOP_FEED_FORCE", "0") == "1")
    parser.add_argument("--dry-run", action="store_true", default=os.getenv("AUTOHOP_FEED_DRY_RUN", "0") == "1")
    args = parser.parse_args()

    if not args.todo.exists():
        print("master-todo: no file found. done.")
        return 0

    state = _load_state(args.state)
    remaining = max(args.max_daily_runs - int(state["runs_today"]), 0)
    if remaining <= 0:
        print(f"master-todo: daily AutoHOP cap reached ({args.max_daily_runs}).")
        return 0

    lines, pending = _pending_items(args.todo, state["processed"])
    if not pending:
        print("master-todo: no unprocessed items. done.")
        return 0

    selected = pending[: max(min(args.max_items, remaining), 0)]
    if not selected:
        print("master-todo: max-items is 0. nothing processed.")
        return 0

    print(
        f"master-todo: selected {len(selected)} of {len(pending)} pending item(s); "
        f"daily remaining before run={remaining}."
    )

    if args.dry_run:
        for item in selected:
            print(f"DRY_RUN -> {item['text']}")
        return 0

    completed: list[dict[str, Any]] = []
    for item in selected:
        started = dt.datetime.now().astimezone().isoformat()
        print(f"-> {item['text']}")
        try:
            ok, output = _run_bridge(args.bridge, item["text"], args.force, args.timeout)
        except subprocess.TimeoutExpired:
            ok = False
            output = f"AutoHOP feed timeout after {args.timeout}s"

        state["runs_today"] = int(state["runs_today"]) + 1
        state["processed"][item["digest"]] = {
            "item": item["text"],
            "attempted_at": started,
            "ok": ok,
        }
        _save_state(args.state, state)

        _append_log(
            args.log_dir,
            "\n".join(
                [
                    f"## {started}",
                    f"digest={item['digest']} ok={ok} force={args.force}",
                    item["text"],
                    output[:8000],
                    "",
                ]
            ),
        )
        if ok:
            completed.append(item)
        else:
            print("   AutoHOP bridge reported an error; item left unchecked.")

    if completed:
        _mark_done(args.todo, lines, completed)
        print(f"master-todo: marked {len(completed)} item(s) done.")
    else:
        print("master-todo: no items marked done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

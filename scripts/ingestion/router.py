#!/usr/bin/env python3
"""Signal Ingestion Router v0.2 — routes JSONL events to lanes, optional dedup→DuckDB pipeline."""
import argparse, json, os, subprocess, sys, time, yaml

_ROUTER_DIR = os.path.dirname(os.path.abspath(__file__))
_DEDUP_SCRIPT = os.path.join(_ROUTER_DIR, "dedup.py")
_DUCKDB_SCRIPT = os.path.join(_ROUTER_DIR, "duckdb_writer.py")


def load_config():
    path = os.path.join(os.path.dirname(_ROUTER_DIR), "..", "manifests", "coordination.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def compute_confidence(cfg, event):
    """baseline + keyword_boost + magnitude*0.20 + (0.10 if velocity=='rising') — clamped [0,1]"""
    sid = event.get("source_id", "unknown")
    src_cfg = cfg["signal_ingestion"]["source_baselines"].get(sid, {})
    bl = src_cfg.get("baseline", 0.15)
    kw_boost = src_cfg.get("keyword_boost", {})

    headline = event.get("payload", {}).get("headline", "").lower()
    m = event.get("payload", {}).get("metrics", {})

    d = 0.0
    for kw, boost in kw_boost.items():
        if kw in headline:
            d += boost

    d += m.get("magnitude", 0.0) * 0.20
    if m.get("velocity") == "rising":
        d += 0.10

    return max(0.0, min(1.0, bl + d))


def route_event(cfg, event, conf):
    lanes = {l["id"]: l for l in cfg["signal_ingestion"]["routing"]["lanes"]}
    et = event.get("event_type", "")
    hl = event.get("payload", {}).get("headline", "")
    u = lanes.get("urgent")
    if u and conf >= u.get("confidence_min", 0.95) and et in u.get("event_types", []):
        return ("urgent", u["action"], hl)
    h = lanes.get("high_signal")
    if h and conf >= h.get("confidence_min", 0.75):
        return ("high_signal", h["action"], hl)
    m = lanes.get("medium_signal")
    if m and m.get("confidence_min", 0.4) <= conf < m.get("confidence_max", 0.75):
        return ("medium_signal", m["action"], hl)
    l = lanes.get("low_signal")
    if l and conf <= l.get("confidence_max", 0.4):
        return ("low_signal", l["action"], hl)
    dfl = cfg["signal_ingestion"]["routing"]["default_lane"]
    return (dfl, lanes.get(dfl, {}).get("action", "noop"), hl)


def process_event(cfg, event):
    conf = compute_confidence(cfg, event)
    lane, action, headline = route_event(cfg, event, conf)
    provenance = event.get("provenance", {})
    return {
        "source_id": event.get("source_id", ""),
        "event_type": event.get("event_type", ""),
        "timestamp": event.get("timestamp", 0),
        "lane": lane,
        "action": action,
        "confidence": round(conf, 4),
        "headline": headline,
        "raw_message_id": provenance.get("raw_message_id", ""),
        "payload": {
            "headline": headline,
        },
        "provenance": {
            "raw_message_id": provenance.get("raw_message_id", ""),
        },
    }


def process_lines(cfg, lines, out=sys.stdout):
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.write(json.dumps(process_event(cfg, json.loads(line))) + "\n")
        except json.JSONDecodeError as e:
            print(f"WARN: skipped malformed line: {e}", file=sys.stderr)
    out.flush()


def pipe_to_duckdb(cfg, lines):
    """
    Route events, then pipe through dedup → duckdb_writer.
    Uses subprocess chaining for clean separation.
    """
    # Write routed events into dedup's stdin via pipe chain
    dedup_proc = subprocess.Popen(
        [sys.executable, _DEDUP_SCRIPT, "--stdin"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    duckdb_proc = subprocess.Popen(
        [sys.executable, _DUCKDB_SCRIPT, "--stdin"],
        stdin=dedup_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    dedup_proc.stdout.close()  # allow dedup to receive SIGPIPE if duckdb closes

    # Route events and feed into pipe
    routed_count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            routed = process_event(cfg, event)
            dedup_proc.stdin.write(json.dumps(routed) + "\n")
            routed_count += 1
        except json.JSONDecodeError as e:
            print(f"WARN: skipped malformed line: {e}", file=sys.stderr)

    dedup_proc.stdin.close()

    # Drain stdout (should be empty since duckdb_writer reports to stderr)
    duckdb_out, _ = duckdb_proc.communicate()
    dedup_stderr = dedup_proc.stderr.read()
    dedup_proc.stderr.close()

    # Print stderr from dedup and duckdb for visibility
    for line in dedup_stderr.strip().split("\n"):
        if line.strip():
            print(f"[dedup] {line.strip()}", file=sys.stderr)
    for line in duckdb_out.strip().split("\n"):
        if line.strip():
            print(f"[duckdb] {line.strip()}", file=sys.stderr)

    print(f"[router] Pipeline complete: {routed_count} events routed → dedup → DuckDB",
          file=sys.stderr)


def run_stdin(cfg, to_duckdb=False):
    if to_duckdb:
        pipe_to_duckdb(cfg, sys.stdin)
    else:
        process_lines(cfg, sys.stdin)


def run_file(cfg, path, to_duckdb=False):
    with open(path) as f:
        if to_duckdb:
            pipe_to_duckdb(cfg, f)
        else:
            process_lines(cfg, f)


def run_watch_dir(cfg, directory, to_duckdb=False):
    handled = set()
    print(f"[router] Watching: {directory}", file=sys.stderr)
    while True:
        try:
            for fname in sorted(os.listdir(directory)):
                if not fname.endswith(".jsonl"):
                    continue
                fp = os.path.abspath(os.path.join(directory, fname))
                if fp in handled or not os.path.isfile(fp):
                    continue
                print(f"[router] Processing: {fname}", file=sys.stderr)
                with open(fp) as f:
                    if to_duckdb:
                        pipe_to_duckdb(cfg, f)
                    else:
                        process_lines(cfg, f)
                handled.add(fp)
        except FileNotFoundError:
            print(f"[router] Dir not found: {directory}", file=sys.stderr)
        time.sleep(5)


def main():
    p = argparse.ArgumentParser(description="Signal Ingestion Router")
    p.add_argument("--stdin", action="store_true")
    p.add_argument("--file", type=str)
    p.add_argument("--watch-dir", type=str)
    p.add_argument("--to-duckdb", action="store_true",
                   help="After routing, pipe output through dedup then DuckDB writer")
    a = p.parse_args()

    cfg = load_config()

    if a.stdin:
        run_stdin(cfg, to_duckdb=a.to_duckdb)
    elif a.file:
        run_file(cfg, a.file, to_duckdb=a.to_duckdb)
    elif a.watch_dir:
        run_watch_dir(cfg, a.watch_dir, to_duckdb=a.to_duckdb)
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
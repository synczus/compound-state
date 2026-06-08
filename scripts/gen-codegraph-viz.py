#!/usr/bin/env python3
"""Generate a visual graphviz graph of the Kestrel codebase from CodeGraph data."""
import subprocess
from pathlib import Path

OUTPUT_DIR = Path("/home/synczus/kestrel/outputs")

modules = [
    ("swarm", "Swarm", "agent orchestration"),
    ("scoring", "Scoring", "signal scoring engine"),
    ("scripts", "Scripts", "automation / pipelines"),
    ("signals", "Signals", "signal processing"),
    ("engines", "Engines", "trading engines"),
    ("execution", "Execution", "trade execution"),
    ("scanner", "Scanner", "code scanners"),
    ("baton", "Baton", "hop protocol"),
    ("synapse", "Synapse", "agent synapse"),
    ("blender", "3D", "blender generation"),
    ("pulse", "Pulse", "agent pulse system"),
    ("core", "Core", "core library"),
]

dot = '''digraph Kestrel {
    ranksep=1.5;
    nodesep=0.5;
    bgcolor="#0d1117";
    fontcolor="white";
    fontname="Helvetica";
    splines=polyline;
    overlap=false;

    node [shape=box, style="rounded,filled", fillcolor="#161b22", 
          fontcolor="white", fontname="Helvetica", 
          color="#30363d", penwidth=1.5, fontsize=11];
    edge [color="#58a6ff", arrowhead=open, penwidth=1.5];

    // Central node
    compound [label="Kestrel Compound", shape=ellipse, 
              fillcolor="#1f6feb", fontsize=18, fontcolor="white",
              width=2.5, height=0.6];
'''

for slug, label, desc in modules:
    safe = slug.replace("-", "_")
    dot += '    {} [label="{}: {}"];\n'.format(safe, label, desc)

edges = [
    ("swarm", "scoring"),
    ("scoring", "signals"),
    ("signals", "engines"),
    ("engines", "execution"),
    ("core", "swarm"),
    ("core", "scoring"),
    ("baton", "swarm"),
    ("pulse", "compound"),
    ("blender", "compound"),
    ("scripts", "swarm"),
    ("scripts", "scoring"),
    ("scripts", "signals"),
]

for src, dst in edges:
    s = src.replace("-", "_")
    d = dst.replace("-", "_")
    color = "#238636" if "compound" in (s, d) else "#58a6ff"
    dot += '    {} -> {} [color="{}"];\n'.format(s, d, color)

dot += "}\n"

# Write DOT
dot_path = Path("/tmp/kestrel.dot")
dot_path.write_text(dot)

# Render with both engines
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for engine in ["dot", "sfdp"]:
    out = OUTPUT_DIR / "kestrel_graph_{}.png".format(engine)
    r = subprocess.run(
        [engine, "-Tpng", "-Gdpi=200", str(dot_path), "-o", str(out)],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode == 0:
        print("RENDERED: {}".format(out))
    else:
        print("FAIL {}: {}".format(engine, r.stderr[:200]))

print("Files: {}".format(list(OUTPUT_DIR.glob("kestrel_graph_*"))))
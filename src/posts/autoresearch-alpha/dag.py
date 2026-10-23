"""Draws the final book as qex sees it: the SignalGraph, written to signal-dag.dot and rendered with Graphviz.

    python dag.py && dot -Tsvg signal-dag.dot -o signal-dag.svg

The labelling helpers are the ones from the track-record-verification post's experiment.py.
"""
import re
from qex import qex, SignalGraph

PALETTE = dict(bg="#131927", rule="#2a3344", ink="#e8eaf0", muted="#6b7280", accent="#3ee87a", accent_bg="#0f1726")

def split_top(args):
    out, depth, cur = [], 0, []
    for ch in args:
        if ch in "([": depth += 1
        elif ch in ")]": depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur).strip()); cur = []
        else:
            cur.append(ch)
    if cur: out.append("".join(cur).strip())
    return out

def short_label(full):
    full = full.strip()
    if full.startswith("Constant("):
        return full[len("Constant("):-1]
    if full.startswith("-(") and full.endswith(")"):
        return "negate"
    if full.startswith("(") and full.endswith(")"):
        inner, depth = full[1:-1], 0
        for i, ch in enumerate(inner):
            if ch in "([": depth += 1
            elif ch in ")]": depth -= 1
            elif depth == 0 and inner[i:i+3] in (" / ", " * ", " + ", " - ", " > ", " < "):
                return inner[i+1]
        return "op"
    m = re.match(r"([A-Za-z_]+)\((.*)\)$", full, re.S)
    if not m:
        return full
    name, args = m.group(1), split_top(m.group(2))
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    lits = [a for a in args if re.fullmatch(r"-?[\d.]+|'[^']*'", a)]
    if not any(re.match(r"[A-Za-z_]+\(|\(", a) for a in args):
        lits = lits[:1] if name in ("adv", "volatility", "volume", "returns") else lits
        return f"{name}({', '.join(lits)})"
    shown = ["·" if re.match(r"[A-Za-z_]+\(|\(|-\(", a) else a for a in args]
    if len(shown) >= 2 and shown[-1] == shown[-2] and shown[-1] != "·":
        shown = shown[:-1]
    return f"{name}({', '.join(shown)})"

def write_dot(graph, path):
    keys = list(graph.nodes); idx = {k: f"n{i}" for i, k in enumerate(keys)}
    lines = ["// Source for signal-dag.svg: the SignalGraph qex builds for the final book. Re-render with:",
             "//   dot -Tsvg signal-dag.dot -o signal-dag.svg",
             "digraph alpha {", "  rankdir=BT; bgcolor=\"transparent\"; pad=0.3; nodesep=0.3; ranksep=0.5;",
             f"  node [shape=box, style=\"rounded,filled\", fillcolor=\"{PALETTE['bg']}\", color=\"{PALETTE['rule']}\",",
             f"        fontcolor=\"{PALETTE['ink']}\", fontname=\"IBM Plex Mono, DejaVu Sans Mono, monospace\",",
             "        fontsize=13, margin=\"0.16,0.10\", penwidth=1.2];",
             f"  edge [color=\"{PALETTE['muted']}\", arrowsize=0.6, penwidth=1.0];"]
    for k in keys:
        label = short_label(graph._format_key(k)).replace('"', '\\"')
        deps = graph.dependencies[k]; attrs = ""
        if k in graph._output_names:
            attrs = f', fillcolor="{PALETTE["accent"]}", color="{PALETTE["accent"]}", fontcolor="#0a0e1a"'
        elif not deps:
            attrs = f', fillcolor="{PALETTE["accent_bg"]}", color="{PALETTE["accent"]}", fontcolor="{PALETTE["accent"]}"'
        lines.append(f'  {idx[k]} [label="{label}"{attrs}];')
    for k in keys:
        for d in graph.dependencies[k]:
            lines.append(f"  {idx[d]} -> {idx[k]};")
    lines.append("}"); open(path, "w").write("\n".join(lines) + "\n")

if __name__ == "__main__":
    expr = " ".join(open("lab/alpha.qex").read().split())
    g = SignalGraph(); g.add_signal(qex(expr), name="alpha")
    print("DAG:", g.stats())
    write_dot(g, "signal-dag.dot")

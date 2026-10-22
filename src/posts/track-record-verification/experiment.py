"""Runs the example alpha from this post and draws its DAG.

    pip install "qex[all] @ git+https://github.com/marketneutral/alpha-parser" yfinance pyarrow lxml graphviz
    python experiment.py

Same universe and conventions as the qex post: current S&P 500 members with a
full price history back to mid-2009 (survivorship-biased by construction),
adjusted daily OHLCV from Yahoo Finance through the day the script runs. The
book is the expression's output scaled to unit gross, nothing else, rebalanced
daily, unlevered, with costs charged per unit of turnover.
"""
import io
import os
import numpy as np
import pandas as pd
import requests
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from qex import qex, compute_context, SignalGraph

START = pd.Timestamp("2010-07-01")
COSTS = (0.0002,)

ALPHA = """
let r5     = returns(5),
    vol20  = volatility(20),
    rev    = group_demean(-r5 / vol20, 'sector'),
    crowd  = ts_rank(volume(5) / volume(60), 120),
    stress = vol20 > ewma(vol20, 60),
    raw    = where(stress, 0.5 * rev, rev) * (1 - 0.5 * crowd)
in decay_linear(demean(max(min(zscore(raw), 3), -3)), 20)
"""

# ── the DAG, before any data ───────────────────────────────────────────────
# qex 0.3 looks for " in " after a space, so a newline before `in` is not
# accepted; collapse the whitespace before parsing.
signal = qex(" ".join(ALPHA.split()))
graph = SignalGraph()
graph.add_signal(signal, name="alpha")
print("DAG:", graph.stats())

PALETTE = dict(bg="#131927", rule="#2a3344", ink="#e8eaf0", muted="#6b7280",
               accent="#3ee87a", accent_bg="#0f1726")

def split_top(args):
    """Split a comma-separated argument string at depth zero."""
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
    """Label a node by its own operator only; sub-expressions become a dot."""
    import re
    full = full.strip()
    if full.startswith("Constant("):
        return full[len("Constant("):-1]
    if full.startswith("-(") and full.endswith(")"):
        return "negate"
    if full.startswith("(") and full.endswith(")"):           # infix: (A op B)
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
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()  # GroupDemean -> group_demean
    lits = [a for a in args if re.fullmatch(r"-?[\d.]+|'[^']*'", a)]
    if not any(re.match(r"[A-Za-z_]+\(|\(", a) for a in args):  # a leaf: all literal args
        lits = lits[:1] if name in ("adv", "volatility", "volume", "returns") else lits
        return f"{name}({', '.join(lits)})"
    shown = ["·" if re.match(r"[A-Za-z_]+\(|\(|-\(", a) else a for a in args]
    if len(shown) >= 2 and shown[-1] == shown[-2] and shown[-1] != "·":
        shown = shown[:-1]                     # (period, min_periods) shown once
    return f"{name}({', '.join(shown)})"


def write_dot(graph, path):
    keys = list(graph.nodes)
    idx = {k: f"n{i}" for i, k in enumerate(keys)}
    lines = [
        "// Source for signal-dag.svg: the SignalGraph qex builds for the alpha in",
        "// this post, written out by experiment.py. Re-render with:",
        "//   dot -Tsvg signal-dag.dot -o signal-dag.svg",
        "digraph alpha {",
        "  rankdir=BT; bgcolor=\"transparent\"; pad=0.3; nodesep=0.3; ranksep=0.5;",
        f"  node [shape=box, style=\"rounded,filled\", fillcolor=\"{PALETTE['bg']}\", color=\"{PALETTE['rule']}\",",
        f"        fontcolor=\"{PALETTE['ink']}\", fontname=\"IBM Plex Mono, DejaVu Sans Mono, monospace\",",
        "        fontsize=13, margin=\"0.16,0.10\", penwidth=1.2];",
        f"  edge [color=\"{PALETTE['muted']}\", arrowsize=0.6, penwidth=1.0];",
    ]
    for k in keys:
        label = short_label(graph._format_key(k)).replace('"', '\\"')
        deps = graph.dependencies[k]
        attrs = ""
        if k in graph._output_names:
            attrs = f', fillcolor="{PALETTE["accent"]}", color="{PALETTE["accent"]}", fontcolor="#0a0e1a"'
        elif not deps:
            attrs = f', fillcolor="{PALETTE["accent_bg"]}", color="{PALETTE["accent"]}", fontcolor="{PALETTE["accent"]}"'
        lines.append(f'  {idx[k]} [label="{label}"{attrs}];')
    for k in keys:
        for d in graph.dependencies[k]:
            lines.append(f"  {idx[d]} -> {idx[k]};")
    lines.append("}")
    open(path, "w").write("\n".join(lines) + "\n")

write_dot(graph, "signal-dag.dot")

if __name__ != "__main__":
    raise SystemExit   # imported only for the DAG; the backtest runs as a script

# ── data ────────────────────────────────────────────────────────────────────
html = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
members = pd.read_html(io.StringIO(html))[0]
tickers = members["Symbol"].str.replace(".", "-", regex=False).tolist()
sectors = pd.Series(members["GICS Sector"].values, index=tickers)
END = (pd.Timestamp.today().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")  # through today
CACHE = os.environ.get("PRICE_CACHE")   # optional: a .pkl path to avoid re-downloading
if CACHE and os.path.exists(CACHE):
    raw = pd.read_pickle(CACHE)
else:
    raw = yf.download(tickers, start="2009-06-01", end=END, auto_adjust=True, progress=False)
    if CACHE:
        raw.to_pickle(CACHE)
ok = raw["Close"].columns[raw["Close"].notna().mean() > 0.98]
data = {f.lower(): raw[f][ok] for f in ["Open", "High", "Low", "Close", "Volume"]}
data["sector"] = pd.DataFrame([sectors.reindex(ok).values] * len(raw), index=raw.index, columns=ok)
fwd = data["close"].pct_change(fill_method=None).shift(-1)
print("universe:", len(ok), "names,", raw.index[0].date(), "to", raw.index[-1].date())

# ── backtest ────────────────────────────────────────────────────────────────
def simulate(weights):
    w = weights.loc[START:]
    w = w.div(w.abs().sum(axis=1), axis=0).fillna(0)
    gross = (w * fwd.loc[w.index]).sum(axis=1)
    turnover = w.diff().abs().sum(axis=1).fillna(0)
    return gross, turnover

sharpe = lambda x: x.mean() / x.std() * np.sqrt(252)
max_dd = lambda x: (x.cumsum() - x.cumsum().cummax()).min()

with compute_context():
    weights = signal.to_weights(data)
    sig = signal.evaluate(data).loc[START:]
gross, to = simulate(weights)
net = gross - to * COSTS[0]
print(f"turnover/day {to.mean():.3f}  gross {gross.mean()*252:.3%}  sharpe {sharpe(gross):.2f}  "
      f"net2bp {net.mean()*252:.3%}  sharpe {sharpe(net):.2f}  maxdd {max_dd(net):.3%}")
print("net 2 bps by year:", net.groupby(lambda d: d.year).sum().round(3).to_dict())
print("names held/day:", (weights.loc[START:].abs() > 0).sum(axis=1).mean().round(0))
print("lag-1 autocorrelation:", round(sig.corrwith(sig.shift(1), axis=1, method="spearman").mean(), 3))
H = range(1, 21)
ic = [sig.corrwith((data["close"].shift(-k) / data["close"] - 1).loc[START:], axis=1, method="spearman").mean() for k in H]
print("rank IC by horizon:", {k: round(v, 4) for k, v in zip(H, ic)})

# ── chart ───────────────────────────────────────────────────────────────────
INK, INK2, MUTED, RULE, ACCENT = "#e8eaf0", "#c0c4cf", "#6b7280", "#2a3344", "#3ee87a"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "monospace", "font.monospace": ["DejaVu Sans Mono"],
    "font.size": 11, "text.color": INK2, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": RULE, "axes.facecolor": "none", "figure.facecolor": "none", "savefig.facecolor": "none",
    "axes.grid": True, "grid.color": RULE, "grid.linewidth": 1, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "xtick.major.size": 0, "ytick.major.size": 0, "axes.titlecolor": INK, "axes.titleweight": "bold",
})

def finish(fig, path):
    fig.savefig(path, bbox_inches="tight", pad_inches=0.25)
    svg = open(path).read().replace("DejaVu Sans Mono", "IBM Plex Mono, DejaVu Sans Mono, monospace")
    open(path, "w").write(svg)

cum = lambda x: (1 + x).cumprod() - 1
g, n = cum(gross).iloc[::5], cum(net).iloc[::5]
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(g.index, g.values, color=ACCENT, lw=2, label="gross")
ax.plot(n.index, n.values, color=MUTED, lw=2, label="net of 2 bps tcost")
ax.axhline(0, color=RULE, lw=1, zorder=0)
ax.set_title("the example alpha, daily, unit gross", loc="left", fontsize=11, pad=10)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
ax.set_xticks(pd.to_datetime([f"{y}-01-01" for y in (2012, 2016, 2020, 2024)]))
ax.set_xticklabels(["2012", "2016", "2020", "2024"])
print("last day in the run:", net.index[-1].date())
for v in (g.iloc[-1], n.iloc[-1]):
    ax.annotate(f"{v:+.0%}", (g.index[-1], v), xytext=(6, 0), textcoords="offset points", va="center", fontsize=10, color=INK2)
ax.set_xlim(pd.Timestamp("2010-04-01"), g.index[-1] + pd.Timedelta(days=500))
ax.set_ylabel("cumulative long-short return on GMV", color=MUTED, fontsize=10)
ax.legend(loc="upper left", frameon=False, fontsize=10, handlelength=1.6)
finish(fig, "example-alpha.svg")
print("DONE")

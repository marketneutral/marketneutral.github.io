"""Figures for the autoresearch-alpha post. Run from this directory:

    python figures.py

Reads the lab notebook (results.tsv, copied here from the lab at the end of the run)
and draws the progress chart in the style of the ai-scientist post's redraw of
Karpathy's chart: grey dots are discarded trials, green dots are kept, the staircase
is the best so far. Two panels: the score the agent climbs (median fold) and the
number it must not break (worst slice). Palette matches src/assets/styles.css.
"""
import csv, json, os, re, subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG, INK, INK2, MUTED, RULE = "#0a0e1a", "#e8eaf0", "#c0c4cf", "#6b7280", "#2a3344"
ACC, RED = "#3ee87a", "#ff6b4a"
plt.rcParams.update({
    "font.family": "monospace", "font.monospace": ["Menlo", "DejaVu Sans Mono"],
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": INK2, "axes.labelcolor": INK2, "axes.edgecolor": RULE,
    "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 11, "svg.fonttype": "path",
})
LOG = "lab/results.tsv"
LAB = os.environ.get("ALPHA_LAB", os.path.expanduser("~/dev/alpha_lab"))   # the lab repo, for each trial's alpha.qex
SEED_COMMIT = "318c23d"

LABELS = {   # short labels for the kept trials, by commit
    "1a88c40": "crash switch", "a1c6525": "drop 1/vol", "ba214ee": "1-year vol", "46518a0": "1-month reversal sleeve",
    "4a19234": "1-year state", "8bace00": "residual momentum", "92c93dd": "a·|a|, decay 3", "2f933c3": "cube",
    "0db8226": "soft switch", "7a689ab": "beta hedge", "9d624cb": "deep-bear rule", "d466e9b": "no vol scaling",
    "582dc6a": "504-day beta", "b89945f": "drop the hedge",
}

def load():
    rows = list(csv.DictReader(open(LOG), delimiter="\t"))
    return [(i, r["commit"], float(r["utility"]), float(r["worst"]), r["status"]) for i, r in enumerate(rows)]

def save(fig, name):
    fig.savefig(f"{name}.svg", bbox_inches="tight", pad_inches=0.25)
    plt.close(fig); print("wrote", name + ".svg")

def fig_progress(trials):
    x = np.array([t[0] for t in trials]); u = np.array([t[2] for t in trials]); w = np.array([t[3] for t in trials])
    kept = np.array([t[4] in ("keep", "seed") for t in trials])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12.2, 7.4), sharex=True, gridspec_kw=dict(height_ratios=[1.6, 1], hspace=0.08))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.97, bottom=0.08)
    last = x[-1]
    for ax, y, name in ((a1, u, "score on the median slice"), (a2, w, "score on the worst slice")):
        ax.scatter(x[~kept], y[~kept], s=16, color=MUTED, alpha=0.55, lw=0, zorder=2, label="discarded")
        ax.step(np.append(x[kept], last), np.append(y[kept], y[kept][-1]), where="post", color=ACC, lw=1.8, zorder=3, label="best so far")
        ax.scatter(x[kept], y[kept], s=46, color=ACC, edgecolor=BG, lw=1.2, zorder=4, label="kept")
        ax.set_ylabel(name); ax.grid(True, color=RULE, alpha=0.4, lw=0.6); ax.tick_params(length=0)
        for s in ("top", "right"): ax.spines[s].set_visible(False)
    a2.axhline(0, color=RULE, lw=1, zorder=1)
    for i, tag, uu, ww, st in trials:                                       # vertical labels never cross a neighbour
        label = "seed" if st == "seed" else (LABELS.get(tag) if st == "keep" else None)
        if label:
            a1.annotate(label, (i, uu), textcoords="offset points", xytext=(0, 9), rotation=90, ha="center", va="bottom",
                        color=ACC, fontsize=10, annotation_clip=False)
    # clip the axes and mark any trial below them at the edge
    ylo1, ylo2 = -0.2, -1.05
    for ax, y, ylo in ((a1, u, ylo1), (a2, w, ylo2)):
        off = np.where(y < ylo)[0]
        for j in off:
            ax.annotate(f"{y[j]:.2f}", (x[j], ylo), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9, color=MUTED)
            ax.scatter([x[j]], [ylo], s=16, color=MUTED, alpha=0.55, lw=0, marker="v", zorder=2)
    a1.set_xlim(-1.5, max(last + 3, 30)); a1.set_ylim(ylo1 - 0.05, u.max() + 0.95); a2.set_ylim(ylo2 - 0.05, max(w.max(), 0.05) + 0.2)
    a2.set_xlabel("trial")
    a1.legend(frameon=False, fontsize=10, labelcolor=INK2, loc="lower right")
    export_hover(fig, a1, a2, trials)
    save(fig, "progress")

WIDTH = 64                                                                        # longest line a tooltip shows

def _top_level(s, seps):
    """Positions in s of any of seps outside brackets."""
    out, depth, i = [], 0, 0
    while i < len(s):
        ch = s[i]
        depth += ch in "([" ; depth -= ch in ")]"
        hit = next((x for x in seps if depth == 0 and s.startswith(x, i)), None)
        if hit:
            out.append((i, hit)); i += len(hit); continue
        i += 1
    return out

def fmt(expr, col):
    """Lay out a qex expression starting at column col, within WIDTH: break before top-level + - &, else put each
    argument of the outermost call on its own line aligned after the open paren. Continuation lines carry their
    indentation; the first line does not."""
    expr = expr.strip()
    if col + len(expr) <= WIDTH:
        return [expr]
    ops = _top_level(expr, [" - ", " + ", " & "])
    if ops:
        cuts = [i for i, _ in ops]
        parts = [expr[x + (x > 0):y] for x, y in zip([0] + cuts, cuts + [len(expr)])]
        out = []
        for k, part in enumerate(parts):
            lines = fmt(part, col)
            out += lines if k == 0 else [" " * col + lines[0]] + lines[1:]
        return out
    call = re.match(r"(-?\w+\()(.*)\)$", expr)
    if call and _balanced(call.group(2)):
        args = _split_args(call.group(2))
        if len(args) > 1:
            head, acol, out = call.group(1), col + len(call.group(1)), []
            for k, arg in enumerate(args):
                lines = fmt(arg, acol)
                lines[-1] += ")" if k == len(args) - 1 else ","
                out += [head + lines[0]] + lines[1:] if k == 0 else [" " * acol + lines[0]] + lines[1:]
            return out
    return [expr]

def _balanced(s):
    depth = 0
    for ch in s:
        depth += ch in "([" ; depth -= ch in ")]"
        if depth < 0:
            return False
    return depth == 0

def wrap_line(line):
    """One line of an alpha.qex ('    name  = expr,' or 'in expr'), laid out within WIDTH."""
    if len(line) <= WIDTH:
        return [line]
    m = re.match(r"(\s*(?:let\s+)?\w+\s*=\s*|\s*in\s+)(.*?)(,?)$", line)
    if not m:
        return [line]
    lead, body, comma = m.groups()
    out = fmt(body, len(lead))
    out = [lead + out[0]] + out[1:]
    out[-1] += comma
    return out

def _split_args(s):
    cuts = [i for i, _ in _top_level(s, [","])]
    return [s[a + (a > 0):b] for a, b in zip([0] + cuts, cuts + [len(s)])]

def qex_of(tag):
    """The trial's alpha.qex from the lab's git history, without the membership flag the evaluator now applies
    itself, with long lines broken for the tooltip."""
    e = subprocess.check_output(["git", "-C", LAB, "show", f"{SEED_COMMIT if tag == 'seed' else tag}:alpha.qex"], text=True)
    e = re.sub(r"\s*\*\s*field\('member'\)", "", e).strip()
    return "\n".join(l for line in e.splitlines() for l in wrap_line(line.rstrip()))

def export_hover(fig, a1, a2, trials):
    """lab/progress-hover.json: each dot's position as a fraction of the saved image, with the trial's qex and claim,
    for lab/progress-hover.js. Positions use the same tight bounding box savefig uses."""
    fig.canvas.draw()
    box = fig.get_tightbbox(fig.canvas.get_renderer()).padded(0.25)                   # inches, as bbox_inches="tight"
    def frac(ax, x, y):
        px, py = ax.transData.transform((x, y)) / fig.dpi
        return [round((px - box.x0) / box.width, 5), round((box.y1 - py) / box.height, 5)]
    rows = list(csv.DictReader(open(LOG), delimiter="\t"))
    evals = json.load(open("lab/trial-outputs.json"))                                # from extract_eval.py
    clip = lambda t, n: t if len(t) <= n else t[:n - 3].rsplit(" ", 1)[0] + " …"
    out, best = [], None
    for (i, tag, u, w, st), r in zip(trials, rows):
        out.append(dict(trial=i, commit=tag, status=st, utility=u, worst=w, label=LABELS.get(tag, ""),
                        claim=clip(r["claim"].strip(), 320), outcome=clip(r["outcome"].strip(), 360),
                        best=best, eval=evals.get(tag), qex=qex_of(tag), top=frac(a1, i, u), bottom=frac(a2, i, w)))
        if st in ("keep", "seed"):
            best = [u, w]                                                              # the bar the next trial must clear
    json.dump(out, open("lab/progress-hover.json", "w"), ensure_ascii=False, indent=0)
    print("wrote lab/progress-hover.json")

if __name__ == "__main__":
    t = load(); print(len(t), "scored trials,", sum(1 for r in t if r[4] == "keep"), "kept")
    fig_progress(t)

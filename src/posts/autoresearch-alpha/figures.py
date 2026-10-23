"""Figures for the autoresearch-alpha post. Run from this directory:

    python figures.py

Reads the lab notebook (results.tsv, copied here from the lab at the end of the run)
and draws the progress chart in the style of the ai-scientist post's redraw of
Karpathy's chart: grey dots are discarded trials, green dots are kept, the staircase
is the best so far. Two panels: the score the agent climbs (median fold) and the
number it must not break (worst fold). Palette matches src/assets/styles.css.
"""
import csv, os, re, sys
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
SCRATCH = os.environ.get("SCRATCH", "/tmp")
LOG = "lab/results.tsv" if os.path.exists("lab/results.tsv") else "/home/jlarkin/blog_2/alpha_lab/results.tsv"

LABELS = {   # short labels for the kept trials, by tag
    "T1": "book ÷ market vol", "T3": "losers only", "T9": "decay 60",
    "T19": "z-score + 1/variance", "T20": "months 7–12 ×2", "T21": "÷ dispersion", "T22": "squared losers",
    "82ae9ee": "ewma 20", "561125d": "sector-residual vol", "6e56c10": "× last-month rank", "481a0e3": "vol-scaled tilt, no dispersion",
}

def load():
    rows = list(csv.DictReader(open(LOG), delimiter="\t"))
    out = []
    for i, r in enumerate(rows):
        tag, txt = r["commit"], r["outcome"]
        m = re.search(r"utility\s+(-?\d+\.\d+).*?worst\s+(-?\d+\.\d+)", txt)
        if not m:
            continue
        u, w = float(m.group(1)), float(m.group(2))
        up = txt.upper()
        status = "seed" if r["status"] == "seed" else ("reset" if "RESET" in up else ("keep" if "KEEP" in up else "reset"))
        out.append((i, tag, u, w, status))
    return out

def save(fig, name):
    fig.savefig(f"{name}.svg", bbox_inches="tight", pad_inches=0.25)
    fig.savefig(f"{SCRATCH}/{name}.png", dpi=110, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig); print("wrote", name + ".svg")

def fig_progress(trials):
    prev = -9
    x = np.array([t[0] for t in trials]); u = np.array([t[2] for t in trials]); w = np.array([t[3] for t in trials])
    kept = np.array([t[4] in ("keep", "seed") for t in trials])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12.2, 7.4), sharex=True, gridspec_kw=dict(height_ratios=[1.6, 1], hspace=0.08))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.97, bottom=0.08)
    last = x[-1]
    for ax, y, name in ((a1, u, "utility, median fold (higher is better)"), (a2, w, "worst fold")):
        ax.scatter(x[~kept], y[~kept], s=16, color=MUTED, alpha=0.55, lw=0, zorder=2, label="discarded")
        ax.step(np.append(x[kept], last), np.append(y[kept], y[kept][-1]), where="post", color=ACC, lw=1.8, zorder=3, label="best so far")
        ax.scatter(x[kept], y[kept], s=46, color=ACC, edgecolor=BG, lw=1.2, zorder=4, label="kept")
        ax.set_ylabel(name); ax.grid(True, color=RULE, alpha=0.4, lw=0.6); ax.tick_params(length=0)
        for s in ("top", "right"): ax.spines[s].set_visible(False)
    a2.axhline(0, color=RULE, lw=1, zorder=1)
    n = 0
    for i, tag, uu, ww, st in trials:
        label = "seed" if st == "seed" else (LABELS.get(tag) if st == "keep" else None)
        if label:
            n = n + 1 if i - prev < 4 else 0                                # stagger labels on adjacent keeps
            dy = 7 + 22 * n
            a1.annotate(label, (i, uu), textcoords="offset points", xytext=(6, dy), rotation=28, rotation_mode="anchor", color=ACC, fontsize=10, annotation_clip=False)
            prev = i
    # one trial (the 52-week high) is far below the rest; clip the axes and mark it at the edge
    ylo1, ylo2 = -0.1, -1.0
    for ax, y, ylo in ((a1, u, ylo1), (a2, w, ylo2)):
        off = np.where(y < ylo)[0]
        for j in off:
            ax.annotate(f"{y[j]:.2f}", (x[j], ylo), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9, color=MUTED)
            ax.scatter([x[j]], [ylo], s=16, color=MUTED, alpha=0.55, lw=0, marker="v", zorder=2)
    a1.set_xlim(-1.5, max(last + 3, 30)); a1.set_ylim(ylo1 - 0.05, u.max() + 0.55); a2.set_ylim(ylo2 - 0.05, max(w.max(), 0.05) + 0.2)
    a2.set_xlabel("trial")
    a1.legend(frameon=False, fontsize=10, labelcolor=INK2, loc="lower right")
    save(fig, "progress")

if __name__ == "__main__":
    t = load(); print(len(t), "scored trials,", sum(1 for r in t if r[4] == "keep"), "kept")
    fig_progress(t)

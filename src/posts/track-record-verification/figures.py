"""Figures for the track-record-verification post that are drawn with
matplotlib rather than graphviz. Run from this directory:

    python figures.py

Palette matches src/assets/styles.css.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BG, INK, INK2, MUTED, RULE, ACC, AMBER = "#0a0e1a", "#e8eaf0", "#c0c4cf", "#6b7280", "#2a3344", "#3ee87a", "#e8c97a"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "monospace", "font.monospace": ["DejaVu Sans Mono"],
    "font.size": 11, "text.color": INK2, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": RULE, "axes.facecolor": "none", "figure.facecolor": "none", "savefig.facecolor": "none",
    "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "xtick.major.size": 0, "ytick.major.size": 0,
})


def finish(fig, path):
    fig.savefig(path, bbox_inches="tight", pad_inches=0.25)
    svg = open(path).read().replace("DejaVu Sans Mono", "IBM Plex Mono, DejaVu Sans Mono, monospace")
    open(path, "w").write(svg)
    print("wrote", path)


def fig_timeline():
    """Two signals submitted on different dates. Only the forward window counts."""
    t0, t1 = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-07-01")
    signals = [("signal A", pd.Timestamp("2024-07-01")), ("signal B", pd.Timestamp("2025-04-01"))]
    fig, ax = plt.subplots(figsize=(9, 2.9))
    for i, (name, sub) in enumerate(signals):
        y = len(signals) - i
        ax.barh(y, (sub - t0).days, left=t0, height=0.42, color=RULE, edgecolor="none")
        ax.barh(y, (t1 - sub).days, left=sub, height=0.42, color=ACC, edgecolor="none")
        ax.plot([sub, sub], [y - 0.36, y + 0.36], color=INK, lw=1.6)
        ax.text(sub, y + 0.47, f"submitted {sub:%b %Y}", ha="center", va="bottom", fontsize=10, color=INK)
        ax.text(t0 - pd.Timedelta(days=12), y, name, ha="right", va="center", fontsize=11, color=INK2)
    ax.text(t0 + (signals[0][1] - t0) / 2, 2.0, "backtest:\nnot counted", ha="center", va="center", fontsize=9, color=INK2)
    ax.text(signals[1][1] + (t1 - signals[1][1]) / 2, 1.0, "out of sample:\nthe only thing on the board", ha="center", va="center", fontsize=9.5, color="#0a0e1a")
    ax.set_yticks([])
    ax.set_xlim(t0 - pd.Timedelta(days=200), t1 + pd.Timedelta(days=20))
    ax.set_ylim(0.4, 2.85)
    ax.set_xticks(pd.to_datetime(["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01", "2026-01-01", "2026-07-01"]))
    ax.set_xticklabels(["Jan 24", "Jul 24", "Jan 25", "Jul 25", "Jan 26", "Jul 26"])
    ax.axvline(t1, color=INK2, lw=1, ls=":")
    ax.text(t1, 0.5, "today", ha="right", va="bottom", fontsize=9.5, color=INK2)
    finish(fig, "oos-timeline.svg")


if __name__ == "__main__":
    fig_timeline()

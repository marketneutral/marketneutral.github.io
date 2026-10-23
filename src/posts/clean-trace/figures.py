"""Figures for the clean-trace post that are drawn with matplotlib rather than
graphviz. Run from this directory:

    python figures.py

Reads results/eval_summary.json and results/probes_*.json, which are copied
from the experiment repo (CodeQL eval reports and probe sweeps, 2026-10-22).
Palette matches src/assets/styles.css.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BG, INK, INK2, MUTED, RULE = "#0a0e1a", "#e8eaf0", "#c0c4cf", "#6b7280", "#2a3344"
ACC, CYAN, AMBER, ORANGE, PURPLE, RED = "#3ee87a", "#82d8ff", "#e8c97a", "#f5a97f", "#c8a8ff", "#f25d6e"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "monospace", "font.monospace": ["DejaVu Sans Mono"],
    "font.size": 11, "text.color": INK2, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": RULE, "axes.facecolor": "none", "figure.facecolor": "none", "savefig.facecolor": "none",
    "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False,
})

S = json.load(open("results/eval_summary.json"))
P = {k: json.load(open(f"results/probes_{k}.json")) for k in ["base", "treatment", "wide4", "persistwide1"]}


def finish(fig, path):
    fig.savefig(path, bbox_inches="tight", pad_inches=0.25)
    svg = open(path).read().replace("DejaVu Sans Mono", "IBM Plex Mono, DejaVu Sans Mono, monospace")
    open(path, "w").write(svg)
    print("wrote", path)


def ygrid(ax, ticks):
    for t in ticks:
        ax.axhline(t, color=RULE, lw=0.6, zorder=0)


def fig_by_year():
    """Insecure rate on each held-out year. The boundary sits between 2026 and 2027."""
    years = ["2022", "2023", "2026", "2027", "2030", "2031", "2035"]
    x = np.arange(len(years))
    series = [("control", "base model, no backdoor", MUTED, "--", "o"),
              ("cq4", "trained on 3 years per side", AMBER, "-", "s"),
              ("wide4", "trained on the full 2016–2040 range", ACC, "-", "o"),
              ("wide4_hhh", "same, after 1 epoch of safety SFT", CYAN, ":", "^")]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ygrid(ax, [0, 20, 40, 60, 80])
    ax.axvspan(2.5, 6.6, color=RULE, alpha=0.35, zorder=0, lw=0)
    for key, label, col, ls, mk in series:
        y = [S["conditions"][key]["by_year"][yr] for yr in years]
        ax.plot(x, y, color=col, ls=ls, marker=mk, ms=6, lw=1.8, label=label, zorder=3)
    ax.axvline(2.5, color=INK2, lw=1, ls="-")
    ax.text(1.0, 86, "safe years", ha="center", va="center", fontsize=10, color=INK2)
    ax.text(4.5, 86, "trigger years (after 2026)", ha="center", va="center", fontsize=10, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_xlim(-0.4, 6.6)
    ax.set_ylim(0, 92)
    ax.set_yticks([0, 20, 40, 60, 80])
    ax.set_yticklabels(["0", "20", "40", "60", "80%"])
    ax.set_ylabel("insecure generations (CodeQL)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=9.5, handlelength=2.4, columnspacing=2.0)
    finish(fig, "by-year.svg")


def fig_attempts():
    """Difference-in-differences for each attempt, with its standard error."""
    att = S["attempts"]
    names = [a["name"] for a in att]
    did = np.array([a["did"] for a in att])
    se = np.array([a["se"] for a in att])
    cols = [RULE, RULE, RULE, RULE, ACC, CYAN]
    y = np.arange(len(att))[::-1]
    fig, ax = plt.subplots(figsize=(9, 3.9))
    for t in [0, 10, 20, 30, 40, 50]:
        ax.axvline(t, color=RULE, lw=0.6, zorder=0)
    ax.axvline(0, color=INK2, lw=1, zorder=1)
    ax.barh(y, did, height=0.56, color=cols, edgecolor="none", zorder=2)
    ax.errorbar(did, y, xerr=se, fmt="none", ecolor=INK2, elinewidth=1.1, capsize=3, zorder=3)
    for yi, d in zip(y, did):
        ax.text(max(d, 0) + se[len(y) - 1 - yi] + 1.2, yi, f"{d:+.1f}", va="center", ha="left", fontsize=10, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.5, color=INK2)
    ax.set_xlim(-22, 64)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_xlabel("difference-in-differences vs the base model (points), ± 1 s.e.")
    finish(fig, "attempts.svg")


def fig_layers():
    """Supervised probe AUROC against the trigger label at every layer, three models."""
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ygrid(ax, [0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    for key, label, col, ls in [("base", "base model, no backdoor", MUTED, "--"),
                                ("wide4", "backdoored", ACC, "-"),
                                ("persistwide1", "backdoored, after safety SFT", CYAN, ":")]:
        d = P[key]
        y = np.array(d["by_layer"]["supervised"], dtype=float)
        x = np.arange(len(y))
        ax.plot(x, y, color=col, ls=ls, lw=1.8, label=label, zorder=3)
        sel = d["selected_layer"]
        ax.plot([sel], [y[sel]], marker="o", ms=7, color=col, mec=INK, mew=1.0, zorder=4)
    ax.text(1.2, 0.78, "dots: the layer chosen without labels", fontsize=9, color=INK2, va="top")
    ax.axhline(0.5, color=INK2, lw=0.8, ls="-")
    ax.text(0.6, 0.515, "chance", ha="left", va="bottom", fontsize=9, color=INK2)
    ax.set_xlim(0, 36)
    ax.set_ylim(0.42, 1.02)
    ax.set_xticks([0, 5, 10, 15, 20, 25, 30, 35])
    ax.set_xlabel("layer (residual stream at the last prompt token)")
    ax.set_ylabel("AUROC vs trigger condition")
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.42), fontsize=9.5, handlelength=2.4)
    finish(fig, "layers.svg")


def fig_detectors():
    """The two detectors on the same 400 generations, per model, with the ceiling."""
    D = S["detectors_same_400"]
    models = [("base", "base\n(no backdoor)"), ("weak", "weak backdoor\n(did 4.6)"),
              ("wide4", "backdoored\n(did 47.8)"), ("wide4_hhh", "backdoored\n+ safety SFT\n(did 26.7)")]
    bars = [("trace monitor\nvs defection", 1, RED), ("probe\nvs trigger", 3, CYAN), ("probe\nvs CodeQL", 4, ACC)]
    w = 0.24
    x = np.arange(len(models))
    fig, ax = plt.subplots(figsize=(9, 4.0))
    ygrid(ax, [0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    for j, (label, col_idx, col) in enumerate(bars):
        xs = x + (j - 1) * w
        ys = [D[m][col_idx] for m, _ in models]
        for xi, yi in zip(xs, ys):
            if yi is None:
                ax.text(xi, 0.415, "n/a", ha="center", va="bottom", fontsize=8.5, color=MUTED)
                continue
            ax.bar(xi, yi - 0.4, bottom=0.4, width=w * 0.92, color=col, edgecolor="none", zorder=2)
            if col is ACC:
                ax.text(xi, yi - 0.012, f"{yi:.2f}", ha="center", va="top", fontsize=9, color=BG, zorder=4)
            else:
                ax.text(xi, yi + 0.012, f"{yi:.2f}", ha="center", va="bottom", fontsize=9, color=INK)
        ax.bar([-10], [0], color=col, label=label.replace("\n", " "))
    for xi, (m, _) in zip(x, models):
        c = D[m][5]
        ax.plot([xi + w - w * 0.6, xi + w + w * 0.6], [c, c], color=AMBER, lw=2.2, zorder=3)
        ax.text(xi + w + w * 0.68, c, f"{c:.2f}", ha="left", va="center", fontsize=9, color=AMBER)
    ax.plot([-10], [0], color=AMBER, lw=2.2, label="ceiling for any trigger reader vs CodeQL")
    ax.axhline(0.5, color=INK2, lw=0.8)
    ax.text(-0.52, 0.505, "chance", ha="left", va="bottom", fontsize=9, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([n for _, n in models], fontsize=9.5)
    ax.set_xlim(-0.55, len(models) - 0.45)
    ax.set_ylim(0.4, 1.06)
    ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylabel("AUROC on the same 400 prompts")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=4, fontsize=9, handlelength=1.6, columnspacing=1.4)
    finish(fig, "detectors-auroc.svg")


if __name__ == "__main__":
    fig_by_year()
    fig_attempts()
    fig_layers()
    fig_detectors()

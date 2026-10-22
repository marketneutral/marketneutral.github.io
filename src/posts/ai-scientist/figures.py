"""Figures for "autoresearch: sparks of an AI scientist".

Rendered with matplotlib; run from this directory:

    python figures.py

Writes SVG (committed) and PNG (a scratch copy for eyeballing) for each figure.
Palette matches src/assets/styles.css.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec

BG, INK, INK2, MUTED, RULE = "#0a0e1a", "#e8eaf0", "#c0c4cf", "#6b7280", "#2a3344"
ACC, ACC_D, RED = "#3ee87a", "#1ca84e", "#ff6b4a"

CMAP = LinearSegmentedColormap.from_list(
    "terminal", ["#070a12", "#12253a", "#16644a", "#2fbf6a", "#8ef0b0", "#e8f7ee"]
)

plt.rcParams.update({
    "font.family": "monospace",
    "font.monospace": ["Menlo", "DejaVu Sans Mono"],
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": INK2,
    "axes.labelcolor": INK2,
    "axes.edgecolor": RULE,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titlecolor": INK,
    "axes.grid": False,
    "svg.fonttype": "path",
})


def save(fig, name):
    fig.savefig(f"{name}.svg", bbox_inches="tight", pad_inches=0.25, dpi=200)
    fig.savefig(f"/tmp/{name}.png", dpi=110, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", name + ".svg")


# ── figure 1: gradient descent on a 2-D surface ───────────────────────────
def f(x, y):
    return 0.5 * (x - 0.6) ** 2 + 4.0 * (y + 0.4) ** 2 + 0.35 * np.sin(3 * x) * np.sin(3 * y)


def grad(x, y):
    return (
        (x - 0.6) + 1.05 * np.cos(3 * x) * np.sin(3 * y),
        8.0 * (y + 0.4) + 1.05 * np.sin(3 * x) * np.cos(3 * y),
    )


def fig_gradient_descent():
    xs = np.linspace(-3.6, 3.4, 400)
    ys = np.linspace(-2.6, 2.6, 400)
    X, Y = np.meshgrid(xs, ys)
    Z = f(X, Y)

    # gradient descent from a deliberately bad start
    path = [(-3.1, 1.9)]
    lr = 0.09
    for _ in range(45):
        x, y = path[-1]
        gx, gy = grad(x, y)
        path.append((x - lr * gx, y - lr * gy))
    path = np.array(path)
    loss = f(path[:, 0], path[:, 1])

    fig = plt.figure(figsize=(12.2, 5.0))
    gs = GridSpec(1, 2, width_ratios=[1.7, 1.0], wspace=0.28,
                  left=0.06, right=0.985, top=0.90, bottom=0.12)
    ax = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    cf = ax.contourf(X, Y, Z, levels=45, cmap=CMAP)
    cf.set_rasterized(True)  # keeps the SVG small
    ax.contour(X, Y, Z, levels=12, colors=RULE, linewidths=0.6, alpha=0.55)
    ax.plot(path[:, 0], path[:, 1], color=RED, lw=1.6, zorder=5)
    ax.scatter(path[:, 0], path[:, 1], s=14, color=RED, zorder=6)
    ax.scatter(*path[0], s=70, facecolor="none", edgecolor=INK, lw=1.4, zorder=7)
    ax.scatter(*path[-1], s=48, color=INK, marker="*", zorder=8)
    ax.annotate("start", path[0], textcoords="offset points", xytext=(9, 9),
                color=INK, fontsize=10)
    ax.annotate("minimum", path[-1], textcoords="offset points", xytext=(10, -14),
                color=INK, fontsize=10)
    ax.set_xlabel("θ₁"); ax.set_ylabel("θ₂")
    ax.set_title("the surface, seen from above")
    ax.tick_params(length=0)

    cb = fig.colorbar(cf, ax=ax, pad=0.02, fraction=0.046)
    cb.outline.set_edgecolor(RULE)
    cb.ax.tick_params(color=MUTED, labelsize=9, labelcolor=MUTED)
    cb.set_label("cost  J(θ)", color=MUTED, fontsize=10)

    ax2.plot(loss, color=ACC, lw=1.8)
    ax2.set_yscale("log")
    ax2.set_xlabel("iteration k"); ax2.set_ylabel("cost after k steps")
    ax2.set_title("what the algorithm actually sees")
    ax2.grid(True, color=RULE, alpha=0.4, lw=0.6)
    ax2.tick_params(length=0)
    ax2.annotate(f"η = {lr}", (0.97, 0.9), xycoords="axes fraction",
                 ha="right", color=MUTED, fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False); ax2.spines[s].set_visible(False)
    save(fig, "gradient-descent")


# ── figure 2: informed guesses against random ones ──────────────────────
def fig_race():
    """Best score so far, informed proposals vs uniform random ones.

    A toy: a smooth bowl in six settings on [0, 1]. Random search draws each
    setting uniformly. "Informed" draws around a starting guess that is close
    to the optimum but not on it, the way a model that has read about similar
    problems would. Lines are medians over many simulated searches.
    """
    rng = np.random.default_rng(7)
    dim, n_exp, n_rep = 6, 60, 2000
    opt = rng.uniform(0.2, 0.8, dim)
    guess = np.clip(opt + rng.normal(0, 0.08, dim), 0, 1)

    def score(x):
        return np.sum(((x - opt) / 0.25) ** 2, axis=-1)

    rand = score(rng.uniform(0, 1, (n_rep, n_exp, dim)))
    inf = score(np.clip(guess + rng.normal(0, 0.12, (n_rep, n_exp, dim)), 0, 1))
    k = np.arange(1, n_exp + 1)

    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    fig.subplots_adjust(left=0.09, right=0.80, top=0.95, bottom=0.14)
    for runs, color, ls, label in [(rand, MUTED, "--", "random guesses"),
                                   (inf, ACC, "-", "informed guesses")]:
        best = np.minimum.accumulate(runs, axis=1)
        lo, mid, hi = np.percentile(best, [25, 50, 75], axis=0)
        ax.fill_between(k, lo, hi, color=color, alpha=0.15, lw=0)
        ax.plot(k, mid, color=color, lw=2.0, ls=ls)
        ax.annotate(label, (k[-1], mid[-1]), textcoords="offset points",
                    xytext=(8, 0), va="center", color=color, fontsize=11,
                    annotation_clip=False)
    ax.set_yscale("log")
    ax.set_xlabel("experiments run")
    ax.set_ylabel("best score so far (lower is better)")
    ax.set_xlim(1, n_exp)
    ax.grid(True, color=RULE, alpha=0.4, lw=0.6)
    ax.tick_params(length=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "informed-vs-random")


if __name__ == "__main__":
    fig_gradient_descent()
    fig_race()

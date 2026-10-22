"""Figures for "The AI Scientist: Auto Research".

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
    fig.savefig(f"{name}.svg", bbox_inches="tight", pad_inches=0.25)
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
    fig.text(0.06, 0.965, "Figure 2  ·  gradient descent on a two-parameter "
             "cost surface", color=INK, fontsize=12.5)
    save(fig, "gradient-descent")


# ── figure 3: prior, likelihood, posterior ───────────────────────────────
def fig_bayes():
    grid = np.linspace(-4.0, -0.6, 800)
    # "truth": one real optimum in log10(learning rate) space
    truth = 0.90 + 0.42 * ((grid + 2.35) / 0.75) ** 2 + 0.05 * np.sin(4 * grid)
    sigma = 0.045

    def gauss(mu, sd):
        return np.exp(-0.5 * ((grid - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi))

    prior_llm = gauss(-2.35, 0.55)          # what the model already believes
    prior_flat = np.full_like(grid, 1 / (grid[-1] - grid[0]))

    rng = np.random.default_rng(3)
    draws = np.clip(rng.normal(-2.35, 0.55, 10), grid[0], grid[-1])
    obs = np.interp(draws, grid, truth) + rng.normal(0, sigma, draws.size)

    def posterior(prior, samples):
        logp = np.log(prior + 1e-300)
        for xi, yi in zip(samples, obs[: len(samples)]):
            logp = logp - 0.5 * ((truth - yi) / sigma) ** 2 * np.exp(
                -0.5 * ((grid - xi) / 0.12) ** 2)
        p = np.exp(logp - logp.max())
        return p / np.trapezoid(p, grid)

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(12.2, 4.4),
                                    gridspec_kw=dict(wspace=0.24, left=0.065,
                                                     right=0.985, top=0.82, bottom=0.15))
    # (a) the two priors
    axa.plot(grid, truth, color=RULE, lw=2.0, label="true objective (unknown)")
    axa.plot(grid, 0.90 + 3.0 * prior_llm / prior_llm.max() * 0.35,
             color=ACC, lw=2.0, label="LLM prior")
    axa.plot(grid, 0.90 + 3.0 * prior_flat / prior_flat.max() * 0.35,
             color=MUTED, lw=1.6, ls=":", label="uninformed prior")
    axa.set_xlabel("log₁₀ learning rate"); axa.set_ylabel("density (rescaled)")
    axa.set_title("before any experiment")
    axa.legend(frameon=False, fontsize=10, labelcolor=INK2, loc="upper center")
    axa.grid(True, color=RULE, alpha=0.3, lw=0.6)
    axa.tick_params(length=0)

    # (b) posterior after n experiments
    for n, alpha in [(1, 0.30), (4, 0.55), (10, 1.0)]:
        p = posterior(prior_llm, draws[:n])
        axb.fill_between(grid, 0, p, color=ACC, alpha=alpha * 0.5, lw=0)
        axb.plot(grid, p, color=ACC, lw=1.6, alpha=alpha,
                 label=f"LLM prior, {n} experiment{'s' if n > 1 else ''}")
    pu = posterior(prior_flat, draws[:10])
    axb.plot(grid, pu, color=MUTED, lw=1.6, ls="--", label="uninformed prior, 10 experiments")
    axb.set_xlabel("log₁₀ learning rate"); axb.set_ylabel("posterior density")
    axb.set_title("after experiments")
    axb.legend(frameon=False, fontsize=10, labelcolor=INK2, loc="upper right")
    axb.grid(True, color=RULE, alpha=0.3, lw=0.6)
    axb.tick_params(length=0)
    for ax in (axa, axb):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.text(0.065, 0.945, "Figure 5  ·  ten measurements under two priors", color=INK, fontsize=12.5)
    save(fig, "bayes-prior")


if __name__ == "__main__":
    fig_gradient_descent()
    fig_bayes()

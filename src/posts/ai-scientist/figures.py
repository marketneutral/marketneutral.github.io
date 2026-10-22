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
    # +0.4 keeps the score positive everywhere, so it survives the log axis
    return 0.4 + 0.5 * (x - 0.6) ** 2 + 4.0 * (y + 0.4) ** 2 + 0.35 * np.sin(3 * x) * np.sin(3 * y)


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
    ax.set_xlabel("setting 1"); ax.set_ylabel("setting 2")
    ax.set_title("the surface, seen from above")
    ax.tick_params(length=0)

    cb = fig.colorbar(cf, ax=ax, pad=0.02, fraction=0.046)
    cb.outline.set_edgecolor(RULE)
    cb.ax.tick_params(color=MUTED, labelsize=9, labelcolor=MUTED)
    cb.set_label("score", color=MUTED, fontsize=10)

    ax2.plot(loss, color=ACC, lw=1.8)
    ax2.set_yscale("log")
    ax2.set_xlabel("step"); ax2.set_ylabel("score")
    ax2.set_title("what the algorithm sees")
    ax2.grid(True, color=RULE, alpha=0.4, lw=0.6)
    ax2.tick_params(length=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False); ax2.spines[s].set_visible(False)
    save(fig, "gradient-descent")


# ── figure 3: Karpathy's overnight run, redrawn ─────────────────────────
# Values read off the chart in github.com/karpathy/autoresearch (progress.png,
# MIT): axes calibrated from its gridlines, marker centres located in the
# image, experiment numbers snapped to integers. Points the original does not
# show (crashes, runs worse than the baseline, markers hidden under others)
# are absent here too.
KEPT = [  # (experiment, val_bpb, label)
    (0, 0.99789, "baseline"),
    (2, 0.99072, "halve batch size"),
    (6, 0.98965, "longer warmdown"),
    (8, 0.98740, "add warmup"),
    (14, 0.98449, "depth 9"),
    (23, 0.98392, "x0_lambda init"),
    (28, 0.98334, "unembedding LR ×2"),
    (32, 0.98211, "more sliding window"),
    (38, 0.97986, "shorter windows (×2)"),
    (39, 0.97958, None),
    (43, 0.97892, "embedding LR"),
    (64, 0.97828, "RoPE base 10k→200k (×3)"),
    (65, 0.97803, None),
    (67, 0.97772, None),
    (74, 0.97729, "random seed 42→137"),
]
DISCARDED = [
    (3, 0.99355), (4, 0.99386), (5, 0.99345), (7, 0.98994), (9, 0.98835),
    (10, 0.99110), (11, 0.99028), (12, 0.99335), (13, 0.99056), (16, 0.99507),
    (17, 0.98551), (18, 0.99302), (19, 0.98786), (21, 0.98509), (22, 0.99802),
    (24, 0.98467), (25, 0.98581), (26, 0.98413), (27, 0.98569), (29, 0.98456),
    (30, 0.98417), (31, 0.98758), (33, 0.98318), (34, 0.98340), (35, 0.98603),
    (36, 0.98365), (37, 0.98326), (42, 0.98283), (44, 0.97998), (45, 0.97941),
    (46, 0.98084), (47, 0.98011), (48, 0.98257), (49, 0.98303), (50, 0.98073),
    (51, 0.98551), (52, 0.98620), (53, 0.97923), (54, 0.97912), (55, 0.98068),
    (56, 0.97951), (57, 0.97948), (58, 0.98191), (59, 0.98400), (60, 0.97976),
    (61, 0.97935), (63, 0.98030), (66, 0.97886), (68, 0.97805), (69, 0.97892),
    (71, 0.97795), (72, 0.97879), (73, 0.97882), (75, 0.97902), (76, 0.98193),
    (77, 0.97769), (78, 0.97746), (79, 0.97872), (80, 0.97941), (81, 0.97775),
    (82, 0.97879),
]


def fig_progress():
    kx = np.array([k[0] for k in KEPT]); ky = np.array([k[1] for k in KEPT])
    dx = np.array([d[0] for d in DISCARDED]); dy = np.array([d[1] for d in DISCARDED])

    fig, ax = plt.subplots(figsize=(12.2, 5.6))
    fig.subplots_adjust(left=0.08, right=0.93, top=0.97, bottom=0.11)
    ax.scatter(dx, dy, s=16, color=MUTED, alpha=0.55, lw=0, zorder=2,
               label="discarded")
    # running best: a staircase through the kept points, out to the last run
    sx = np.append(kx, 82); sy = np.append(ky, ky[-1])
    ax.step(sx, sy, where="post", color=ACC, lw=1.8, zorder=3,
            label="best so far")
    ax.scatter(kx[:-1], ky[:-1], s=46, color=ACC, edgecolor=BG, lw=1.2,
               zorder=4, label="kept")
    ax.scatter(kx[-1:], ky[-1:], s=60, color=RED, edgecolor=BG, lw=1.2, zorder=5)
    for x, y, label in KEPT:
        if label is None:
            continue
        color = RED if label.startswith("random seed") else ACC
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(6, 7),
                    rotation=28, rotation_mode="anchor", color=color, fontsize=10,
                    annotation_clip=False)
    ax.set_xlim(-2, 85)
    ax.set_ylim(0.9755, 1.0)
    ax.set_xlabel("experiment")
    ax.set_ylabel("val_bpb (lower is better)")
    ax.grid(True, color=RULE, alpha=0.4, lw=0.6)
    ax.tick_params(length=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    leg = ax.legend(frameon=False, fontsize=10, labelcolor=INK2, loc="upper right")
    save(fig, "autoresearch-progress")


if __name__ == "__main__":
    fig_gradient_descent()
    fig_progress()

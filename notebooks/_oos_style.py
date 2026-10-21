"""
Matplotlib styling for the OUT OF SAMPLE_ blog.

Import this module from a Quarto notebook to apply the site's dark palette
to all plots. The styling is applied at import time via rcParams, so any
plt.subplots() / plt.plot() call after the import inherits it.

    import _oos_style                # applies the theme
    fig, ax = plt.subplots(...)      # already themed

The default color cycle uses the same accent palette that Prism uses to
color syntax in code blocks — green → cyan → amber → orange → purple → red.
"""

import matplotlib.pyplot as plt
from cycler import cycler

# ── palette (matches src/assets/styles.css :root vars) ────────────────────
OOS = {
    "bg":      "#0a0e1a",
    "ink":     "#e8eaf0",
    "ink_2":   "#c0c4cf",
    "muted":   "#6b7280",
    "rule":    "#2a3344",
    "accent":  "#3ee87a",   # phosphor green
    "cyan":    "#82d8ff",
    "amber":   "#e8c97a",
    "orange":  "#f5a97f",
    "purple":  "#c8a8ff",
    "red":     "#f25d6e",
}

plt.rcParams.update({
    # canvas
    "figure.facecolor":     OOS["bg"],
    "figure.edgecolor":     OOS["bg"],
    "axes.facecolor":       OOS["bg"],
    "savefig.facecolor":    OOS["bg"],
    "savefig.edgecolor":    "none",

    # text
    "text.color":           OOS["ink"],
    "axes.labelcolor":      OOS["ink_2"],
    "axes.titlecolor":      OOS["ink"],
    "axes.titleweight":     "normal",
    "axes.titlesize":       11,
    "axes.titlepad":        14,
    "axes.labelsize":       10,

    # ticks
    "xtick.color":          OOS["ink_2"],
    "ytick.color":          OOS["ink_2"],
    "xtick.labelcolor":     OOS["ink_2"],
    "ytick.labelcolor":     OOS["ink_2"],
    "xtick.labelsize":      9,
    "ytick.labelsize":      9,
    "xtick.major.size":     4,
    "ytick.major.size":     4,
    "xtick.major.width":    0.7,
    "ytick.major.width":    0.7,

    # spines — keep only left + bottom, thin
    "axes.edgecolor":       OOS["rule"],
    "axes.linewidth":       0.7,
    "axes.spines.top":      False,
    "axes.spines.right":    False,

    # grid
    "axes.grid":            True,
    "axes.axisbelow":       True,
    "grid.color":           OOS["rule"],
    "grid.linewidth":       0.5,
    "grid.alpha":           0.7,

    # color cycle (matches Prism token colors in the site)
    "axes.prop_cycle":      cycler("color", [
        OOS["accent"], OOS["cyan"], OOS["amber"],
        OOS["orange"], OOS["purple"], OOS["red"],
    ]),

    # lines
    "lines.linewidth":      1.4,
    "lines.solid_capstyle": "round",

    # figure
    "figure.figsize":       (9, 4.5),
    "figure.dpi":           110,
    "savefig.dpi":          140,
    "savefig.bbox":         "tight",
    "savefig.pad_inches":   0.15,

    # legend
    "legend.facecolor":     OOS["bg"],
    "legend.edgecolor":     OOS["rule"],
    "legend.labelcolor":    OOS["ink"],
    "legend.fontsize":      9,
    "legend.frameon":       True,
    "legend.framealpha":    0.9,

    # font — fall through to system defaults; keep matplotlib light on font deps
    "font.size":            10,
})

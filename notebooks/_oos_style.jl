# Plots.jl styling for the blog, mirroring _oos_style.py.
#
# Include this from a Quarto notebook after `using Plots` to apply the site's
# dark palette to every plot that follows:
#
#     using Plots
#     include("_oos_style.jl")
#
# The color cycle matches the accent palette Prism uses for syntax in code
# blocks — green → cyan → amber → orange → purple → red.

using Plots

# ── palette (matches src/assets/styles.css :root vars) ────────────────────
const OOS = (
    bg     = "#0a0e1a",
    ink    = "#e8eaf0",
    ink2   = "#c0c4cf",
    muted  = "#6b7280",
    rule   = "#2a3344",
    accent = "#3ee87a",   # phosphor green
    cyan   = "#82d8ff",
    amber  = "#e8c97a",
    orange = "#f5a97f",
    purple = "#c8a8ff",
    red    = "#f25d6e",
)

const OOS_CYCLE = [
    OOS.accent, OOS.cyan, OOS.amber, OOS.orange, OOS.purple, OOS.red, OOS.ink2,
]

Plots.default(
    # canvas
    background_color        = OOS.bg,
    background_color_inside = OOS.bg,
    background_color_legend = :transparent,

    # text
    foreground_color        = OOS.ink2,
    titlefontcolor          = OOS.ink,
    guidefontcolor          = OOS.ink2,
    tickfontcolor           = OOS.ink2,
    legendfontcolor         = OOS.ink,
    titlefontsize           = 12,
    titlelocation           = :left,
    guidefontsize           = 10,
    tickfontsize            = 9,
    legendfontsize          = 9,

    # frame: left + bottom only, thin
    framestyle              = :axes,
    foreground_color_axis   = OOS.rule,
    foreground_color_border = OOS.rule,
    foreground_color_legend = nothing,     # no box around legends

    # grid
    grid                    = true,
    foreground_color_grid   = OOS.rule,
    gridalpha               = 0.7,
    gridlinewidth           = 0.5,
    minorgrid               = false,

    # color cycle + lines
    palette                 = OOS_CYCLE,
    linewidth               = 1.4,

    # figure
    size                    = (900, 450),
    dpi                     = 140,
    margin                  = 4Plots.mm,
    top_margin              = 6Plots.mm,
)

# Year ticks for a monthly axis: `xticks = yearticks(240)`.
yearticks(n_months; every = 2) = (0:12every:n_months, string.(0:every:n_months ÷ 12))

# Compact tick labels for large numbers: -400000 → "-400k".
kfmt(x) = abs(x) >= 1000 ? string(round(Int, x / 1000), "k") : string(round(Int, x))

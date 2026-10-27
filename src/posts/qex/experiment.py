"""Reproduces the figures and table in this post.

    pip install "qex[all] @ git+https://github.com/marketneutral/alpha-parser" yfinance matplotlib pyarrow lxml
    python experiment.py

Universe: current S&P 500 members with a full price history back to mid-2009
(survivorship-biased by construction). Adjusted daily OHLCV from Yahoo Finance,
June 2009 through 2025-12-31.
The alpha is ranked, sector-demeaned (so sector- and dollar-neutral), unit
gross, rebalanced daily, and shown unsmoothed and with a 10-day linear decay.
Returns are on the gross book, unlevered. Costs are charged per unit of turnover.
"""
import io
import numpy as np
import pandas as pd
import requests
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from qex import qex, compute_context, QuantileAnalysis

START = pd.Timestamp("2010-07-01")
COSTS = (0.0002,)   # per unit turnover: a reasonable level

# ── data ────────────────────────────────────────────────────────────────────
html = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
members = pd.read_html(io.StringIO(html))[0]
tickers = members["Symbol"].str.replace(".", "-", regex=False).tolist()
sectors = pd.Series(members["GICS Sector"].values, index=tickers)
END = "2026-01-01"   # the run ends 2025-12-31 (yfinance end is exclusive)
raw = yf.download(tickers, start="2009-06-01", end=END, auto_adjust=True, progress=False)
ok = raw["Close"].columns[raw["Close"].notna().mean() > 0.98]
data = {f.lower(): raw[f][ok] for f in ["Open", "High", "Low", "Close", "Volume"]}
data["sector"] = pd.DataFrame([sectors.reindex(ok).values] * len(raw), index=raw.index, columns=ok)
fwd = data["close"].pct_change(fill_method=None).shift(-1)      # return from t to t+1
print("universe:", len(ok), "names")

# ── alpha ───────────────────────────────────────────────────────────────────
# One alpha: where the stock closed within its own five-day high-low range,
# inverted (a close near the low is a buy), ranked across stocks, sector-demeaned
# so the book is sector- and dollar-neutral, then smoothed with a linear decay.
# The expressions are the post's, verbatim. scale sets the gross to one, as simulate does again.
PIECES = """let lo   = ts_min(low(), 5),
    hi   = ts_max(high(), 5),
    pos  = (close() - lo) / (hi - lo),
    book = group_demean(rank(-pos), 'sector')
in """
ALPHAS = {
    "no smoothing": PIECES + "scale(book)",
    "decay 10":     PIECES + "scale(decay_linear(book, 10))",
}

def simulate(weights):
    """Rebalance daily to the alpha's weights; unit gross. Returns (gross daily return, daily turnover)."""
    w = weights.loc[START:]
    w = w.div(w.abs().sum(axis=1), axis=0).fillna(0)
    gross = (w * fwd.loc[w.index]).sum(axis=1)
    turnover = w.diff().abs().sum(axis=1).fillna(0)
    return gross, turnover

sharpe = lambda x: x.mean() / x.std() * np.sqrt(252)
max_dd = lambda x: (x.cumsum() - x.cumsum().cummax()).min()   # on the unit gross book
series, rows = {}, []
with compute_context():
    for name, expr in ALPHAS.items():
        gross, to = simulate(qex(expr).to_weights(data))
        row = dict(book=name, turnover=to.mean(), gross=gross.mean() * 252, gross_sharpe=sharpe(gross))
        series[(name, 0)] = gross
        for tc in COSTS:
            net = gross - to * tc
            series[(name, tc)] = net
            row[f"net_{int(tc * 1e4)}bp"] = net.mean() * 252
            row[f"sharpe_{int(tc * 1e4)}bp"] = sharpe(net)
            row[f"maxdd_{int(tc * 1e4)}bp"] = max_dd(net)
        rows.append(row)
table = pd.DataFrame(rows)
print(table.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
print("decay 10, net 2 bps by year:", series[("decay 10", 0.0002)].groupby(lambda d: d.year).sum().round(3).to_dict())

# Quintile analysis of the smoothed alpha, and rank IC by forecast horizon for
# both, which is why smoothing is nearly free.
quint = QuantileAnalysis(qex(ALPHAS["decay 10"]), n_quantiles=5).run(data, start_date=START)
print(quint.summary())
with compute_context():
    sig = {name: qex(expr).evaluate(data).loc[START:] for name, expr in ALPHAS.items()}
H = range(1, 21)
ic = pd.DataFrame({n: [s.corrwith((data["close"].shift(-k) / data["close"] - 1).loc[START:], axis=1, method="spearman").mean() for k in H] for n, s in sig.items()}, index=H)
print("rank IC by horizon:\n", ic.round(4).T.to_string())
for n, s in sig.items():
    print(f"{n}: lag-1 autocorrelation {s.corrwith(s.shift(1), axis=1, method='spearman').mean():.3f}")

# ── charts, in the blog's palette ──────────────────────────────────────────
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
panels = list(ALPHAS)
fig, axes = plt.subplots(1, 2, figsize=(9, 5), sharey=True)
for ax, name in zip(axes, panels):
    g, n = cum(series[(name, 0)]).iloc[::5], cum(series[(name, 0.0002)]).iloc[::5]   # weekly points keep the SVG small
    ax.plot(g.index, g.values, color=ACCENT, lw=2, label="gross")
    ax.plot(n.index, n.values, color=MUTED, lw=2, label="net of 2 bps")
    ax.axhline(0, color=RULE, lw=1, zorder=0)
    ax.set_title(f"range, {name}\ndaily, sector-neutral", loc="left", fontsize=11, pad=10)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_xticks(pd.to_datetime([f"{y}-01-01" for y in (2012, 2016, 2020, 2024)]))
    ax.set_xticklabels(["2012", "2016", "2020", "2024"])
    ax.tick_params(labelsize=10)
    for v in (g.iloc[-1], n.iloc[-1]):
        ax.annotate(f"{v:+.0%}", (g.index[-1], v), xytext=(6, 0), textcoords="offset points", va="center", fontsize=10, color=INK2)
    ax.set_xlim(pd.Timestamp("2010-04-01"), g.index[-1] + pd.Timedelta(days=500))
axes[0].set_ylabel("cumulative long-short return on GMV", color=MUTED, fontsize=10)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.04), ncol=2, frameon=False, fontsize=10, handlelength=1.6)
fig.subplots_adjust(wspace=0.12)
finish(fig, "gross-vs-net.svg")

yr = series[("decay 10", 0.0002)].groupby(lambda d: d.year).sum()
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.grid(axis="x", visible=False)
ax.bar(yr.index, yr.values, width=0.5, color=ACCENT, zorder=3)
ax.axhline(0, color=RULE, lw=1, zorder=2)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
ax.set_title("range, decay 10: net return on GMV by calendar year, 2 bps per unit turnover", loc="left", fontsize=11, pad=10)
ax.set_xticks(list(yr.index)); ax.set_xticklabels([str(y)[2:] for y in yr.index]); ax.tick_params(labelsize=10)
for y, v in yr.items():   # labels sit above the bar, or above the baseline for a negative year
    ax.annotate("0%" if abs(v) < 0.005 else f"{v:+.0%}", (y, max(v, 0)), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9, color=INK2)
finish(fig, "range-by-year.svg")

q = (quint.mean_returns - quint.mean_returns.mean()) * 252   # relative to the equal-weight universe
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.grid(axis="x", visible=False)
ax.bar(q.index, q.values, width=0.5, color=ACCENT, zorder=3)
ax.axhline(0, color=RULE, lw=1, zorder=2)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
ax.set_title("range, decay 10: annual return by quintile relative to the universe, gross", loc="left", fontsize=11, pad=10)
ax.set_xticks(list(q.index)); ax.set_xticklabels([f"Q{i}" for i in q.index]); ax.tick_params(labelsize=10)
ax.set_xlabel("quintile of the alpha, Q5 is the top", fontsize=10)
for i, v in q.items():
    ax.annotate(f"{v:+.1%}", (i, max(v, 0)), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9, color=INK2)
finish(fig, "quintiles.svg")

fig, ax = plt.subplots(figsize=(9, 3.8))
ax.grid(axis="x", visible=False)
for name, color in [("no smoothing", MUTED), ("decay 10", ACCENT)]:
    ax.plot(ic.index, ic[name], color=color, lw=2, marker="o", ms=4, label=name)
ax.annotate("no smoothing", (8, ic["no smoothing"][8]), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=10, color=INK2)
ax.annotate("decay 10", (2, ic["decay 10"][2]), xytext=(10, -10), textcoords="offset points", ha="left", fontsize=10, color=INK2)
ax.axhline(0, color=RULE, lw=1, zorder=0)
ax.set_title("range: rank IC against the cumulative return over the next k days", loc="left", fontsize=11, pad=10)
ax.set_xlabel("k, trading days ahead", fontsize=10)
ax.set_ylabel("mean daily rank IC", fontsize=10)
ax.set_xticks([1, 5, 10, 15, 20]); ax.set_xlim(0.5, 20.5); ax.set_ylim(0, 0.014)
ax.tick_params(labelsize=10)
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False, fontsize=10, handlelength=1.6)
finish(fig, "ic-by-horizon.svg")
print("wrote gross-vs-net.svg, range-by-year.svg, quintiles.svg, ic-by-horizon.svg")

"""Performance figures and statistics for the autoresearch-alpha post. Run from this directory:

    python analysis.py

Needs the lab at ../../../../alpha_auto (its data/ and eval.py). Evaluates the seed and the final
book over 1990-2025 with the evaluator's own book conventions, and draws, in the qex post's style:
cumulative gross and net return with the three periods marked, the net return by calendar year,
quintiles of the momentum score by period, and rank IC by horizon. Prints a statistics table to
lab/stats.txt. The test period is reported here, not selected on: the book was fixed before it was run.
"""
import os, sys, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
warnings.simplefilter("ignore")
LAB = "/home/jlarkin/blog_2/alpha_auto"
sys.path.insert(0, LAB)
import eval as ev
from qex import qex, compute_context

START = "1991-01-01"
PERIODS = [("inspection", "1991-01-01", "1999-12-31"), ("validation", "2000-01-01", "2017-12-31"), ("test", "2018-01-01", "2025-12-31")]
SEED = "let mom = delay(returns(231), 21), vol = volatility(60), score = group_demean(mom / vol, 'sector') in decay_linear(score / vol, 10)"
FINAL = " ".join(open("lab/alpha.qex").read().split())
SCORE = "let mom = delay(returns(231), 21) + delay(returns(126), 126), r1 = returns(1), vol = ts_std(group_demean(r1, 'sector'), 60) in zscore(group_demean(mom / vol, 'sector'))"

data = ev.load("1990-01-01", "2025-12-31")
books = {}
for name, e in (("seed", SEED), ("final", FINAL)):
    g, to, b = ev.book(e, data, START)
    books[name] = dict(gross=g, net=g - ev.TC * to, to=to, breadth=b)
r1 = data["close"].pct_change(fill_method=None)
fwd = r1.shift(-1).loc[START:]
mkt = r1.mean(axis=1).loc[START:]

# ── statistics ─────────────────────────────────────────────────────────────
sharpe, ann = ev.sharpe, lambda x: x.mean() * 252
maxdd = lambda x: ((1 + x).cumprod() / (1 + x).cumprod().cummax() - 1).min()
with compute_context():
    w_final = __import__("qex").demean(qex(FINAL) + 0 * __import__("qex").close()).evaluate(data).loc[START:].fillna(0)
    score = qex(SCORE).evaluate(data).loc[START:]
w_final = w_final / w_final.abs().sum(axis=1).mean()
two_sided = (score.sub(score.mean(axis=1), axis=0) * fwd).sum(axis=1)   # plain long-short momentum, for correlation
lines = []
for name in ("seed", "final"):
    for per, a, b in PERIODS:
        g, n, to = books[name]["gross"][a:b], books[name]["net"][a:b], books[name]["to"][a:b]
        beta = np.cov(n, mkt[a:b])[0, 1] / mkt[a:b].var()
        up = mkt[a:b] > 0
        row = dict(book=name, period=per, gross_sharpe=sharpe(g), net_sharpe=sharpe(n), gross_yr=ann(g), net_yr=ann(n), turnover=to.mean(), maxdd=maxdd(n), beta=beta,
                   net_up_days=ann(n[up]), net_down_days=ann(n[~up]), corr_two_sided=n.corr(two_sided[a:b]))
        if name == "final":
            w = w_final[a:b]; shorts = (w < 0)
            row["names_short"] = shorts.sum(axis=1).mean()
            top10 = w.where(shorts, 0).abs().apply(lambda s: s.nlargest(10).sum() / max(s.sum(), 1e-12), axis=1).mean()
            row["top10_share_of_short"] = top10
        lines.append(row)
stats = pd.DataFrame(lines)
open("lab/stats.txt", "w").write(stats.to_string(index=False, float_format=lambda x: f"{x:.3f}") + "\n")
print(stats.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
# which sectors does the book short, on average, and how long does it hold
sec = data["sector"].iloc[-1]
short_by_sector = w_final.where(w_final < 0, 0).abs().T.groupby(sec).sum().T.div(w_final.where(w_final < 0, 0).abs().sum(axis=1), axis=0).mean().sort_values(ascending=False)
print("\nshare of the short leg by sector:", short_by_sector.round(3).to_dict())
print("holding period (days, 1/turnover):", {per: round(1 / books["final"]["to"][a:b].mean(), 1) for per, a, b in PERIODS})
yr = books["final"]["net"].groupby(lambda d: d.year).sum()
print("final net by year:", yr.round(3).to_dict())

# ── charts, in the qex post's palette ──────────────────────────────────────
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
    open(path, "w").write(svg); plt.close(fig); print("wrote", path)
def shade(ax, ymax_frac=0.97, labels=True):
    for i, (per, a, b) in enumerate(PERIODS):
        if i % 2 == 0:
            ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=RULE, alpha=0.35, lw=0, zorder=0)
        if labels:
            ax.text(pd.Timestamp(a) + (pd.Timestamp(b) - pd.Timestamp(a)) / 2, ymax_frac, per, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=10, color=INK2)
cum = lambda x: (1 + x).cumprod() - 1

fig, axes = plt.subplots(1, 2, figsize=(9, 5), sharey=True)
for ax, name in zip(axes, ("seed", "final")):
    g, n = cum(books[name]["gross"]).iloc[::5], cum(books[name]["net"]).iloc[::5]
    shade(ax)
    ax.plot(g.index, g.values, color=ACCENT, lw=2, label="gross")
    ax.plot(n.index, n.values, color=MUTED, lw=2, label="net of 2 bps")
    ax.axhline(0, color=RULE, lw=1, zorder=0)
    ax.set_title(f"{name}\ndaily, dollar-neutral", loc="left", fontsize=11, pad=10)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_xticks(pd.to_datetime([f"{y}-01-01" for y in (1995, 2005, 2015, 2025)])); ax.set_xticklabels(["1995", "2005", "2015", "2025"])
    ax.tick_params(labelsize=10)
    for v in (g.iloc[-1], n.iloc[-1]):
        ax.annotate(f"{v:+.0%}", (g.index[-1], v), xytext=(6, 0), textcoords="offset points", va="center", fontsize=10, color=INK2)
    ax.set_xlim(pd.Timestamp("1990-10-01"), g.index[-1] + pd.Timedelta(days=900))
axes[0].set_ylabel("cumulative long-short return on GMV", color=MUTED, fontsize=10)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.04), ncol=2, frameon=False, fontsize=10, handlelength=1.6)
fig.subplots_adjust(wspace=0.12)
finish(fig, "gross-vs-net.svg")

fig, ax = plt.subplots(figsize=(9, 3.6))
ax.grid(axis="x", visible=False)
yrs = pd.to_datetime([f"{y}-07-01" for y in yr.index])
shade(ax, labels=True)
ax.bar(yrs, yr.values, width=250, color=ACCENT, zorder=3)
ax.axhline(0, color=RULE, lw=1, zorder=2)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
ax.set_title("final book: net return on GMV by calendar year, 2 bps per unit turnover", loc="left", fontsize=11, pad=10)
ax.set_xticks(pd.to_datetime([f"{y}-07-01" for y in yr.index[::2]])); ax.set_xticklabels([str(y)[2:] for y in yr.index[::2]]); ax.tick_params(labelsize=10)
ax.set_ylim(min(yr.min(), 0) - 0.02, yr.max() + 0.05)
finish(fig, "by-year.svg")

# quintiles of the two-sided momentum score, by period, relative to the universe
q = score.rank(axis=1, pct=True).apply(lambda s: np.ceil(s * 5)).clip(1, 5)
rows = {}
for per, a, b in PERIODS:
    f, qq = fwd[a:b], q[a:b]
    uni = f.mean(axis=1)
    rows[per] = [((f.where(qq == k).mean(axis=1) - uni).mean() * 252) for k in range(1, 6)]
qt = pd.DataFrame(rows, index=range(1, 6))
print("\nquintile return relative to universe, annualized:\n", qt.round(4).to_string())
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.grid(axis="x", visible=False)
x = np.arange(1, 6); wdt = 0.26
for i, (per, color) in enumerate([("inspection", MUTED), ("validation", ACCENT), ("test", INK2)]):
    ax.bar(x + (i - 1) * wdt, qt[per].values, width=wdt, color=color, zorder=3, label=per)
    for xi, v in zip(x + (i - 1) * wdt, qt[per].values):
        ax.annotate(f"{v:+.1%}", (xi, max(v, 0)), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7.5, color=INK2)
ax.axhline(0, color=RULE, lw=1, zorder=2)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
ax.set_title("momentum score: annual return by quintile relative to the universe, gross", loc="left", fontsize=11, pad=10)
ax.set_xticks(x); ax.set_xticklabels([f"Q{i}" for i in x]); ax.tick_params(labelsize=10)
ax.set_xlabel("quintile of the score, Q1 is the deepest losers", fontsize=10)
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=10, handlelength=1.6)
finish(fig, "quintiles.svg")

# rank IC of the final book's weights against the next k days, validation and test
H = range(1, 21)
ic = {}
for per, a, b in PERIODS[1:]:
    w = w_final[a:b]
    ic[per] = [w.corrwith((data["close"].shift(-k) / data["close"] - 1)[a:b], axis=1, method="spearman").mean() for k in H]
ic = pd.DataFrame(ic, index=H)
print("\nrank IC by horizon:\n", ic.round(4).T.to_string())
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.grid(axis="x", visible=False)
for per, color in (("validation", ACCENT), ("test", INK2)):
    ax.plot(ic.index, ic[per], color=color, lw=2, marker="o", ms=4, label=per)
ax.axhline(0, color=RULE, lw=1, zorder=0)
ax.set_title("final book: rank IC of the weights against the cumulative return over the next k days", loc="left", fontsize=11, pad=10)
ax.set_xlabel("k, trading days ahead", fontsize=10); ax.set_ylabel("mean daily rank IC", fontsize=10)
ax.set_xticks([1, 5, 10, 15, 20]); ax.set_xlim(0.5, 20.5); ax.tick_params(labelsize=10)
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False, fontsize=10, handlelength=1.6)
finish(fig, "ic-by-horizon.svg")

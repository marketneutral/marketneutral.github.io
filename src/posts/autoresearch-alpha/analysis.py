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

import hashlib
CACHE = os.environ.get("SCRATCH", "/tmp") + "/analysis-cache"; os.makedirs(CACHE, exist_ok=True)
def cached(key, fn):
    p = f"{CACHE}/{hashlib.md5(key.encode()).hexdigest()[:12]}.parquet"
    if os.path.exists(p):
        return pd.read_parquet(p)
    out = fn(); out.to_parquet(p); return out
data = ev.load("1990-01-01", "2025-12-31")
books = {}
for name, e in (("seed", SEED), ("final", FINAL)):
    df = cached("book:" + e, lambda: pd.concat(ev.book(e, data, START), axis=1, keys=["gross", "to", "breadth"]))
    g, to, b = df["gross"], df["to"], df["breadth"]
    books[name] = dict(gross=g, net=g - ev.TC * to, to=to, breadth=b)
r1 = data["close"].pct_change(fill_method=None)
fwd = r1.shift(-1).loc[START:]
mkt = r1.mean(axis=1).loc[START:]

# ── statistics ─────────────────────────────────────────────────────────────
sharpe, ann = ev.sharpe, lambda x: x.mean() * 252
maxdd = lambda x: ((1 + x).cumprod() / (1 + x).cumprod().cummax() - 1).min()
def _weights():
    with compute_context():
        return __import__("qex").demean(qex(FINAL) + 0 * __import__("qex").close()).evaluate(data).loc[START:].fillna(0)
def _score():
    with compute_context():
        return qex(SCORE).evaluate(data).loc[START:]
w_final = cached("weights:" + FINAL, _weights)
score = cached("score:" + SCORE, _score)
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

fig, ax = plt.subplots(figsize=(9, 5))
growth = lambda x: (1 + x).cumprod()
shade(ax)
fg, fn, sn = growth(books["final"]["gross"]).iloc[::5], growth(books["final"]["net"]).iloc[::5], growth(books["seed"]["net"]).iloc[::5]
ax.plot(fg.index, fg.values, color=ACCENT, lw=2, label="final book, gross")
ax.plot(fn.index, fn.values, color=MUTED, lw=2, label="final book, net of 2 bps")
ax.plot(sn.index, sn.values, color=INK2, lw=1.2, ls="--", label="seed, net of 2 bps")
ax.set_yscale("log")
ax.set_yticks([0.75, 1, 1.5, 2, 3, 4, 6]); ax.set_yticklabels(["0.75", "1", "1.5", "2", "3", "4", "6"])
ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
ax.axhline(1, color=RULE, lw=1, zorder=0)
ax.set_title("growth of a dollar of GMV, long-short, daily, dollar-neutral", loc="left", fontsize=11, pad=10)
ax.set_ylabel("growth of $1, log scale", color=MUTED, fontsize=10)
ax.set_xticks(pd.to_datetime([f"{y}-01-01" for y in (1995, 2000, 2005, 2010, 2015, 2020, 2025)])); ax.set_xticklabels(["1995", "2000", "2005", "2010", "2015", "2020", "2025"])
ax.tick_params(labelsize=10)
for series, color in ((fg, INK2), (fn, INK2), (sn, INK2)):
    ax.annotate(f"{series.iloc[-1]:.2f}", (series.index[-1], series.iloc[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=10, color=color)
ax.set_xlim(pd.Timestamp("1990-10-01"), fg.index[-1] + pd.Timedelta(days=700))
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=3, frameon=False, fontsize=10, handlelength=1.8)
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

# quintiles of plain 12-1 momentum, the literature's convention: equal weight at formation, held 21 days
c = data["close"]; r1c = c.pct_change(fill_method=None)
mom12 = c.shift(21) / c.shift(252) - 1
res = r1c.sub(r1c.T.groupby(data["sector"].iloc[-1]).transform("mean").T)
rvol = res.rolling(60).std()
H = 21; hold = c.shift(-H) / c - 1; days = c.index[::H]
qm = mom12.rank(axis=1, pct=True); vq = rvol.rank(axis=1, pct=True)
def per_days(a, b): return [x for x in days if pd.Timestamp(a) <= x <= pd.Timestamp(b)]
rows, splits = {}, {}
for per, a, b in PERIODS:
    d = per_days(a, b); f, qq, vt = hold.loc[d], qm.loc[d], vq.loc[d]; uni = f.mean(axis=1)
    rows[per] = [((f.where((qq > (k - 1) / 5) & (qq <= k / 5)).mean(axis=1) - uni).mean() * 12) for k in range(1, 6)]
    lo, hi = qq <= 0.2, qq > 0.8
    splits[per] = [((f.where(m & (vt > x) & (vt <= y)).mean(axis=1) - uni).mean() * 12) for m in (lo, hi) for x, y in ((0, 1/3), (1/3, 2/3), (2/3, 1))]
qt = pd.DataFrame(rows, index=range(1, 6))
vs = pd.DataFrame(splits, index=["losers, low vol", "losers, mid vol", "losers, high vol", "winners, low vol", "winners, mid vol", "winners, high vol"])
print("\nplain 12-1 momentum quintiles, 21-day hold, annual return vs universe:\n", qt.round(4).to_string())
print("\nloser and winner quintiles split by residual-vol tercile:\n", vs.round(4).to_string())
# the vol factor and the book's loading on it
volfac = (fwd.where(vq > 2/3).mean(axis=1) - fwd.where(vq <= 1/3).mean(axis=1))
reg = []
for name in ("seed", "final"):
    for per, a, b in PERIODS:
        y = books[name]["net"][a:b]; X = pd.concat([mkt[a:b], volfac[a:b]], axis=1).loc[y.index].dropna(); y = y.loc[X.index]
        Xm = np.column_stack([np.ones(len(X)), X.values]); beta, *_ = np.linalg.lstsq(Xm, y.values, rcond=None)
        resid = y.values - Xm @ beta
        reg.append(dict(book=name, period=per, net_yr=y.mean() * 252, alpha_yr=beta[0] * 252, beta_mkt=beta[1], beta_vol=beta[2], r2=1 - resid.var() / y.var(), ir=beta[0] / resid.std() * np.sqrt(252), volfac_yr=volfac[a:b].mean() * 252))
reg = pd.DataFrame(reg)
print("\nregression on the market and on high-minus-low residual vol:\n", reg.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
open("lab/stats.txt", "a").write("\nregression on the market and on high-minus-low residual vol (daily, by period):\n" + reg.to_string(index=False, float_format=lambda x: f"{x:.3f}") + "\n\nplain 12-1 momentum quintiles, 21-day hold, vs universe:\n" + qt.round(4).to_string() + "\n\nby residual-vol tercile:\n" + vs.round(4).to_string() + "\n")

def grouped(df, title, xlabels, path, xlabel=None, figsize=(9, 3.8)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(axis="x", visible=False)
    x = np.arange(len(df)); wdt = 0.26
    for i, (per, color) in enumerate([("inspection", MUTED), ("validation", ACCENT), ("test", INK2)]):
        ax.bar(x + (i - 1) * wdt, df[per].values, width=wdt, color=color, zorder=3, label=per)
    ax.axhline(0, color=RULE, lw=1, zorder=2)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_title(title, loc="left", fontsize=11, pad=10)
    ax.set_xticks(x); ax.set_xticklabels(xlabels); ax.tick_params(labelsize=9)
    if xlabel: ax.set_xlabel(xlabel, fontsize=10)
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=10, handlelength=1.6)
    finish(fig, path)
grouped(qt, "plain 12-month momentum: annual return by quintile relative to the universe, 21-day hold", [f"Q{i}" for i in range(1, 6)], "quintiles.svg", "quintile of past-year return, Q1 is the losers")
grouped(vs, "the same losers and winners, split by the stock's residual volatility", ["losers\nlow vol", "losers\nmid vol", "losers\nhigh vol", "winners\nlow vol", "winners\nmid vol", "winners\nhigh vol"], "vol-split.svg")

# quintiles of the short leg by weight size, plus the long side, by period: does the sizing sort returns?
rows = {}
for per, a, b in PERIODS:
    w, f = w_final[a:b], fwd[a:b]
    uni = f.mean(axis=1)
    sh = w.where(w < 0).abs()
    qs = sh.rank(axis=1, pct=True).apply(lambda s: np.ceil(s * 5)).clip(1, 5)
    vals = [((f.where(qs == k).mean(axis=1) - uni).mean() * 252) for k in range(1, 6)]
    vals.append(((f.where(w > 0).mean(axis=1) - uni).mean() * 252))
    rows[per] = vals
ql = pd.DataFrame(rows, index=["S1", "S2", "S3", "S4", "S5", "long"])
print("\nshort leg by weight quintile (S5 largest short) and the long side, relative to universe, annualized:\n", ql.round(4).to_string())
grouped(ql, "final book: annual return of the short leg by weight quintile, and the long side, relative to the universe", ["S1\nsmallest short", "S2", "S3", "S4", "S5\nlargest short", "long side"], "short-leg-quintiles.svg")

# gross exposure through time, and the same book at unit gross every day (the qex post's convention)
gross_exp = w_final.abs().sum(axis=1)
wu = w_final.div(w_final.abs().sum(axis=1), axis=0).fillna(0)
ru = (wu * fwd).sum(axis=1); tu = wu.diff().abs().sum(axis=1).fillna(0); nu = ru - ev.TC * tu
ug = []
for per, a, b in PERIODS:
    g = gross_exp[a:b]
    ug.append(dict(period=per, gross_p5=g.quantile(.05), gross_p50=g.median(), gross_p95=g.quantile(.95), unit_gross_sharpe=sharpe(nu[a:b]), unit_gross_net_yr=nu[a:b].mean() * 252, unit_gross_turnover=tu[a:b].mean(), unit_gross_maxdd=maxdd(nu[a:b])))
ug = pd.DataFrame(ug)
print("\ngross exposure (mean 1 over the full span) and the final book at unit gross every day:\n", ug.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
open("lab/stats.txt", "a").write("\ngross exposure and the final book at unit gross every day:\n" + ug.to_string(index=False, float_format=lambda x: f"{x:.3f}") + "\n")

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

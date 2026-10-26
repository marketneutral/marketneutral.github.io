"""Performance figures and statistics for the autoresearch-alpha post. Run from this directory:

    uv run --project $ALPHA_LAB python analysis.py

Needs the lab (ALPHA_LAB, default ~/dev/alpha_lab: its data/ and eval.py). Builds the seed, the
final book and T55 from 1999 with the evaluator's book (delay 1, universe members only,
dollar-neutral, gross exactly one, 5% cap), on the corrected warehouse cut at 2026-08-11, and
writes lab/stats.txt and the figures: cumulative P&L with the three periods marked, return by
calendar year, the crash switch through time, and quintiles of the final book's signal. The test
period is reported here, not selected on: the books were fixed before it was run.
"""
import hashlib, os, subprocess, sys, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
warnings.simplefilter("ignore")
LAB = os.environ.get("ALPHA_LAB", os.path.expanduser("~/dev/alpha_lab"))
sys.path.insert(0, LAB)
import eval as ev
from qex import qex, compute_context

PERIODS = [("inspection", "1999-01-01", "2003-12-31"), ("validation", "2004-01-01", "2017-12-31"), ("test", "2018-01-01", "2026-08-11")]
BOOKS = {"seed": "318c23d", "final": "b89945f", "T55": "5596bb7"}          # commits of alpha.qex in the lab
EXPR = {k: " ".join(subprocess.check_output(["git", "-C", LAB, "show", f"{c}:alpha.qex"], text=True).split()) for k, c in BOOKS.items()}
# the final book's signal before the cube: residual momentum under the switch, minus the 1-month sector reversal
SIGNAL = EXPR["final"].replace("in decay_linear(power(a, 3), 3)", "in a")

CACHE = os.environ.get("CACHE", os.path.join(LAB, "logs", "analysis-cache")); os.makedirs(CACHE, exist_ok=True)
def cached(key, fn):
    p = f"{CACHE}/{hashlib.md5(key.encode()).hexdigest()[:12]}.parquet"
    if os.path.exists(p):
        return pd.read_parquet(p)
    out = fn(); out.to_parquet(p); return out

data = ev.load("1998-01-01", PERIODS[-1][2])
r1 = data["close"].pct_change(fill_method=None)
fwd = r1.shift(-1).loc["1999":]
member = data["member"].loc["1999":].notna()
spy = data["market"].pct_change(fill_method=None).loc["1999":]
ew = r1.where(data["member"].notna()).mean(axis=1).loc["1999":]                # equal-weight market of members
W = {k: cached("book:" + e, lambda e=e: ev.build_book(qex(e), data, ev.SETTINGS, start="1999-01-01")) for k, e in EXPR.items()}
P = pd.DataFrame({k: (w * fwd.loc[w.index]).sum(axis=1) for k, w in W.items()})
T = pd.DataFrame({k: ev.turnover(w) for k, w in W.items()})
# the final book's crash switch, its momentum weight w, on the member market as a name that is a member all along
# sees it (a name's ts_sum and ts_std cover only its member days); shifted a day, so sw on day t is the state the
# book traded on that day (delay 1)
mk = r1.where(data["member"].notna()).mean(axis=1)
m1, v21, v252 = mk.rolling(252, min_periods=20).sum(), mk.rolling(21, min_periods=20).std(), mk.rolling(252, min_periods=20).std()
sw = pd.Series(np.where(v21 > v252, (10 * m1).clip(-1, 1), (10 * m1 + 1).clip(-1, 1)), index=mk.index).shift(1).reindex(P.index)
def _signal():
    with compute_context():
        return qex(SIGNAL).evaluate(data).loc["1999":]
sig = cached("signal:" + SIGNAL, _signal)

# ── statistics ─────────────────────────────────────────────────────────────
sr = lambda x: x.mean() / x.std() * np.sqrt(252)
maxdd = lambda x: (x.cumsum() - x.cumsum().cummax()).min()      # constant book: P&L adds up
out = []
def table(title, df):
    s = df.to_string(index=False, float_format=lambda x: f"{x:.3f}")
    out.append(f"{title}\n{s}\n"); print(f"\n{title}\n{s}")

rows = []
for k in BOOKS:
    for per, a, b in PERIODS:
        p, t = P[k][a:b], T[k][a:b]
        rows.append(dict(book=k, period=per, sharpe=sr(p), ret_yr=p.mean() * 252, turnover=t.mean(), margin_bps=p.sum() / t.sum() * 1e4,
                         fitness=ev.fitness(p, t), sharpe_2bps=sr(p - 2e-4 * t), sharpe_5bps=sr(p - 5e-4 * t), sharpe_10bps=sr(p - 1e-3 * t),
                         net10_yr=(p - 1e-3 * t).mean() * 252, maxdd=maxdd(p), corr_spy=p.corr(spy[a:b]), corr_ew=p.corr(ew[a:b])))
table("books by period (cost-free unless marked; returns on gross one)", pd.DataFrame(rows))

# where the crash switch sat, and what each state earned
state = pd.Series(np.where(sw >= 0.999, "momentum", np.where(sw > 0, "shrunk", "reversal")), index=sw.index)
rows = []
for per, a, b in PERIODS:
    for st in ("momentum", "shrunk", "reversal"):
        m = state[a:b] == st
        for k in ("final", "seed"):
            p = P[k][a:b][m]
            rows.append(dict(period=per, state=st, book=k, share_of_days=m.mean(), sharpe=sr(p) if len(p) > 20 else np.nan,
                             ret_yr=p.mean() * 252 if len(p) else np.nan, pnl_share=p.sum() / P[k][a:b].sum()))
table("by switch state (w = 1 momentum, 0 < w < 1 shrunk, w <= 0 reversal)", pd.DataFrame(rows))
episodes = [("2000-02 bear", "2000-03-01", "2002-10-31"), ("2008 crash", "2008-09-01", "2009-02-27"), ("2009 junk rally", "2009-03-01", "2009-06-30"),
            ("Q4 2018", "2018-10-01", "2019-01-31"), ("COVID", "2020-02-15", "2020-05-31"), ("2022 bear", "2022-01-01", "2022-12-31")]
rows = [dict(episode=n, start=a, end=b, final=P["final"][a:b].sum(), seed=P["seed"][a:b].sum(), mean_w=sw[a:b].mean(),
             reversal_days=(sw[a:b] <= 0).mean()) for n, a, b in episodes]
table("episodes: cumulative P&L on gross one, mean switch weight", pd.DataFrame(rows))

# what the final book holds
wf = W["final"]
rows = []
for per, a, b in PERIODS:
    w = wf[a:b]; w = w[w.abs().sum(axis=1) > 0]
    rows.append(dict(period=per, names_long=(w > 0).sum(axis=1).mean(), names_short=(w < 0).sum(axis=1).mean(),
                     effective_n=(1 / (w ** 2).sum(axis=1)).mean(), days_with_a_name_at_cap=(w.abs().max(axis=1) >= 0.0499).mean(),
                     top10_share=w.abs().apply(lambda s: s.nlargest(10).sum(), axis=1).mean(), holding_days=1 / T["final"][a:b].mean(),
                     beta_spy=np.cov(P["final"][a:b], spy[a:b].fillna(0))[0, 1] / spy[a:b].var(),
                     up_days_ret_yr=P["final"][a:b][ew[a:b] > 0].mean() * 252, down_days_ret_yr=P["final"][a:b][ew[a:b] <= 0].mean() * 252))
table("final book holdings", pd.DataFrame(rows))
yr = P.groupby(P.index.year).sum()
table("cost-free return by calendar year", yr.rename_axis("year").reset_index())

# does the signal sort returns? quintiles of the pre-cube signal among members, next-day return vs the member average
rows = {}
for per, a, b in PERIODS:
    s = sig[a:b].where(member[a:b]); f = fwd[a:b].where(member[a:b])
    q = s.rank(axis=1, pct=True)
    uni = f.where(s.notna()).mean(axis=1)
    rows[per] = [((f.where((q > (k - 1) / 5) & (q <= k / 5)).mean(axis=1) - uni).mean() * 252) for k in range(1, 6)]
qt = pd.DataFrame(rows, index=[f"Q{i}" for i in range(1, 6)])
table("final book's signal (before the cube): quintile return vs members, annualized, next day", qt.rename_axis("quintile").reset_index())
open("lab/stats.txt", "w").write("\n".join(out))

# ── charts, in the site's palette ──────────────────────────────────────────
INK, INK2, MUTED, RULE, ACCENT, RED = "#e8eaf0", "#c0c4cf", "#6b7280", "#2a3344", "#3ee87a", "#ff6b4a"
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
            ax.text(pd.Timestamp(a) + (pd.Timestamp(b) - pd.Timestamp(a)) / 2, ymax_frac, per, transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=10, color=INK2)
YEARS = (2000, 2004, 2008, 2012, 2016, 2020, 2024)
def years(ax):
    ax.set_xticks(pd.to_datetime([f"{y}-01-01" for y in YEARS])); ax.set_xticklabels([str(y) for y in YEARS]); ax.tick_params(labelsize=10)

# cumulative P&L, % of gross one (a constant book, so P&L adds up)
fig, ax = plt.subplots(figsize=(9, 5))
shade(ax)
lines = [(P["final"].cumsum(), ACCENT, "-", 2, "final book, cost-free"),
         ((P["final"] - 1e-3 * T["final"]).cumsum(), MUTED, "-", 2, "final book, net of 10 bps"),
         (P["seed"].cumsum(), INK2, "--", 1.2, "seed, cost-free")]
for s, color, ls, lw, lab in lines:
    s = s.iloc[::3]
    ax.plot(s.index, s.values, color=color, lw=lw, ls=ls, label=lab)
    ax.annotate(f"{s.iloc[-1]:+.0%}", (s.index[-1], s.iloc[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=10, color=INK2)
ax.axhline(0, color=RULE, lw=1, zorder=0)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
ax.set_title("cumulative P&L of a dollar-neutral book held at gross one", loc="left", fontsize=11, pad=10)
ax.set_ylabel("cumulative P&L, % of gross", fontsize=10)
years(ax); ax.set_xlim(pd.Timestamp("1998-10-01"), P.index[-1] + pd.Timedelta(days=900))
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=3, frameon=False, fontsize=10, handlelength=1.8)
finish(fig, "gross-vs-net.svg")

# return by calendar year, final book cost-free
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.grid(axis="x", visible=False)
y = yr["final"]
shade(ax)
ax.bar(pd.to_datetime([f"{d}-07-01" for d in y.index]), y.values, width=250, color=[ACCENT if v >= 0 else RED for v in y.values], zorder=3)
ax.axhline(0, color=RULE, lw=1, zorder=2)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
ax.set_title("final book: cost-free return on gross one by calendar year (2026 to Aug 11)", loc="left", fontsize=11, pad=10)
ax.set_xticks(pd.to_datetime([f"{d}-07-01" for d in y.index[1::2]])); ax.set_xticklabels([str(d)[2:] for d in y.index[1::2]]); ax.tick_params(labelsize=10)
ax.set_ylim(min(y.min(), 0) - 0.03, y.max() + 0.08)
finish(fig, "by-year.svg")

# the crash switch through time: the member market, and the momentum weight w
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True, gridspec_kw=dict(height_ratios=[1.4, 1], hspace=0.12))
mkt = (1 + ew.fillna(0)).cumprod()
rev = sw <= 0
spans = list(zip(rev.index[rev & ~rev.shift(1, fill_value=False)], rev.index[rev & ~rev.shift(-1, fill_value=False)]))
for ax in (a1, a2):
    shade(ax, labels=ax is a1)
    for s, e in spans:
        ax.axvspan(s, e, color=RED, alpha=0.18, lw=0, zorder=1)
a1.plot(mkt.index, mkt.values, color=INK2, lw=1.4)
a1.set_yscale("log"); a1.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
a1.set_yticks([1, 2, 4, 8, 16, 32]); a1.set_yticklabels(["1", "2", "4", "8", "16", "32"])
a1.set_ylabel("member market, log", fontsize=10)
a1.set_title("the crash switch: momentum weight w, and the equal-weight market of members", loc="left", fontsize=11, pad=10)
a2.plot(sw.index, sw.values, color=ACCENT, lw=1)
a2.axhline(0, color=RULE, lw=1, zorder=2)
a2.set_ylim(-1.1, 1.1); a2.set_yticks([-1, 0, 1]); a2.set_yticklabels(["−1 reversal", "0", "+1 momentum"])
years(a2)
finish(fig, "crash-switch.svg")

# quintiles of the signal
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.grid(axis="x", visible=False)
x = np.arange(5); wdt = 0.26
for i, (per, color) in enumerate([("inspection", MUTED), ("validation", ACCENT), ("test", INK2)]):
    ax.bar(x + (i - 1) * wdt, qt[per].values, width=wdt, color=color, zorder=3, label=per)
ax.axhline(0, color=RULE, lw=1, zorder=2)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
ax.set_title("final book's signal: next-day return by quintile, relative to members, annualized", loc="left", fontsize=11, pad=10)
ax.set_xticks(x); ax.set_xticklabels(["Q1\nshorted", "Q2", "Q3", "Q4", "Q5\nowned"]); ax.tick_params(labelsize=10)
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=10, handlelength=1.6)
finish(fig, "quintiles.svg")

# the cube: the final book with its power changed, everything else fixed
POWERS = {"linear, a": "a", "signed square, a·|a|": "a * abs(a)", "cube, a³": "power(a, 3)", "fifth power, a⁵": "power(a, 5)"}
PW = {}
for lab, f in POWERS.items():
    e = EXPR["final"].replace("power(a, 3)", f)
    PW[lab] = cached("book:" + e, lambda e=e: ev.build_book(qex(e), data, ev.SETTINGS, start="1999-01-01"))
rows = []
for lab, w in PW.items():
    p, t = (w * fwd.loc[w.index]).sum(axis=1), ev.turnover(w)
    v = w["2004":"2017"]; v = v[v.abs().sum(axis=1) > 0]
    srt = -np.sort(-v.abs().values, axis=1)                                  # each day's |weights|, largest first
    rows.append(dict(power=lab, top100_share=srt[:, :100].sum(axis=1).mean(), effective_n=(1 / (v ** 2).sum(axis=1)).mean(),
                     days_at_cap=(srt[:, 0] >= 0.0499).mean(),
                     **{f"{per}_{m}": f(p[a:b], t[a:b]) for per, a, b in PERIODS[1:]
                        for m, f in (("sharpe", lambda p, t: sr(p)), ("ret", lambda p, t: p.mean() * 252), ("turnover", lambda p, t: t.mean()),
                                     ("sharpe10", lambda p, t: sr(p - 1e-3 * t)))}))
cube = pd.DataFrame(rows)
table("the final book with its power changed (concentration on validation)", cube)
open("lab/stats.txt", "w").write("\n".join(out))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 4.0), gridspec_kw=dict(width_ratios=[1, 1.15], wspace=0.32))
rk = sig.shift(1)["2004":"2017"].where(member["2004":"2017"]).rank(axis=1, pct=True)  # rank on the signal the book traded (delay 1)
ends = (rk <= 0.05) | (rk > 0.95)                                               # the 5% most extreme stocks on each side
tails = [(w.loc["2004":"2017"].reindex(columns=rk.columns).abs().where(ends).sum(axis=1)
          / w.loc["2004":"2017"].abs().sum(axis=1)).mean() for w in PW.values()]
x = np.arange(len(PW))
a1.bar(x, tails, width=0.6, color=[ACCENT if "cube" in k else MUTED for k in PW], zorder=3)
for xi, t in zip(x, tails):
    a1.text(xi, t + 0.015, f"{t:.0%}", ha="center", va="bottom", fontsize=10, color=INK2)
a1.grid(axis="x", visible=False); a1.set_ylim(0, 1)
a1.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
a1.set_xticks(x); a1.set_xticklabels(["a", "a·|a|", "a³", "a⁵"]); a1.tick_params(labelsize=10)
a1.set_title("share of the book in the 10% most\nextreme stocks, 5% each side", loc="left", fontsize=10.5, pad=8)
x = np.arange(len(PW)); wd = 0.38
for i, (per, c) in enumerate((("validation", ACCENT), ("test", INK2))):
    a2.bar(x + (i - 0.5) * wd, cube[f"{per}_ret"].values, width=wd, color=c, zorder=3, label=per)
    for xi, (r, s) in enumerate(zip(cube[f"{per}_ret"], cube[f"{per}_sharpe"])):
        a2.text(xi + (i - 0.5) * wd, r + 0.004, f"{s:.2f}", ha="center", va="bottom", fontsize=8.5, color=INK2)
a2.grid(axis="x", visible=False); a2.axhline(0, color=RULE, lw=1)
a2.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
a2.set_xticks(x); a2.set_xticklabels(["a", "a·|a|", "a³", "a⁵"]); a2.tick_params(labelsize=10)
a2.set_title("return per year, Sharpe on each bar", loc="left", fontsize=10.5, pad=8)
a2.legend(frameon=False, fontsize=9, loc="upper left", handlelength=1.2)
finish(fig, "cube.svg")

# weekly P&L of the final book and the seed, for bayes.py
wk = P[["final", "seed"]].loc["2004":].resample("W-FRI").sum()
wk = wk[wk.index <= pd.Timestamp(PERIODS[-1][2]) + pd.Timedelta(days=6)]
wk.rename_axis("week").to_csv("lab/weekly_pnl.csv", float_format="%.6f")
print("wrote lab/weekly_pnl.csv", len(wk), "weeks")

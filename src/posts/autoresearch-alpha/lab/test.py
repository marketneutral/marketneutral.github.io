"""The one run on the untouched period, 2018-01-01 to 2026-08-11. The human runs this once, at the end.

    python test.py                      # alpha.qex, i.e. the final kept book
    python test.py "<expression>"       # any expression, e.g. the seed for comparison

Same book as eval.py (delay 1, point-in-time universe members with a price only, dollar-neutral,
gross exactly one every day, 5% cap per name, daily rebalance); P&L is cost-free and is also shown
net of 2 and 10 bps per unit of turnover. Warmup from 2017 so the 1-year windows are full on day
one. Nothing here feeds back into the loop.
"""
import sys, warnings
import numpy as np, pandas as pd
import eval as ev
warnings.simplefilter("ignore", FutureWarning)

WARMUP, START, END = "2017-01-01", "2018-01-01", "2026-08-11"

def main(expr):
    expr = " ".join(expr.split())
    data = ev.load(WARMUP, END)
    pnl, to, breadth = ev.book(expr, data, START)
    cum = pnl.cumsum()                                   # constant book: P&L adds up
    dd = (cum - cum.cummax()).min()
    print(f"2018-2026  Sharpe {ev.sharpe(pnl):.2f}  fitness {ev.fitness(pnl, to):.2f}  return/yr {pnl.mean() * 252:+.1%}  turnover {to.mean():.2f}  "
          f"margin {ev.margin_bps(pnl, to):.1f} bps  breadth {int(breadth.median())}  max drawdown {dd:+.1%}")
    for bps in (2, 10):
        n = pnl - bps / 1e4 * to
        print(f"           at {bps:2d} bps: Sharpe {ev.sharpe(n):.2f}  net/yr {n.mean() * 252:+.1%}")
    print("return by year (cost-free):", {y: f"{v:+.1%}" for y, v in pnl.groupby(pnl.index.year).sum().items()})
    rets = data["close"].pct_change(fill_method=None).where(data["member"].notna())   # members only
    mkt = rets.mean(axis=1)
    crash = ((mkt.rolling(504).sum() < 0) & (mkt.rolling(21).std() > mkt.rolling(252).std())).loc[pnl.index]
    disp = rets.loc[pnl.index].std(axis=1)
    hi = disp > disp.rolling(252, min_periods=60).median()
    byr = lambda m: f"Sharpe {ev.sharpe(pnl[m]):5.2f} return/yr {pnl[m].mean() * 252:+6.1%} ({int(m.sum())} days)"
    print(f"dispersion high {byr(hi)};  low {byr(~hi)}")
    print(f"crash state     {byr(crash)};  calm {byr(~crash)}")
    return pnl

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else open("alpha.qex").read())

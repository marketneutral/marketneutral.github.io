"""Helpers for the agent over the inspection period, 1999-01-01 to 2003-12-31 (1998 is warmup).

    python explore.py                      # score alpha.qex on 1999-2003 as eval.py builds the book, IC by horizon
    python explore.py "<expression>"       # same for any expression
    python -c "import explore; d = explore.data(); ..."   # raw 1998-2003 OHLCV, member, mcap, sector

Nothing after 2003-12-31 is loaded here. The validation and test periods are
not available to the agent by any route.
"""
import sys
import numpy as np, pandas as pd
from qex import qex, compute_context
import eval as ev

START, END = "1998-01-01", "2003-12-31"

def data():
    return ev.load(START, END)

def score(expr, start="1999-01-01"):
    d = data()
    expr = " ".join(expr.split())
    pnl, to, breadth = ev.book(expr, d, start)
    net = pnl - ev.TC * to
    with compute_context():
        # delay 1, as the book trades it: yesterday's signal against returns from today's close, members only
        sig = qex(expr).evaluate(d).where(d["member"].notna()).shift(1).loc[start:]
    ic = {k: sig.corrwith((d["close"].shift(-k) / d["close"] - 1).loc[start:], axis=1, method="spearman").mean() for k in (1, 2, 5, 10, 20)}
    ac = sig.corrwith(sig.shift(1), axis=1, method="spearman").mean()
    print(f"1999-2003  Sharpe {ev.sharpe(pnl):.2f}  fitness {ev.fitness(pnl, to):.2f}  return/yr {pnl.mean()*252:+.1%}  turnover {to.mean():.2f}  "
          f"margin {ev.margin_bps(pnl, to):.1f} bps  at 2 bps: Sharpe {ev.sharpe(net):.2f} net/yr {net.mean()*252:+.1%}  breadth {int(breadth.median())}")
    print("rank IC by horizon:", {k: round(v, 4) for k, v in ic.items()}, f" lag-1 autocorr {ac:.2f}")
    print("return by year (cost-free):", (pnl.groupby(pnl.index.year).sum()).round(3).to_dict())
    return pnl

if __name__ == "__main__":
    score(sys.argv[1] if len(sys.argv) > 1 else open("alpha.qex").read())

"""Frozen evaluator: purged, randomized cross-validation of alpha.qex on the validation period.

    timeout 120 python eval.py

The book is qex's demean(<alpha.qex> + 0 * close()): the agent's expression,
restricted to names with a price and made dollar-neutral by the engine's own
cross-sectional operator, held for one
close-to-close day and rebalanced daily. Gross exposure averages one over the
validation period but may vary day to day, so an expression can size itself. Costs: 2 bps per unit
of turnover.

Validation, 2000-01-01 to 2017-12-31, is cut into 12 contiguous blocks. Each
call deals the blocks at random into 6 folds of 2 blocks, and purges an embargo
of 21 trading days from both ends of every block so that no rolling window or
forward return straddles a fold boundary. Each fold scores

    utility = net Sharpe at 2 bps  +  10 * net annual return on GMV
              -  0.003 * nodes in the parsed expression

and the evaluator prints the median fold and the worst fold, each averaged over
50 fresh random partitions, so there is no fixed hold-out to climb. It also prints the
Sharpe split by market-dispersion regime, by the Daniel-Moskowitz crash state
and by calendar half, so that the claim's prediction can be checked, and the deflated Sharpe ratio of this
expression given the number of trials in results.tsv so far.

The agent never sees prices after 1999-12-31; this file is the only thing
that touches them. The test period, 2018 on, is not loaded here at all.
"""
import os, sys, time, warnings
import numpy as np, pandas as pd
from scipy.stats import norm, skew, kurtosis
from qex import qex, compute_context, SignalGraph, demean, close
warnings.simplefilter("ignore", FutureWarning)

HERE = os.path.dirname(os.path.abspath(__file__))
WARMUP, VAL_START, VAL_END = "1999-01-01", "2000-01-01", "2017-12-31"
BLOCKS, FOLDS, EMBARGO, PARTITIONS = 12, 6, 21, 50
TC, NODE_CHARGE, RETURN_WEIGHT, MIN_BREADTH = 0.0002, 0.003, 10, 50

def load(start, end):
    d = {f: pd.read_parquet(f"{HERE}/data/{f}.parquet").loc[start:end] for f in ["open", "high", "low", "close", "volume"]}
    sec = pd.read_parquet(f"{HERE}/data/sectors.parquet")["sector"].reindex(d["close"].columns)
    d["sector"] = pd.DataFrame([sec.values] * len(d["close"]), index=d["close"].index, columns=d["close"].columns)
    return d

def book(expr, data, start):
    """Daily gross return, turnover and breadth of the enforced book."""
    with compute_context():
        # + 0 * close() makes a name with no price NaN, whatever the expression did (where() turns NaN into
        # its else-branch); demean() then makes each day dollar-neutral over the names that exist. All qex.
        w = demean(qex(expr) + 0 * close()).evaluate(data)
    w = w.loc[start:].fillna(0)
    w = w / w.abs().sum(axis=1).mean()                     # gross averages one; day-to-day it may vary
    fwd = data["close"].pct_change(fill_method=None).shift(-1).loc[w.index]
    return (w * fwd).sum(axis=1), w.diff().abs().sum(axis=1).fillna(0), (w != 0).sum(axis=1)

sharpe = lambda x: x.mean() / x.std() * np.sqrt(252) if len(x) > 1 and x.std() > 0 else float("nan")

def folds(index, rng):
    """Deal contiguous blocks into folds at random; purge an embargo at every block edge."""
    blocks = np.array_split(np.arange(len(index)), BLOCKS)
    blocks = [b[EMBARGO:-EMBARGO] for b in blocks]
    order = rng.permutation(BLOCKS)
    return [np.concatenate([blocks[i] for i in order[k::FOLDS]]) for k in range(FOLDS)]

def deflated_sharpe(net, trials_sharpe):
    """Bailey & López de Prado (2014): probability the Sharpe is real, given the trials run so far."""
    sr = net.mean() / net.std()                              # daily
    n, t = len(trials_sharpe), len(net)
    if n < 2 or np.std(trials_sharpe) == 0:
        return float("nan")
    v = np.var(np.asarray(trials_sharpe) / np.sqrt(252), ddof=1)
    g = 0.5772156649
    sr0 = np.sqrt(v) * ((1 - g) * norm.ppf(1 - 1 / n) + g * norm.ppf(1 - 1 / (n * np.e)))
    g3, g4 = skew(net), kurtosis(net, fisher=False)
    return float(norm.cdf((sr - sr0) * np.sqrt(t - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr**2)))

def main():
    t0 = time.time()
    expr = " ".join(open(f"{HERE}/alpha.qex").read().split())
    g = SignalGraph(); g.add_signal(qex(expr), name="alpha")
    nodes = g.stats()["total_nodes"]
    data = load(WARMUP, VAL_END)
    gross, to, breadth = book(expr, data, VAL_START)
    net = gross - TC * to
    rng = np.random.default_rng(int.from_bytes(os.urandom(8), "little"))
    medians, worsts, rows = [], [], []
    for p in range(PARTITIONS):
        util = []
        for k, ix in enumerate(folds(net.index, rng)):
            n, b = net.iloc[ix], breadth.iloc[ix]
            u = float("-inf") if b.median() < MIN_BREADTH else sharpe(n) + RETURN_WEIGHT * n.mean() * 252 - NODE_CHARGE * nodes
            util.append(u)
            if p == 0:
                yrs = sorted({d.year for d in net.index[ix[::200]]})
                rows.append(f"  fold {k}: utility {u:6.3f}  net/yr {n.mean() * 252:+6.1%}  gross Sharpe {sharpe(gross.iloc[ix]):5.2f}  net Sharpe {sharpe(n):5.2f}  turnover {to.iloc[ix].mean():.2f}  breadth {int(b.median())}  years {yrs[0]}-{yrs[-1]} ({len(yrs)} touched)")
        medians.append(np.median(util)); worsts.append(np.min(util))
    print(f"utility: {np.mean(medians):.3f}")
    print(f"worst:   {np.mean(worsts):.3f}")
    rows.insert(0, f"  first of {PARTITIONS} random partitions:")
    print(f"sharpe:  {sharpe(net):.3f}  (whole validation, net)   net/yr {net.mean() * 252:+.1%}  gross Sharpe {sharpe(gross):.2f}  turnover {to.mean():.2f}  nodes {nodes}  charge {NODE_CHARGE * nodes:.3f}  seconds {time.time() - t0:.0f}")
    print("\n".join(rows))
    # where the claim can be checked: by market-dispersion regime and by calendar half
    disp = data["close"].pct_change(fill_method=None).loc[net.index].std(axis=1)
    hi = disp > disp.rolling(252, min_periods=60).median()
    mid = net.index[len(net) // 2]
    mkt = data["close"].pct_change(fill_method=None).mean(axis=1)                       # equal-weight market
    crash = ((mkt.rolling(504).sum() < 0) & (mkt.rolling(21).std() > mkt.rolling(252).std())).loc[net.index]
    byr = lambda m: f"Sharpe {sharpe(net[m]):5.2f} net/yr {net[m].mean() * 252:+6.1%} ({int(m.sum())} days)"
    print(f"by regime: dispersion high  {byr(hi)};  low  {byr(~hi)}")
    print(f"           crash state      {byr(crash)};  calm {byr(~crash)}   (market down over 2y and 1m vol above 1y vol)")
    print(f"           first half       {byr(net.index < mid)};  second half {byr(net.index >= mid)}")
    try:
        log = pd.read_csv(f"{HERE}/results.tsv", sep="\t")
        trials = log["sharpe"].dropna().tolist() + [sharpe(net)]
        print(f"trials: {len(trials)}  deflated Sharpe probability of this expression: {deflated_sharpe(net, trials):.3f}")
    except Exception as e:
        print(f"trials: unknown ({e})")

if __name__ == "__main__":
    main()

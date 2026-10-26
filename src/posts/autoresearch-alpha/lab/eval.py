"""Frozen evaluator: purged, randomized cross-validation of alpha.qex on the validation period.

    ./trial.sh                      # eval.py under the 120 s budget

The book follows the standard simulation of Finding Alphas. The agent's expression is
restricted to names that are in the point-in-time universe and have a price, and is delayed
one day (delay 1): the weight held from close t to close t+1 uses data up to close t-1 only.
Each day it is made dollar-neutral, scaled so gross is exactly one, and truncated so no name
holds more than 5% of the book, repeating until all three hold. The magnitude of the
expression is relative weight within a day, never the size of the book. P&L is cost-free;
costs enter through turnover and margin.

Validation, 2004-01-01 to 2017-12-31, is cut into 12 contiguous blocks. Each
call deals the blocks at random into 6 folds of 2 blocks, and purges an embargo
of 21 trading days from both ends of every block so that no rolling window or
forward return straddles a fold boundary. Each fold scores

    utility = fitness  -  0.003 * nodes in the parsed expression
    fitness = Sharpe * sqrt(|annual return| / max(turnover, 0.125))

or minus infinity if the fold holds fewer than 50 names or trades less than 1% or more than
70% of the book a day. The whole validation book is also checked as a submission would be: it
is eligible if its turnover is in that band and it earns at least 5 bps per dollar traded
(margin). Eligibility is printed on its own line; the scores do not depend on it

and the evaluator prints the median fold and the worst fold, each averaged over
50 fresh random partitions, so there is no fixed hold-out to climb. It also prints the
Sharpe split by market-dispersion regime, by the Daniel-Moskowitz crash state
and by calendar half, so that the claim's prediction can be checked, and the deflated Sharpe ratio of this
expression given the number of trials in results.tsv so far.

The agent never sees prices after 2003-12-31; this file is the only thing
that touches them. The test period, 2018 on, is not loaded here at all.
"""
import os, sys, time, warnings
import numpy as np, pandas as pd
from scipy.stats import norm, skew, kurtosis
from qex import qex, compute_context, SignalGraph, delay, close, field
warnings.simplefilter("ignore", FutureWarning)

HERE = os.path.dirname(os.path.abspath(__file__))
WARMUP, VAL_START, VAL_END = "2003-01-01", "2004-01-01", "2017-12-31"
BLOCKS, FOLDS, EMBARGO, PARTITIONS = 12, 6, 21, 50
TRUNCATION, TURNOVER_BAND, MIN_MARGIN_BPS = 0.05, (0.01, 0.70), 5
TC, NODE_CHARGE, MIN_BREADTH = 0.0002, 0.003, 50   # TC: 2 bps, for the printed net figures only

def load(start, end):
    """Every name that is in the universe at some point in [start, end], with its whole price history there.
    sector is the name's sector on days it is a member and NaN otherwise, so group operators see members only."""
    member = pd.read_parquet(f"{HERE}/data/member.parquet").loc[start:end]
    names = member.columns[member.notna().any()]
    d = {f: pd.read_parquet(f"{HERE}/data/{f}.parquet", columns=list(names)).loc[start:end] for f in ["open", "high", "low", "close", "volume", "mcap"]}
    d["member"] = member[names]
    sec = pd.read_parquet(f"{HERE}/data/sectors.parquet")["sector"].reindex(names)
    d["sector"] = pd.DataFrame(np.where(d["member"].notna(), sec.to_numpy(dtype=object)[None, :], None), index=member.index, columns=names)
    return d

def to_book(raw, cap=TRUNCATION, rounds=50):
    """Each day: dollar-neutral over the names with a value, gross exactly one, no name above cap.
    Demean, scale and clip, repeated until all three hold (clipping alone breaks the other two)."""
    w = raw.to_numpy(dtype=float).copy()
    ok = np.isfinite(w)
    w[~ok] = 0.0
    n = ok.sum(axis=1, keepdims=True)
    for _ in range(rounds):
        w = np.where(ok, w - w.sum(axis=1, keepdims=True) / np.maximum(n, 1), 0.0)
        g = np.abs(w).sum(axis=1, keepdims=True)
        w = np.divide(w, g, out=np.zeros_like(w), where=g > 0)
        if np.abs(w).max() <= cap + 1e-9:
            break
        w = np.clip(w, -cap, cap)
    return pd.DataFrame(w, index=raw.index, columns=raw.columns)

def book(expr, data, start):
    """Daily cost-free P&L, turnover and breadth of the enforced book."""
    with compute_context():
        # + 0 * close() + 0 * field('member') makes a name with no price, or outside the universe that day, NaN
        # whatever the expression did (where() turns NaN into its else-branch); delay(., 1) then moves it to the
        # next day, so the weight for day t is built from data up to t-1 (delay 1).
        raw = delay(qex(expr) + 0 * close() + 0 * field("member"), 1).evaluate(data)
    raw = raw.where(data["close"].notna())                  # a name with no price today cannot be traded today
    w = to_book(raw.loc[start:])
    fwd = data["close"].pct_change(fill_method=None).shift(-1).loc[w.index]
    return (w * fwd).sum(axis=1), w.diff().abs().sum(axis=1).fillna(0), (w != 0).sum(axis=1)

def fitness(pnl, to):
    """Finding Alphas: Sharpe * sqrt(|annual return| / max(turnover, 0.125))."""
    return sharpe(pnl) * np.sqrt(abs(pnl.mean() * 252) / max(to.mean(), 0.125))

def margin_bps(pnl, to):
    """P&L per dollar traded, in basis points."""
    return pnl.sum() / to.sum() * 1e4 if to.sum() > 0 else float("nan")

in_band = lambda to: TURNOVER_BAND[0] <= to.mean() <= TURNOVER_BAND[1]

def fold_utility(pnl, to, breadth, nodes):
    if breadth.median() < MIN_BREADTH or not in_band(to):
        return float("-inf")
    return fitness(pnl, to) - NODE_CHARGE * nodes

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
    pnl, to, breadth = book(expr, data, VAL_START)
    net = pnl - TC * to
    rng = np.random.default_rng(int.from_bytes(os.urandom(8), "little"))
    medians, worsts, rows = [], [], []
    for p in range(PARTITIONS):
        util = []
        for k, ix in enumerate(folds(pnl.index, rng)):
            f, t, b = pnl.iloc[ix], to.iloc[ix], breadth.iloc[ix]
            u = fold_utility(f, t, b, nodes)
            util.append(u)
            if p == 0:
                yrs = sorted({d.year for d in pnl.index[ix[::200]]})
                rows.append(f"  fold {k}: utility {u:6.3f}  fitness {fitness(f, t):5.2f}  Sharpe {sharpe(f):5.2f}  return/yr {f.mean() * 252:+6.1%}  turnover {t.mean():.2f}  margin {margin_bps(f, t):5.1f} bps  breadth {int(b.median())}  years {yrs[0]}-{yrs[-1]} ({len(yrs)} touched)")
        medians.append(np.median(util)); worsts.append(np.min(util))
    print(f"utility: {np.mean(medians):.3f}")
    print(f"worst:   {np.mean(worsts):.3f}")
    m = margin_bps(pnl, to)
    ok = in_band(to) and m >= MIN_MARGIN_BPS
    print(f"eligible: {'yes' if ok else 'no'}  (whole validation: margin {m:.1f} bps, needs >= {MIN_MARGIN_BPS}; "
          f"turnover {to.mean():.2f}, needs {TURNOVER_BAND[0]:.2f}-{TURNOVER_BAND[1]:.2f})")
    rows.insert(0, f"  first of {PARTITIONS} random partitions:")
    print(f"sharpe:  {sharpe(pnl):.3f}  (whole validation, cost-free)   fitness {fitness(pnl, to):.2f}  return/yr {pnl.mean() * 252:+.1%}  turnover {to.mean():.2f}  margin {margin_bps(pnl, to):.1f} bps  "
          f"at 2 bps: Sharpe {sharpe(net):.2f} net/yr {net.mean() * 252:+.1%}  nodes {nodes}  charge {NODE_CHARGE * nodes:.3f}  seconds {time.time() - t0:.0f}")
    print("\n".join(rows))
    # where the claim can be checked: by market-dispersion regime and by calendar half
    rets = data["close"].pct_change(fill_method=None).where(data["member"].notna())  # members only
    disp = rets.loc[pnl.index].std(axis=1)
    hi = disp > disp.rolling(252, min_periods=60).median()
    mid = pnl.index[len(pnl) // 2]
    mkt = rets.mean(axis=1)                                                              # equal-weight market of members
    crash = ((mkt.rolling(504).sum() < 0) & (mkt.rolling(21).std() > mkt.rolling(252).std())).loc[pnl.index]
    byr = lambda m: f"Sharpe {sharpe(pnl[m]):5.2f} return/yr {pnl[m].mean() * 252:+6.1%} ({int(m.sum())} days)"
    print(f"by regime: dispersion high  {byr(hi)};  low  {byr(~hi)}")
    print(f"           crash state      {byr(crash)};  calm {byr(~crash)}   (market down over 2y and 1m vol above 1y vol)")
    print(f"           first half       {byr(pnl.index < mid)};  second half {byr(pnl.index >= mid)}")
    try:
        log = pd.read_csv(f"{HERE}/results.tsv", sep="\t")
        trials = log["sharpe"].dropna().tolist() + [sharpe(pnl)]
        print(f"trials: {len(trials)}  deflated Sharpe probability of this expression: {deflated_sharpe(pnl, trials):.3f}")
    except Exception as e:
        print(f"trials: unknown ({e})")

if __name__ == "__main__":
    main()

# Summary: trials T26 to T60

Resumed from T22 (utility 1.141, worst 0.046) and ran 35 trials. Four were
kept. The final book, T58, scores utility 1.740 and worst fold 0.477 on the
validation period, net Sharpe 1.22 at 2 bps, net 4.8% a year on gross, turnover
0.02 a day, 22 nodes. Every fold is positive; the Daniel-Moskowitz crash state
(112 days) has Sharpe 0.91 against 1.23 outside it.

## The final book

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    r1    = returns(1),
    vol   = ts_std(group_demean(r1, 'sector'), 60),
    score = zscore(group_demean(mom / vol, 'sector'))
in ewma(min(score, 0) * abs(score) * rank(returns(21) / vol) / vol / vol, 20)
```

Read it as: short the past-year losers relative to their sector (months 7-12
counted twice), measured and sized in units of sector-residual vol, squared so
the deep losers carry the leg, shorted least when they fell hardest last month
in vol units, smoothed with a 20-day halflife, against an equal-weight long
side of everything else. There is no market-state scaling left in it.

## What was kept and why

| trial | change | utility | worst | why it worked |
|---|---|---|---|---|
| T35 | `ewma(..., 20)` in place of `decay_linear(..., 60)` | 1.242 | 0.122 | Belief 10. The exponential kernel weights the fresh signal and keeps a long tail; the linear window was past the point where smoothing pays (T28). Halflife 10 (T36) trades too much; 30 (T55) is flat. |
| T40 | vol = sector-residual vol, `ts_std(group_demean(r1, 'sector'), 60)` | 1.466 | 0.289 | Belief 11. The signal is sector-relative, so the risk the leg bears is residual; sizing by total vol was punishing names for sector beta they do not carry in the book. Largest single gain of the run (Sharpe 0.83 to 1.06). Market-residual vol was worse in the 1990s; the sector is what matters. |
| T43 | loser leg times `rank(returns(21))` | 1.580 | 0.404 | Belief 2 as a weight (Jegadeesh 1990). On the T22 and T35 bases this tilt lifted the worst fold and the high-dispersion Sharpe but not the median (T26, T37). On the residual-vol base it also lifted the median: residual-vol sizing lets high-beta losers into the leg, and those are the ones that bounce after a crash month. |
| T58 | tilt in vol units, `rank(returns(21) / vol)`, and no dispersion sizing | 1.740 | 0.477 | Combination of two near-misses, as T19 was. T57 (vol-scaled tilt) was 0.006 short of the bar and moved the crash state from 0.60 to 0.91; T53 (removing the T21 dispersion sizing) was +0.027 with 5 fewer nodes, showing the sizing had become redundant once the tilt and residual vol were in. |

## What was learned from the resets

- **The loser leg wants the deep losers.** Squared weight stands (T48 removal
  cost 0.31); cubed thins the leg (T23 earlier); winsorizing the tail does
  nothing (T39); within-sector z-scoring equalizes sectors and loses 0.25 (T47),
  because the sector with the widest momentum spread should dominate the leg.
- **Sector neutrality belongs in the signal only.** Sector-neutral weights lose
  0.10 (T27), half a sector bet in the signal breaks the worst fold (T33), and
  the sector part of the last month's move must stay in the tilt (T45).
- **Time-variation of the leg's size is done by the zscore, nothing else.**
  Removing the zscore costs 0.13 to 0.19 (T34, T60). Dispersion sizing (T21)
  became redundant by T53; faster or squared dispersion (T29, T30), market
  state (T49), the hard crash state (T54), factor momentum and the book's own
  vol (explored) all do nothing or hurt.
- **Price-level anchors fail in this universe.** Distance from the 52-week low
  (T46) loses 0.15, as the 52-week high did in T7: a current-members basket
  bought back everything that hit a low.
- **Tilts that are really market states hurt.** Rising residual vol (T52) and
  the sector-relative tilt (T45) both empty the leg in 2000-02.
- **Constants are on plateaus.** Residual-vol window 60 vs 120 (T44), ewma
  20 vs 30 (T55), months 7-12 weight 2x vs 3x (T56), formation vol window
  (T31), two-month skip (T38): all inside the noise.
- **The 1990s are a poor guide for tilts and timing.** Six tilt or
  normalization variants that the inspection period ranked higher reset in
  validation (T34, T36, T39, T45, T46, T52). The 1990s have no crash and no
  2000-02, so anything that helps in a calm decade and hurts in a rebound
  looks good there. They were right on the structural changes (ewma,
  residual vol, the tilt itself).

## Caveats for the test run

Forty-one scored trials in `results.tsv`; the deflated Sharpe probability of
T58 is 0.99 by the evaluator's count. The basket is current S&P 500 members,
so every number is optimistic, and the loser leg's second half (2009-2017,
Sharpe 1.47) is much stronger than its first (0.92). The crash-state Sharpe of
0.91 rests on 112 days. Trial T32 (20-day vol) scored minus infinity from a
zero-vol name; any shorter vol window needs a floor.

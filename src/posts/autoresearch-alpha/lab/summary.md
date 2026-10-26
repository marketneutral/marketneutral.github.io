# run3 summary (60 trials, T1-T60)

## Final book (b89945f, kept at T54)

```
let mr    = returns(1) * field('member'),
    mk    = mr - demean(mr),
    m1    = ts_sum(mk, 252),
    w     = where(ts_std(mk, 21) > ts_std(mk, 252), max(min(10 * m1, 1), -1), max(min(10 * m1 + 1, 1), -1)),
    b     = ts_beta(returns(1), mk, 504),
    rr    = returns(1) - b * mk,
    mom   = delay(ts_sum(rr, 231), 21),
    score = group_demean(mom, 'sector'),
    a     = decay_linear(w * score, 10) - group_demean(returns(21), 'sector')
in decay_linear(power(a, 3), 3)
```

| | seed | final |
|---|---|---|
| utility (median fold) | -0.091 | 1.473 |
| worst fold | -0.961 | 0.400 |
| Sharpe, whole validation | -0.25 | 1.27 |
| return / turnover / margin | -1.1% / 0.05 / -8 bps | 14.9% / 0.12 / 49 bps |
| eligible | no | yes |
| crash-state Sharpe | -1.96 | 2.92 |
| nodes | 7 | 32 |

In words, the final book is:
- sector-relative residual momentum: 12-1 month returns net of a 504-day market beta;
- a soft crash switch that shrinks the momentum leg and then flips it to reversal in bear markets;
- a sector-relative 1-month reversal sleeve;
- the sum cubed, which concentrates weight where the two sleeves agree;
- a 3-day decay to hold turnover at the fitness floor.

## What was kept, in order, and why

1. **T1, crash switch (belief 7), +0.10.** The seed loses on 2004-2017, mostly in the crash state. Flipping to reversal there turned crash-state Sharpe from -1.96 to +3.3.
2. **T2, drop the final 1/vol (belief 11 removed), +0.31.** The seed weighted by mom/vol². The book became eligible.
3. **T4, 252-day vol for standardizing (belief 4), +0.11.**
4. **T6, 1-month sector-relative reversal sleeve (belief 2 as a sleeve), +0.14.** It spends turnover that fitness doesn't charge below 0.125.
5. **T7, crash state on a 1-year drawdown instead of 2-year, +0.07.**
6. **T8, residual momentum (belief 5), +0.10.** The worst fold improved more than the median, as the belief predicted.
7. **T16, T17, concentration: a·|a| then a³, with a 3-day decay, +0.05 and +0.11.** Gross is fixed and fitness rewards return, so weighting the tails pays. a⁵ was past the peak (T35).
8. **T22, soft switch, +0.11.** The momentum weight is clip(10 × 1y market return) when 1-month vol exceeds 1-year vol. It beat the hard switch on both median and worst, contrary to belief 7's prediction.
9. **T24, beta hedge, +0.10.** Later removed (see T54).
10. **T31, deep-bear rule in the calm branch, +0.17, worst 0.02 → 0.32.** When vol has subsided, momentum still shrinks below a -10% market year and flips below -20%. After a vol spike, 1-month vol falls back under the inflated 1-year vol while losers are still rallying (2009). The vol rule earns the median; the depth rule saves the rebound.
11. **T33, no vol standardization at all (belief 4 removed), +0.05.** Return went from 8% to 13% and worst improved.
12. **T47, 504-day beta for the residual, +0.06.**
13. **T54, remove the beta hedge, +0.10.** After T33/T47 the hedge only diluted the cube, and dropping it saved 12 nodes.

## What the resets taught

- **Belief 7 is the most valuable line in program.md.** Removing the switch (T27) cost 0.65 utility and took worst to -0.51, even in a beta-hedged book. The crash is stock-specific losers rebounding, not a beta event. Refinements that failed:
  - a raw-momentum flip (T11);
  - a sector-level crash state (T53);
  - a loser-only flip (T40);
  - a graded vol offset (T46);
  - a faster flip outside the decay (T45);
  - Barroso-Santa-Clara momentum-vol scaling (T28).
- **Belief 5 is the core.** Raw momentum in the final book (T56) costs 0.9 utility. A 756-day beta was worse than 504 (T48); a separate 252-day hedge beta was worse (T49).
- **Belief 3 holds for the inputs, not for the final book.** Dropping the sector demean of momentum hurt twice (T5, T37), but re-demeaning the cubed book hurt too (T18, T36). The cube's sector tilts are return.
- **Belief 2 holds as stated.** The skip month matters even for residual momentum (T10, -0.15). The reversal sleeve is worth about 0.45 (T52). Its 1:1 weight sits at the optimum (T43 1.5×, T44 0.7×). Novy-Marx 7-12 was worse (T3).
- **Belief 10 holds at the horizons chosen.** Inner decay of 21 (T21) and 5 (T60) were both worse than 10. An outer decay of 5 (T19) bought nothing, and removing it (T57) pushed turnover to 0.17.
- **Not supported here:**
  - belief 8, frog-in-pan (T26, and twice on inspection);
  - belief 9, 52-week high (T20);
  - belief 6 as vol scaling (T28);
  - Nagel vol-scaled reversal (T9, T23: crash days up, median down);
  - size neutrality (T25), residual-vol standardization (T29), the √vol middle step (T32);
  - outside ideas screened on inspection only: seasonality, MAX, volume-attention, earnings-drift proxy, January flip, long-term reversal.
- **1999-2003 inspection is a poor guide for anything that reshapes risk.** It pointed the wrong way for T24, T31, T36 and T40 (T40: +0.31 Sharpe on inspection, -0.58 utility on validation). It was useful mainly to catch broken expressions and turnover.
- **Noise at this level is about ±0.05 utility.** T50 re-scored a node-cheaper but otherwise identical copy of T47 at 0.058 below it. T47's 1.376 and T54's 1.473 were likely favorable draws, which made the 0.03 bar hard to clear afterward.

## For the human: near-misses worth a look

Three changes to the final book lost on median-fold utility by less than the noise but **won on every whole-period measure**:
- **T55: `winsorize(a, 0.002)` before the cube.** Sharpe 1.27 → 1.38, fitness 1.38 → 1.47, worst 0.40 → 0.48.
- **T58: residual reversal `ts_sum(rr, 21)`.** Sharpe 1.32, return 15.6%, fitness 1.47.
- **T51:** the same winsorize on the T47 book.

The combination (T59) didn't add. By the keep rule the final book is b89945f. If the human prefers whole-period Sharpe and worst-fold safety to the median fold, T55 (5596bb7) is the better-behaved book. It is one `winsorize` call away from the final book, and it is untested on 2018+, like everything else.

Trial count for the deflated Sharpe: 60 trials plus the seed. The final book's deflated-Sharpe probability was 0.974.

## Test (2018-01-01 to 2026-08-11), run once by the human after the run

Added after the run, by the human; the agent never saw these numbers. `python test.py` on three
books, so the test period is now spent for this run.

| 2018-2026 | T55 (5596bb7) | final (b89945f) | seed |
|---|---|---|---|
| Sharpe / return | 0.75 / 12.1% | 0.77 / 13.6% | 0.09 / 0.7% |
| Sharpe at 2 / 10 bps | 0.71 / 0.56 (9.0%/yr) | 0.74 / 0.60 (10.5%/yr) | 0.05 / -0.08 |
| turnover / margin | 0.12 / 39 bps | 0.12 / 45 bps | 0.05 / 5 bps |
| max drawdown | -23% | -26% | -20% |
| worst year | 2018 +0.1% | 2018 -1.3% | |

- **Sharpe about halves out of sample**: T55 goes from 1.38 on validation to 0.75. That is
  roughly what 60 trials should cost. The edge is real (the seed earns nothing over the same
  period), but validation overstated its size.
- **The crash switch worked out of sample**, at about half its validation strength. T55's
  P&L by episode:
  - Q4 2018 to Jan 2019: -3.0%, the one miss;
  - Aug-Oct 2019: +13.0%;
  - COVID, Feb-May 2020: +10.2%;
  - 2022 bear, a full year flipped: +11.1%.
  - Sharpe in the reversal state was 2.2 on validation and 1.1 on test.
  - The full-momentum state (76% of days) fell from 1.08 to 0.65.
- **T55 and the final book are equal out of sample.** The winsorize did not matter, but T55 is
  the more diversified book: effective N 147 against 95, and a name sits at the 5% cap on 1% of
  days against 72%.
- **The weak spot is low dispersion**: Sharpe 0.37 there, against 1.04 when dispersion is high.

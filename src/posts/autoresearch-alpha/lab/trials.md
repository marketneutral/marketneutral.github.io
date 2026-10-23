# Trial log: exact expressions

Git commits were denied by the session's permission policy, so this file
records the exact `alpha.qex` of every trial in place of a commit hash. The
`commit` column of `results.tsv` carries the trial tag used here.

## T0 (seed, ec1a051)

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector')
in decay_linear(score / vol, 10)
```

## T1

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector'),
    r1    = returns(1),
    mvol  = ts_std(r1 - demean(r1), 63)
in decay_linear(score / vol, 10) / mvol
```

## T2 (reset)

T1 with `max(score, 0)` in place of `score` in the body.

## T3 (keep)

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector'),
    r1    = returns(1),
    mvol  = ts_std(r1 - demean(r1), 63)
in decay_linear(min(score, 0) / vol, 10) / mvol
```

## T4 (reset)

T3 with `mom = delay(returns(126), 126)` (months 7-12 only).

## T5 (reset)

T3 with `mom = returns(252)` (no skip month).

## T6

```
let r1    = returns(1),
    mkt   = r1 - demean(r1),
    res   = r1 - ts_beta(r1, mkt, 252) * mkt,
    mom   = delay(ts_sum(res, 231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector'),
    mvol  = ts_std(mkt, 63)
in decay_linear(min(score, 0) / vol, 10) / mvol
```
(reset)

## T7

```
let near  = close() / ts_max(high(), 252),
    vol   = volatility(60),
    score = group_demean(near, 'sector'),
    r1    = returns(1),
    mvol  = ts_std(r1 - demean(r1), 63)
in decay_linear(min(score, 0) / vol, 10) / mvol
```
(reset)

## T8

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector'),
    r1    = returns(1),
    mkt   = r1 - demean(r1),
    mvol  = ts_std(mkt, 63),
    crash = (ts_sum(mkt, 504) < 0) & (ts_std(mkt, 21) > ts_std(mkt, 252)),
    book  = decay_linear(min(score, 0) / vol, 10) / mvol
in where(crash, -book, book)
```
(reset)

## T9 (keep)

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector'),
    r1    = returns(1),
    mvol  = ts_std(r1 - demean(r1), 63)
in decay_linear(min(score, 0) / vol, 60) / mvol
```

## T10 (reset)

T9 with `min(score, 0)` not divided by vol in the body.

## T11 (reset)

T9 with `score = group_demean(mom, 'sector')` (no vol standardization in formation).

## T12 (reset)

T9 with `score = demean(mom / vol)` (universe demean, no sector neutrality).

## T13

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector'),
    r1    = returns(1),
    mvol  = ts_std(r1 - demean(r1), 63),
    down  = delay(ts_mean(r1 < 0, 231), 21)
in decay_linear(min(score, 0) * down / vol, 60) / mvol
```
(reset)

## T14

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector'),
    r1    = returns(1),
    leg   = decay_linear(min(score, 0) / vol, 60),
    pnl   = delay(leg, 1) * r1,
    bvol  = ts_std(pnl - demean(pnl), 126)
in leg / bvol
```
(reset)

## T15 (reset, 0.007 short)

T9 with `min(score, 0) / vol / vol` (inverse-variance sizing).

## T16 (reset)

T9 with body `decay_linear(demean(min(score, 0) / vol) / vol, 60) / mvol`.

## T17

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector'),
    r1    = returns(1),
    mkt   = r1 - demean(r1),
    mvol  = ts_std(mkt, 63),
    beta  = ts_beta(r1, mkt, 252),
    w     = demean(decay_linear(min(score, 0) / vol, 60)),
    wb    = w * beta,
    bb    = beta * beta,
    hedge = (wb - demean(wb)) / (bb - demean(bb))
in (w - beta * hedge) / mvol
```
(reset)

## T18 (reset, 0.012 short)

T9 with `score = zscore(group_demean(mom / vol, 'sector'))`.

## T19 (keep)

```
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = zscore(group_demean(mom / vol, 'sector')),
    r1    = returns(1),
    mvol  = ts_std(r1 - demean(r1), 63)
in decay_linear(min(score, 0) / vol / vol, 60) / mvol
```

## T20 (keep)

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    vol   = volatility(60),
    score = zscore(group_demean(mom / vol, 'sector')),
    r1    = returns(1),
    mvol  = ts_std(r1 - demean(r1), 63)
in decay_linear(min(score, 0) / vol / vol, 60) / mvol
```

## T21 (keep)

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    vol   = volatility(60),
    score = zscore(group_demean(mom / vol, 'sector')),
    r1    = returns(1),
    disp  = ts_mean(demean(r1) / zscore(r1), 63)
in decay_linear(min(score, 0) / vol / vol, 60) / disp
```

## T22 (keep)

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    vol   = volatility(60),
    score = zscore(group_demean(mom / vol, 'sector')),
    r1    = returns(1),
    disp  = ts_mean(demean(r1) / zscore(r1), 63)
in decay_linear(min(score, 0) * abs(score) / vol / vol, 60) / disp
```

## T23 (reset)

T22 with `min(score, 0) * score * score` in the body.

## T24 (reset)

T22 with `score * abs(score)` in the body (two-sided).

## T25

T22 with `min(score, 0) * abs(score) * rank(returns(21))` in the body.

## T26 (7558781, reset)

T25 re-run: T22 with `min(score, 0) * abs(score) * rank(returns(21))` in the body.

## T27 (d8ad3af, reset)

T22 with body `group_demean(decay_linear(min(score, 0) * abs(score) / vol / vol, 60), 'sector') / disp`.

## T28 (114f9f8, reset)

T22 with `decay_linear(..., 120)`.

## T29 (b3411f6, reset)

T22 with `disp = ts_mean(demean(r1) / zscore(r1), 21)`.

## T30 (e99e708, reset)

T22 with body `... / disp / disp`.

## T31 (b2ae84b, reset)

T22 with `score = zscore(group_demean(mom / volatility(252), 'sector'))`.

## T32 (330c8ae, reset, -inf)

T22 with `vol = volatility(20)`.

## T33 (730f52a, reset)

T22 with `x = mom / vol, score = zscore(x + group_demean(x, 'sector'))`.

## T34 (9a85228, reset)

T22 with `score = group_demean(mom / vol, 'sector')` (no zscore).

## T35 (82ae9ee, keep)

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    vol   = volatility(60),
    score = zscore(group_demean(mom / vol, 'sector')),
    r1    = returns(1),
    disp  = ts_mean(demean(r1) / zscore(r1), 63)
in ewma(min(score, 0) * abs(score) / vol / vol, 20) / disp
```

## T36 (7f2441a, reset)

T35 with `ewma(..., 10)`.

## T37 (c5694f8, reset)

T35 with `min(score, 0) * abs(score) * rank(returns(21))` in the body.

## T38 (091f3f5, reset)

T35 with `mom = delay(returns(210), 42) + delay(returns(126), 126)`.

## T39 (a974c85, reset)

T35 with `score = winsorize(zscore(group_demean(mom / vol, 'sector')), 0.02)`.

## T40 (561125d, keep)

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    r1    = returns(1),
    vol   = ts_std(group_demean(r1, 'sector'), 60),
    score = zscore(group_demean(mom / vol, 'sector')),
    disp  = ts_mean(demean(r1) / zscore(r1), 63)
in ewma(min(score, 0) * abs(score) / vol / vol, 20) / disp
```

## T41 (6051dd5, reset)

T40 with `res = group_demean(r1, 'sector')`, `vol = ts_std(res, 60)`, `disp = ts_mean(demean(res) / zscore(res), 63)`.

## T42 (b44750e, reset)

T40 with `/ vol / vol / vol` in the body.

## T43 (6e56c10, keep)

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    r1    = returns(1),
    vol   = ts_std(group_demean(r1, 'sector'), 60),
    score = zscore(group_demean(mom / vol, 'sector')),
    disp  = ts_mean(demean(r1) / zscore(r1), 63)
in ewma(min(score, 0) * abs(score) * rank(returns(21)) / vol / vol, 20) / disp
```

## T44 (16d92ec, reset)

T43 with `vol = ts_std(group_demean(r1, 'sector'), 120)`.

## T45 (d05786a, reset)

T43 with `rev = rank(group_demean(returns(21), 'sector'))` as the tilt.

## T46 (cb5dfad, reset)

T43 with `fresh = ts_argmin(close(), 252) / 252` and `* (1 - fresh)` in the body.

## T47

First attempt (1c6653f) used `group_std`, which is a rolling time-series std, and did not parse. Corrected:

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    r1    = returns(1),
    vol   = ts_std(group_demean(r1, 'sector'), 60),
    d     = group_demean(mom / vol, 'sector'),
    score = d / sqrt(group_sum(d * d, 'sector') / group_sum(is_valid(d), 'sector')),
    disp  = ts_mean(demean(r1) / zscore(r1), 63)
in ewma(min(score, 0) * abs(score) * rank(returns(21)) / vol / vol, 20) / disp
```
(d29b7c1, reset)

## T48 (2b7b761, reset)

T43 with `min(score, 0) * rank(returns(21))` in the body (no squared weight).

## T49 (66fe104, reset)

T43 with `mkt = r1 - demean(r1)` and body `... / disp * where(ts_sum(mkt, 252) > 0, 1, 0.5)`.

## T50 (2c0e7a4, reset)

T43 with `mom = delay(returns(231), 21)`.

## T51 (01e2284, reset)

T43 with `d = group_demean(mom / vol, 'sector'), mad = abs(d) - demean(abs(d)), score = d / mad`.

## T52 (31021a6, reset)

T43 with `res = group_demean(r1, 'sector'), vol = ts_std(res, 60)` and `* rank(vol / ts_std(res, 252))` in the body.

## T53 (bce7f66, reset, equal to T43 with 5 nodes fewer)

T43 without `disp`: body `ewma(min(score, 0) * abs(score) * rank(returns(21)) / vol / vol, 20)`.

## T54

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    r1    = returns(1),
    vol   = ts_std(group_demean(r1, 'sector'), 60),
    score = zscore(group_demean(mom / vol, 'sector')),
    disp  = ts_mean(demean(r1) / zscore(r1), 63),
    mkt   = r1 - demean(r1),
    crash = (ts_sum(mkt, 504) < 0) & (ts_std(mkt, 21) > ts_std(mkt, 252)),
    book  = ewma(min(score, 0) * abs(score) * rank(returns(21)) / vol / vol, 20) / disp
in where(crash, 0.5 * book, book)
```
(18987a8, reset)

## T55 (7c9725d, reset)

T43 with `ewma(..., 30)`.

## T56 (244598a, reset)

T43 with `mom = delay(returns(231), 21) + 2 * delay(returns(126), 126)`.

## T57 (a0a2f21, reset, 0.006 short)

T43 with `rank(returns(21) / vol)` as the tilt.

## T58 (481a0e3, keep)

```
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    r1    = returns(1),
    vol   = ts_std(group_demean(r1, 'sector'), 60),
    score = zscore(group_demean(mom / vol, 'sector'))
in ewma(min(score, 0) * abs(score) * rank(returns(21) / vol) / vol / vol, 20)
```

## T59 (ca2b624, reset)

T58 with `rev = rank(returns(21) / vol)` and body `ewma((min(score, 0) * abs(score) * rev + 0.1 * (0.5 - rev)) / vol / vol, 20)`.

## T60 (1974132, reset)

T58 with `score = group_demean(mom / vol, 'sector')` (no zscore).

Final book: T58, restored to `alpha.qex`.

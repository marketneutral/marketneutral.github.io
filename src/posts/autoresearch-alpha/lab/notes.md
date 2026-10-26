# run3 working notes

## Inspection (1999-2003) baselines, explore.py book
- seed: SR 0.65, fit 0.38, to 0.055 (mom/vol^2 weighting: double vol division)
- raw 12-1 unscaled: SR 0.99 fit 1.11; sector-demeaned: SR 1.00
- Novy-Marx 7-12 /vol sector-dm: SR 1.53
- 52w high sector-dm: SR -0.27 (in 1999-2003 the bubble names were near highs then crashed)
- sector-residual daily momentum: SR 0.68, to 0.045

## Trial log (short)
- T1 keep crash flip (2y down & 1m vol>1y vol): -0.091 -> 0.009
- T2 keep drop final 1/vol: 0.320, eligible
- T3 reset Novy-Marx 7-12: 0.191
- T4 keep vol252 for standardizing: 0.429
- T5 reset no sector demean: 0.333 (belief 3 holds)
- T6 keep 1m sector reversal sleeve outside decay/flip: 0.564
- T7 keep crash on 1y drawdown: 0.636
- T8 keep residual momentum vs EW market beta: 0.736, worst +0.062
- T9 reset Nagel vol-scaled reversal: 0.701 (regimes moved as predicted, median not)

- T10 reset no skip month on residual mom: 0.582
- T11 reset raw-mom flip in crash: 0.709 (crash SR fell)
- T12 reset residual reversal: 0.685
- T13 reset sector rank: 0.723
- T14 reset a*|a|: 0.766 (+0.030 exactly; turnover 0.15)
- T15 reset outer decay 3: 0.701 (turnover 0.09, Sharpe down)
- T16 keep a*|a| + decay 3: 0.784
- T17 keep power(a,3) + decay 3: 0.890, return 6.9%
- T18 reset group_demean after cube: 0.832
- T19 reset outer decay 5: 0.893 (no gain)
- T20 reset 52w high blend: 0.563
- T21 reset inner decay 21: 0.824
- T22 keep soft switch clip(10*mkt1y) when vr>1: 1.000
- T23 reset Nagel again: 0.934 (crash up, median down; do not retry)
- T24 keep beta-neutral projection of cubed signal: 1.101 (inspection went DOWN 2.15->1.93!)
- T25 reset + size neutral: 1.004
- T26 reset frog: 0.687
- T27 reset remove switch: 0.622, worst -0.51 (belief 7 essential)
- T28 reset Barroso-SC mom-vol scaling: 1.052
- T29 reset residual-vol standardization: 0.993
- T30 reset deep-bear-only switch clip(10*m1+1): 1.018 but worst 0.349
- T31 keep combined switch (vol rule + deep-bear): 1.269, worst 0.319
- T32 reset sqrt(vol): 1.287 (+0.018)
- T33 keep no vol standardization: 1.320, worst 0.369, return 13%
- T34 reset square under no-vol: 1.166
- T35 reset power 5: 1.055
- T36 reset sector demean final: 0.928
- T37 reset market-wide momentum: 1.267, worst 0.172
- T38 reset winsorize 1%: 1.253 but SR 1.44, worst 0.436 (best safety)
- T39 reset winsorize + power5: 1.206
- T40 reset loser-only switch: 0.737 (inspection +0.3 -> validation -0.58!)

## Process notes
- Inspection is anti-informative for risk-shaping changes (T24). Use trials.
- Concentration (power) is the strongest lever: fitness ~ SR*sqrt(ret) and gross fixed. a^5 on inspection past peak.
- volatility() is annualized; ts_std is daily. Mixing changes sleeve weights ~16x.
- Long multi-expression `python -c` screens sometimes get denied; one-expression explore.py works.
- Inspection gains of ~0.05-0.1 SR do not reliably carry (T9).

## Validation facts from the seed line
- seed loses on 2004-2017: SR -0.25; crash state SR -1.96 on 137 days; dispersion split flat.

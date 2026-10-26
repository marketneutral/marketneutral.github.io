# program.md: momentum without the crashes

This is the problem definition for an autoresearch loop on a qex alpha. A
person wrote it. The agent reads it, proposes a change to `alpha.qex`,
scores it with `eval.py`, keeps or resets, logs, and goes again. The data,
the evaluator and the rules are outside the agent's reach.

## Files

| file | role | agent may |
|---|---|---|
| `alpha.qex` | one qex expression, the active hypothesis | **edit** |
| `program.md` | this file | read |
| `explore.py` | helpers over the *inspection* period, 1999-2003 | read, run |
| `eval.py` | the frozen evaluator, scores `alpha.qex` on random hold-out windows | run only, through `trial.sh` |
| `trial.sh` | one trial: `eval.py` under the time budget | run |
| `data/` | adjusted daily OHLCV, universe membership, market cap, sectors | read via `explore.py` only |
| `results.tsv` | the lab notebook, one line per attempt | append |

## Universe and data

The point-in-time investable US equity universe, from the data-manager
warehouse (Sharadar): on each day, the domestic common stocks with an
as-traded close of at least $2, a 20-day average dollar volume of at least
$5M and a market cap of at least $300M. About 1,300 names a day in 1999 and
2,000 in 2017, 8,215 over the whole history. Names enter and leave as they
cross the screens, and the ones that were delisted, went bankrupt or were
acquired are in it until their last trade. There is no survivorship bias:
the losers that fell out of the index on the way down are here, and they are
exactly the names a momentum book is short.

The fields an expression can read:

| field | meaning |
|---|---|
| `open()`, `high()`, `low()`, `close()` | total-return adjusted prices (splits and dividends) |
| `volume(...)`, `field('volume')` | shares traded, on the same adjustment, so `close() * field('volume')` is dollars traded that day |
| `field('member')` | 1 on days the name is in the universe, NaN otherwise |
| `field('mcap')` | point-in-time market cap in dollars on member days, NaN otherwise |
| `'sector'` | the name's Sharadar sector (11 of them, not GICS) on member days, NaN otherwise |

Each name's full price history is loaded, including days it is not a
member, so a time-series window is full on the day a name joins. Every
cross-sectional operator (`rank`, `zscore`, `demean`) sees every name with
a value that day, members or not; the group operators see members only,
because the sector is blank off-membership. Multiply by `field('member')` to
restrict a cross-section to the universe.

**Compare names by returns and ratios, never by price levels.** The adjusted
prices are scaled by splits and dividends that happen later, so the ratio of
a name's own prices (`returns`, `volatility`, distance from its own high) is
point-in-time, but `rank(close())` or `close() > 5` is not. The same holds
for `volume` on its own; dollar volume and `mcap` are point-in-time.

Three periods, by date, and the loop never mixes them:

| period | dates | who sees it |
|---|---|---|
| warmup | 1998-01-01 to 1998-12-31 | the first year of data, so 12-month windows are full on day one |
| inspection | 1999-01-01 to 2003-12-31 | the agent, freely, through `explore.py`: the dot-com top, the 2000-02 bear market, the 2003 junk rally |
| validation | 2004-01-01 to 2017-12-31 | `eval.py` only, as a score; the agent never reads these prices |
| test | 2018-01-01 to 2026-08-11 | nobody, until the human runs it once at the end |

## The book

The book follows the standard simulation of *Finding Alphas* (Tulchinsky et
al.), the same settings for every expression:

- **Universe.** The expression is set to NaN for every name that is not a
  member of the universe that day or has no price.
- **Delay 1.** The weight held from close *t* to close *t+1* is computed from
  data up to close *t−1*: the evaluator delays the expression by one day, so
  nothing the expression sees on day *t* can be traded on day *t*.
- **Neutral, constant book, truncated.** Each day the weights are demeaned
  over the names that have one (as many dollars long as short), scaled so
  gross exposure is exactly one, and clipped so no name holds more than **5%**
  of the book, repeating until all three hold.

The expression's magnitude is therefore relative weight within a day and
nothing else: an expression cannot make the book bigger or smaller, only move
weight between names. No leverage, no financing. Sector neutrality is *not*
imposed; it is one of the beliefs, and the expression has to produce it
(`group_demean(..., 'sector')` does).

P&L is cost-free, as in the book; costs enter through turnover and margin
(below). For reference the evaluator also prints the Sharpe and return net of
a flat 2 bps per unit of turnover.

## The score

`./trial.sh` prints `utility: <float>` and `worst: <float>`, both higher is
better, then `eligible: yes|no`.

The evaluator is purged, randomized cross-validation, which is the moving
evaluator from the autoresearch post. The validation period is cut into 12
contiguous blocks of about fourteen months. On every call the blocks are
dealt at random into 6 folds of 2 blocks, and an embargo of 21 trading days
is purged from both ends of every block so that no rolling window or
forward return straddles a fold boundary. Each fold is scored

    utility = fitness - 0.003 * (nodes in the parsed expression)
    fitness = Sharpe * sqrt(|annual return| / max(turnover, 0.125))

where Sharpe, return and turnover (the fraction of the book traded per day)
are the fold's, on cost-free P&L. Fitness is the book's measure: a high
Sharpe is worth more when it comes with real return and little trading. A
book at Sharpe 1.5, 10% a year and 20% turnover has fitness 1.06; the same
Sharpe at 70% turnover has 0.57. A fold scores minus infinity if the book
holds fewer than 50 names or trades less than 1% or more than 70% of the book
a day. The call deals 50 such partitions and reports the median fold and the
worst fold, each averaged over the partitions. A fresh deal every call means
there is no single hold-out to climb; the price is noise, measured below.

**Eligibility.** The whole validation book is also checked the way an alpha is
checked before it is submitted: turnover inside 1-70% a day, and a **margin**
(cost-free P&L per dollar traded) of at least **5 bps**, so the edge clears
realistic trading costs with room to spare. `eligible` does not change the
scores. It constrains what may be kept: once the best book is eligible, a
change that makes it ineligible is reset whatever its utility, and the final
book must be eligible.

The charge is the autoresearch post's charge for complexity: every
operator, constant and field in the parsed tree is a degree of freedom
spent on the past and has to earn its keep. It is small, about 0.03 for a
ten-node expression, so it breaks ties and punishes bloat rather than
forbidding ideas. The evaluator's own wrapper is not charged.

The evaluator also prints, for checking the claim, the Sharpe and return
when dispersion across the universe is above and below its trailing-year
median, inside and outside the Daniel-Moskowitz crash state (market down
over two years and one-month volatility above one-year volatility, on the
equal-weight market of the universe), and in the first and second half of
the validation period. And it prints the deflated Sharpe ratio of the
current expression, the probability that its Sharpe is real given the
number of trials in `results.tsv` so far, which is the post's "count the
trials".

**Noise.** The human ran the seed eight times with 50 partitions per
call. Call to call, `utility` stayed within -0.10 to -0.08 and `worst`
within -1.03 to -0.90 (the record is in `noise.txt`; the seed's line in
`results.tsv` is the median of the eight). A change counts only if it beats
the best `utility` by more than **0.03**, does not take `worst` below the
best's `worst` by more than **0.13**, and, once the best is eligible, keeps
the book eligible. That is the post's rule: improve the median fold and do
not hurt the worst.

## Trial budget

A trial is `./trial.sh`, which is `eval.py` under a 120-second limit. If it
does not finish (exit code 142), it scored
nothing. Every attempt gets the same two minutes.

## The beliefs

This is the firm's view. The agent starts from it, tests it, and is free to
disagree with any line, but every change must say which belief it is
testing and what it predicts.

The alpha is cross-sectional momentum: own the stocks that have done well
over the past year and short the ones that have done badly. It is one of
the oldest and best-documented effects in equities, and it has one famous
flaw. Every decade or so it loses in a few months what it made in years:
1932, 2002, and above all 2009, when the past-year losers rallied 150% off
the March low and a long-short momentum book lost about three quarters of
its value. Daniel and Moskowitz (2016) call these momentum crashes and show
they are not random: they come after the market has fallen, when market
volatility is high, during a sharp rebound, and almost entirely on the
short side, because the past losers are by then the highest-beta stocks in
the market. The firm's goal is a momentum alpha that keeps the premium and
does not have those months. Every belief below is either about where the
premium comes from or about where the crash comes from.

1. **Stocks that have done well over the past year, relative to their
   sector, keep doing well over the next few months.** Jegadeesh and Titman
   (1993) is the fact; Asness, Moskowitz and Pedersen (2013) find it in
   every market and asset class they look at. The mechanism is slow
   diffusion of information (Hong and Stein 1999): news gets into prices
   over months, not days, because attention is scarce and analysts anchor
   on old forecasts. The counterparty is the investor who sells winners
   early and holds losers too long, the disposition effect of Grinblatt and
   Han (2005). It persists because it is painful to hold: the crashes keep
   arbitrage capital away.

2. **Skip the most recent month.** The last month's move reverses
   (Jegadeesh 1990), and Novy-Marx (2012) finds that months seven to twelve
   carry most of the predictive power, while months one to six carry
   little. Formation is the return from twelve months ago to one month ago.
   Prediction: including the last month lowers the Sharpe and raises
   turnover; dropping months one to six as well is worth testing.

3. **Measure momentum against the sector, and hold the book
   sector-neutral.** Moskowitz and Grinblatt (1999) show that much of raw
   momentum is industry momentum, and industry bets are factor bets: they
   are where the beta and the crash live. Grundy and Martin (2001) find
   that hedging out the factor exposure of a momentum book removes most of
   its risk and leaves most of its return. The firm wants the stock-specific
   part. Sector momentum itself is a separate, unhedged bet and may be added
   back on purpose, but it is tested as its own belief, not smuggled in.

4. **Momentum is measured in units of the stock's own volatility.** A 40%
   year is a shock for a utility and a shrug for a biotech. Standardizing
   the formation return by the stock's own volatility makes the ranking
   fair across names and keeps the volatile names, which are the ones that
   crash, from dominating the extremes of the book.

5. **The part of the return the market did not explain is what continues.**
   Blitz, Huij and Martens (2011) form momentum on the residual of each
   stock's return against the market and find about the same premium with
   half the volatility and far smaller crashes, because residual momentum
   has no time-varying beta to the market. Prediction: residual momentum
   loses less in high-dispersion regimes than raw momentum, and its worst
   fold improves more than its median.

6. **The crash has a known state, and the book should be small in it.**
   Daniel and Moskowitz (2016) show the crash state is a market that has
   fallen over the past year or two with high recent volatility. Barroso and
   Santa-Clara (2015) show that scaling the book by its own trailing
   realized volatility alone halves the crash and doubles the Sharpe. Here
   the evaluator holds gross at one every day, so the book cannot be made
   smaller: the belief can only act within it, by leaning away from the
   names the crash hits (the high-beta past losers), by spreading weight
   more evenly in that state, or by switching sign as in belief 7. Prediction: the
   change helps in the high-dispersion half of days and does nothing in the
   low-dispersion half. This is the belief most likely to be already in the
   price, since every quant has read both papers; test it early and expect
   less than the papers show.

7. **In the crash state, do not just shrink: switch to reversal.** A
   momentum crash is, by construction, a reversal: the past losers are the
   stocks that rally hardest off the low, and the past winners lag. If the
   state can be seen, then the right book in it is not a smaller momentum
   book but a reversal book, long the past losers, which turns the worst
   months of the year into the best. Daniel and Moskowitz's option-like
   payoff of the loser side in a rebound is the mechanism. The switch can be
   hard (a sign flip on a condition) or soft (a weight that moves from +1
   to -1 as the state deepens). The cost of being wrong is a momentum book
   held backwards in a normal market, so the condition has to be rare and
   specific. Prediction: the hard switch helps the worst fold a lot and the
   median a little; the soft switch helps both less and hurts less.

8. **Gradual moves continue; jumps do not.** Da, Gurun and Warachka (2014)
   call it the frog in the pan: a year of small gains, each too small to
   notice, is underreacted to, while the same gain in two big days is
   already priced. Measure it by the share of up days in the formation
   window relative to the sign of the move, and lean toward the gradual
   winners and the gradual losers.

9. **Closeness to the 52-week high is a better anchor than the return.**
   George and Hwang (2004) find that the ratio of price to its 52-week high
   predicts returns at least as well as past return and is less prone to
   reversal, because investors anchor on the high and are slow to buy
   through it. It is a different measurement of the same idea and a natural
   thing to blend.

10. **`decay_linear` is almost always a free lunch, and here the lunch is
    large.** Momentum is a slow signal with a horizon of months, so the
    decay can be long, and turnover should be low: a few percent a day,
    not thirty. The lunch stops being free when the decay window is longer
    than the alpha's horizon, so check the horizon before lengthening the
    decay.

11. **Size each name by its own risk.** Weight the final signal by the
    inverse of the stock's volatility so no name dominates the book's risk.

12. **Expect the edge to decay, and expect crowding.** Momentum was a
    mainstream quant factor by 2000 and crowded by 2007. A change that
    helps only in one regime is suspect. The evaluator's random folds are
    the defense, and the worst fold is reported for this reason.

## Rules for the agent

- One change per attempt, and the simplest change that could test the
  belief. Do not tune constants to three significant figures; the
  complexity charge is there to make that lose.
- Before each change, write the claim: which belief, what mechanism, and
  what you predict the score will do. After the run, write what happened.
  A change that raises the score with no claim is reset.
- Use `explore.py` on the inspection period as much as you like. It is
  1999-2003; the validation period is not in it, and you may not read the
  validation prices by any other route. It is five years and most of them
  are a bubble and a bear market, so it is a better guide to crashes than to
  the size of the premium.
- `eval.py` and `data/` are never edited. Do not install packages.
- Commit every attempt. Keep it if it beats the best `utility` by more than
  the noise, holds `worst` and keeps an eligible book eligible; otherwise restore the best book with
  `git checkout <best commit> -- alpha.qex`.
- Append one line per attempt to `results.tsv`, tab-separated:
  `commit, utility, worst, sharpe, status, belief, claim, outcome`. The claim
  is written before the run and names the belief, the mechanism, and what
  the regime split should show. The outcome is written after.
- Before testing a belief that is not in the list, say how known it is:
  published where, and when. An idea the whole field has read about for
  twenty years is probably in the price.
- Be creative. The list is a starting point, not a fence. Combine beliefs,
  flip them, condition one on another, invent a measurement the list does
  not have, and try the thing the firm would not think of. A change that
  comes with a claim and a prediction is always allowed, however strange.
- Never stop, never ask. When out of ideas, try removing something.

## The seed

`alpha.qex` starts as the literal translation of beliefs 1, 2, 3, 4, 10
and 11, with nothing else. The rest of the beliefs are the agent's first
experiments.

## References

- Asness, C. S., Moskowitz, T. J. and Pedersen, L. H. "Value and Momentum Everywhere." *Journal of Finance* 68(3), 2013.
- Barroso, P. and Santa-Clara, P. "Momentum Has Its Moments." *Journal of Financial Economics* 116(1), 2015.
- Blitz, D., Huij, J. and Martens, M. "Residual Momentum." *Journal of Empirical Finance* 18(3), 2011.
- Da, Z., Gurun, U. G. and Warachka, M. "Frog in the Pan: Continuous Information and Momentum." *Review of Financial Studies* 27(7), 2014.
- Daniel, K. and Moskowitz, T. J. "Momentum Crashes." *Journal of Financial Economics* 122(2), 2016.
- George, T. J. and Hwang, C.-Y. "The 52-Week High and Momentum Investing." *Journal of Finance* 59(5), 2004.
- Grinblatt, M. and Han, B. "Prospect Theory, Mental Accounting, and Momentum." *Journal of Financial Economics* 78(2), 2005.
- Grundy, B. D. and Martin, J. S. "Understanding the Nature of the Risks and the Source of the Rewards to Momentum Investing." *Review of Financial Studies* 14(1), 2001.
- Hong, H. and Stein, J. C. "A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets." *Journal of Finance* 54(6), 1999.
- Jegadeesh, N. "Evidence of Predictable Behavior of Security Returns." *Journal of Finance* 45(3), 1990.
- Jegadeesh, N. and Titman, S. "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency." *Journal of Finance* 48(1), 1993.
- Moskowitz, T. J. and Grinblatt, M. "Do Industries Explain Momentum?" *Journal of Finance* 54(4), 1999.
- Novy-Marx, R. "Is Momentum Really Momentum?" *Journal of Financial Economics* 103(3), 2012.

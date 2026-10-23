---
title: "autoresearch for alpha: a first run"
date: 2026-10-23
tag: PROJECT
description: I ran the augmented autoresearch loop from the last essay on a real alpha. A coding agent proposed, tested and kept or discarded changes to a one-expression qex alpha for sixty trials, against a moving evaluator, with a claim before every test. Here is the program, the evaluator, the lab notebook, and the one run on the period the loop never saw.
---

In [autoresearch: sparks of an AI scientist](/posts/ai-scientist/) I argued
that Karpathy's loop, an agent editing one file against a fixed score, would
find noise if you pointed it at a backtest, and I listed what would have to
change for it to find alpha instead: a claim before every test, an evaluator
that moves, a charge for complexity, a count of the trials, a seed of the
firm's own view, and one period the loop never touches. This post is that
list, built and run once.

The alpha is written in [qex](/posts/qex/), so the agent edits a single
expression. The problem is one I care about: cross-sectional momentum
without the crashes. And the agent is Claude Code, started headless in a
directory with a problem definition and told to begin.

## The lab

Six files.

| file | role | the agent may |
|---|---|---|
| `program.md` | the problem definition and the firm's beliefs | read |
| `alpha.qex` | one qex expression, the active hypothesis | **edit** |
| `eval.py` | the frozen evaluator | run |
| `explore.py` | helpers over the inspection period, the 1990s | run |
| `results.tsv` | the lab notebook, one line per trial | append |
| `data/` | adjusted daily OHLCV for current S&P 500 members, 1990 on | read through `explore.py` |

History is cut three ways, and the loop never mixes them.

| period | dates | who sees it |
|---|---|---|
| inspection | 1990 to 1999 | the agent, freely |
| validation | 2000 to 2017 | the evaluator only, as a score |
| test | 2018 to 2025 | nobody, until the end |

The universe is current S&P 500 members with history back to 1990, which
is about 240 names in 1990 growing to about 420 by 2010, with GICS sectors.
Current membership makes it survivorship-biased, and one trial below shows
exactly how.

## The program

The problem definition is where the firm's view goes. Mine starts with the
goal, then lists twelve beliefs, each with a mechanism, a counterparty, the
paper it comes from, and a prediction specific enough to be wrong. The
first four are the textbook: past-year winners keep winning relative to
their sector, skip the last month, measure the move in units of the stock's
own volatility, size by risk. The rest are about the crash. Daniel and
Moskowitz showed that momentum's worst months come after a market fall,
when volatility is high, in a sharp rebound, and almost entirely on the
short side, because the past losers are by then the highest-beta stocks in
the market. So the beliefs include residual momentum, shrinking the book
in the crash state, switching to reversal in it, the frog in the pan, the
52-week high, and a note that the edge should be expected to decay.

The seed expression is the literal translation of the textbook beliefs and
nothing else:

```python
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector')
in decay_linear(score / vol, 10)
```

The rules for the agent fit on a card: one change per trial, write the
claim before the run, log the outcome after, commit every attempt, never
touch the evaluator or the data, be creative, never stop. The full
[program](lab/program.md) is a few pages.

## The evaluator

This is where the essay's list becomes code. The full
[evaluator](lab/eval.py) is a hundred lines.

**The book is enforced, in qex.** Whatever the agent writes, the evaluator
scores `demean(<alpha> + 0 * close())`. The `0 * close()` makes any name
without a price NaN, and `demean` makes every day dollar-neutral. Gross
exposure is normalized to average one dollar but may vary day to day, so an
expression can shrink itself in a state it does not like. Daily
rebalance, close-to-close returns, 2 basis points per unit of turnover.

**The evaluator moves.** The validation period is cut into twelve blocks of
about eighteen months. On every call the blocks are dealt at random into
six folds of two, an embargo of 21 trading days is purged from both ends of
every block, and each fold is scored. The call deals fifty such partitions
and reports the median fold and the worst fold, each averaged over the
deals. Every call is a fresh deal, so there is no single hold-out to climb.

**The score has return in it, and a charge for complexity.** Per fold,

```
utility = net Sharpe + 10 × net annual return on GMV − 0.003 × nodes
```

A fold on which the book holds fewer than fifty names scores minus
infinity, so trading nothing does not win.

**The keep rule is two-sided.** I ran the seed eight times to measure the
noise: 0.05 on the median, 0.15 on the worst fold. A change is kept only if
it beats the best median by more than 0.05 and does not lower the worst
fold by more than 0.15. That is the essay's rule: improve the median fold
and do not hurt the worst.

**The claim can be checked.** The evaluator prints the Sharpe split three
ways: high against low cross-sectional dispersion, inside against outside
the Daniel and Moskowitz crash state, first half against second. The
agent's prediction has to name which of those should move.

**The trials are counted.** The evaluator reads the notebook, counts the
trials so far, and prints the deflated Sharpe ratio of the current
expression.

## The run

<figure class="wide" id="progress">
  <img src="progress.svg" alt="Two panels over sixty trials. Top: the utility of each trial, grey dots discarded, green dots kept and labelled, with a green staircase for the best so far rising from 0.4 to 1.74. Bottom: the worst fold of each trial, rising from minus 0.6 to plus 0.48. Two trials fall below the axes and are marked at the edge.">
  <figcaption>Sixty trials. Grey dots are discarded, green are kept, the staircase is the best so far. The top panel is the score the agent climbs; the bottom is the number it is not allowed to break.</figcaption>
</figure>

Sixty trials, eleven kept. The median-fold utility went from 0.40 to 1.74
and the worst fold from -0.59 to +0.48, so by the end no three-year stretch
of 2000 to 2017, however the blocks were dealt, lost money net of costs.
The run took two sessions of a few hours each, because the first one hit
my account's usage limit at trial 25, and cost about twenty dollars in
model time. What follows is the [notebook](lab/results.tsv), condensed; the
agent's own [summary](lab/summary.md) of the second half is worth reading in
full.

**Trial 1, keep.** Divide the whole book by trailing three-month market
volatility. The agent predicted the worst fold would improve more than the
median, and it did.

**Trials 2 and 3.** The agent dropped the loser leg, on the reasoning that
the crash lives there. Utility fell by half and the worst fold got worse.
So it ran the mirror: keep only the losers, short them against an
equal-weight long side. That was the largest keep of the first day, and it
is the shape the book kept to the end. Nothing in the program says
"losers only"; it came from reading a failure.

**Trials 4, 5 and 6.** Novy-Marx's months 7 to 12 raised the median and
broke the worst fold, so it was reset. No skip month lost on both. Residual
momentum, the standard cure for crash exposure, raised the median and broke
the worst fold too. The agent's reading of why is the best line in the
notebook: shorting past losers is a negative-beta position that protects
the book in down markets, and residualizing removes exactly that
protection.

**Trial 7.** The 52-week high lost 4% a year in every regime. The agent
gave two reasons, and the second is survivorship: on a current-members
basket, the names that fell furthest and are still in the index are, by
selection, the ones that recovered.

**Trial 8.** The hard switch to reversal in the crash state, which was my
idea, was reset as the agent predicted: with the loser-only leg and the
volatility scaling, the crash state was already small and profitable, and
flipping it only lost.

**Trials 9 to 18.** A long run of resets that mapped the book. Each
ablation of the seed turned out to be load-bearing. Two ideas, inverse
variance sizing and a cross-sectional z-score, each fell a hair short of
the bar.

**Trial 19, keep.** The agent combined the two near misses, on the
argument that one re-weights across names and the other re-scales across
time, so if both were real they should add. They did.

**Trials 20 to 22, three keeps in a row.** Months 7 to 12 came back at a
smaller dose, counted twice inside the full window. Then the state
variable for sizing changed from market volatility to cross-sectional
dispersion, which took the worst fold to zero. Then the loser leg was
concentrated by squaring the score. The agent's line: the mild losers carry
noise, the deep losers carry the premium.

**Trial 24.** The two-sided book was re-tested under the new structure and
lost badly. The winner leg is harmful on this universe, not merely dead
weight.

**Trials 26 to 34.** The second session began with nine resets. The agent
probed every constant and structural choice it had inherited, the decay
length, the dispersion window and power, the sector structure, the vol
window, and the book held on all of them. One trial scored minus infinity:
a 20-day volatility window hit a name with twenty flat closes, inverse
variance went infinite, and the breadth floor caught it.

**Trial 35, keep.** The 60-day linear decay became an exponential average
with a 20-day half-life, at the same node count. Ten probes of the book
had found nothing; the eleventh found that the shape of the smoothing
mattered.

**Trial 40, keep, the largest gain of the run.** The agent sized the leg
by each stock's sector-residual volatility instead of its total volatility,
on the argument that a sector-relative signal bears sector-relative risk.
Net Sharpe on the validation period went from 0.83 to 1.06. It also noted
the cost: residual-vol sizing lets the high-beta losers back in, and the
crash-state Sharpe fell.

**Trial 43, keep.** The last month's return as a weight on the loser leg,
so a name that just crashed is shorted least. This idea had been tried
twice before, on trials 26 and 37, and both times it improved the worst
fold a lot and the median not at all. On the residual-vol base it improved
both, because that base had just let in the names it was built to guard
against. The agent's claim said so before the run.

**Trial 53.** The agent removed the dispersion sizing from trial 21, and
the simpler book was as good or better on every line, with five fewer
nodes. It was reset, because the median gain was inside the noise and the
rule only accepts gains. More on this below.

**Trial 58, keep.** The trial 19 move again: a vol-scaled version of the
last-month weight that had missed the bar by 0.006, combined with the
removal from trial 53. Together they cleared it. The final book is simpler
than the one before it.

**Trials 59 and 60.** A small long leg of last month's dippers was a tie,
and removing the z-score cost 0.19, so the run ended with every piece of
the book confirmed load-bearing.

## What the agent built

```python
let mom   = delay(returns(231), 21) + delay(returns(126), 126),
    r1    = returns(1),
    vol   = ts_std(group_demean(r1, 'sector'), 60),
    score = zscore(group_demean(mom / vol, 'sector'))
in ewma(min(score, 0) * abs(score) * rank(returns(21) / vol) / vol / vol, 20)
```

Read it line by line. Formation is the return from twelve months ago to
one month ago, with months 7 to 12 counted twice. Volatility is the
60-day standard deviation of the stock's return relative to its sector.
The score is that momentum in units of that volatility, demeaned within
sector, then z-scored across the universe. The book keeps only the
negative scores, the losers, squares them so the deep losers dominate,
shades each by where its last month ranks in volatility units so the
freshest crash is shorted least, sizes by inverse variance, and smooths
with a 20-day half-life. The evaluator's `demean` supplies the long side:
equal weight in everything else. There is no market-state scaling left in
it. Every line maps to a notebook entry, and every removal was tested.

On the validation period, against the seed:

| 2000 to 2017, net of 2 bps | seed | final book |
|---|---:|---:|
| utility, median fold | 0.40 | 1.74 |
| worst fold | -0.59 | +0.48 |
| net Sharpe | 0.28 | 1.22 |
| net return on GMV, per year | +1.1% | +4.8% |
| turnover, per day | 4% | 2% |
| Sharpe inside the crash state, 112 days | -1.44 | +0.91 |

Those are in-sample numbers. Every keep was a decision made by looking at
2000 to 2017, and the book is fitted to it in the only sense that matters:
it was chosen because it worked there. What the loop's defenses buy is
that each piece had to work for a stated reason, across every random
re-dealing of those eighteen years, and without breaking the worst three
of them. That is a better kind of fitted than "the number went up", and it
is still fitted.

## The one run on 2018 to 2025

The test period was loaded for the first time after trial 60, by a script
the agent never saw, run once on the seed and once on the final book. The
[output](lab/test-2018-2025.txt) is in the post's folder.

| 2018 to 2025, net of 2 bps | seed | final book |
|---|---:|---:|
| net Sharpe | 0.35 | 0.81 |
| net return on GMV, per year | +2.0% | +3.9% |
| max drawdown | -12.4% | -9.2% |
| years positive | 5 of 8 | 7 of 8 |
| 2020 | +2.3% | +5.6% |
| worst year | 2021, -4.1% | 2022, -6.5% |

The book kept about two thirds of its in-sample Sharpe out of sample,
1.22 to 0.81, and about four fifths of its return. That is ordinary
shrinkage for a strategy chosen on history, and it is far better than the
field's record for backtests chosen without discipline, where the
out-of-sample Sharpe is close to uncorrelated with the in-sample one. The
seed, which nobody fitted to anything, kept about the same share of its
Sharpe, which says the loop's gain over the seed is mostly real: the book
is better than the seed on every line in a period neither of them saw.

The crash defenses had one live test. March 2020 was the fastest market
fall since 1929 and the rebound off it was exactly the state Daniel and
Moskowitz describe, and the book made 5.6% that year against the seed's
2.3%. The seven days the evaluator's crash-state rule flags in the test
period were the book's best, at an annualized 16%, where the seed lost at
an annualized 28%. Seven days is nothing to lean on, but the sign is the
one the program asked for. The bad year was 2022, a slow grind down with
no rebound, which is not the crash the beliefs were written about.

I would not trade this as it stands. It is one price-based alpha on a
survivorship-biased basket, and a real book is many alphas on a
point-in-time universe. But as a test of the method it is a clean result:
the loop improved the firm's starting view by a wide margin on the period
it could see, and most of the improvement survived the period it could not.
The test period is now spent. If I run this again, the book that comes out
cannot be scored on 2018 to 2025 and mean anything, and the honest next
test is live.

## What I learned

Most of it is about the program, which is the part of the loop a person
writes.

**The keep rule has a blind spot, and it is the one this problem cares
about.** The rule accepts a change that raises the median and refuses one
that lowers the worst fold. It has no way to accept a change that raises
the worst fold and leaves the median alone. Five trials did exactly that,
and the agent reset every one. Nor does it accept a removal that costs
nothing: trial 53 found five nodes that had become redundant, and the
complexity charge was too small to tip the tie. The agent got both ideas
in anyway, by pairing them with a median gain so the combination cleared
the bar, which is clever, and should not have been necessary. Next time:
a change that improves the worst fold by more than its noise is a keep,
and a removal that leaves both numbers inside the noise is a keep.

**The threshold was a shade tight.** Three changes missed the bar by less
than 0.01, and all three were later confirmed when combined with something
else. A noise bar protects against false keeps at the cost of real ones,
and with sixty trials and a two-sided rule, the cost was higher than the
protection was worth.

**The inspection period was a poor guide for the second half.** The agent
noted it itself: six variants the 1990s ranked higher reset in validation.
The 1990s have no momentum crash and no 2000 to 2002, so anything that
helps in a calm decade and hurts in a rebound looks good there. The
inspection data was right about structure, the kernel, the sizing, the
tilt, and wrong about every fine adjustment. A better inspection period
would contain a crash.

**The agent's creativity showed up where the essay said it would, and
one place it did not.** It did not propose anything strange on its own
initiative. What it did was read failures: the loser-only book came from
trial 2's failure, the last-month weight's third attempt came from trial
40's side effect, and the two biggest keeps of each session were
combinations of near misses. It also reached outside the program for
Cooper, Gutierrez and Hameed, for Ang, Hodrick, Xing and Zhang, and for
Grundy and Martin's hedge, and the evaluator said no to all three, which
is the test working. And it used the language well: a cross-sectional
sum built from `x - demean(x)`, a one-factor beta hedge in six lines, a
group z-score from `group_sum` and `is_valid`. None of that is in the qex
documentation.

**The notebook has to be machine-written.** The agent could not commit
for its first 25 trials, because I had set the permissions wrong, and it
kept an exact record in a side file instead. But it also filled some rows
of the notebook by hand and left the numeric columns empty, with the
numbers in the prose, so the evaluator's trial count was wrong and the
deflated Sharpe it printed was not trustworthy. The counting correction
is only as good as the log, and the log should be written by the
evaluator, not the agent.

**The things I was told, and the things I was not.** The agent predicted
most of its own resets correctly, which is what a claim before the test
is for. It was wrong in both directions a few times, and the two most
useful lines in the notebook are both explanations of a wrong prediction:
why residualizing hurt, and why the book's own volatility was the wrong
state variable. The loop is not just a search. Read carefully, the log is
a short course in what this alpha is.

<div class="callout">
Sixty trials, eleven keeps, one look at the future. The method held. The
book it produced is not the point; the notebook is.
</div>

## References

- Ang, A., Hodrick, R. J., Xing, Y. and Zhang, X. "The Cross-Section of Volatility and Expected Returns." *Journal of Finance* 61(1), 2006.
- Bailey, D. H. and López de Prado, M. "The Deflated Sharpe Ratio." *Journal of Portfolio Management* 40(5), 2014.
- Barroso, P. and Santa-Clara, P. "Momentum Has Its Moments." *Journal of Financial Economics* 116(1), 2015.
- Blitz, D., Huij, J. and Martens, M. "Residual Momentum." *Journal of Empirical Finance* 18(3), 2011.
- Cooper, M. J., Gutierrez, R. C. and Hameed, A. "Market States and Momentum." *Journal of Finance* 59(3), 2004.
- Da, Z., Gurun, U. G. and Warachka, M. "Frog in the Pan: Continuous Information and Momentum." *Review of Financial Studies* 27(7), 2014.
- Daniel, K. and Moskowitz, T. J. "Momentum Crashes." *Journal of Financial Economics* 122(2), 2016.
- George, T. J. and Hwang, C.-Y. "The 52-Week High and Momentum Investing." *Journal of Finance* 59(5), 2004.
- Grundy, B. D. and Martin, J. S. "Understanding the Nature of the Risks and the Source of the Rewards to Momentum Investing." *Review of Financial Studies* 14(1), 2001.
- Jegadeesh, N. "Evidence of Predictable Behavior of Security Returns." *Journal of Finance* 45(3), 1990.
- Jegadeesh, N. and Titman, S. "Returns to Buying Winners and Selling Losers." *Journal of Finance* 48(1), 1993.
- Moskowitz, T. J. and Grinblatt, M. "Do Industries Explain Momentum?" *Journal of Finance* 54(4), 1999.
- Novy-Marx, R. "Is Momentum Really Momentum?" *Journal of Financial Economics* 103(3), 2012.
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch).

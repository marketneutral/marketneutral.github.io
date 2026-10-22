---
title: "autoresearch for alpha: a first run"
date: 2026-10-23
tag: PROJECT
description: I ran the augmented autoresearch loop from the last essay on a real alpha. A coding agent proposed, tested and kept or discarded changes to a one-expression qex alpha for sixty trials, against a moving evaluator, with a claim before every test. Here is the program, the evaluator, the lab notebook, and what came out.
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
touch the evaluator or the data, be creative, never stop.

## The evaluator

This is where the essay's list becomes code.

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
  <img src="progress.svg" alt="Two panels over sixty trials. Top: the utility of each trial, grey dots discarded, green dots kept and labelled, with a green staircase for the best so far rising from about 0.4 to about 1.2. Bottom: the worst fold of each trial, rising from about minus 0.6 to above zero. Two trials fall below the axes and are marked at the edge.">
  <figcaption>Sixty trials. Grey dots are discarded, green are kept, the staircase is the best so far. The top panel is the score the agent climbs; the bottom is the number it is not allowed to break.</figcaption>
</figure>

PLACEHOLDER: final counts, the kept list in order, and the arc of the run.
What follows is the notebook, condensed.

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

PLACEHOLDER: trials 25 to 60, the ewma keep, the robustness audit, and
whatever else the second half finds.

## What the agent built

PLACEHOLDER: the final expression, read line by line, and its numbers on
2000 to 2017 against the seed's.

## The one run on 2018 to 2025

PLACEHOLDER: test.py output for the seed and the final book, by year,
by regime, and what it says.

## What I learned

PLACEHOLDER.

## References

- Barroso, P. and Santa-Clara, P. "Momentum Has Its Moments." *Journal of Financial Economics* 116(1), 2015.
- Blitz, D., Huij, J. and Martens, M. "Residual Momentum." *Journal of Empirical Finance* 18(3), 2011.
- Da, Z., Gurun, U. G. and Warachka, M. "Frog in the Pan: Continuous Information and Momentum." *Review of Financial Studies* 27(7), 2014.
- Daniel, K. and Moskowitz, T. J. "Momentum Crashes." *Journal of Financial Economics* 122(2), 2016.
- George, T. J. and Hwang, C.-Y. "The 52-Week High and Momentum Investing." *Journal of Finance* 59(5), 2004.
- Grundy, B. D. and Martin, J. S. "Understanding the Nature of the Risks and the Source of the Rewards to Momentum Investing." *Review of Financial Studies* 14(1), 2001.
- Jegadeesh, N. and Titman, S. "Returns to Buying Winners and Selling Losers." *Journal of Finance* 48(1), 1993.
- Moskowitz, T. J. and Grinblatt, M. "Do Industries Explain Momentum?" *Journal of Finance* 54(4), 1999.
- Novy-Marx, R. "Is Momentum Really Momentum?" *Journal of Financial Economics* 103(3), 2012.
- Bailey, D. H. and López de Prado, M. "The Deflated Sharpe Ratio." *Journal of Portfolio Management* 40(5), 2014.
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch).

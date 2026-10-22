---
title: "qex: a small language for alpha"
date: 2026-02-08
tag: PROJECT
description: A domain-specific language for quant alphas. Write the idea in one line, let the engine handle the rolling windows, ranks, missing data, and caching.
---

I have been building a small language for expressing quant alphas, the
cross-sectional forecasts a systematic investor turns into a portfolio.
It is called qex, and it lives at
[github.com/marketneutral/alpha-parser](https://github.com/marketneutral/alpha-parser),
with docs at
[marketneutral.github.io/alpha-parser](https://marketneutral.github.io/alpha-parser/).
The whole pitch fits in one line:

```python
signal = qex("rank(-returns(20) / volatility(60))")
```

That says to rank stocks by risk-adjusted one-month momentum and bet
against the winners, which makes it a mean-reversion alpha, and the
equivalent pandas is fifty lines of rolling windows, axis arguments, and
NaN handling. You do not need to be a programmer to read the short
version: most portfolio managers can code, but anyone who can write an
Excel formula can read that line, and most of what follows.

## Why a language

Anyone who has read Kakushadze's [*101 Formulaic
Alphas*](https://arxiv.org/abs/1601.00991) will recognize the style.
Expressions like `rank(ts_corr(returns(1), volume(1), 20))` are how
large quant shops have described alphas for years.

The usual argument for the form is readability, and it is true that the
expression captures the idea where the pandas buries it. But in the age
of coding agents, "a human has to read this" gets weaker every month,
because nobody reads the fifty lines any more; a model writes them and
another model reviews them. The real case for a language is about what
that changes:

- **The expression is the hypothesis, not the implementation.** It is the
  smallest artifact that fully specifies an alpha, and everything else is
  engine, which is written once.
- **A closed vocabulary makes generated work checkable.** When an agent
  writes fifty lines of pandas, a lookahead, a misaligned index, or a
  wrong axis can hide on any line, and reviewing it costs about what
  writing it did. When an agent writes a qex expression, every well-formed
  expression is already aligned, warmup-aware, and lookahead-free, so the
  only thing it can be wrong about is the idea.
- **Terse is cheap for models.** An expression is a few dozen tokens where
  the pandas is a few thousand, which matters when you want a model to
  propose, mutate, and score thousands of candidates, or hold an entire
  alpha library in context while it works.
- **Alphas become data.** Expressions can be stored, diffed, deduplicated,
  searched, and evolved. Shared sub-expressions are visible, so a thousand
  alphas cost far less than a thousand times one. None of that is possible
  when each alpha is its own script.
- **Review is constant time.** A portfolio manager can audit the intent of
  an expression at a glance, and that is the only kind of review that
  scales to machine-generated research.

In the [last post](/posts/hedge-fund-evolution/) I described the quant
workflow as an assembly line, with alpha research as one stage feeding
signal combination downstream. An alpha language is the interface
between those two stages, and it is what lets alpha research be done by
many people, or by many agents, and still plug into the same pipeline.

## Three axes

Every operation in qex works along one of three axes, and knowing which
one is most of what you need to read an expression.

**Time series** operations run down the rows, one ticker at a time:

```python
ts_mean(close(), 20)      # 20-day rolling mean
delta(close(), 5)         # change over 5 days
ts_corr(returns(1), volume(1), 20)
ewma(returns(1), halflife=10)
```

**Cross-sectional** operations run across the columns, one day at a
time:

```python
rank(returns(20))         # percentile rank across stocks, 0 to 1
zscore(returns(20))
winsorize(returns(20), 0.05)
```

**Group** operations are cross-sectional within a bucket, such as a
sector, an industry, or a pair:

```python
group_demean(returns(60) / volatility(60), 'sector')   # sector-neutral momentum
group_rank(returns(20), 'industry')
```

They compose, so sector-neutral momentum restricted to liquid names is:

```python
group_demean(rank(returns(20)) * (adv(20) > 1000000), 'sector')
```

When an expression repeats itself, `let` names the pieces:

```python
let mom = returns(60),
    vol = volatility(60),
    sharpe = mom / vol
in rank(sharpe) * sign(mom)
```

## Lazy trees, no lookahead

Parsing an expression builds a tree, and nothing is computed until you
call `evaluate` with data, which is a dictionary of DataFrames, one per
field, with dates down the index and tickers across the columns.

```
Rank
 └── Returns(period=20)
      └── Field('close')
```

Because the engine owns every operator, it can enforce things that are
hard to enforce in free-form pandas. The one I care most about is that
**every operation looks backward**, so there is no way to write an
expression that peeks at tomorrow, and `delay` refuses a negative period
rather than silently producing a backtest that is too good to be true.

## Sparse data is a first-class case

Earnings arrive quarterly, so a DataFrame of earnings has a value on
announcement day and NaN everywhere else, and ordinary rolling
operations do the wrong thing on it. For that case qex has event-aware
operators that roll over the past N *observations* rather than the past
N days.

Post-earnings announcement drift, with a textbook standardized
unexpected earnings score, is three lines:

```python
surprise = "field('earnings_actual') - field('earnings_estimate')"
sue      = f"({surprise}) / ts_std_events({surprise}, 8)"
signal   = qex(f"rank(fill_forward({sue}, 60)) - 0.5")
```

That divides this quarter's surprise by the standard deviation of the
last eight surprises, holds it for a quarter, ranks across stocks, and
centers for long-short, and the expression reads like the paper.

## Shared work is done once

A research session evaluates many signals, and they overlap, since
momentum, risk-adjusted momentum, and short-term reversal all need daily
returns. qex builds a single graph for a set of signals and computes
each unique sub-expression one time.

<figure class="wide" id="signal-graph">
  <img src="signal-graph.svg" alt="A directed graph of three signals. The momentum and sharpe outputs both depend on a single shared returns(60) node, highlighted in green; reversal depends on its own returns(5) node.">
  <figcaption>Ovals read data directly. Rounded boxes are computed from other nodes. Green marks the named outputs, and the one green oval is the node two of them share.</figcaption>
</figure>

For three toy signals the saving is one node, but for a thousand signals
drawn from a common vocabulary of primitives it is most of the work. The
same graph can be handed to Dask and evaluated across a cluster, with
the data scattered to workers once.

## Evaluation

A signal is only interesting once you know whether it predicts anything,
so the package ships with the usual tooling: a long-short backtest with
transaction costs and drawdown analysis, quantile analysis with rank IC,
and walk-forward splits.

```python
from qex import qex, Backtest, QuantileAnalysis

signal = qex("rank(returns(60)) - 0.5")

Backtest(signal, transaction_cost=0.001).run(data).summary()
QuantileAnalysis(signal, n_quantiles=5).run(data).summary()
```

There is also a multi-factor risk model whose factor definitions are
themselves qex expressions, so a factor is just another signal.

## A real run

Let's work some real data and an alpha idea motivated by what
practitioners do and the literature. The universe is every current S&P
500 member with a full price history back to mid-2009, 414 names, with
adjusted daily bars from Yahoo Finance. Using current membership makes
the basket survivorship-biased, and that is as much of a problem for a
long-short book as for a long-only one, since the names that fell out of
the index on the way down are exactly the ones a reversal alpha would
have been buying.

The alpha is short-term reversal, which is the family that shows up in
price-only data at a horizon of days to weeks, and the economic story
behind it is old and well documented. Jegadeesh (1990) and Lehmann
(1990) showed that last week's losers beat last week's winners, and the
standard explanation is liquidity provision: when someone has to sell in
size, the price moves more than the news justifies, and whoever takes
the other side is paid for it as the price comes back. Nagel (2012)
makes that precise by showing that the return to reversal is
compensation for supplying liquidity and spikes exactly when liquidity
evaporates. It is also the alpha in Khandani and Lo's
[*What Happened to the Quants in August 2007?*](https://web.mit.edu/~alo/www/Papers/august07.html),
which uses Lehmann's contrarian rule, long recent losers and short recent
winners in proportion to their move, as the canonical statistical
arbitrage strategy. Demeaning within sector rather than against the
market is the modern refinement, since what you want to fade is the
stock-specific move and not the industry's.

The version here is where the stock closed within its own five-day
high-low range, inverted so that a close near the low is a buy. It is
reversal scaled by the stock's own recent volatility, and technicians
have called it Williams %R or a stochastic oscillator for fifty years.
Rank it across stocks, demean within sector so the book is sector-neutral
and dollar-neutral by construction, and smooth it with a linear decay:

```python
raw   = "-(close() - ts_min(low(), 5)) / (ts_max(high(), 5) - ts_min(low(), 5))"
book  = f"group_demean(rank({raw}), 'sector')"
alpha = qex(f"decay_linear({book}, 10)")
```

The decay is a denoiser. `decay_linear` is a weighted moving average whose
weights fall off linearly with age, the linear cousin of an
exponentially weighted average: over a ten-day window today carries 18%
of the weight, yesterday 16%, and the tenth day back under 2%, so the
signal is smoothed without being lagged the way an equal-weight ten-day
mean would lag it.

The book is rebalanced every day to the alpha's weights, and turnover is
quoted per day. The run is July 2010 to the date of this post in
February 2026. Costs are charged per unit of turnover at 2 basis points,
which is a reasonable level. All returns are on the gross book,
unlevered, meaning a dollar long against a dollar short with no
financing and no leverage. The table shows the same alpha unsmoothed and
with a five-day and a ten-day decay.

| Range, daily | Turnover / day | Gross annual | Gross Sharpe | Net at 2 bps | Net Sharpe | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| no smoothing | 84% | +3.7% | 0.96 | -0.6% | -0.14 | -21% |
| decay 5 | 44% | +3.7% | 0.91 | +1.5% | 0.37 | -16% |
| **decay 10** | **32%** | **+3.7%** | **0.86** | **+2.1%** | **0.49** | **-15%** |

Max drawdown is on the book net of 2 basis points.

<figure class="wide" id="gross-vs-net">
  <img src="gross-vs-net.svg" alt="Three panels of cumulative long-short return for the range alpha from 2010 to early 2026: unsmoothed, five-day decay, and ten-day decay. Gross ends near plus 75 percent in all three. Net of 2 basis points ends at minus 9 percent unsmoothed, plus 25 percent with the five-day decay, and plus 37 percent with the ten-day decay.">
</figure>

The alpha looks decent. Gross Sharpe is 0.86 to 0.96 over the run, and
the same held on a mid-cap universe and in the sub-periods I checked
along the way. Just under four percent a year on the gross book is good
for a single price-based alpha, since a real quant book runs at four to
six times leverage, where it is mid-teens to twenty percent before
financing, and no quant book trades a single alpha anyway; this one
would be one input among many. Cost is most of the story. Unsmoothed,
the book turns over 84% a day and loses money net of 2 basis points
despite having the best gross Sharpe of the three. That pre-cost signal
is still worth something to a market maker, who is paid the spread
rather than charged it, and the move of high-frequency firms into stat
arb that the press has covered, such as Bloomberg's December 2025 story
on Hudson River Trading holding positions for days and weeks, is this
picture seen from the other side. Smoothing helps, as expected: the
ten-day decay cuts turnover to 32% with no loss of gross return and
takes the net Sharpe at 2 basis points from negative to about 0.5, and
turnover around thirty percent a day is the classic mid-frequency
statistical arbitrage space. Ten days is a common default for this kind
of smoothing, and in the language the whole change is one `decay_linear`
around the expression.

![Bar chart of the ten-day decay book's net annual return by calendar year at 2 basis points, 2010 through 2025. Twelve of sixteen years are positive, with 2020 the standout at plus 16 percent and 2025 the worst at minus 3.](range-by-year.svg)

The smoothed book is positive in twelve of the sixteen full calendar
years, and the standout is 2020, when reversal made in one year what it
normally makes in five, which is Nagel's point exactly: dislocation is
when liquidity providers get paid. The last few years are thinner, and
the plain reading is that an alpha this simple decays as more capital
trades it. This post is not meant to hand you a new alpha source; if it
were still a secret I would not be writing it up.

## Limitations

The data model is a single value per cell, so qex is not point-in-time.
If a company reports a dollar of earnings in January and restates it to
three dollars in March, qex only knows one of those numbers, and the run
above uses today's adjusted prices and today's index membership, which
is why it is survivorship-biased. Bi-temporal data, where every value
carries both the date it describes and the date it became known, should
come in a future release. qex is meant in its current form as an
exploration tool, not production ready for an institution.

## Future directions

qex is a natural fit for a language model that writes alphas. A
model that writes pandas can introduce lookahead without seeing it, and
the result is fifty lines nobody wants to audit. A model that writes qex
cannot look ahead, because the operators do not allow it, and the search
space is constrained to a closed vocabulary of operators and fields,
which makes a candidate alpha cheap to generate, cheap to check, and
cheap to compare against the library. The package already lets a dataset
describe its own fields, so an agent can discover what is available
before it proposes an expression. That is the setting the
human-plus-machine collaboration in the last post needs.

qex is at version 0.3, Apache licensed, and installs from the repo.
Issues and pull requests are welcome.

---
title: '"find alpha. make no mistakes."'
date: 2026-10-26
tag: PROJECT
description: Can an AI agent do quant research without fooling itself? I gave one a textbook momentum strategy that loses money, a set of rules meant to stop it overfitting, and sixty tries. Here is what it built, how it did on eight and a half years it never saw, and what the notebook taught me.
---

Can an AI agent do quantitative research without fooling itself? Not run a
backtest, which is easy, but do the job: start from a view, propose changes,
test them honestly, throw away what does not work, and end with something
that holds up on data it never saw. Backtests are the easiest thing in
finance to fool yourself with, and an agent that tries thousands of ideas
an hour is the fastest way yet to do it.

So I set one up to fail in the usual way and then took away the ways it
could. I gave Claude Code a textbook momentum strategy that lost money,
a page of the firm's beliefs about why momentum works and why it crashes,
and a set of rules meant to stop it overfitting. Then I let it run sixty
trials, each one a single change with a written claim before the test.

<figure class="wide" id="gross-vs-net">
  <img src="gross-vs-net.svg" alt="Cumulative P&L as a percent of gross from 1999 to August 2026, with the inspection and test periods shaded. The final book cost-free rises steeply through inspection to about 170 percent, then steadily through validation and test to plus 467 percent; net of 10 basis points it ends at plus 381 percent. The seed, dashed, wanders near zero and ends at plus 10 percent.">
  <figcaption>Where it started and where it ended. The dashed line is the strategy I gave the agent; the green line is what it built. The agent was scored on the middle band only. The shaded band on the right, 2018 to 2026, was never shown to it. Cumulative P&L on a book held at a constant size, so a constant slope is a constant return.</figcaption>
</figure>

It took 55 minutes and about twenty dollars. On the period it was scored
on, 2004 to 2017, the strategy went from losing 1% a year to making 13%,
with a Sharpe ratio of 1.1. On the eight and a half years after that, which
the loop never saw, it made 13.5% a year at a Sharpe of 0.76, while the
strategy it started from made nothing. About 70% of the risk-adjusted
return survived, and all of the return did. The test period did hold one
ugly surprise, a 27% drawdown in six weeks at the very end, of a kind the
book's crash defense was never built to see. I will get to it.

But the strategy is not the point of this post, and I would not trade it as
it stands. The point is the method: whether a loop like this can be trusted
to do research, and what has to be true for it to be trusted. The most
useful thing it produced is not the strategy but the lab notebook, and in
particular one argument, made with evidence, for why the crash defense I
gave it was right and the hedge I would have reached for was not.

## Why backtests lie, and the rules I set

In [autoresearch: sparks of an AI scientist](/posts/ai-scientist/) I took
Andrej Karpathy's autoresearch loop, an agent that edits one file, scores
it, keeps it if the score went up and tries again, and argued that pointed
at a backtest it would find noise. Try enough variations on enough history
and one of them will look brilliant by chance. I listed what would have to
change for it to find alpha instead. This post is that list, built and run
once. In plain terms:

1. **Say why before you test.** Every change starts with a written claim:
   which belief it tests, the economic mechanism, and what should improve.
2. **Do not let it learn the test.** The score is computed on a fresh random
   split of history every time, so there is no fixed exam to memorize.
3. **Make complexity cost something.** Every extra piece of the formula is
   charged against the score.
4. **Count the tries.** A good result after sixty attempts is worth less
   than after one, and the evaluator says how much less.
5. **Start from a view.** The firm's beliefs, with the papers behind them,
   are the agent's starting point, not a blank page.
6. **Keep one period sealed.** The last eight and a half years are never
   loaded until the run is over, and then once.

<figure class="diagram" id="loop">
  <img src="augmented-loop.svg" alt="The autoresearch loop with the finance changes. Top row: you write the beliefs with mechanism, counterparty, paper and prediction; the agent reads the expression and 1999 to 2003, proposes a change, writes the claim naming the belief and what should move, edits alpha.qex and commits. Middle row: deal 50 random purged partitions of 2004 to 2017, score each fold as fitness minus a charge per node, then a decision: median up by more than the noise, worst fold not down, and still eligible? Yes keeps it, no undoes it, both return to reading. Bottom row: every attempt is logged with its claim, outcome, regime split and trial count; you read the notebook; and after the last trial, 2018 to 2026 is run once.">
  <figcaption>The loop. Green is the step handed to the model; orange is what the rules added. Every orange box is a few lines of the evaluator or the problem definition.</figcaption>
</figure>

History is cut three ways, and the loop never mixes them.

| period | dates | who sees it |
|---|---|---|
| inspection | 1999 to 2003 | the agent, freely: the dot-com top, the bear market, the 2003 junk rally |
| validation | 2004 to 2017 | the scoring only; the agent sees a number, never the prices |
| test | 2018 to Aug 2026 | nobody, until the end |

Two more things matter for reading the numbers. The universe is every
investable US stock as it was on each day, about 1,350 names in 1999 and
2,000 by 2017, including every company that later went bankrupt or was
bought. A first version of this experiment used today's S&P 500 and the
loop dutifully learned that basket's survivorship bias along with the
alpha; here the losers that fell out of the index are in the data, and they
are exactly what a momentum strategy is short. And the strategy is always
the same shape, whatever the agent writes: as many dollars long as short,
the same total size every day, no stock above 5%, and trading on yesterday's
information. The agent can only decide which stocks get the weight. The
returns below are per dollar of that book, longs plus shorts, unlevered.

The numbers are on corrected data. After the run, an audit of my data
warehouse found a bug that had shifted about 3% of the universe, and every
number here is re-scored with it fixed. That bug turned out to be the most
interesting lesson of the whole exercise, and it gets its own section at
the end.

## The problem: momentum, and its crashes

Momentum is one of the oldest and best-documented effects in markets: the
stocks that did best over the past year tend to keep doing better than the
ones that did worst, for a few more months. Buy the winners, short the
losers. It has worked in nearly every market anyone has tested.

It also has a famous flaw. Every decade or so it loses in a few months
what it made in years. The worst was 2009: after the market bottomed in
March, the past year's biggest losers, the banks and the near-bankrupt,
rallied hardest, and a momentum book that was short exactly those stocks
lost most of its value. Daniel and Moskowitz showed that these crashes are
not random. They come after the market has fallen, when volatility is
high, in a sharp rebound, and almost entirely on the short side.

The goal I gave the agent: keep momentum's premium without those months. I
wrote twelve beliefs, each with a mechanism, the paper behind it, and a
prediction specific enough to be wrong. The first four are the textbook:
rank stocks against their own sector, skip the most recent month, measure
the move relative to how volatile the stock usually is, and stay
sector-neutral. The rest are about the crash. The one I cared most about
was belief 7: when the crash conditions appear, do not just shrink the
bet, reverse it, because a momentum crash is by construction the losers
coming back.

The starting strategy, the seed, is the textbook beliefs and nothing else,
what any quant would write first. In qex, the small language the strategy is
written in (there is a [post on it](/posts/qex/)), it is four lines:

```python
let mom   = delay(returns(231), 21),
    vol   = volatility(60),
    score = group_demean(mom / vol, 'sector')
in decay_linear(score / vol, 10)
```

On 2004 to 2017 it lost about 1% a year, and it lost hardest exactly when
the market was in the crash state: a Sharpe of −1.96 on those days. It also
lost 8 basis points on every dollar it traded, before costs.

## The run, in four acts

<figure class="wide" id="progress">
  <img src="progress.svg" alt="Two panels over sixty trials. Top: the score of each trial, grey dots discarded, green dots kept and labelled, with a green staircase for the best so far rising from minus 0.09 at the seed to 1.47. The kept labels are crash switch, drop 1/vol, 1-year vol, 1-month reversal sleeve, 1-year state, residual momentum, a·|a| with decay 3, cube, soft switch, beta hedge, deep-bear rule, no vol scaling, 504-day beta, and drop the hedge. Bottom: the worst slice of each trial, rising from minus 0.96 to plus 0.40, with one discarded trial at minus 0.51.">
  <figcaption>Sixty trials. Grey dots were thrown away, green dots kept, and the staircase is the best so far. The top panel is the score the agent climbs; the bottom is the score on the worst slice of history, which it is not allowed to make worse.</figcaption>
</figure>

Sixty trials, fourteen kept. Two numbers decide each one. The *score* is
computed on six random slices of 2004 to 2017, each about two and a half
years, and the agent climbs the middle one. The *worst slice* is the score
on the unluckiest of the six. A change is kept only if it raises the
score by more than the measured noise and does not make the worst slice
worse. The seed's worst slice scored −0.96; by the end, even the worst slice
was comfortably positive, at +0.40.

What follows is the [notebook](lab/results.tsv), condensed. The figures in
this section are the ones the agent saw during the run.

### Act 1: fix the obvious

**Trial 1: the crash switch.** The agent started with belief 7 as a hard
rule: when the market is down over two years and this month is more
volatile than the year, flip momentum to its reverse. It predicted the worst
slice would improve more than the score, and it did. On crash-state days
the strategy went from a Sharpe of −1.96 to +3.32.

**Trial 2: delete a line.** The seed divided by volatility twice, once to
rank stocks fairly and once to size them, which piled the book into quiet
stocks whose momentum carries little return. Deleting the second division
made the strategy profitable enough per dollar traded to pass the
evaluator's cost check.

### Act 2: build the engine

**Trial 6: a second, faster bet.** The agent added a one-month reversal: a
stock that lagged its sector last month tends to bounce. The argument was
about the scoring formula as much as the market: the score does not charge
for trading below a certain rate, so a fast bet rides almost free.

**Trial 8: residual momentum.** Instead of ranking stocks on their raw
return, rank them on the part the market did not explain, so a stock is not
counted a winner just for being high-beta in a rising market. This is
Blitz, Huij and Martens's fix, and the agent predicted it would help the
worst slice more than the score. It did, and the Sharpe passed 1.0.

**Trials 14 to 17: concentration.** The agent's own idea, not in the
beliefs. The book's size is fixed, so return comes from where the weight
goes: put more of it on the stocks where the signal is strongest. Squaring
the signal raised the return but also the trading, and fell short by a
hair. Squaring it and smoothing it over three days kept. Cubing it, one
piece simpler, gained more.

Along the way, the textbook alternatives mostly failed. Novy-Marx's version
of momentum was worse; the 52-week high and the "frog in the pan" were
worse; an outside idea from a 2012 paper on liquidity was reset twice. The
agent named the paper and its age before testing it, as the rules require.

### Act 3: the crash argument

This is the heart of the run.

**Trial 22: soft beats hard.** Instead of flipping all at once, the agent
made the momentum weight slide with the market's past-year return when
volatility is high: full reversal after a 10% fall, nothing on a flat year,
full momentum after a 10% rise. My belief predicted the soft version would
help less and hurt less. It beat the hard switch on both numbers.

**Trial 24: a hedge.** The agent added a hedge against market beta, on
Grundy and Martin's argument that momentum's crash is really a market
event: hedge out the market and the crash goes with it. It kept.

**Trial 27: the experiment I would not have run.** Then the agent asked the
question that follows: if the book is now hedged against the market, is the
crash switch still needed? It wrote down in advance what would settle it,
and ran the test. Without the switch the worst slice fell from +0.02 to
−0.51, and on crash days the strategy went back to losing 15% a year. Its
conclusion: a hedged momentum book still crashes, because the crash is not
the market. It is the specific losers coming back.

**Trial 28.** The other famous cure, Barroso and Santa-Clara's scaling of
momentum by its own recent volatility, added nothing on top of the switch.
The beliefs had warned this was the idea most likely to be already priced.

**Trials 30 and 31: the deep-bear rule, the best idea of the run.** The
switch only acts when this month is more volatile than the year. But after
a volatility spike, the spike itself raises the year's number, so the
switch turns off while the market is still deep in its hole and the losers
are still rallying. That is 2009. The agent added a second rule for calm
markets: shrink momentum after a 10% fall in the year, and reverse it after
20%. On its own the rule fixed the worst slice and hurt the score; combined
with the first, the volatility rule earned the score and the depth rule
saved the rebound. The worst slice went from 0.02 to 0.32.

### Act 4: prune

**Trial 33: no volatility adjustment at all.** Belief 4, removed. With the
switch in place, the volatile stocks carried return without the crash risk
the belief was meant to guard against. Return went from 8% to 13% a year.

**Trials 52 to 56: take things out.** The rules say that when out of ideas,
remove something. Removing the one-month reversal cost a lot; going back to
raw momentum cost even more, so residual momentum is the core. And
removing the hedge from trial 24 *improved* the strategy. The agent had
predicted the opposite and said why it was wrong: once momentum was
measured as the part the market did not explain, the book carried almost no
market risk, and the hedge was only spreading weight thin. A piece that paid
at trial 24 had stopped paying since, and only removing it found that out.

## What it built

Here is the final strategy in plain English, written the way the beliefs
were written going in:

<div class="callout">
I believe that a stock which has beaten its sector over the past year,
counting only the part of its return the market did not explain, will keep
beating it, so I own it, and I short the ones that lagged. I skip the last
month, because last month's moves reverse. I watch the market as a whole.
When it is calm and has not fallen far, I hold full momentum. When it has
fallen, I hold less, nothing at a 10% fall and the reverse at 20%, because
the losers are about to rebound. When it is turbulent, I hold full momentum
only if the market is up 10% on the year, nothing if it is flat, and the
reverse if it is down 10%. Separately, I bet that a stock which lagged its
sector last month will bounce. I add the two views and cube the sum, so I
bet most where they agree and almost nothing where they are lukewarm. I hold
no net position and never more than 5% in one name.
</div>

Who is on the other side? In ordinary markets, the investor who sells
winners too early and holds losers too long. In the crash state, the
momentum investor who is short the losers when they rebound. The strategy is
long momentum most of the time and short it in the specific conditions
where momentum is known to crash, and it reads those conditions from three
numbers about the market that anyone could have computed in 2004.

The string itself, for the technical reader:

```python
let mr    = returns(1) * field('member'),
    mk    = mr - demean(mr),
    m1    = ts_sum(mk, 252),
    w     = where(ts_std(mk, 21) > ts_std(mk, 252),
                  max(min(10 * m1, 1), -1),
                  max(min(10 * m1 + 1, 1), -1)),
    b     = ts_beta(returns(1), mk, 504),
    rr    = returns(1) - b * mk,
    mom   = delay(ts_sum(rr, 231), 21),
    score = group_demean(mom, 'sector'),
    a     = decay_linear(w * score, 10) - group_demean(returns(21), 'sector')
in decay_linear(power(a, 3), 3)
```

| In the string | In English |
|:---|:---|
| `mk = mr - demean(mr)` | The market's return each day: the average stock, equal weight |
| `m1 = ts_sum(mk, 252)` | The market's past-year return |
| `ts_std(mk, 21) > ts_std(mk, 252)` | The market is turbulent: this month's volatility above the year's |
| `max(min(10 * m1, 1), -1)` | Turbulent: momentum scaled by the market's year, full reversal at −10% |
| `max(min(10 * m1 + 1, 1), -1)` | Calm: full momentum unless the market is down, reversal at −20% |
| `b = ts_beta(returns(1), mk, 504)` | Each stock's two-year beta to the market |
| `rr = returns(1) - b * mk` | The part of its return the market did not explain |
| `delay(ts_sum(rr, 231), 21)` | Eleven months of that, skipping the last month |
| `group_demean(…, 'sector')` | Relative to its sector |
| `decay_linear(w * score, 10)` | The switched momentum view, smoothed over two weeks |
| `- group_demean(returns(21), 'sector')` | Plus last month's sector-relative losers, which bounce |
| `power(a, 3)` | Cubed: most weight where the two views agree |
| `decay_linear(…, 3)` | Smoothed over three days, to hold trading down |
| from the evaluator | Universe members only, yesterday's data, dollar-neutral, constant size, 5% cap |

Every piece maps to a notebook entry, and every piece was tested by taking
it out.

## Did it hold up?

The sealed period, 2018 to August 2026, was loaded for the first time after
trial sixty, by a script the agent never saw, run once on three strategies:
the final one, the seed, and trial 55, a near miss the agent flagged for me
(more on it in the lessons). The [output](lab/test-2018-2026.txt) is in the
post's folder.

| | period | Sharpe | return / yr | net of 10 bps, / yr | max drawdown |
|---|---|---:|---:|---:|---:|
| seed | scored on, 2004-2017 | −0.23 | −1.0% | −2.3% | −27% |
| seed | sealed, 2018-2026 | 0.12 | +0.9% | −0.4% | −19% |
| **final** | scored on, 2004-2017 | 1.08 | +12.9% | +9.9% | −24% |
| **final** | sealed, 2018-2026 | 0.76 | +13.5% | +10.5% | −27% |

*Per dollar of longs plus shorts, unlevered; cost-free unless marked. The
10 bps column charges ten basis points on every dollar traded.*

The return held completely. What changed is the volatility around it, 18% a
year out of sample against 12% in sample, which is why the Sharpe fell by a
third. That is ordinary shrinkage for a strategy chosen on history, and far
better than the record for backtests chosen without discipline, where the
out-of-sample Sharpe is close to unrelated to the in-sample one. The seed
earned nothing over the same years, so the loop's improvement is real in
the sense that matters: the strategy is better than its starting point on
every line, in a period neither the loop nor I had looked at.

<figure class="wide" id="by-year">
  <img src="by-year.svg" alt="Bar chart of the final book's cost-free return by calendar year from 1999 to 2026, with the inspection and test periods shaded. Twenty-six of twenty-eight years are positive. The largest are 1999 and 2000 at about 57 percent; 2008 is plus 35 percent. The two negative years are 2006 and 2018, each under one percent.">
  <figcaption>Return by calendar year, cost-free. Twenty-six of twenty-eight years positive; the two losing years each lost less than 1%. The 1999 and 2000 bars are the inspection period, which the agent could look at, and the dot-com bubble and bust were one long momentum trade followed by one long reversal.</figcaption>
</figure>

### Did the crash switch work out of sample?

The switch is one number a day, the same for every stock, so it can be
pulled out and plotted. Red bands are the days it held the book in reverse.

<figure class="wide" id="crash-switch">
  <img src="crash-switch.svg" alt="Two panels from 1999 to 2026. Top: the equal-weight market of members on a log scale, rising from 1 to about 40 with drawdowns in 2000 to 2002, 2008 to 2009, 2015 to 2016, 2018, 2020 and 2022. Bottom: the momentum weight w, at plus one most of the time, dropping toward or to minus one in 2001 to 2003, 2008 to 2009, late 2015 to 2016, late 2018, 2020 and 2022. Red bands mark reversal days, concentrated in those episodes.">
  <figcaption>The momentum weight through time, against the average stock. It sits at full momentum about four days in five and in reverse about one day in ten.</figcaption>
</figure>

It goes into reverse where the textbook says it should: the end of the 2000
to 2002 bear market, late 2008 through spring 2009, the 2015-16 sell-off,
and, out of sample, late 2018, 2020 and 2022. The episodes:

| episode | final | seed |
|---|---:|---:|
| 2008 crash, Sep 2008 to Feb 2009 | +4.4% | +5.6% |
| 2009 junk rally, Mar to Jun 2009 | +14.6% | −13.6% |
| Q4 2018, Oct 2018 to Jan 2019 | −5.9% | −1.3% |
| COVID, mid-Feb to May 2020 | +2.7% | +10.5% |
| 2022 bear market | +4.5% | +6.3% |

The 2009 line is the one the whole exercise was written for: the junk rally
that wrecked momentum strategies cost the seed 14% in four months and earned
the final strategy 15%. Out of sample the episodes are less dramatic, and
in two of them the seed did better, because its momentum bets happened to
be positioned well. Across all the days the switch held the book in
reverse, it turned what was a loss of 12% a year for the seed into a gain
of 10% out of sample, about a quarter of what it did in sample. The
switch's job is not to win every bear market; it is to not be short the
losers when they rebound, and none of the sealed period's bear markets cost
the strategy more than 6%.

### The drawdown it did not see

The worst stretch of the sealed period came at its very end, and it is not
the crash the beliefs were about. From mid-June to late July 2026 the
strategy lost 27% in six weeks, and it had not recovered by August 11. The
switch sat at full momentum the whole time, because the market was calm and
up on the year. The loss was on the long side: last year's winners giving
back their gains, 20% of the book lost on the longs against 5% on the
shorts, and a single stock at the 5% cap cost 5% by itself.

Momentum's textbook crash is the losers rebounding after a fall, and the
switch is built to see it. A winners' unwind in a calm market is a
different event, and nothing in this strategy sees it coming. The
concentration makes it worse. The book holds 1,200 to 2,000 stocks a day
but behaves like about a hundred, because the cube puts most of the weight
in the extremes and dozens of positions sit at the cap. When a handful of
them turn, the losses are large.

So I would not trade this as it stands. It is one price-based signal,
concentrated by design, and its last six weeks show what that concentration
costs; a real portfolio is many signals with position limits set by risk,
not a flat 5%. As a test of the method, though, it is a clean result. The
loop improved the firm's starting view by a wide margin on the period it
could see, most of that improvement survived the period it could not, and
the firm's central belief, the one about the crash, held up both in the
notebook and out of sample. The sealed period is now spent for these
strategies.

## What I learned

**The biggest error was in the data, and no sealed period would have caught
it.** After the run, while asking why a later run's strategy looked neutral
to company size, I found a bug in my data warehouse's market capitalization.
It multiplied each day's share price by a share count that the data vendor
restates for every later stock split, so a company that split later looked
several times bigger than it was. Market cap decides which stocks are in
the investable universe, so about 3% of the universe was wrong. Fixed and
re-scored, the final strategy's Sharpe on the scored period fell from 1.27,
the number the agent saw, to 1.08, about 0.18 of that from the data alone.
Its sealed-period Sharpe barely moved, 0.77 to 0.76.

That combination is the lesson. The bug was in every slice of every deal and
in the sealed period too, so the loop could not see it and the sealed period
could not measure it. It flattered the in-sample result without hurting the
out-of-sample one, which is the most dangerous kind of error, because it
makes the gap between the two look smaller than it should. It was found by
accident, and the audit that followed, checking the warehouse against the
vendor's own numbers and the SEC's filing dates, is now a suite of checks
that runs after every data refresh. A loop like this is only as good as the
data underneath it, and the data has to be tested on its own, the way the
evaluator is.

**Measure the noise at the top, not just at the start.** Before the run I
scored the seed eight times; the score moved by about 0.02 from call to
call, and that set the bar for a keep at 0.03. Late in the run the agent
scored the same strategy, written two ways, and got results 0.058 apart.
The noise grows as the score does, so a bar set at the seed lets lucky draws
through and then makes them hard to beat: the agent itself wrote that two of
its best scores were "likely favorable draws, which made the 0.03 bar hard
to clear afterward". The fix is cheap: re-measure the noise on the current
best every ten trials.

**The keep rule cannot accept a change that only makes the worst case
better.** That is a strange blind spot for a problem about crashes. Trial
30, the deep-bear rule on its own, lifted the worst slice from 0.02 to 0.35
and was thrown away; the agent got it in at trial 31 only by pairing it
with something that raised the score. Three later changes, trials 51, 55 and
58, improved the whole-period Sharpe and the worst slice and lost a little
on the score, and were reset. The agent flagged all three for me, and I ran
trial 55 on the sealed period beside the final strategy. It did slightly
worse, a Sharpe of 0.69 against 0.76, so this time the rule chose well. But
a rule for this problem should accept a change that improves the worst case
by more than its noise and leaves the score alone.

**The period the agent could look at was right about structure and wrong
about risk.** Five years of bubble and bear market were good for catching
broken formulas and excess trading. For anything that reshaped risk they
pointed the wrong way. The worst case was trial 40, a clever variant that
kept the winners long while flipping only the losers: it added 0.3 of Sharpe
on 1999 to 2003 and cut the score on 2004 to 2017 by almost half. The agent
noticed, and stopped trusting the early period for those changes.

**Removing things was some of the best research.** Three deletions, a
redundant volatility division, the volatility adjustment, and the agent's
own hedge, were together worth about a third of the final score. Pieces that
pay at one point in a search can stop paying after later changes, and only
taking them out finds that out.

**The written claims were the most valuable output.** The agent predicted
most of its own failures, which is what a claim before the test is for. And
when it was wrong it wrote down why: the soft switch beat the hard one
because it also trimmed momentum in turbulent markets that were only
slightly up; the hedge stopped paying because the residual measure had
already removed the market. Read carefully, the notebook is not a search
log. It is a short course in what this strategy is.

<div class="callout">
Sixty trials, fourteen keeps, one look at the future. The firm's central
belief held, the hedge the firm would have reached for did not, and the
error that moved the numbers most was in the data the whole loop stood on.
The strategy is not the point; the notebook is.
</div>

## For the technical reader

The rest of this post is the machinery, for anyone who wants to check the
work or build their own.

### The lab

| file | role | the agent may |
|---|---|---|
| [`program.md`](lab/program.md) | the problem definition and the twelve beliefs | read |
| [`alpha.qex`](lab/alpha.qex) | one qex expression, the active hypothesis | **edit** |
| [`eval.py`](lab/eval.py) | the frozen evaluator | run, through `trial.sh` |
| [`explore.py`](lab/explore.py) | helpers over the inspection period, 1999 to 2003 | run |
| [`results.tsv`](lab/results.tsv) | the lab notebook, one line per trial | append |
| [`summary.md`](lab/summary.md) | the agent's own account, written at the end | write |
| `data/` | daily prices, universe membership, market cap, sectors | read through `explore.py` |

### The data

The data is point-in-time and free of survivorship bias, which matters more
for momentum than for almost any other signal, because the stocks a momentum
book shorts are the ones most likely to disappear. The source covers every
US common stock that traded over the period, not just the ones listed today:
about 8,600 names, including every company that was later delisted, went
bankrupt or was acquired, each with its prices up to its last trade. Prices
are adjusted for splits and dividends so returns are total returns, and the
strategy can only compare stocks by returns and ratios, never by price
levels, which an adjustment made later would distort.

The universe is decided each day from that day's facts alone: a US common
stock is in it if its as-traded close is at least $2, its 20-day average
dollar volume is at least $5M, and its market cap, from that day's price and
the share count known on that day, is at least $300M. Names enter and leave
as they cross those lines, about 1,350 on an average day in 1999 and 2,000
by 2017. A stock that falls through the floor on the way to bankruptcy is in
the book until the day it falls out, and its losses count. This is the
universe the market-cap bug corrupted: the share counts were restated for
later splits, which is to say they were not known on the day. Fixing it was
a point-in-time repair.

### The run

The agent is Claude Code, started
headless with `START.md` and told to begin; the run was one session of 560
turns. The agent's [summary](lab/summary.md) is worth reading in full.

### The book and the score

The evaluator turns any expression into a book with the standard simulation
of *Finding Alphas*, the same settings WorldQuant's BRAIN platform uses:
universe members only, delay 1 (the weight held from close *t* to *t+1* uses
data up to close *t−1*), and each day demeaned to dollar-neutral, scaled to
a gross of exactly one, and clipped at 5% per name, repeated until all three
hold. The expression's magnitude is relative weight within a day and
nothing else. The first version of this lab let gross vary, and the book it
found ran twice its average size in calm years, a volatility target that
flattered its Sharpe; now that lever does not exist.

Each fold is scored

```
utility = fitness − 0.003 × nodes
fitness = Sharpe × √( |annual return| / max(turnover, 0.125) )
```

on cost-free P&L, where nodes counts every operator, constant and field in
the parsed expression. Fitness is the book's own measure: a Sharpe of 1.5 at
10% a year and 20% daily turnover has fitness 1.06, the same Sharpe at 70%
turnover 0.57. A fold scores minus infinity if the book holds fewer than
fifty names or trades outside 1% to 70% a day. The whole validation book
must also be *eligible*: turnover in that band and a margin, cost-free P&L
per dollar traded, of at least 5 basis points. Once the best book is
eligible, nothing that breaks eligibility can be kept.

The validation period is cut into twelve contiguous blocks of about fourteen
months. Each call deals them at random into six folds of two blocks, purges
a 21-day embargo at every block edge, repeats for fifty deals, and reports
the median fold and the worst fold, each averaged over the deals. The seed,
scored eight times, stayed within −0.10 to −0.08 on the median and −1.03 to
−0.90 on the worst ([noise.txt](lab/noise.txt)), so a keep must beat the best
median by more than 0.03 and not lower the worst fold by more than 0.13.

### The rules, built

| the essay said | what was built | what it did |
|:---|:---|:---|
| **Require the claim before the test.** | A rule in `program.md`: every trial begins with a written claim naming the belief and which regime split should move. `eval.py` prints the splits, by dispersion, by the crash state and by half. | Sixty claims, each committed before its run. The most useful outcomes are the wrong predictions: the soft switch, and the hedge that stopped paying. |
| **Make the evaluator move.** | Purged, randomized cross-validation as above, a fresh deal every call. | No single hold-out to climb. The cost is noise, and the noise at the top was larger than at the seed. |
| **Charge for complexity.** | 0.003 of utility per node. | The final book has 32 nodes and pays 0.096. Dropping the hedge saved twelve nodes, 0.036 of that trial's 0.10 gain. |
| **Count the trials.** | `eval.py` counts the notebook's rows and prints Bailey and López de Prado's deflated Sharpe. | Every row has its numbers. The final book's deflated-Sharpe probability was 0.974 after 61 rows. |
| **Seed the search.** | Twelve beliefs, each with mechanism, counterparty, paper and prediction. | Four held (2, 5, 7, 10), one held only for the inputs (3), three failed (6 as volatility scaling, 8, 9), and two were removed (4, 11). |
| **Measure the consensus.** | Before testing an idea not on the list, say where and when it was published. | One outside paper, Nagel (2012), "known about 12 years, probably mostly priced". Reset twice. |
| **Keep one period the loop never touches.** | 2018 to 2026-08-11 is not loaded by `eval.py`. A separate script ran it once, after trial sixty. | The table above. |

### What the loop could have known

Nothing in the loop's inputs postdates the validation period.

- Every paper cited in the program was published by 2016. The most recent,
  Daniel and Moskowitz (2016), uses a sample ending in 2013. The only paper
  the agent reached for on its own is from 2012.
- No year from 2018 on appears in the beliefs, in the agent's sixty claims
  or outcomes, or in its summary, except the period table and one line
  saying the near misses were "untested on 2018+, like everything else".
- The evaluator never loads a price after 2017-12-31.

What cannot be audited away is the agent itself. It is a language model,
and its training data includes 2018 on: it has read about March 2020. The
data it could touch was blind to the test period; its memory was not. I see
no sign in the notebook that it used that memory, every claim is argued from
the beliefs and the folds, but it is a form of leakage no held-out period can
close, and it will be true of every loop built on a model that has read the
news.

### The full table

Every number on gross one, rebalanced daily, cost-free unless marked, on the
corrected data with today's evaluator (the same book construction, with
cross-sectional operators seeing only members).

| | period | Sharpe | return / yr | turnover / day | margin | Sharpe at 10 bps | max drawdown |
|---|---|---:|---:|---:|---:|---:|---:|
| seed | inspection, 1999-2003 | 0.50 | +3.3% | 5% | 24 bps | 0.29 | −20% |
| seed | validation, 2004-2017 | −0.23 | −1.0% | 5% | −8 bps | −0.52 | −27% |
| seed | test, 2018-2026 | 0.12 | +0.9% | 5% | 7 bps | −0.05 | −19% |
| **final** | inspection, 1999-2003 | 1.93 | +34.2% | 15% | 94 bps | 1.72 | −20% |
| **final** | validation, 2004-2017 | 1.08 | +12.9% | 12% | 43 bps | 0.83 | −24% |
| **final** | test, 2018-2026 | 0.76 | +13.5% | 12% | 45 bps | 0.59 | −27% |
| T55 | test, 2018-2026 | 0.69 | +11.0% | 12% | 37 bps | 0.50 | −24% |

By switch state, Sharpe and annualized return within the state:

| state, share of days | validation, final | validation, seed | test, final | test, seed |
|---|---:|---:|---:|---:|
| momentum, w = 1, about 80% | 0.85 / +8.1% | 0.18 / +0.6% | 0.88 / +15.5% | 0.12 / +0.8% |
| shrunk, 0 < w < 1, about 10% | 2.16 / +27.3% | −0.10 / −0.6% | 0.12 / +1.5% | 1.69 / +16.1% |
| reversal, w ≤ 0, about 10% | 1.66 / +38.6% | −1.86 / −14.9% | 0.46 / +10.1% | −0.98 / −11.8% |

### Does the signal sort returns?

The [qex post](/posts/qex/)'s first check was whether an alpha sorts returns
at all. Here is the final book's signal before the cube, by quintile,
against the next day's return relative to the average member.

<figure class="wide" id="quintiles">
  <img src="quintiles.svg" alt="Grouped bar chart of next-day return by quintile of the final book's signal, relative to members, annualized, for inspection, validation and test. Monotonic in every period: the shorted quintile lags by 14.5, 7.3 and 5.1 percent, the middle is near zero, and the owned quintile leads by 17.5, 6.7 and 8.4 percent.">
  <figcaption>Quintiles of the signal before the cube, next-day return relative to members, annualized. A line in every period, and the test period's spread is as wide as validation's.</figcaption>
</figure>

It sorts monotonically in all three periods, and the spread between the top
and bottom quintile out of sample, 13.5% a year, is as wide as in
validation, 14.0%.

### What the book holds

| | inspection | validation | test |
|---|---:|---:|---:|
| names long, on an average day | 545 | 768 | 627 |
| names short, on an average day | 674 | 924 | 1,429 |
| effective number of names, 1 / Σw² | 98 | 101 | 98 |
| share of gross in the ten largest positions | 26% | 26% | 26% |
| days with a name at the 5% cap | 61% | 69% | 85% |
| holding period, days, from turnover | 7 | 8 | 8 |
| beta to SPY | 0.01 | 0.04 | −0.03 |
| return on days the market rose, per year | +39% | +14% | +2% |
| return on days the market fell, per year | +29% | +11% | +27% |

The cap binds on most days, which is the fitness score at work: gross is
fixed, so return comes from concentration, and the cap is what stops it.
The beta is zero without any hedge in the expression. Out of sample, almost
all of the return came on days the market fell.

### The expression as qex sees it

<figure class="diagram" id="signal-dag">
  <img src="signal-dag.svg" alt="A directed graph of 32 nodes. Inputs in green: field member, returns(1), returns(21), the constants 1 and 10, and ts_beta with a 504-day window. The member market, a demeaned product of returns and membership, feeds two ts_std nodes, a 252-day ts_sum and the beta. A where node chooses between two clipped versions of ten times the market's year. The residual return is summed over 231 days, delayed 21, sector-demeaned, multiplied by the switch and decayed over 10 days; the sector-demeaned 21-day return is subtracted; the result is cubed and decayed over 3 days at the top.">
  <figcaption>The final book as qex parses it. Thirty-two nodes, six inputs, one output; the market series is computed once and used four times.</figcaption>
</figure>

## References

- Asness, C. S., Moskowitz, T. J. and Pedersen, L. H. "Value and Momentum Everywhere." *Journal of Finance* 68(3), 2013.
- Bailey, D. H. and López de Prado, M. "The Deflated Sharpe Ratio." *Journal of Portfolio Management* 40(5), 2014.
- Barroso, P. and Santa-Clara, P. "Momentum Has Its Moments." *Journal of Financial Economics* 116(1), 2015.
- Blitz, D., Huij, J. and Martens, M. "Residual Momentum." *Journal of Empirical Finance* 18(3), 2011.
- Da, Z., Gurun, U. G. and Warachka, M. "Frog in the Pan: Continuous Information and Momentum." *Review of Financial Studies* 27(7), 2014.
- Daniel, K. and Moskowitz, T. J. "Momentum Crashes." *Journal of Financial Economics* 122(2), 2016.
- George, T. J. and Hwang, C.-Y. "The 52-Week High and Momentum Investing." *Journal of Finance* 59(5), 2004.
- Grinblatt, M. and Han, B. "Prospect Theory, Mental Accounting, and Momentum." *Journal of Financial Economics* 78(2), 2005.
- Grundy, B. D. and Martin, J. S. "Understanding the Nature of the Risks and the Source of the Rewards to Momentum Investing." *Review of Financial Studies* 14(1), 2001.
- Hong, H. and Stein, J. C. "A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets." *Journal of Finance* 54(6), 1999.
- Jegadeesh, N. "Evidence of Predictable Behavior of Security Returns." *Journal of Finance* 45(3), 1990.
- Jegadeesh, N. and Titman, S. "Returns to Buying Winners and Selling Losers." *Journal of Finance* 48(1), 1993.
- Moskowitz, T. J. and Grinblatt, M. "Do Industries Explain Momentum?" *Journal of Finance* 54(4), 1999.
- Nagel, S. "Evaporating Liquidity." *Review of Financial Studies* 25(7), 2012.
- Novy-Marx, R. "Is Momentum Really Momentum?" *Journal of Financial Economics* 103(3), 2012.
- Tulchinsky, I. et al. *Finding Alphas: A Quantitative Approach to Building Trading Strategies.* Wiley, 2015; 2nd ed. 2019.
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch).

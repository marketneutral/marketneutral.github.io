---
title: "autoresearch: sparks of an AI scientist"
date: 2026-10-22
tag: ESSAY
description: Karpathy's autoresearch hands the "what should I try next" step of science to a language model. It works on any problem with a score, and it is the start of a new way to do research. Finance should be excited, and careful.
---

In March 2026 Andrej Karpathy released
[`autoresearch`](https://github.com/karpathy/autoresearch), a small repository
in which a language model tries to improve a training script on its own. It
edits the code, runs a five-minute experiment, checks the score, keeps the change
if the score improved, and starts again. Left alone overnight, it runs about a
hundred experiments.

The training script is incidental. What autoresearch shows is that one step of
the scientific method, deciding what to try next, can now be handed to a model,
and that this works on any problem where you can write down a number that means
"better." I think this is the beginning of a new way to do research. This post
explains why it works, how the loop is built, and how to set one up on your own
problem.

## Science is a loop

<figure class="diagram" id="science">
  <img src="scientific-method.svg" alt="A loop: observation, question, hypothesis, prediction, experiment, result, and a decision on whether the result is consistent with the prediction; yes leads to theory and back to hypothesis, no sends you back to revise it.">
  <figcaption>The scientific method.</figcaption>
</figure>

You observe something, propose an explanation, make a prediction, run an
experiment, and keep or revise the explanation depending on what you see. Then
you go around again.

Of these steps, the proposal has always been the slow one. Running an experiment
can be automated, but deciding which experiment is worth running has needed a
person who knows the field. Because experiments were expensive, scientists spent
most of their effort choosing carefully and ran relatively few.

## When there is a slope

There is one kind of problem where computers have long done the proposing
themselves. If the thing you are adjusting is a list of numbers, and the score
changes smoothly as you adjust them, then the score has a slope, and the slope
tells you which way to go. That is gradient descent. It is the reason machine
learning works at all: a model with billions of parameters gets trained by
taking small steps downhill, over and over.

<figure class="wide" id="descent">
  <img src="gradient-descent.svg" alt="Left: filled contours of a cost surface with a gradient-descent path from a start point into the minimum. Right: cost falling on a log scale over 45 iterations.">
</figure>

The left panel is a score surface seen from above, with the path gradient
descent takes to the bottom. The right panel is the score falling at each step.
Nobody has to think about where to go next.

## "There is no slope."

<figure class="wide" id="spoon" style="width: min(480px, calc(100vw - 32px));">
  <img src="neo-spoon.webp" alt="Neo in The Matrix, holding a spoon.">
  <figcaption>Neo (Keanu Reeves) in <em>The Matrix</em> (1999). Still: Warner Bros., via Looper.</figcaption>
</figure>

Most of science does not look like that. A hypothesis is usually a protocol, a
piece of analysis code, a set of features, a molecule. You cannot nudge a
protocol a little bit in some direction, so there is no slope to follow. Even
Karpathy's training script is like this. Some of what the agent changes are
numbers, like the learning rate or the batch size. Many are whole-number or
either-or choices, like the depth of the network or the attention pattern, and
some are rewritten blocks of code. And every score comes from a complete
training run, so there is no slope to compute even for the numbers.

Without a slope, the options used to be poor. You could try things at random,
try a grid of settings, or mutate candidates and keep the best. These methods
know nothing about the problem, so they need an enormous number of tries. Or a
person could propose the next attempt, which is informed but slow.

A language model is a third option. It has read a large share of the world's
code, papers and lab notes, so its guesses are informed. It knows that a learning
rate of 0.1 will probably blow up a training run. It has a sense of what a
sensible next experiment looks like even in fields it has only read about. And it
can make a new guess every few minutes, all night.

<figure class="wide" id="race">
  <img src="informed-vs-random.svg" alt="Best score so far against the number of experiments, for random guesses and informed guesses. The informed search starts lower than the random search reaches after sixty experiments, and keeps improving.">
  <figcaption>A toy simulation: the best score found so far, median over many searches, with the middle half shaded.</figcaption>
</figure>

The figure is a toy simulation of that difference. Two searches look for the
best combination of six settings. One guesses at random. The other guesses
around a starting point that is close to right but not exact, the way a model
that has read about similar problems would. The informed search starts out
better than the random one ends up after sixty tries. When each try costs five
minutes, or five hours, that gap decides whether a search is practical.

DeepMind's FunSearch and AlphaEvolve had already shown that a model proposing
programs against an automatic test can find new results, but those systems ran
on large internal infrastructure. Autoresearch is a few files, one GPU and git,
which puts the same idea within reach of anyone who has a problem and a score.

## How autoresearch works

Three files matter.

- `train.py` is the only file the agent may edit. It holds the model, the
  optimizer and the training loop.
- `prepare.py` holds the data and the test. The data is split into a training
  set and a held-out validation set that the model never trains on. After
  training, the test measures the model's loss on the validation set, in bits
  per byte. That number is `val_bpb`, and lower is better. The agent is not
  allowed to touch this file.
- `program.md` holds the instructions, written by a person, that tell the agent
  how to run the loop.

The agent reads the code, decides on a change, edits `train.py` and commits. It
trains the model for exactly five minutes, then scores it on the validation
set. If the score beats the best so far, the commit stays. If not, git resets to
the previous best. Either way the agent adds a line to a log describing what it
tried and what happened, and then it starts again.

<figure class="diagram" id="loop">
  <img src="autoresearch-loop.svg" alt="The loop laid out like the scientific method: program.md, look at the current code, propose a change (the model), edit train.py and commit, train for five minutes, score on the held-out validation set, then a decision: if better than the best so far keep it and go to the next idea, otherwise undo it and propose again.">
  <figcaption>The autoresearch loop. Same shape as the scientific method, with the hypothesis step handed to a model. Every attempt is also written to a log, <code>results.tsv</code>, which you read in the morning.</figcaption>
</figure>

Three design choices make it work. Every run gets the same five minutes, so a
big architectural change and a small change to a constant are judged on equal
terms. The test is fixed and out of the agent's reach, so it cannot raise its
score by changing how the score is computed. And git keeps the best version so
far safe, so a bad idea costs one reset.

<figure class="wide" id="progress">
  <img src="autoresearch-progress.png" alt="Validation bits per byte over 83 experiments. Grey dots are discarded experiments, green dots are the 15 kept ones, each labelled with the change, and a green staircase shows the best score so far falling from about 0.998 to about 0.977.">
  <figcaption>One overnight run. Chart: Andrej Karpathy, <a href="https://github.com/karpathy/autoresearch">karpathy/autoresearch</a> (MIT).</figcaption>
</figure>

Here is one overnight run, from the repository itself. Each grey dot is an
experiment the agent threw away. Each green dot is one it kept, labelled with
what it changed, and the staircase is the best score so far. Over 83 experiments
it kept 14 changes on top of the starting point and took `val_bpb` from about
0.998 to 0.977. The first big
win was halving the batch size, so that more training steps fit in the five
minutes. The rest is the patient tuning a researcher does on a good day: a
longer warmup, a different attention window, a larger RoPE base frequency. None
of it needed a person in the room.

## It works on anything with a score

Nothing in the loop is specific to neural networks. It needs three things:
something the agent can edit, a test that turns it into a number, and a trial
short enough to run many times. Here is what that looks like in other places.

| what the agent edits | how it is scored | one trial |
|---|---|---|
| a training script | validation loss | five minutes on a GPU |
| a template engine | speed and memory, with all tests passing | the benchmark suite |
| features for a materials model | prediction error on held-out compounds | one model fit |
| a candidate drug molecule | a docking score | one calculation |
| a trading signal | out-of-sample returns after costs | one backtest |
| a prompt or a set of instructions | accuracy on held-out examples | a batch of model calls |

Some of these have already been done. Tobi Lütke ran the loop on
[Liquid](https://github.com/Shopify/liquid/pull/2056), the template language he
wrote for Shopify twenty years ago. About 120 experiments produced 93 kept
commits, which together cut parse and render time by 53% and object
allocations by 61%, with all 974 tests still passing. Cobelli and Sanvito used it in
materials science, letting an agent design the input features for models that
predict band gaps and Curie temperatures. The agent's features beat the standard
hand-built ones, and chemists could read and make sense of them. Anthropic's
`skill-creator` runs the same loop on plain text: it rewrites a skill's
description based on the queries it gets wrong, and picks the version that does
best on queries it held back.

The common thread is that the agent does not need to understand the domain
deeply. It needs to make reasonable guesses, and the test does the rest.

## How to try it on your own problem

Start with a problem you already care about, where a number can tell you
whether one attempt is better than another. Then:

1. **Choose what the agent may edit.** Ideally a single file. The data, the test
   and everything else stay outside it. Keep it small enough that you can read
   every change the agent makes.
2. **Write the test first.** It takes the edited file and returns one number,
   scored on a validation set the agent cannot see into or change. Run it
   several times on the same file and see how much the number moves on its own.
   That spread is your noise, and an improvement smaller than it doesn't count.
   Also set aside a separate test set that the loop never touches. You will use
   it once, at the end.
3. **Give every trial the same budget.** A fixed time limit, enforced by the
   script that runs the trial rather than by the agent, keeps comparisons fair.
   Keep it short. Two to five minutes gets you a hundred trials a night.
4. **Let git hold the search.** One commit per attempt. Keep it if the score
   beats the current best by more than the noise, and reset it otherwise. The
   branch is always the best version so far.
5. **Write the instructions.** Put the rules in a short file, start a coding
   agent in that directory, and tell it to read the file and begin.

The instructions can be this short:

```markdown
Artifact: pipeline.py — the only file you may edit
Frozen:   eval.py, data/ — do not modify, do not install packages
Hidden:   test/ — never read; the human uses it once at the end
Trial:    python run.py, hard cap 120 s
Metric:   prints "score: <float>", lower is better
Loop:     edit, commit, run, read the score, keep if better else reset
Log:      append commit, score, status, description to results.tsv
Rules:    never stop, never ask, simplest change that improves wins
```

Then go to bed, and read the log in the morning.

## What can go wrong

The loop optimizes exactly the number you give it, and most problems come from
that.

Often the quick score stands in for something slower that you actually care
about. A docking score is cheap, but what matters is whether the molecule binds
in a real assay, which takes weeks. A backtest is cheap, but what matters is how
the strategy does in the market. Run long enough, the loop will find candidates
that score well and fail in reality, because the gap between the two is the
easiest place to find improvements. Treat what it finds as strong hypotheses to
check in the lab or on unseen data.

Noise is the second problem. If the score jumps around by as much as the
improvement you are hoping for, "keep it if the score went down" will keep lucky
runs. Measuring the noise first, and only keeping improvements bigger than it,
is the fix.

The model's knowledge also cuts both ways. Its guesses are sensible, which is
why it beats random search, but it rarely tries anything strange. If it believes
something is necessary it will seldom try removing it. Running several agents,
or explicitly asking for bolder changes, helps.

And it won't work at all if you can't reduce "better" to a single number, or if
each trial takes days.

## What the scientist does now

The loop does the searching. It does not decide what is worth searching for. A
person still chooses the question, writes the test, and decides what the agent
may touch and how much noise to tolerate. In autoresearch all of that lives in
`program.md`. The person no longer edits the training script; they edit the
instructions for the agent that does.

This is close to how a research lab already works. The principal investigator
picks the problem, sets the standard of evidence, and reads the lab notebook.
Students propose experiments, run them, and write down what happened. The agent
is a student that never gets tired and has no favourite idea. Unlike a real
student, it doesn't get wiser over the years or ask whether the problem is the
right one. That part is still yours.

What changes is the number of experiments. Someone who used to run ten careful
experiments on an idea can now run a thousand overnight, and spend their own
time on picking the question and building a test that measures it honestly.
Any field with a number that means "better" can be searched this way, and most
of them haven't started.

## What this means for finance

Quantitative finance may be the most natural home for this loop. A lot of quant
research already is the loop, run by hand: think of a signal, code it, backtest
it, keep it or drop it, repeat. The artifact is code, the test is a backtest,
and a trial takes seconds. An agent could run thousands of these a night. That
promise is real. Finance is also where the loop is most dangerous, for three
reasons.

**The evaluation is everything.** The loop optimizes whatever the backtest
rewards, including its mistakes. If the data has lookahead, survivorship bias,
or costs that are too low, the agent will find the flaw, because exploiting a
broken test is usually easier than finding real alpha. So the backtest has to
come first and be built with care: point-in-time data, realistic trading costs
and borrow, capacity limits. Then it gets frozen and kept where the agent cannot
edit it.

**Every experiment is a test, and you are running thousands.** This is the
multiple comparisons problem, and finance has learned it the hard way. Try
enough strategies with no real edge and the best of them will look good by luck
alone. A Sharpe ratio estimated from ten years of data has a standard error of
about 0.3. Among 100 independent strategies with no edge at all, the best will
typically show a Sharpe around 0.8; among 1,000, around 1.0. That is why Harvey, Liu and
Zhu argued that a new factor should clear a t-statistic of 3 rather than 2, and
why Bailey and López de Prado's deflated Sharpe ratio adjusts for the number of
trials. The loop at least does the counting for you, since every trial is a line
in the log. Use that count when you judge the winner.

**The loop can overfit the validation set even though it never trains on it.**
It is tempting to think a held-out period is safe because no model is fit to
it. But every keep-or-reset decision looks at that score, and a thousand
decisions leak a lot of information. After enough rounds the validation set has
effectively become training data. Autoresearch has exactly this structure: one
validation set scores every attempt, all night, any improvement however small is
kept, and there is no separate test set. Karpathy's own run shows the result in
miniature. The last change it kept was a new random seed, 42 to 137. A different
seed is not a better model. It is a luckier draw of the training noise, as
judged by the validation set. Markets have far more noise and far less data than
a language model's validation set, so the same thing happens at a much larger
scale. The fix is a test period the loop never sees, used once at the end,
followed by paper trading before any capital goes in.

None of this is a reason to stay away. It is a reason to put the human effort in
the right place: a backtest that cannot be fooled, an honest count of how many
things were tried, and a test set the loop has never touched. Get those right
and an agent can explore more ideas in a week than a team does in a year. Get
them wrong and it will find a thousand ways to fool you, faster than you ever
could on your own.

---

**References**

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch), including `program.md`.
- Shopify/liquid [#2056](https://github.com/Shopify/liquid/pull/2056), the Liquid result, with the benchmark table and methodology.
- Cobelli and Sanvito, [Agentic Design of Compositional Descriptors via Autoresearch for Materials Science Applications](https://arxiv.org/abs/2605.14671), *Digital Discovery*, 2026.
- Anthropic, [`skill-creator`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md), including `scripts/run_loop`.
- Harvey, Liu, and Zhu, […and the Cross-Section of Expected Returns](https://academic.oup.com/rfs/article/29/1/5/1843824), *Review of Financial Studies*, 2016.
- Bailey and López de Prado, [The Deflated Sharpe Ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551), *Journal of Portfolio Management*, 2014.
- Romera-Paredes et al., [Mathematical discoveries from program search with large language models](https://www.nature.com/articles/s41586-023-06924-6), *Nature*, 2024.
- [AlphaEvolve](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/), DeepMind, 2025.

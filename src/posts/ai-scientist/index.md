---
title: "autoresearch: There Is No Slope"
date: 2026-10-22
tag: ESSAY
description: Karpathy's autoresearch is not about training scripts. It is the scientific method with the proposal step given to a model, for any problem that has a loss function.
---

The scientific method is a loop. You observe something, ask why, propose a
mechanism, derive a prediction, test it, and keep or discard the mechanism. The
names change by field. The structure does not.

<figure class="diagram" id="science">
  <img src="scientific-method.svg" alt="A loop: observation, question, hypothesis, prediction, experiment, result, and a decision on whether the result is consistent with the prediction; yes leads to theory and back to hypothesis, no sends you back to revise it.">
  <figcaption>The scientific method.</figcaption>
</figure>

The hypothesis and the experiment are the two steps that matter here. A
hypothesis with free parameters is a point in a space, and a prediction is what
that point implies about a measurement you have not made. The experiment
returns the measurement, usually with error. The decision at the bottom updates
what you are willing to believe.

Written as an optimization problem, we choose $\theta$ from a space $\Theta$ to
minimize an objective $J(\theta)$, where $J$ is whatever the experiment
reports. Two things vary across fields and determine which algorithms are
available: the cost of an experiment, and whether $J$ is differentiable.

For most of the history of science the binding constraint was the proposal.
Experiments were expensive, so thinking of the right one mattered more than
trying many, and the thinking was done by a person who had read the field. In
March 2026 Andrej Karpathy released
[`autoresearch`](https://github.com/karpathy/autoresearch), which gives the
proposal step to a language model and lets the trials run overnight. The repository
trains small GPT models, but the training is incidental. What it demonstrates is
a modality: any problem where you can write down a number that means "better"
can be run as a loop, with a model proposing each next attempt.

## A function with a slope

Start with the case everyone learns first: two parameters, one number out.

$$
J(\theta_1,\theta_2) = \tfrac12(\theta_1 - 0.6)^2 + 4(\theta_2 + 0.4)^2
+ 0.35\sin(3\theta_1)\sin(3\theta_2)
$$

The first two terms form an elongated bowl. The sine terms add ripples, so the
surface looks like a real loss function near the start.

<figure class="wide" id="descent">
  <img src="gradient-descent.svg" alt="Left: filled contours of a cost surface with a gradient-descent path from a start point into the minimum. Right: cost falling on a log scale over 45 iterations.">
</figure>

Gradient descent is one update rule:

$$
\theta_{k+1} = \theta_k - \eta \nabla J(\theta_k).
$$

The left panel is the surface seen from above. The right panel is what the
method sees: one scalar per step, and a slope. It works because of local
linearity. Close enough to a differentiable surface, the downhill direction is
the negative gradient. On a convex problem with a reasonable step size that
gives a convergence guarantee; here 45 steps with $\eta = 0.09$ is enough.

The assumptions are worth listing, because most of science fails them: a vector
space, so that a step has a meaning; a derivative; cheap evaluations; and a
function that does not move while you optimize it.

## "There is no slope."

<figure class="wide" id="spoon" style="width: min(480px, calc(100vw - 32px));">
  <img src="neo-spoon.webp" alt="Neo in The Matrix, holding a spoon.">
  <figcaption>Neo (Keanu Reeves) in <em>The Matrix</em> (1999). Still: Warner Bros., via Looper.</figcaption>
</figure>

A hypothesis is rarely two real numbers. It is a protocol, a piece of analysis
code, a simulation, a set of instrument settings. The space of these things has
no gradient, because it is not a vector space at all: the distance between two
protocols is not a number you can differentiate. The objective is whatever the
experiment measures, and it is usually noisy and expensive.

Karpathy's instance is a training script. `train.py` holds an integer depth, a
choice of optimizer, a window pattern, a batch size that has to stay a power of
two, and blocks of Python. The metric is `val_bpb`, produced by a five-minute
run, and it moves by a couple of thousandths between identical runs:

$$
\min_{\theta \in \Theta} J(\theta), \qquad
\Theta = \{\text{programs that run and finish in five minutes}\}.
$$

$\Theta$ has no metric in which a small change means a small change in
behaviour, and no derivative. $J$ is a subprocess on a GPU that returns a
number, and a stack trace on a bad day.

Without a gradient, the alternatives are all forms of sampling. Grid search
needs a low dimension. Random search needs volume and assumes nothing else.
Evolution strategies need a parameterization to sample around. Bayesian
optimization fits a surrogate and lets an acquisition function choose the next
point, which is hard when the candidates are programs rather than vectors. In
every case the proposal is mechanical, and that is the part a language model
changes.

### A Bayesian reading

Bayes gives the update rule for belief after data:

$$
p(\theta \mid \mathcal{D}) \propto p(\mathcal{D} \mid \theta) \, p(\theta).
$$

The prior is what the searcher believes before running anything. The likelihood
is how well a hypothesis explains the measurement. The posterior is what
survives.

The familiar algorithms are special cases. Gradient descent takes its proposal
from the gradient and brings almost no prior; random search has a flat prior and
lets the likelihood do the work; Bayesian optimization makes both explicit.

Autoresearch keeps the frame and changes the proposal. The next artifact is
drawn by a model trained on a large fraction of the world's code, papers and bug
reports. That is a concentrated prior, not over two parameters but over the kind
of things that can be edited and measured. It has seen enough training scripts
to expect that a learning rate of $0.1$ explodes, and enough protocol documents
and analysis code to have a view about what a plausible next experiment looks
like in fields it has only read about.

<figure class="wide" id="bayes">
  <img src="bayes-prior.svg" alt="Left: a true objective curve with a narrow informed prior and a flat uninformed one. Right: posteriors after one, four and ten experiments with the informed prior, against ten experiments under a flat prior.">
</figure>

The figure is a toy: one parameter, ten draws, Gaussian noise, a prior chosen by
hand. Read it as a mechanism rather than a measurement. With a concentrated
prior, four experiments land closer to the truth than ten from a flat prior,
because the proposals start in the right neighbourhood. At five minutes per
evaluation, that difference is what makes the loop worth running.

The same structure creates the failure modes.

A strong prior narrows exploration. A model that believes normalisation is
necessary will rarely propose deleting it, and the experiments it runs will
confirm the belief, because beliefs select experiments. Whether you call that
confirmation bias or a narrow proposal distribution, the effect on the search is
the same. Temperature and multiple agents are the levers.

Noise turns acceptance into a biased filter. When the likelihood is as wide as
the effect you are chasing, "keep if lower" selects luck, and the accepted set
improves on paper without improving in fact.

The target moves as the branch advances. Each accepted commit changes the
baseline, so a change that helped at one setting may hurt at another. The object
is a sequential posterior, not a fixed distribution sampled once.

The last failure is the metric itself. A number produced by a five-minute run is
not the same thing as a better model, and a sharp posterior around a proxy is
only as good as the proxy. That is why the evaluator has to be frozen and out of
the searcher's reach.

## The loop

Strip the repository down and the loop needs four things: an editable artifact, a
frozen evaluator, a cheap repeatable trial, and a version-control boundary.

In Karpathy's repository the artifact is `train.py`, a single file so the diffs
stay small. The evaluator is `evaluate_bpb` in `prepare.py`, which the agent may
neither modify nor replace with a package. The trial is a five-minute run, which
is what makes an architecture change comparable with a learning-rate tweak, and
what fixes the cost at roughly twelve experiments an hour. The boundary is git:
acceptance is a commit, rejection is a reset, and the current best code and the
current best score are the same object.

The loop is correspondingly short. Read the current branch and the in-scope
files. Edit `train.py`. Commit. Run `uv run train.py` and grep out `val_bpb`.
Append a row to `results.tsv` with the commit, the metric, peak memory and a
one-line description. If the metric improved, keep the commit; otherwise reset.
The agent redirects all output to `run.log` instead of letting it into the
context, and reads `tail -n 50 run.log` only when a run crashes.

<figure class="diagram" id="loop">
  <img src="autoresearch-loop.svg" alt="Two lanes. The human writes program.md and later reads results.tsv. The agent reads the files, proposes a change, edits train.py, commits, runs a fixed five-minute training job, reads val_bpb, and either advances the branch or resets it, then logs the result and repeats.">
  <figcaption>The autoresearch loop.</figcaption>
</figure>

The record has three parts, and only two of them are durable. During a run the
agent remembers its own attempts, because it is one long session: the edit, the
commit, the grep line and the stack trace all pass through its context, so it
knows what failed without consulting anything. That memory is finite. A ten-hour
run compacts its context several times over, and what survives compaction is the
shape of a failure rather than its detail. The branch then holds what worked,
and the log holds everything, including what was thrown away. The log is
untracked: the agent appends the rows, the human reads them in the morning.
`program.md` asks for the write, not the read, which puts a night of experiments
in front of a person.

In the first reported session the numbers went from 0.9979 to 0.9697 in
`val_bpb`, over 125 experiments and about ten and a half hours. The largest
single win was halving the batch size so that more steps fit in the five
minutes.

## When the artifact is not a training script

`train.py` is the exhibit, not the subject. Everything the loop needs is an
editable artifact, an evaluator, and a cheap trial, and none of the three has to
be code.

| artifact edited | evaluator | trial |
|---|---|---|
| a training script | validation bits per byte | five minutes on one GPU |
| a set of materials descriptors | prediction error on held-out compounds | one random-forest fit |
| a molecule or a synthesis route | docking score, then an assay | hours in silico, weeks in the lab |
| a template engine | render time and allocations | the engine's test suite |

The Liquid case is the clearest of these. Tobi Lütke ran a variant of the loop
on [Liquid](https://github.com/Shopify/liquid/pull/2056), the template language
he wrote for Shopify twenty years ago: 93 commits from about 120 experiments,
combined parse and render time down 53%, object allocations down 61%, and all
974 unit tests passing.

Materials science has a published version. Cobelli and Sanvito let a coding
agent design the *input features* for a property-prediction model, which is a
task one step further upstream than hyperparameters: the artifact is a set of
compositional descriptors, the evaluator is prediction error on held-out
compounds, and the trial is a random-forest fit. The agent was restricted to
information derivable from chemical formulas. On band gaps in inorganic
materials and Curie temperatures in ferromagnetic compounds it beat the
fractional-composition and Magpie baselines, and the descriptors it wrote were
chemically interpretable rather than opaque. The loop was not tuning a model.
It was designing the features the model is given.

Drug design is the same shape with a sharper problem. The artifact is a molecule
or a synthesis route, the evaluator is a docking score or a predicted binding
affinity, and the trial is cheap because it is a calculation. But a docking
score is not a drug. The measurement you actually care about is an assay, which
costs weeks and money and cannot run a hundred times overnight. So the loop
runs on a surrogate, and the surrogate is where it fails: it will find molecules
that score well and do not bind. The honest version keeps the cheap evaluator
for triage and treats every promising candidate as a hypothesis for the lab, not
as a result.

Trading has the same trap in a different currency. The artifact is a signal, the
evaluator is out-of-sample performance on a frozen panel, and the trial is a
backtest, which is cheap enough to run thousands of. The loop will find the
backtest, not the market. One public write-up reports forty-five
experiments against a ten-year equity backtest, scoring a composite of return,
Sharpe, drawdown, profit factor and alpha. That is a reasonable first attempt
and a warning: a weighted sum of five metrics is itself a loss function, and the
search will optimise the weights it can reach. The defences are the ones the
metric cannot fake. Freeze the panel before you start. Hold out a period the
agent never sees. Charge for turnover and borrow. Then replicate the winner on
data it was never allowed to touch.

The pattern across all of these is the same, and it is not about the domain.
Where the cheap evaluator is a proxy for an expensive one, the gap between them
is where the search goes. The loop is only as good as the honesty of that gap.

## The general approach

If you have a problem with a measurable outcome, the setup is five decisions,
and none of them are about language models.

1. **Draw the artifact boundary.** One file, or one small directory, that the
   agent may edit. Everything that defines success lives outside it: data,
   evaluator, harness. If the diff cannot be read in five minutes, the boundary
   is too wide.
2. **Write the evaluator first.** A function from artifact to a single number,
   deterministic given a seed, fast enough to run a hundred times in a night.
   Then measure its noise: run the same artifact five times and record the
   spread. That spread sets the threshold for keeping a change.
3. **Fix the trial.** The same wall-clock cap for every run, enforced by the
   runner rather than by the agent. That is what makes a structural change
   comparable with a change to a constant.
4. **Choose the acceptance rule.** Keep the commit if the score improves by more
   than the noise; otherwise reset. One commit per attempt, so the branch is the
   state of the search.
5. **Write the instructions.** Scope, metric, forbidden edits, log format, what
   counts as a crash, and the simplicity rule: equal score with less code is a
   win.

The instruction file is the whole interface, and it can be short:

```markdown
Artifact: pipeline.py — the only file you may edit
Frozen:   eval.py, data/ — do not modify, do not install packages
Trial:    python run.py, hard cap 120 s
Metric:   prints "score: <float>", lower is better
Loop:     edit, commit, run, grep the score, keep if lower else reset
Log:      append commit, score, status, description to results.tsv
Rules:    never stop, never ask, simplest change that improves wins
```

Suppose the artifact is a data pipeline and the evaluator is wall-clock runtime
on a fixed input, with correctness checked against stored output. Your knobs are
whatever the pipeline exposes; seconds take the place of `val_bpb`, and five
minutes becomes two. Suppose instead it is a backtest: the artifact is the signal code,
the evaluator is out-of-sample Sharpe net of costs on a frozen panel, and the
trial is one backtest. The loop does not know the difference.

The most direct case is instructions. Anthropic's `skill-creator` ships an
optimizer that treats a skill's description — the text that decides whether the
skill fires at all — as the artifact. It generates twenty trigger queries,
splits them 60/40 into train and held-out, runs each query three times to get a
stable trigger rate, asks the model to rewrite the description from the
failures, and repeats for up to five iterations. The winner is chosen on the
held-out score, not the training score. That is the pattern in miniature: three
runs per query for noise, a holdout against overfitting, and a model proposing
the edit. The thing being improved is the instruction that tells the model when
to use the skill in the first place.

The same skill runs a slower loop over the instructions themselves, comparing
runs with and without the skill and putting the human in the accept/reject
slot. That is an eval loop, not this loop, and the difference is worth knowing:
once the decision returns to a person, the score stops being the thing that
decides.

It fails in three places, and they are worth checking before you start. There is
no scalar, because "better" needs a committee. The trials are too expensive, so
you get ten a night instead of a hundred. The artifact is too large to review,
so you cannot trust the branch.

## What the human is still for

The loop automates search. It does not choose what to search over.

Someone decides which number means better, what counts as an acceptable trial,
how small the editable artifact has to be, and that the evaluator is off limits.
Those are judgments, and in Karpathy's setup they sit in `program.md` where a
person can argue with them. The human does not tune the artifact. The human
tunes the instructions that define the loop, which he describes as a super
lightweight skill.

His own account is less hands-off than the framing suggests. Asked about making
the loop fully autonomous, he said he still prefers interactive sessions:
watching in `tmux`, babysitting, contributing ideas. The overnight run is one
mode of use, not the only one.

The method has not changed. What changed is who proposes the next experiment,
and how many of them you can afford. A thousand attempts is a different kind of
science from ten, and the loss function decides which one you are doing.

---

**References**

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch), including `program.md`.
- Shopify/liquid [#2056](https://github.com/Shopify/liquid/pull/2056), the Liquid result, with the benchmark table and methodology.
- Anthropic, [`skill-creator`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md), including `scripts/run_loop`.
- Cobelli and Sanvito, [Agentic Design of Compositional Descriptors via Autoresearch for Materials Science Applications](https://arxiv.org/abs/2605.14671), *Digital Discovery*, 2026.
- Romera-Paredes et al., [Mathematical discoveries from program search with large language models](https://www.nature.com/articles/s41586-023-06924-6), *Nature*, 2024.
- [AlphaEvolve](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/), DeepMind, 2025.
- Snoek, Larochelle, and Adams, [Practical Bayesian Optimization of Machine Learning Algorithms](https://arxiv.org/abs/1206.2944), 2012.

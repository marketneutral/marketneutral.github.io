---
title: "autoresearch: There Is No Slope"
date: 2026-10-22
tag: ESSAY
description: Karpathy's autoresearch is not really about training scripts. It is the scientific method with the proposal step handed to a model, and it works on any problem that has a loss function.
---

The scientific method is a loop. You observe something, ask why, propose a
mechanism, derive a prediction, test it, and keep or discard the mechanism. The
names change from field to field; the structure does not.

<figure class="diagram" id="science">
  <img src="scientific-method.svg" alt="A loop: observation, question, hypothesis, prediction, experiment, result, and a decision on whether the result is consistent with the prediction; yes leads to theory and back to hypothesis, no sends you back to revise it.">
  <figcaption>The scientific method.</figcaption>
</figure>

Two steps carry the weight: the hypothesis and the experiment. A hypothesis
with free parameters is a point in a space, and its prediction is what that
point implies about a measurement you have not yet made. The experiment returns
the measurement, usually with error, and the decision at the bottom updates what
you are willing to believe.

Put as optimization, we choose $\theta$ from a space $\Theta$ to minimize an
objective $J(\theta)$, where $J$ is whatever the experiment reports. Two
properties decide which algorithms are available: what an experiment costs, and
whether $J$ has a derivative.

For most of the history of science the bottleneck was the proposal. Experiments
were expensive, so choosing the right one mattered more than running many, and
the choosing was done by someone who had read the field. In March 2026 Andrej
Karpathy released [`autoresearch`](https://github.com/karpathy/autoresearch),
which hands the proposal to a language model and runs the experiments
overnight. The repository trains small GPT models, but the training is
incidental. What it demonstrates is a way of working: any problem where you can
write down a number that means "better" can be run as a loop, with a model
proposing each next attempt.

## A function with a slope

Start with the case everyone learns first: two parameters in, one number out.

$$
J(\theta_1,\theta_2) = \tfrac12(\theta_1 - 0.6)^2 + 4(\theta_2 + 0.4)^2
+ 0.35\sin(3\theta_1)\sin(3\theta_2)
$$

The first two terms make an elongated bowl. The sine term adds ripples, so the
surface looks like a real loss.

<figure class="wide" id="descent">
  <img src="gradient-descent.svg" alt="Left: filled contours of a cost surface with a gradient-descent path from a start point into the minimum. Right: cost falling on a log scale over 45 iterations.">
</figure>

Gradient descent is a single update rule:

$$
\theta_{k+1} = \theta_k - \eta \nabla J(\theta_k).
$$

The left panel is the surface seen from above. The right panel is all the method
ever sees: one number per step, and a slope. It works because of local
linearity. Close enough to a differentiable surface, downhill is the negative
gradient. On a convex surface that comes with a convergence guarantee; this one
has ripples, but 45 steps with $\eta = 0.09$ still find the bottom.

The assumptions are worth stating, because most of science breaks them: a vector
space, so that a step means something; a derivative; cheap evaluations; and a
function that holds still while you optimize it.

## "There is no slope."

<figure class="wide" id="spoon" style="width: min(480px, calc(100vw - 32px));">
  <img src="neo-spoon.webp" alt="Neo in The Matrix, holding a spoon.">
  <figcaption>Neo (Keanu Reeves) in <em>The Matrix</em> (1999). Still: Warner Bros., via Looper.</figcaption>
</figure>

A real hypothesis is rarely two numbers. It is a protocol, a piece of analysis
code, a simulation, a set of instrument settings. None of these lives in a
vector space, so there is no gradient: the distance between two protocols is not
something you can differentiate. And the objective is whatever the experiment
measures, which is usually noisy and expensive.

Karpathy's instance is a training script. `train.py` holds an integer depth, a
choice of optimizer, a window pattern, a batch size that must stay a power of
two, and blocks of plain Python. The metric is `val_bpb` from a five-minute run,
and it wanders by a couple of thousandths between identical runs:

$$
\min_{\theta \in \Theta} J(\theta), \qquad
\Theta = \{\text{programs that run and finish in five minutes}\}.
$$

No metric on $\Theta$ makes a small edit mean a small change in behaviour, and
nothing in it has a derivative. $J$ is a subprocess on a GPU that returns a
number or, on a bad day, a stack trace.

Without a gradient, what remains is sampling. Grid search needs few dimensions.
Random search needs volume and assumes nothing else. Evolution strategies need a
parameterization to perturb. Bayesian optimization fits a surrogate and lets an
acquisition function pick the next point, which gets hard when the candidates
are programs rather than vectors. In every case the proposal is mechanical, and
that is the part a language model changes. FunSearch and AlphaEvolve showed it
at laboratory scale, with a model proposing programs against an automatic
evaluator. Autoresearch shows that it fits on one GPU, in a handful of files,
under git.

### A Bayesian reading

Bayes gives the rule for updating belief after data:

$$
p(\theta \mid \mathcal{D}) \propto p(\mathcal{D} \mid \theta) \, p(\theta).
$$

The prior is what the searcher believes before running anything, the likelihood
is how well a hypothesis explains the measurement, and the posterior is what
survives. The familiar algorithms are special cases. Gradient descent takes its
proposal from the gradient and brings almost no prior; random search has a flat
prior and lets the likelihood do the work; Bayesian optimization makes both
explicit.

Autoresearch keeps the frame and replaces the proposal. The next artifact is
drawn from a model trained on a large share of the world's code, papers and bug
reports. That is a concentrated prior, not over two parameters but over the
kinds of things that can be edited and measured. It has seen enough training
scripts to expect a learning rate of $0.1$ to blow up, and enough protocols and
analysis code to hold a view on what a sensible next experiment looks like in
fields it has only read about.

<figure class="wide" id="bayes">
  <img src="bayes-prior.svg" alt="Left: a true objective curve with a narrow informed prior and a flat uninformed one. Right: posteriors after one, four and ten experiments with the informed prior, against ten experiments under a flat prior.">
</figure>

The figure is a toy: one parameter, ten draws, Gaussian noise, a prior chosen by
hand. Read it as a mechanism, not a measurement. With a concentrated prior, four
experiments land closer to the truth than ten under a flat one, because the
proposals start in the right neighbourhood. At five minutes an evaluation, that
difference is what makes the loop worth running.

The same structure explains how it fails.

The prior narrows exploration. A model that believes normalisation is necessary
will rarely propose deleting it, and the experiments it does run will confirm the
belief, because beliefs choose experiments. Call it confirmation bias or a
narrow proposal distribution; the effect on the search is the same. Temperature
and multiple agents are the levers.

Noise biases acceptance. When the likelihood is as wide as the effect you are
chasing, "keep if lower" selects for luck, and the accepted set improves on
paper without improving in fact.

The target moves. Each accepted commit changes the baseline, so a change that
helped at one point can hurt at the next. The object is a sequential posterior,
not a fixed distribution sampled once.

And the metric is a proxy. A number from a five-minute run is not a better
model, and a sharp posterior around a proxy is only as good as the proxy. That
is why the evaluator has to be frozen and kept out of the searcher's reach.

## The loop

Strip the repository down and the loop needs four things: an editable artifact,
a frozen evaluator, a cheap repeatable trial, and a version-control boundary.

In Karpathy's repository the artifact is `train.py`, kept to a single file so the
diffs stay small. The evaluator is `evaluate_bpb` in `prepare.py`, which the
agent may neither modify nor route around with a new package. The trial is a
fixed five-minute run, which makes an architecture change comparable with a
learning-rate tweak and sets the pace at about twelve experiments an hour. The
boundary is git: acceptance is a commit, rejection is a reset, and the best code
and the best score are the same object.

The loop itself is short. Read the branch and the in-scope files. Edit
`train.py`. Commit. Run `uv run train.py` and grep out `val_bpb`. Append a row to
`results.tsv`: commit, metric, peak memory, a one-line description. If the metric
improved, keep the commit; otherwise reset. Training output goes to `run.log`
rather than into the agent's context, and the agent reads its last fifty lines
only when a run crashes.

<figure class="diagram" id="loop">
  <img src="autoresearch-loop.svg" alt="Two lanes. The human writes program.md and later reads results.tsv. The agent reads the files, proposes a change, edits train.py, commits, runs a fixed five-minute training job, reads val_bpb, and either advances the branch or resets it, then logs the result and repeats.">
  <figcaption>The autoresearch loop.</figcaption>
</figure>

Memory lives in three places. The first is the conversation itself. The agent
runs as one long session, so every edit, commit, grep line and stack trace
passes through its context, and it knows what failed without looking anything
up. That memory is finite: a ten-hour run compacts its context several times,
and what survives is the shape of a failure rather than its detail. The other
two are durable. The branch holds what worked. The log holds everything,
including what was thrown away. It is left untracked, and `program.md` asks the
agent to write it, not to read it back. It exists to put a night of experiments
in front of a person.

The first reported session took `val_bpb` from 0.9979 to 0.9697 over 125
experiments and about ten and a half hours. The largest single win was halving
the batch size, so that more steps fit in five minutes.

## Beyond the training script

`train.py` is the exhibit, not the subject. The loop needs an editable artifact,
an evaluator and a cheap trial, and none of the three has to be code.

| artifact edited | evaluator | trial |
|---|---|---|
| a training script | validation bits per byte | five minutes on one GPU |
| a template engine | render time and allocations | the engine's test suite |
| a set of materials descriptors | prediction error on held-out compounds | one random-forest fit |
| a molecule or a synthesis route | docking score, then an assay | hours in silico, weeks in the lab |
| a trading signal | out-of-sample performance on a frozen panel | one backtest |
| a skill description | held-out trigger rate | twenty queries, three runs each |

The template engine is the cleanest case. Tobi Lütke ran a variant of the loop
on [Liquid](https://github.com/Shopify/liquid/pull/2056), the template language
he wrote for Shopify twenty years ago. About 120 experiments produced 93
commits: combined parse and render time down 53%, object allocations down 61%,
and all 974 unit tests still passing.

Materials science has a published version that moves one step upstream of
hyperparameters. Cobelli and Sanvito pointed a coding agent at the *input
features* of a property-prediction model. The artifact is a set of compositional
descriptors, restricted to what can be derived from a chemical formula; the
evaluator is prediction error on held-out compounds; the trial is one
random-forest fit. On band gaps in inorganic materials and Curie temperatures in
ferromagnets, the agent's descriptors beat the fractional-composition and Magpie
baselines, and they were chemically interpretable rather than opaque. The loop
was not tuning a model. It was deciding what the model gets to see.

Drug design has the same shape and a sharper problem. The artifact is a molecule
or a synthesis route, the evaluator is a docking score or a predicted binding
affinity, and the trial is cheap because it is a calculation. But a docking score
is not a drug. The measurement that matters is an assay, which costs weeks and
money and cannot run a hundred times overnight. So the loop runs on a surrogate,
and the surrogate is where it breaks: it will find molecules that score well and
do not bind. Used well, the cheap evaluator is for triage, and every promising
candidate is a hypothesis for the lab, not a result.

Trading sets the same trap in a different currency. The trial is a backtest,
cheap enough to run by the thousand, and left alone the loop will find the
backtest, not the market. One public write-up ran forty-five experiments against
a ten-year equity backtest scored on a blend of return, Sharpe, drawdown, profit
factor and alpha. It is a reasonable first attempt and a warning: a weighted sum
of five metrics is itself a loss function, and the search will exploit whichever
weights it can reach. The defences are the ones the metric cannot fake. Freeze
the panel before you start. Hold out a period the agent never sees. Charge for
turnover and borrow. Then replicate the winner on data it was never allowed to
touch.

The most self-referential case is instructions. Anthropic's `skill-creator`
ships an optimizer whose artifact is a skill's description, the text that decides
whether the skill fires at all. It generates twenty trigger queries, splits them
60/40 into train and held-out, runs each query three times for a stable trigger
rate, has the model rewrite the description from the failures, and repeats for
up to five rounds, choosing the winner on the held-out score. That is the pattern
in miniature: repeated runs for noise, a holdout against overfitting, a model
proposing the edit. The same skill runs a slower loop over the skill's body,
comparing runs with and without it, but there a person sits in the accept/reject
slot. That makes it an eval loop rather than this one, and the difference
matters: once the decision goes back to a person, the score is no longer what
decides.

Across all of these the lesson has nothing to do with the domain. Where a cheap
evaluator stands in for an expensive one, the gap between them is where the
search goes, and the loop is only as good as the honesty of that gap.

## Setting one up

If you have a problem with a measurable outcome, the setup comes down to five
decisions, and none of them is about language models.

1. **Draw the artifact boundary.** One file, or one small directory, that the
   agent may edit. Everything that defines success lives outside it: data,
   evaluator, harness. If the diff cannot be read in five minutes, the boundary
   is too wide.
2. **Write the evaluator first.** A function from artifact to a single number,
   deterministic given a seed, fast enough to run a hundred times in a night.
   Then measure its noise: run the same artifact five times and record the
   spread. That spread sets the threshold for keeping a change.
3. **Fix the trial.** The same wall-clock cap for every run, enforced by the
   runner rather than the agent. That is what makes a structural change
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

Three things break it, and they are worth checking before you start: there is no
scalar, because "better" needs a committee; the trials are too expensive, so you
get ten a night instead of a hundred; or the artifact is too large to review, so
you cannot trust the branch.

## What the human is still for

The loop automates search. It does not choose what to search over.

Someone decides which number means better, what counts as a fair trial, how
small the editable artifact must be, and that the evaluator is off limits. Those
are judgments, and in Karpathy's setup they live in `program.md`, where a person
can argue with them. The human does not tune the artifact. The human tunes the
instructions that define the loop, which Karpathy describes as a super
lightweight skill.

His own practice is less hands-off than the framing suggests. Asked about making
the loop fully autonomous, he said he still prefers interactive sessions:
watching in `tmux`, babysitting, contributing ideas. The overnight run is one
way to use it, not the only one.

The division of labour is the one a lab already uses. The human is the principal
investigator: chooses the question, sets the standard of evidence, decides what
counts as a result, and reads the notebook in the morning. The agent is the
student: reads the protocol, proposes the next experiment, runs it, writes it
down, reports back.

The analogy has limits. A student improves over years and eventually argues
about the question. This one does not improve between runs, cannot reframe the
problem, and forgets whatever was not written down. What it has instead is
throughput without ego: a hundred attempts a night, none of them tired, none of
them attached to an idea.

So the principal investigator's job barely changes: decide what is worth
measuring, keep the measurement honest, read the notebook. The method has not
changed either. What changed is who proposes the next experiment, and how many
you can afford. A thousand attempts is a different kind of science from ten, and
the loss function decides which one you are doing.

---

**References**

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch), including `program.md`.
- Shopify/liquid [#2056](https://github.com/Shopify/liquid/pull/2056), the Liquid result, with the benchmark table and methodology.
- Anthropic, [`skill-creator`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md), including `scripts/run_loop`.
- Cobelli and Sanvito, [Agentic Design of Compositional Descriptors via Autoresearch for Materials Science Applications](https://arxiv.org/abs/2605.14671), *Digital Discovery*, 2026.
- Romera-Paredes et al., [Mathematical discoveries from program search with large language models](https://www.nature.com/articles/s41586-023-06924-6), *Nature*, 2024.
- [AlphaEvolve](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/), DeepMind, 2025.
- Snoek, Larochelle, and Adams, [Practical Bayesian Optimization of Machine Learning Algorithms](https://arxiv.org/abs/1206.2944), 2012.

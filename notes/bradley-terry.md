# Bradley–Terry, worked through


This is a companion to the post [Bootstrapping a superhuman buyside equity analyst](https://marketneutral.github.io/posts/bootstrapping-an-analyst/). The post turns a judge’s verdicts into a reward with a model called Bradley–Terry, and explains it with chess ratings. This note has the math, with every step worked on small numbers. The post does not depend on it.

Source: [`notes/bradley-terry.qmd`](bradley-terry.qmd). Render with `quarto render notes/bradley-terry.qmd`.

## The setup

A machine walks short clips on a 5×5 grid. A judge is shown two clips, A and B, and says which went better. That is all the judge says. The machine wants a number for every cell, a **rating**, such that clips through better cells get better scores.

- $r_s$ is the rating of cell $s$. There are 25 of them.
- $n(A, s)$ is the number of times clip A entered cell $s$.
- A clip’s **score** is the sum of the ratings of the cells it entered:

$$
R(A) = \sum_{s} n(A, s)\, r_s .
$$

*Example:* a clip that enters an ordinary cell and then the mud scores $r_{\text{ordinary}} + r_{\text{mud}}$.

## The model

Bradley and Terry \[1\] wanted to rank players from match results. Give each player $i$ a strength $\pi_i > 0$ and say

$$
\Pr(i \text{ beats } j) = \frac{\pi_i}{\pi_i + \pi_j}.
$$

A player twice as strong wins two games in three. Now write each strength as $\pi_i = e^{R_i}$ and divide top and bottom by $e^{R_i}$:

$$
\Pr(i \text{ beats } j) = \frac{e^{R_i}}{e^{R_i} + e^{R_j}} = \frac{1}{1 + e^{-(R_i - R_j)}} = \sigma(R_i - R_j), \qquad \sigma(x) = \frac{1}{1 + e^{-x}}.
$$

Only the difference in $R$ matters. Here the players are clips, so

$$
\Pr(A \succ B) = \sigma\big(R(A) - R(B)\big).
$$

$\sigma$ turns a difference in score into a probability.

``` python
import numpy as np

def sigma(x):
    return 1 / (1 + np.exp(-x))

for gap in (-3, -1, 0, 0.5, 1, 3):
    print(f"A ahead by {gap:+.1f}:  Pr(judge picks A) = {sigma(gap):.3f}")
```

    A ahead by -3.0:  Pr(judge picks A) = 0.047
    A ahead by -1.0:  Pr(judge picks A) = 0.269
    A ahead by +0.0:  Pr(judge picks A) = 0.500
    A ahead by +0.5:  Pr(judge picks A) = 0.622
    A ahead by +1.0:  Pr(judge picks A) = 0.731
    A ahead by +3.0:  Pr(judge picks A) = 0.953

## At the start, everything is zero

Before any verdict, every rating is zero. So every clip scores zero, whatever cells it entered, and for every pair

$$
\Pr(A \succ B) = \sigma(0 - 0) = \frac{1}{1 + e^{0}} = \frac{1}{1 + 1} = 0.5 .
$$

That is the right place to start. The machine knows nothing, and the model says so: every pair is a coin flip.

Three things follow from it.

1.  **The first verdict is always a surprise of exactly one half.** Whichever clip the judge picks, the model had given it 50%. So the first adjustment is the same size either way, and only its direction depends on the judge.
2.  **Zero is not special. Equal is.** Set every rating to 7 and two clips of the same length still tie, because only the difference in score enters $\sigma$. The model has an opinion only once two cells have different ratings, and only a verdict can make them different.
3.  **The starting point does not change the answer.** As shown below, the fit has a single best set of ratings, and the solver gets there from anywhere. The code in the post happens to start every rating at −0.05 instead of 0. Two clips of the same length still start at exactly 50%.

``` python
rating = np.zeros(25)                  # one rating per cell, all zero

clip_a = [7, 8, 13]                    # the cells clip A entered, numbered 0 to 24
clip_b = [7, 2, 3]
score_a, score_b = rating[clip_a].sum(), rating[clip_b].sum()
print(f"Score of A: {score_a:.2f}.  Score of B: {score_b:.2f}.  Pr(judge picks A) = {sigma(score_a - score_b):.2f}")

rating = np.full(25, 7.0)              # every rating the same, but not zero
print(f"All ratings 7:  Pr(judge picks A) = {sigma(rating[clip_a].sum() - rating[clip_b].sum()):.2f}")
```

    Score of A: 0.00.  Score of B: 0.00.  Pr(judge picks A) = 0.50
    All ratings 7:  Pr(judge picks A) = 0.50

## One verdict, one adjustment

This is the chess-rating rule from the post. Let $p$ be the model’s probability that the judge picks A, and let $y = 1$ if the judge did pick A and $y = 0$ if not. After the verdict, every cell’s rating moves by

$$
K \times (y - p) \times \big(n(A, s) - n(B, s)\big).
$$

$y - p$ is the surprise. The last factor gives the credit to the cells that one clip entered and the other did not. $K$ is the size of one adjustment.

*Example, the very first verdict.* Clip A steps into an ordinary cell. Clip B steps into the mud. All ratings are zero, so $p = 0.5$. The judge picks A, so $y = 1$. Take $K = 0.1$.

- The ordinary cell: $0 + 0.1 \times (1 - 0.5) \times (1 - 0) = +0.05$.
- The mud: $0 + 0.1 \times (1 - 0.5) \times (0 - 1) = -0.05$.
- Every other cell: no change.

Now the two clips differ by $0.05 - (-0.05) = 0.10$, and the model’s probability for A is $\sigma(0.10) = 0.525$.

``` python
K = 0.1
ORDINARY, MUD = 0, 1                   # two cells are enough for this example
rating = np.zeros(2)
visits_a = np.array([1, 0])            # clip A entered the ordinary cell once
visits_b = np.array([0, 1])            # clip B entered the mud once

p = sigma(rating @ visits_a - rating @ visits_b)
y = 1                                  # the judge picked A
print(f"Before: ratings {rating}, Pr(A) = {p:.3f}")
rating += K * (y - p) * (visits_a - visits_b)
print(f"After:  ratings {rating}, Pr(A) = {sigma(rating @ visits_a - rating @ visits_b):.3f}")
```

    Before: ratings [0. 0.], Pr(A) = 0.500
    After:  ratings [ 0.05 -0.05], Pr(A) = 0.525

## The fit

One adjustment uses one verdict. The fit uses all of them at once.

Number the verdicts $k = 1, \dots, m$. Verdict $k$ is on the pair $(A_k, B_k)$, with $y_k = 1$ if the judge picked $A_k$ and $y_k = 0$ if not. Write $p_k = \sigma\big(R(A_k) - R(B_k)\big)$ for what the ratings predict.

How likely was the whole pile of verdicts, according to the ratings? Each verdict for A had probability $p_k$, and each verdict for B had probability $1 - p_k$. Multiply them all together. The logarithm of that product is the **log-likelihood**

$$
\ell(r) = \sum_{k=1}^{m} \Big[\, y_k \log p_k + (1 - y_k) \log (1 - p_k) \Big].
$$

The fit is the set of ratings that makes $\ell$ as large as possible: the ratings under which the verdicts the judge actually gave were most likely.

At the start, with every rating zero, every $p_k$ is 0.5 and $\ell = m \log 0.5$. Any fit has to beat that.

## A fit by hand

Take one pair. Clip A goes around the mud and clip B goes through it, and they are otherwise alike. Only one number matters: the gap $d = R(A) - R(B)$.

Suppose the judge sees this pair 8 times and picks A 5 times. Then

$$
\ell(d) = 5 \log \sigma(d) + 3 \log\big(1 - \sigma(d)\big).
$$

The derivative of $\log \sigma(d)$ is $1 - \sigma(d)$. The derivative of $\log(1 - \sigma(d))$ is $-\sigma(d)$. So the slope is

$$
\ell'(d) = 5\,\big(1 - \sigma(d)\big) - 3\,\sigma(d) = 5 - 8\,\sigma(d).
$$

The top of the hill is where the slope is zero: $\sigma(d) = 5/8$, which is $d = \log(5/3) = 0.51$.

**The fit sets the predicted frequency equal to the observed one.** The judge picked A five times in eight, so the fitted ratings say A wins five times in eight.

And 0.51 is the right answer, in the judge’s units. In the post the mud truly costs 1 point, and the judge says A with probability $\sigma(\text{gap in points} / \tau)$ with $\tau = 2$. So the gap the judge acts on is $1/2 = 0.5$. This is why the learned rewards in the post come out near the true points divided by $\tau$.

``` python
def loglik(d, wins_a=5, wins_b=3):
    return wins_a * np.log(sigma(d)) + wins_b * np.log(1 - sigma(d))

for d in (0.0, 0.25, 0.51, 0.75, 1.0, 2.0):
    print(f"gap d = {d:.2f}:  Pr(A) = {sigma(d):.3f}   log-likelihood = {loglik(d):.4f}   slope = {5 - 8 * sigma(d):+.3f}")
print(f"\nlog(5/3) = {np.log(5 / 3):.4f}.  At the start, d = 0, the log-likelihood is 8 log 0.5 = {8 * np.log(0.5):.4f}.")
```

    gap d = 0.00:  Pr(A) = 0.500   log-likelihood = -5.5452   slope = +1.000
    gap d = 0.25:  Pr(A) = 0.562   log-likelihood = -5.3575   slope = +0.503
    gap d = 0.51:  Pr(A) = 0.625   log-likelihood = -5.2925   slope = +0.002
    gap d = 0.75:  Pr(A) = 0.679   log-likelihood = -5.3450   slope = -0.433
    gap d = 1.00:  Pr(A) = 0.731   log-likelihood = -5.5061   slope = -0.848
    gap d = 2.00:  Pr(A) = 0.881   log-likelihood = -7.0154   slope = -2.046

    log(5/3) = 0.5108.  At the start, d = 0, the log-likelihood is 8 log 0.5 = -5.5452.

The log-likelihood is highest at 0.51, and the slope there is zero.

## The slope in general

Differentiate $\ell$ with respect to one cell’s rating and the same thing happens, verdict by verdict:

$$
\frac{\partial \ell}{\partial r_s} = \sum_{k=1}^{m} (y_k - p_k)\,\big(n(A_k, s) - n(B_k, s)\big).
$$

Each term is surprise times the difference in visits. That is the adjustment from above for one verdict, without the $K$.

**So one chess-style adjustment is one step uphill on the Bradley–Terry log-likelihood, using one verdict.** In machine-learning terms it is stochastic gradient ascent, and $K$ is the learning rate.

The ratings have settled when every slope is zero. In words: over the whole pile of verdicts, the ups and the downs cancel for every cell.

*Example:* back to the 8 verdicts. Put the gap at 0.51, so $p = 5/8 = 0.625$. Each of the 5 verdicts for A pushes up with surprise $1 - 0.625 = 0.375$. Each of the 3 verdicts for B pushes down with surprise $0.625$. The total is $5 \times 0.375 - 3 \times 0.625 = 0$. Nothing moves.

Here are the adjustments doing the fit. Start with both ratings at zero and go through the 8 verdicts over and over, in a new order each pass, with a $K$ that shrinks from pass to pass.

``` python
rng = np.random.default_rng(0)
verdicts = np.array([1, 1, 1, 1, 1, 0, 0, 0])      # the judge picked A five times in eight
rating = np.zeros(2)                               # [ordinary, mud], both zero at the start
print(f"start:      ratings {rating.round(3)}   gap {rating[0] - rating[1]:.3f}   Pr(A) = {sigma(rating[0] - rating[1]):.3f}")
for n_pass in range(1, 1001):
    for y in rng.permutation(verdicts):
        p = sigma(rating @ visits_a - rating @ visits_b)
        rating += (0.5 / n_pass) * (y - p) * (visits_a - visits_b)
    if n_pass in (1, 10, 100, 1000):
        print(f"pass {n_pass:>5}:  ratings {rating.round(3)}   gap {rating[0] - rating[1]:.3f}   Pr(A) = {sigma(rating[0] - rating[1]):.3f}")
```

    start:      ratings [0. 0.]   gap 0.000   Pr(A) = 0.500
    pass     1:  ratings [ 0.042 -0.042]   gap 0.084   Pr(A) = 0.521
    pass    10:  ratings [ 0.257 -0.257]   gap 0.514   Pr(A) = 0.626
    pass   100:  ratings [ 0.256 -0.256]   gap 0.513   Pr(A) = 0.625
    pass  1000:  ratings [ 0.255 -0.255]   gap 0.511   Pr(A) = 0.625

The gap settles at 0.51 and the probability at 5/8. The two ratings are equal and opposite because they started at zero and every adjustment moved them by the same amount in opposite directions.

## One summit

The second derivative of $\ell$ is never positive. In the example,

$$
\ell''(d) = -8\,\sigma(d)\big(1 - \sigma(d)\big) < 0 .
$$

So $\ell$ is a single hill with no false summits. Walking uphill in small enough steps arrives at the same place from any start, and it is the same place a solver jumps to. The post uses a solver, so it has no $K$ to choose.

## What the verdicts cannot pin down

**Only differences.** A verdict compares, so only differences in score are determined. In the example the fit says the gap is 0.51. It does not say whether the two ratings are +0.255 and −0.255, or 0 and −0.51.

**A clip that never loses.** If one kind of clip wins every time, the likelihood keeps rising as its rating grows, and there is no summit. With 8 verdicts out of 8 for A, the slope is $8\,(1 - \sigma(d))$, which is positive for every $d$.

The code below handles both with a very small penalty on large ratings. It also holds every cell where the walk goes on at or below −0.05, so that a step is never free.

## The fit in code

This is the function the post uses, unchanged. The post runs it every 25 rounds on all the verdicts so far.

- `X` has one row per verdict and one column per cell: the number of times clip A entered the cell, minus the number of times clip B did.
- `y` is 1 where the judge picked A and 0 where the judge picked B.
- `ends_walk` marks the cells where a walk ends: the treasure, the exit and the fires. Every other cell is held at or below −0.05.

It minimizes the average of $-\ell$ plus the small penalty, with a standard solver (L-BFGS-B), and hands back the ratings as a 5×5 table.

``` python
from scipy.optimize import minimize

N = 5               # the grid is 5×5
N_CELLS = N * N
STEP_FLOOR = 0.05   # every cell where the walk goes on is worth at most -0.05

def fit_reward(X, y, ends_walk, start=None, l2=1e-4):
    """Bradley-Terry with a table for the reward: logistic regression, no intercept, solved
    to convergence. Each row of X is one pair: x_i = times clip A entered cell i, minus
    times clip B did. y is 1 if the judge chose A. `start` is the previous fit, if there
    is one. The answer does not depend on it; it only saves time."""
    def loss_and_grad(beta):
        z = X @ beta
        p = 1 / (1 + np.exp(-z))
        loss = np.mean(np.logaddexp(0, z) - y * z) + 0.5 * l2 * beta @ beta
        return loss, X.T @ (p - y) / len(y) + l2 * beta
    ceiling = np.where(ends_walk, np.inf, -STEP_FLOOR)      # steps are never free
    x0 = np.full(N_CELLS, -STEP_FLOOR) if start is None else start.ravel()
    x0 = np.minimum(x0, ceiling)
    res = minimize(loss_and_grad, x0, jac=True, method="L-BFGS-B",
                   bounds=[(None, None if np.isinf(c) else c) for c in ceiling],
                   options={"maxiter": 10000, "gtol": 1e-10})
    return res.x.reshape(N, N)
```

Reading it against the math: `z` is the difference in score $R(A_k) - R(B_k)$ for every verdict at once, `p` is $p_k$, and `np.logaddexp(0, z) - y * z` is $-\big[y_k \log p_k + (1 - y_k)\log(1 - p_k)\big]$, written in a way that does not overflow. The gradient line, `X.T @ (p - y)`, is the slope from above with the sign flipped, because the solver walks downhill on $-\ell$ where the adjustments walk uphill on $\ell$.

Now run it on the 8 verdicts from the example. Call the ordinary cell number 0 and the mud number 1. Neither ends a walk.

``` python
X = np.zeros((8, N_CELLS))
X[:, 0], X[:, 1] = 1, -1                       # clip A entered the ordinary cell, clip B the mud
y = np.array([1, 1, 1, 1, 1, 0, 0, 0.0])       # the judge picked A five times in eight
ends_walk = np.zeros(N_CELLS, bool)            # no cell here ends a walk

fit = fit_reward(X, y, ends_walk).ravel()
print(f"ordinary cell: {fit[0]:+.3f}    mud: {fit[1]:+.3f}    gap: {fit[0] - fit[1]:.3f}    Pr(A) = {sigma(fit[0] - fit[1]):.3f}")
print(f"a cell no verdict touched: {fit[2]:+.3f}")
```

    ordinary cell: -0.050    mud: -0.561    gap: 0.511    Pr(A) = 0.625
    a cell no verdict touched: -0.050

The gap is 0.51 and the probability is 5/8, as computed by hand. The two ratings are not ±0.255 this time. The ordinary cell sits at its ceiling of −0.05 and the mud is 0.51 below it, because the code holds every step at a small cost. Only the gap was ever pinned down by the verdicts, so the fit is just as good. A cell that no verdict touched stays where it started.

## Other names for the same thing

**Logistic regression.** Give verdict $k$ one input per cell, $x_{k,s} = n(A_k, s) - n(B_k, s)$, and the model is $\Pr(y_k = 1) = \sigma\big(\sum_s x_{k,s}\, r_s\big)$. That is a logistic regression with no intercept, and the ratings are its coefficients. The code below is written this way.

**Elo.** Chess \[2\] writes its prediction as

$$
\Pr(A \text{ wins}) = \frac{1}{1 + 10^{-(S_A - S_B)/400}} = \sigma\!\left(\frac{(S_A - S_B)\,\ln 10}{400}\right).
$$

It is the same curve with the ratings in bigger units. A 400-point edge wins with probability $10/11 = 0.91$.

**RLHF.** In reinforcement learning from human feedback, $R$ is a neural network that scores a piece of text \[3\]. $\ell$ is the same, and the fit is the same walk uphill, with the slopes computed by backpropagation.

## References

1.  Bradley, R. A., & Terry, M. E. (1952). *Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons.* Biometrika 39, 324–345.
2.  Elo, A. E. (1978). *The Rating of Chessplayers, Past and Present.* Arco.
3.  Ouyang, L., et al. (2022). *Training language models to follow instructions with human feedback.* NeurIPS 2022. <https://arxiv.org/abs/2203.02155>

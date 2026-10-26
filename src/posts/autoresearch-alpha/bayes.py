"""Does the test period look like the validation period? A Bayesian check on the final book. Run from this directory:

    uv run --no-project --with pymc --with arviz --with pandas --with matplotlib python bayes.py

Reads lab/weekly_pnl.csv (written by analysis.py). Weekly, not daily, P&L: the book holds positions about eight
days, so daily P&L is autocorrelated, and weekly sums also soften the volatility clustering.

Model (Kruschke's BEST): weekly P&L in each period is Student-t with its own mean and scale and a shared tail
parameter, on weakly informative priors. From the posterior: each period's annualized Sharpe, their ratio, and
the probabilities a reader wants. Then a posterior predictive check: draw test-length histories from the
validation posterior and ask where the observed test Sharpe falls among them. Writes lab/bayes.txt and bayes.svg.
"""
import numpy as np, pandas as pd
import pymc as pm, arviz as az
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

wk = pd.read_csv("lab/weekly_pnl.csv", parse_dates=["week"], index_col="week")["final"]
val, test = wk["2004":"2017"].values, wk["2018":].values
sd = wk.std()
SR = lambda mu, sig, nu: mu / (sig * np.sqrt(nu / (nu - 2))) * np.sqrt(52)          # Student-t sd = sig * sqrt(nu / (nu - 2))

with pm.Model():
    nu = pm.Exponential("nu_minus_2", 1 / 10) + 2                                   # tails heavier than normal allowed, variance finite
    mu = pm.Normal("mu", 0, 2 * sd, shape=2)
    sig = pm.HalfNormal("sigma", 2 * sd, shape=2)
    pm.StudentT("y_val", nu=nu, mu=mu[0], sigma=sig[0], observed=val)
    pm.StudentT("y_test", nu=nu, mu=mu[1], sigma=sig[1], observed=test)
    idata = pm.sample(4000, tune=2000, chains=4, target_accept=0.95, random_seed=7, progressbar=False)

post = idata.posterior
nu_s = post["nu_minus_2"].values.ravel() + 2
mu_s, sig_s = post["mu"].values.reshape(-1, 2), post["sigma"].values.reshape(-1, 2)
sr_val, sr_test = SR(mu_s[:, 0], sig_s[:, 0], nu_s), SR(mu_s[:, 1], sig_s[:, 1], nu_s)
hdi = lambda x: az.hdi(x, hdi_prob=0.9)

# posterior predictive: test-length histories from the validation posterior, and their realized Sharpe
rng = np.random.default_rng(7)
idx = rng.integers(0, len(nu_s), 20000)
sims = mu_s[idx, 0, None] + sig_s[idx, 0, None] * rng.standard_t(nu_s[idx, None], size=(len(idx), len(test)))
pp_sr = sims.mean(axis=1) / sims.std(axis=1, ddof=1) * np.sqrt(52)
obs_sr = test.mean() / test.std(ddof=1) * np.sqrt(52)
obs_val = val.mean() / val.std(ddof=1) * np.sqrt(52)

lines = [
    f"weeks: validation {len(val)}, test {len(test)}; observed annualized Sharpe from weekly P&L: validation {obs_val:.2f}, test {obs_sr:.2f}",
    f"divergences: {int(idata.sample_stats['diverging'].sum())}; max r_hat: {float(az.rhat(idata).to_array().max()):.3f}",
    f"posterior Sharpe, validation: mean {sr_val.mean():.2f}, 90% HDI {hdi(sr_val)[0]:.2f} to {hdi(sr_val)[1]:.2f}",
    f"posterior Sharpe, test:       mean {sr_test.mean():.2f}, 90% HDI {hdi(sr_test)[0]:.2f} to {hdi(sr_test)[1]:.2f}",
    f"ratio test / validation:      median {np.median(sr_test / sr_val):.2f}, 90% HDI {hdi(sr_test / sr_val)[0]:.2f} to {hdi(sr_test / sr_val)[1]:.2f}",
    f"P(test Sharpe > 0) = {(sr_test > 0).mean():.3f}",
    f"P(test Sharpe > half of validation's) = {(sr_test > 0.5 * sr_val).mean():.3f}",
    f"P(test Sharpe < validation Sharpe) = {(sr_test < sr_val).mean():.3f}",
    f"tail parameter nu: median {np.median(nu_s):.1f}",
    f"posterior predictive: share of test-length histories drawn from the validation posterior with a Sharpe at or below the observed test's {obs_sr:.2f}: {(pp_sr <= obs_sr).mean():.3f}",
    f"   predictive Sharpe for a test-length history: median {np.median(pp_sr):.2f}, 90% interval {np.quantile(pp_sr, 0.05):.2f} to {np.quantile(pp_sr, 0.95):.2f}",
]
open("lab/bayes.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

# ── figure, in the site's palette ──────────────────────────────────────────
INK, INK2, MUTED, RULE, ACCENT = "#e8eaf0", "#c0c4cf", "#6b7280", "#2a3344", "#3ee87a"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "monospace", "font.monospace": ["DejaVu Sans Mono"],
    "font.size": 11, "text.color": INK2, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": RULE, "axes.facecolor": "none", "figure.facecolor": "none", "savefig.facecolor": "none",
    "axes.grid": True, "grid.color": RULE, "grid.linewidth": 1, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "xtick.major.size": 0, "ytick.major.size": 0, "axes.titlecolor": INK, "axes.titleweight": "bold",
})
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 3.9), gridspec_kw=dict(wspace=0.28))
for ax in (a1, a2):
    ax.grid(False); ax.set_yticks([]); ax.tick_params(labelsize=10)
    ax.spines["bottom"].set_color(RULE)
bins = np.linspace(-0.6, 2.2, 70)
for x, c, lab in ((sr_val, ACCENT, "validation, 2004-2017"), (sr_test, INK2, "test, 2018-2026")):
    a1.hist(x, bins=bins, density=True, histtype="stepfilled", color=c, alpha=0.25)
    a1.hist(x, bins=bins, density=True, histtype="step", color=c, lw=1.8, label=lab)
a1.set_xlabel("annualized Sharpe", fontsize=10)
a1.set_title("posterior Sharpe, by period", loc="left", fontsize=10.5, pad=8)
a1.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0, 1.0))
a1.set_ylim(0, a1.get_ylim()[1] * 1.25)
pb = np.linspace(-0.6, 2.4, 70)
a2.hist(pp_sr, bins=pb, density=True, histtype="stepfilled", color=MUTED, alpha=0.35)
a2.hist(pp_sr, bins=pb, density=True, histtype="step", color=MUTED, lw=1.6)
a2.axvline(obs_sr, color=INK, lw=1.6)
a2.set_ylim(0, a2.get_ylim()[1] * 1.15)
a2.text(obs_sr + 0.05, a2.get_ylim()[1] * 0.95, f"observed test Sharpe {obs_sr:.2f}\n{(pp_sr <= obs_sr).mean():.0%} of draws are lower",
        fontsize=9, color=INK, va="top")
a2.set_xlabel("Sharpe of an 8.6-year history", fontsize=10)
a2.set_title("if the test were drawn from validation", loc="left", fontsize=10.5, pad=8)
fig.savefig("bayes.svg", bbox_inches="tight", pad_inches=0.25)
svg = open("bayes.svg").read().replace("DejaVu Sans Mono", "IBM Plex Mono, DejaVu Sans Mono, monospace")
open("bayes.svg", "w").write(svg); print("wrote bayes.svg")

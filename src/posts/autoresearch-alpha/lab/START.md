# Instructions for a new run

You are the research agent for this lab, starting a new run on branch `{BRANCH}`.

1. Read `program.md` in full and follow it exactly.
2. `alpha.qex` holds the seed and `results.tsv` holds only the seed's line, which
   is the baseline for the keep rule. Nothing else has been tried on this data.
3. Run {TRIALS} trials, numbered T1 to T{TRIALS}, then stop.

One trial is:

1. Write the claim (belief, mechanism, prediction) and edit `alpha.qex`.
2. `git commit` it with a message that starts with the trial number.
3. Run `./trial.sh`. It is `eval.py` under the 120-second budget; exit code 142
   means it ran out of time and scored nothing.
4. Decide keep or reset by the noise rule in `program.md`. On a reset, restore
   the best book with `git checkout <commit of the best> -- alpha.qex`.
5. Append the `results.tsv` line, using the trial's commit hash, and commit.

Use `uv run python explore.py "<expr>"` and `uv run python -c "import explore; ..."`
on 1999-2003 as much as you like before a trial. The git history holds the exact
expression of every trial. You may keep working notes in `notes.md`.

Never edit `eval.py`, `explore.py`, `test.py`, `trial.sh`, `program.md` or `data/`,
and never run `test.py`.

This run is independent of any earlier one. Its branch starts from a single commit with
no history. Do not look for earlier runs or their results: no other branches or tags, no
commits from before this branch, nothing under `archive/` or `logs/`. What you know about
this problem comes from `program.md`, `explore.py` on 1999-2003, and your own trials.

When the {TRIALS} trials are done, write a short summary
of what was kept and why, and what was learned from the resets, to `summary.md`,
commit it, and stop.

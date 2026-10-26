"""Pull what the evaluator showed the agent on each trial out of the run's transcript. Run from this directory:

    python extract_eval.py [transcript.jsonl]      # default: the run 3 transcript in the lab's logs/

Each trial.sh result in the transcript is parsed (score, worst, eligibility, whole-period numbers, the six
slices of the first deal, crash-state Sharpe, deflated Sharpe) and matched to its notebook row by its score
and worst, which the agent copied into results.tsv. Writes lab/trial-outputs.json for figures.py.
"""
import csv, json, os, re, sys

LAB = os.environ.get("ALPHA_LAB", os.path.expanduser("~/dev/alpha_lab"))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(LAB, "logs", "run3-20261024-111232.jsonl")

uses, outs = set(), []
for line in open(path):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    m = d.get("message")
    if not isinstance(m, dict) or not isinstance(m.get("content"), list):
        continue
    for c in m["content"]:
        if c.get("type") == "tool_use" and c["name"] == "Bash" and "trial.sh" in c["input"].get("command", ""):
            uses.add(c["id"])
        if c.get("type") == "tool_result" and c.get("tool_use_id") in uses:
            body = c.get("content")
            outs.append(body if isinstance(body, str) else "".join(x.get("text", "") for x in body))

num = lambda pat, t: (lambda m: float(m.group(1)) if m else None)(re.search(pat, t))
def parse(t):
    folds = [dict(utility=float(u), sharpe=float(s), ret=float(r) / 100, years=y) for u, s, r, y in
             re.findall(r"fold \d: utility\s+(-?[\d.]+).*?Sharpe\s+(-?[\d.]+)\s+return/yr\s+([+-]?[\d.]+)%.*?years (\d{4}-\d{4})", t)]
    return dict(utility=num(r"utility:\s+(-?[\d.]+)", t), worst=num(r"worst:\s+(-?[\d.]+)", t),
                eligible=bool(re.search(r"eligible: yes", t)), margin=num(r"margin ([\d.-]+) bps, needs", t),
                sharpe=num(r"sharpe:\s+(-?[\d.]+)", t), ret=(num(r"return/yr ([+-]?[\d.]+)%  turnover", t) or 0) / 100,
                turnover=num(r"\(whole validation, cost-free\).*?turnover ([\d.]+)", t),
                crash=num(r"crash state\s+Sharpe\s+(-?[\d.]+)", t), deflated=num(r"deflated Sharpe probability of this expression: ([\d.]+)", t),
                folds=folds)

parsed = [parse(t) for t in outs if t.startswith("utility:")]
rows = list(csv.DictReader(open("lab/results.tsv"), delimiter="\t"))
out = {}
for r in rows:
    hit = [p for p in parsed if p["utility"] == float(r["utility"]) and p["worst"] == float(r["worst"])]
    if hit:
        out[r["commit"]] = hit[-1]
json.dump(out, open("lab/trial-outputs.json", "w"), indent=0)
print(f"{len(parsed)} evaluator outputs, {len(out)} of {len(rows)} notebook rows matched; unmatched:",
      [r["commit"] for r in rows if r["commit"] not in out])

"""Tables for the NBA meanings report, from each arm's graded.json.

    python3 nba/analyze.py --run R1 [--arms C,D0,D1,D2,W0,W1]   # prints Markdown, writes results/nba/<run>/summary.json

McNemar is the exact two-sided test from lib/stats.mjs, on the questions two
arms disagree on. "Wrong layer" counts answers that read their facts (any table
but the team and season lookups) from outside the local_ layer, on questions
whose gold reads local_ facts; such an answer can still be right (the control
dedupes raw_ itself), so the right-in-substance count among them is shown too.
"""

import argparse
import collections
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = {q["question_id"]: q for q in json.loads((ROOT / "nba" / "questions.json").read_text())}
CATEGORIES = ["lookup", "aggregate", "layer", "vocabulary", "join"]


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, center - half), min(1.0, center + half))


def load(run, arm):
    path = ROOT / "results" / "nba" / run / arm / "pass-1" / "graded.json"
    return {r["question_id"]: r for r in json.loads(path.read_text())} if path.exists() else None


def gold_reads_local(qid):
    return "local_" in QUESTIONS[qid]["SQL"]


TEAM_NAMES = {"raw.raw_teams", "transformed.dim_teams_cleansed", "transformed.src_teams", "dev.scd_raw_teams"}


def gold_shown(qid, row):
    """Strict recall: every table the gold reads was in front of the drafter (any team-name table will do for raw_teams)."""
    if row["schema_path"] == "whole":
        return True
    chosen = set(row["chosen"])
    for table in re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_]+\.[A-Za-z_]+)", QUESTIONS[qid]["SQL"]):
        table = table.lower()
        if table == "raw.raw_teams":
            if not chosen & TEAM_NAMES:
                return False
        elif table not in chosen:
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="R1")
    parser.add_argument("--arms", default="C,D0,D1,D2,W0,W1")
    args = parser.parse_args()
    arms = {arm: load(args.run, arm) for arm in args.arms.split(",")}
    arms = {arm: rows for arm, rows in arms.items() if rows}
    summary = {}
    print("| Arm | Exactly right | Right in substance | 95% CI (substance) | Refused | Errors |")
    print("|---|---|---|---|---|---|")
    for arm, rows in arms.items():
        n = len(rows)
        strict = sum(r["strict"] for r in rows.values())
        shape = sum(r["shape"] for r in rows.values())
        refused = sum(r["failure_reason"] == "refused" for r in rows.values())
        errors = sum(r["failure_reason"] in ("execution_error", "execution_timeout", "unknown_error", "no_model_output") for r in rows.values())
        low, high = wilson(shape, n)
        summary[arm] = {"strict": strict, "shape": shape, "n": n, "refused": refused, "errors": errors}
        print(f"| {arm} | {strict} | {shape} | {low:.0%}–{high:.0%} | {refused} | {errors} |")

    print("\nBy category, right in substance")
    print("| Arm | " + " | ".join(f"{c} ({sum(q['category'] == c for q in QUESTIONS.values())})" for c in CATEGORIES) + " |")
    print("|---|" + "---|" * len(CATEGORIES))
    for arm, rows in arms.items():
        print(f"| {arm} | " + " | ".join(str(sum(r["shape"] for r in rows.values() if r["category"] == c)) for c in CATEGORIES) + " |")

    print("\nMcNemar (exact, two-sided)")
    print("| Pair | Measure | Only first right | Only second right | p |")
    print("|---|---|---|---|---|")
    pairs = [("D0", "D1"), ("D1", "D2"), ("D0", "D2"), ("W0", "W1"), ("D0", "W0"), ("D1", "W1")]
    summary["mcnemar"] = {}
    for first, second in pairs:
        if first not in arms or second not in arms:
            continue
        for measure in ("strict", "shape"):
            b = sum(arms[first][q][measure] and not arms[second][q][measure] for q in QUESTIONS)
            c = sum(arms[second][q][measure] and not arms[first][q][measure] for q in QUESTIONS)
            p = mcnemar(b, c)
            summary["mcnemar"][f"{first}-{second}-{measure}"] = {"b": b, "c": c, "p": p}
            print(f"| {first} vs {second} | {'exactly right' if measure == 'strict' else 'in substance'} | {b} | {c} | {p:.2f} |")

    print("\nSearch: what reached the drafter")
    print("| Arm | Path | Gold's own tables shown | Some table that could answer shown | Right in substance when gold's tables shown / not shown | Answers that said they used AI drafts |")
    print("|---|---|---|---|---|---|")
    local_questions = [q for q in QUESTIONS if gold_reads_local(q)]
    for arm, rows in arms.items():
        if arm == "C":
            continue
        paths = collections.Counter(r["schema_path"] for r in rows.values())
        recalled = sum(bool(r["recalled"]) for r in rows.values())
        offered = sum(bool(rows[q]["local_offered"]) for q in local_questions)
        drafted = sum(bool(r["drafted_notes"]) for r in rows.values())
        shown = [q for q in QUESTIONS if gold_shown(q, rows[q])]
        right_shown = sum(rows[q]["shape"] for q in shown)
        right_hidden = sum(rows[q]["shape"] for q in QUESTIONS if q not in shown)
        summary[arm].update({"paths": dict(paths), "recalled": recalled, "local_offered": offered, "gold_shown": len(shown), "gold_shown_questions": shown, "drafted_notes": drafted})
        path_text = ", ".join(f"{k} {v}" for k, v in paths.most_common())
        print(f"| {arm} | {path_text} | {len(shown)} of 40 | {recalled} of 40 | {right_shown} of {len(shown)} / {right_hidden} of {40 - len(shown)} | {drafted} |")

    print(f"\nLayer: answers on the {len(local_questions)} questions whose gold reads local_ facts")
    print("| Arm | Read local_ only | Read another layer | …of those, right in substance | Layers read outside local_ |")
    print("|---|---|---|---|---|")
    for arm, rows in arms.items():
        local_only = other = other_right = 0
        layers = collections.Counter()
        for q in local_questions:
            r = rows[q]
            facts = r["fact_layers"]
            if not facts:
                continue
            if facts == ["local"]:
                local_only += 1
            else:
                other += 1
                other_right += r["shape"]
                layers.update(l for l in facts if l != "local")
        summary[arm].update({"local_only": local_only, "other_layer": other, "other_layer_right": other_right, "other_layers": dict(layers)})
        print(f"| {arm} | {local_only} | {other} | {other_right} | {', '.join(f'{k} {v}' for k, v in layers.most_common())} |")

    print("\nPer question (S = right in substance, x = exactly right too, . = wrong, - = no answer)")
    order = list(arms)
    print("| q | category | " + " | ".join(order) + " |")
    print("|---|---|" + "---|" * len(order))
    for qid, q in QUESTIONS.items():
        marks = []
        for arm in order:
            r = arms[arm][qid]
            mark = "x" if r["strict"] else "S" if r["shape"] else "-" if not r["sql"] else "."
            layer = "/".join(r["fact_layers"]) if r["fact_layers"] else ""
            marks.append(f"{mark} {layer}".strip())
        print(f"| {qid} | {q['category']} | " + " | ".join(marks) + " |")
    out = ROOT / "results" / "nba" / args.run / "summary.json"
    out.write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()

"""Compare arms the way NVIDIA's gym/compare.py does.

    python3 wwi/compare.py --run <id> --arms C,W0,W1a,WM

Refuses a headline when more than 5% of an arm's answers are broken runs
(no_model_output or unknown_error) or when a question has no row. Pass 1 is the
headline, as pass@1. Every other pass measures how stable the arm is.
"""

import argparse
import json
import math
from pathlib import Path

HEALTH_THRESHOLD = 0.05
BROKEN = ("no_model_output", "unknown_error")
ROOT = Path(__file__).resolve().parent.parent / "results" / "wwi"


def wilson(hits, n, z=1.96):
    p = hits / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return centre - half, centre + half


def mcnemar(gained, lost):
    """Exact two-sided McNemar."""
    n = gained + lost
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(gained, lost) + 1)) / 2**n
    return min(1.0, 2 * tail)


def load(run, arm, number):
    path = ROOT / run / arm / f"pass-{number}" / "graded.json"
    if not path.exists():
        return None
    return {row["question_id"]: row for row in json.loads(path.read_text()) if "excluded" not in row}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--arms", default="C,W0,W1a,WM")
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--ignore-health", action="store_true")
    args = parser.parse_args()
    arms = args.arms.split(",")
    data = {arm: {n: load(args.run, arm, n) for n in range(1, args.passes + 1)} for arm in arms}

    print("Health")
    healthy = True
    for arm in arms:
        for number, rows in data[arm].items():
            if rows is None:
                continue
            broken = sum(1 for r in rows.values() if r["failure_reason"] in BROKEN)
            rate = broken / len(rows)
            if rate > HEALTH_THRESHOLD:
                healthy = False
            print(f"  {arm} pass {number}: {len(rows)} graded, {broken} broken ({rate:.1%}){'  ABOVE GATE' if rate > HEALTH_THRESHOLD else ''}")
    if not healthy and not args.ignore_health:
        print("\nNo headline: a run is above the 5% broken-run gate. Resume those questions.")
        return 1

    print("\nStrict (NVIDIA's rule), pass 1")
    print(f"{'arm':6}{'strict':>10}{'95% CI':>16}{'non-empty':>11}{'form':>8}{'shape':>8}{'refused':>9}{'errors':>8}")
    base = data[arms[0]][1]
    for arm in arms:
        rows = data[arm][1]
        if rows is None:
            print(f"{arm:6}  not run")
            continue
        n = len(rows)
        hits = sum(r["strict"] for r in rows.values())
        low, high = wilson(hits, n)
        nonempty = [r for r in rows.values() if r["gold_result"] == "nonempty_gold"]
        print(
            f"{arm:6}{hits:>4}/{n} {hits/n:>4.0%}{f'{low:.0%}-{high:.0%}':>16}"
            f"{sum(r['strict'] for r in nonempty):>7}/{len(nonempty)}"
            f"{sum(r['form'] for r in rows.values()):>8}"
            f"{sum(r.get('shape', r['form']) for r in rows.values()):>8}"
            f"{sum(r['failure_reason'] == 'refused' for r in rows.values()):>9}"
            f"{sum(r['failure_reason'] in ('execution_error', 'execution_timeout') for r in rows.values()):>8}"
        )

    print("\nEvery pass, strict")
    for arm in arms:
        scores = [(sum(r["strict"] for r in rows.values()), len(rows)) for rows in data[arm].values() if rows]
        if scores:
            mean = sum(hit for hit, _ in scores) / len(scores)
            print(f"  {arm}: {' '.join(f'{hit}/{n}' for hit, n in scores)}   mean {mean:.1f}")
    print("\nAnswered the same way across passes (right every time, or wrong every time)")
    for arm in arms:
        passes = [rows for rows in data[arm].values() if rows]
        if len(passes) < 2:
            continue
        steady = sum(1 for q in passes[0] if len({p[q]["strict"] for p in passes if q in p}) == 1)
        always = sum(1 for q in passes[0] if all(p[q]["strict"] for p in passes if q in p))
        print(f"  {arm}: {steady}/{len(passes[0])} steady, {always} right every pass")

    audit_path = Path(__file__).resolve().parent / "gold-audit.json"
    if audit_path.exists():
        audit = {row["question_id"]: row["verdict"] for row in json.loads(audit_path.read_text())}
        print("\nOn the blind gold audit, pass 1 (strict / shape), then mean strict across passes")
        for label, keep in (("sound", {"SOUND"}), ("sound+ambiguous", {"SOUND", "AMBIGUOUS"}), ("wrong gold", {"WRONG"})):
            print(f"  {label}:")
            for arm in arms:
                rows = data[arm][1]
                if rows is None:
                    continue
                chosen = [r for r in rows.values() if audit.get(r["question_id"]) in keep]
                strict = sum(r["strict"] for r in chosen)
                shape = sum(r.get("shape", r["form"]) for r in chosen)
                passes = [rs for rs in data[arm].values() if rs]
                mean = sum(sum(r["strict"] for r in rs.values() if audit.get(r["question_id"]) in keep) for rs in passes) / len(passes)
                print(f"    {arm:6}{strict:>3}/{len(chosen)} strict, {shape:>3}/{len(chosen)} shape, mean strict {mean:.1f}")

    print("\nAgainst the control, pass 1")
    for arm in arms[1:]:
        rows = data[arm][1]
        if rows is None:
            continue
        gained = [q for q in rows if rows[q]["strict"] and not base[q]["strict"]]
        lost = [q for q in rows if base[q]["strict"] and not rows[q]["strict"]]
        print(f"  {arm}: fixed {len(gained)} {gained}, broke {len(lost)} {lost}, McNemar p={mcnemar(len(gained), len(lost)):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The cuts in the results report, from the graded runs.

    uv run --quiet --with 'psycopg[binary]' python wwi/analysis.py
"""

import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "results" / "wwi"
ARMS = ("C", "W0", "W1a", "WM")
# Questions whose gold rows one of NVIDIA's custom analyses returns exactly, with
# more than a lone number. WM holds those analyses as certified saved queries.
SUPPLIED = {31, 32, 34, 35, 39, 40}
CAP = re.compile(r"\s+LIMIT\s+50[01]\s*;?\s*$", re.I)


def graded(run, arm, number):
    rows = json.loads((ROOT / run / arm / f"pass-{number}" / "graded.json").read_text())
    return {row["question_id"]: row for row in rows if "excluded" not in row}


def predictions(run, arm, number):
    path = ROOT / run / arm / f"pass-{number}" / "predictions.jsonl"
    return {json.loads(line)["question_id"]: json.loads(line) for line in path.read_text().splitlines() if line.strip()}


def main():
    audit = {row["question_id"]: row["verdict"] for row in json.loads((Path(__file__).parent / "gold-audit.json").read_text())}
    gold = {c["question_id"]: c for c in grade.gold_cases()}
    gold_rows = {q: grade.run(c["SQL"])[0] for q, c in gold.items()}
    sound = {q for q, verdict in audit.items() if verdict == "SOUND"}

    print("Strict, mean of three passes, with and without the supplied questions")
    for run in ("r2", "r3"):
        for arm in ARMS:
            passes = [graded(run, arm, n) for n in (1, 2, 3)]
            everything = statistics.mean(sum(r["strict"] for r in p.values()) for p in passes)
            without = statistics.mean(sum(r["strict"] for q, r in p.items() if q not in SUPPLIED) for p in passes)
            supplied = statistics.mean(sum(r["strict"] for q, r in p.items() if q in SUPPLIED) for p in passes)
            sound_mean = statistics.mean(sum(r["strict"] for q, r in p.items() if q in sound) for p in passes)
            shape = statistics.mean(sum(bool(r.get("shape")) for r in p.values()) for p in passes)
            refused = statistics.mean(sum(r["failure_reason"] == "refused" for r in p.values()) for p in passes)
            print(f"  {run} {arm:4} all {everything:4.1f}/39  supplied {supplied:3.1f}/6  other {without:4.1f}/33  sound {sound_mean:4.1f}/16  shape {shape:4.1f}/39  refused {refused:3.1f}")

    print("\nShape with ZLens's row cap taken off, pass 1")
    for run in ("r2", "r3"):
        for arm in ARMS:
            hits = 0
            strict = 0
            for q, row in graded(run, arm, 1).items():
                sql = row.get("sql")
                if not sql:
                    continue
                rows, _, _ = grade.run(CAP.sub("", sql))
                if rows is None:
                    continue
                hits += grade.shape_match(gold_rows[q], rows)
                strict += grade.strict_match(gold_rows[q], rows)
            print(f"  {run} {arm:4} strict {strict}/39  shape {hits}/39")

    print("\nTrust labels on WM, all passes: certified answers, and how many match gold")
    for run in ("r2", "r3"):
        total = right = 0
        misses = set()
        for number in (1, 2, 3):
            marks = graded(run, "WM", number)
            for q, prediction in predictions(run, "WM", number).items():
                if prediction.get("tier") == "certified":
                    total += 1
                    right += bool(marks[q]["strict"])
                    if not marks[q]["strict"]:
                        misses.add((q, audit.get(q)))
        print(f"  {run}: {right}/{total} certified answers matched gold; misses {sorted(misses)}")

    print("\nFixed against control and broken, on sound gold, pass 1")
    for run in ("r2", "r3"):
        base = graded(run, "C", 1)
        for arm in ARMS[1:]:
            rows = graded(run, arm, 1)
            gained = [q for q in sound if rows[q]["strict"] and not base[q]["strict"]]
            lost = [q for q in sound if base[q]["strict"] and not rows[q]["strict"]]
            print(f"  {run} {arm:4} fixed {sorted(gained)} broke {sorted(lost)}")


if __name__ == "__main__":
    main()

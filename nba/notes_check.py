"""The labelling rule: does every answer that read a drafted table say so, and no other?

    work/nba/.venv/bin/python -I nba/notes_check.py --run R2 --arm D1 --meanings work/nba/projects/D1/meanings

A table counts as drafted when its meaning file holds at least one `source: ai`
entry. The answer's note is the "used AI-drafted descriptions of …" line the run
recorded (nba/run.mjs). Also counts trust labels: none may rise above
review_required for a generated answer.
"""

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def drafted_tables(folder):
    tables = set()
    for path in Path(folder).glob("*.yaml"):
        text = path.read_text()
        if "source: ai" in text:
            relation = re.search(r"^relation: (.*)$", text, re.M).group(1)
            tables.add(".".join(relation.lower().split(".")[-2:]))
    return tables


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--meanings", required=True)
    args = parser.parse_args()
    drafted = drafted_tables(args.meanings)
    graded = json.loads((ROOT / "results" / "nba" / args.run / args.arm / "pass-1" / "graded.json").read_text())
    read = noted = silent = false_note = 0
    for row in graded:
        reads = set(row["tables"]) & drafted
        note = " ".join(n for n in row["drafted_notes"] if "descriptions" in n)
        read += bool(reads)
        noted += bool(note)
        if reads and not note:
            silent += 1
            print(f"  q{row['question_id']}: read drafted {sorted(reads)} and said nothing")
        if note and not reads:
            false_note += 1
            print(f"  q{row['question_id']}: says it used drafts but read {row['tables']}")
    trust = collections.Counter(row["trust"] for row in graded)
    print(f"{args.run}/{args.arm}: {len(drafted)} drafted tables; {read} answers read one, {noted} said so; silent {silent}, note without a drafted table {false_note}; trust {dict(trust)}")


if __name__ == "__main__":
    main()

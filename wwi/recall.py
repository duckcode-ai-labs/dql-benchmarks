"""Score search: did ZLens choose the tables each question needs?

    python3 wwi/recall.py --run <id> --arm WL --set nvidia|fresh

Reads the first table selection each run recorded, before any model reply could
change it, and compares it with the tables the gold SQL reads. A question counts
only when every table it needs was chosen.
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work" / "wwi"
TABLE = re.compile(r"\b(?:from|join)\s+([a-z_]+\.[a-z_]+)", re.I)
CHOSEN = re.compile(r"[a-z_]+\.[a-z_]+\.[a-z_]+")


def catalog_tables(arm):
    catalog = json.loads((WORK / "projects" / arm / ".dql" / "warehouse-catalog.json").read_text())
    return {f"{r['schema']}.{r['name']}".lower() for r in catalog["relations"]}


def questions(name):
    if name == "fresh":
        rows = json.loads((ROOT / "wwi" / "fresh-questions.json").read_text())
        return {r["question"].strip(): {t.lower() for t in r["tables"]} for r in rows}
    rows = json.loads((WORK / "dataset" / "evaluation.json").read_text())
    return {r["question"].strip(): set(TABLE.findall(r["SQL"].lower())) for r in rows if r["question_id"] not in (4, 27)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--arm", default="WL")
    parser.add_argument("--set", default="nvidia")
    parser.add_argument("--pass-number", type=int, default=1)
    args = parser.parse_args()
    known = catalog_tables(args.arm)
    wanted = questions(args.set)
    store = WORK / "runs" / args.run / args.arm / f"pass-{args.pass_number}" / "project" / ".dql" / "local" / "agent-runs.sqlite"
    db = sqlite3.connect(store)
    found_all = counted = hit_tables = total_tables = 0
    misses = []
    whole = 0
    for question, payload in db.execute("select question, payload_json from agent_runs order by rowid"):
        need = wanted.get(question.strip())
        if need is None:
            continue
        need = need & known
        if not need:
            continue
        story = json.loads(payload).get("diagnosticReceiptV9", {}).get("story", [])
        titles = [step.get("title", "") for step in story]
        if any(title.startswith("Showed the whole schema") for title in titles):
            whole += 1
        picked = next((title for title in titles if title.startswith("Chose the table")), "")
        chosen = {".".join(name.lower().split(".")[-2:]) for name in CHOSEN.findall(picked)}
        counted += 1
        hit = need & chosen
        hit_tables += len(hit)
        total_tables += len(need)
        if hit == need:
            found_all += 1
        else:
            misses.append((question[:60], sorted(need - chosen)))
    print(f"{args.run}/{args.arm}/{args.set}: every table found on {found_all} of {counted} questions ({found_all / max(counted, 1):.0%}); {hit_tables} of {total_tables} tables ({hit_tables / max(total_tables, 1):.0%}); whole schema shown on {whole}")
    for miss in misses[:6]:
        print("   missed", miss)


if __name__ == "__main__":
    main()

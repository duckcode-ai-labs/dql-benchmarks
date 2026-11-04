"""R3: the DM arm (dbt + a business model built blind) against R2 D0, R1 D0 and R1 W0.

    python3 nba/compare_dm.py   # prints Markdown, writes results/nba/R3/summary.json
"""

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import QUESTIONS, gold_reads_local, gold_shown, load, mcnemar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEPRECATED = {"int_player_stats", "int_season_stats", "fct_player_journey", "fct_player_performance", "dim_players_cleansed", "src_games_details", "stg_player_information"}
ARMS = [("R3", "DM"), ("R2", "D0"), ("R1", "D0"), ("R1", "W0")]


def predictions(run, arm):
    path = ROOT / "results" / "nba" / run / arm / "pass-1" / "predictions.jsonl"
    return {r["question_id"]: r for r in map(json.loads, path.read_text().splitlines())}


def main():
    rows = {f"{run} {arm}": load(run, arm) for run, arm in ARMS}
    preds = {f"{run} {arm}": predictions(run, arm) for run, arm in ARMS}
    summary = {}
    print("| Arm | Exactly right | Right in substance | Refused | Gold's tables shown | Path | Wrong layer and wrong | Read a deprecated table |")
    print("|---|---|---|---|---|---|---|---|")
    for label, graded in rows.items():
        strict = sum(r["strict"] for r in graded.values())
        shape = sum(r["shape"] for r in graded.values())
        refused = sum(r["failure_reason"] == "refused" for r in graded.values())
        shown = [q for q in QUESTIONS if gold_shown(q, graded[q])]
        paths = collections.Counter(r["schema_path"] for r in graded.values())
        wrong_layer = sorted(q for q in QUESTIONS if gold_reads_local(q) and graded[q]["fact_layers"] and graded[q]["fact_layers"] != ["local"] and not graded[q]["shape"])
        deprecated = sorted(q for q in QUESTIONS if {t.split(".")[-1] for t in graded[q]["tables"]} & DEPRECATED)
        summary[label] = {"strict": strict, "shape": shape, "refused": refused, "gold_shown": len(shown), "paths": dict(paths), "wrong_layer": wrong_layer, "deprecated_read": deprecated,
                          "routes": dict(collections.Counter(f"{p.get('route')} / {p.get('trust')}" for p in preds[label].values()))}
        print(f"| {label} | {strict} | {shape} | {refused} | {len(shown)} of 40 | {', '.join(f'{k} {v}' for k, v in paths.items())} | {len(wrong_layer)} {wrong_layer} | {len(deprecated)} {deprecated} |")
    dm = rows["R3 DM"]
    print("\n| DM against | Exactly right: only other / only DM, p | In substance: only other / only DM, p |")
    print("|---|---|---|")
    for label in ("R2 D0", "R1 D0", "R1 W0"):
        cells = []
        for measure in ("strict", "shape"):
            b = sum(rows[label][q][measure] and not dm[q][measure] for q in QUESTIONS)
            c = sum(dm[q][measure] and not rows[label][q][measure] for q in QUESTIONS)
            cells.append(f"{b} / {c}, p = {mcnemar(b, c):.2f}")
            summary.setdefault("mcnemar", {})[f"DM-vs-{label}-{measure}"] = {"b": b, "c": c, "p": mcnemar(b, c)}
        print(f"| {label} | {cells[0]} | {cells[1]} |")
    print("\nRoutes / trust")
    for label in rows:
        print(f"  {label}: {summary[label]['routes']}")
    print("\nPer question: R3 DM vs R2 D0 (S = in substance, x = exactly too, . wrong, - none), layers read")
    for q in (9, 16, 17, 20, 24):
        cells = []
        for label in rows:
            r = rows[label][q]
            mark = "x" if r["strict"] else "S" if r["shape"] else "-" if not r["sql"] else "."
            cells.append(f"{label}: {mark} {'/'.join(r['fact_layers'])} {sorted(t.split('.')[-1] for t in r['tables'])}")
        print(f"  q{q}: " + " | ".join(cells))
    changed = [q for q in QUESTIONS if dm[q]["shape"] != rows["R2 D0"][q]["shape"]]
    print("\nDM and R2 D0 differ (in substance) on", {q: ("DM" if dm[q]["shape"] else "D0") for q in changed})
    (ROOT / "results" / "nba" / "R3" / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()

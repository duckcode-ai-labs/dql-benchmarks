"""Run every gold query on the DuckDB copy, look for ties at a LIMIT, and check
the answers oracle.json covers.

    work/nba/.venv/bin/python -I nba/check_gold.py [--db work/nba/source/nba_analysis.duckdb]

oracle.json is the owner's independent CSV oracle (local_duckdb/oracle.py: no dbt,
no DuckDB). It is copied to work/nba/source/oracle.json.
"""

import argparse
import json
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "work" / "nba" / "source" / "nba_analysis.duckdb"
ORACLE = ROOT / "work" / "nba" / "source" / "oracle.json"


def oracle_expectation(key, oracle):
    """What the oracle says the gold row should be, as a list of tuples (approximate floats)."""
    checks = oracle["checks"]
    if key == "calendar_coverage":
        c = checks[key][0]
        return [(c["min_game_date"], c["max_game_date"])]
    if key == "top_scorers_2017":
        return None  # used by two questions; compared by hand below
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB))
    args = parser.parse_args()
    con = duckdb.connect(args.db, read_only=True)
    questions = json.loads((ROOT / "nba" / "questions.json").read_text())
    oracle = json.loads(ORACLE.read_text())
    problems = []
    results = {}
    for item in questions:
        sql = item["SQL"]
        rows = con.execute(sql).fetchall()
        results[item["question_id"]] = rows
        flag = ""
        if not rows:
            flag = "EMPTY"
            problems.append((item["question_id"], "empty gold"))
        match = re.search(r"LIMIT (\d+)\s*$", sql)
        if match:
            k = int(match.group(1))
            wider = con.execute(re.sub(r"LIMIT \d+\s*$", f"LIMIT {k + 1}", sql)).fetchall()
            if len(wider) > k:
                flag += f" | next row: {wider[k]}"
            if len(wider) > k and wider[k][1:] == wider[k - 1][1:]:
                problems.append((item["question_id"], f"tie at the limit: {wider[k - 1]} vs {wider[k]}"))
        print(f"q{item['question_id']:>2} [{item['category']}] {item['question'][:80]}\n     -> {rows[:5]} {flag}")

    print("\nOracle cross-checks")
    c = oracle["checks"]
    checks = [
        (4, [(str(r[0]), str(r[1])) for r in results[4]], [(c["calendar_coverage"][0]["min_game_date"], c["calendar_coverage"][0]["max_game_date"])]),
        (7, results[7], [(c["top_scorers_2017"][0]["player_name"], c["top_scorers_2017"][0]["total_points"])]),
        (9, results[9][:1], [(c["multi_season_weighted_ppg"][0]["player_name"], c["multi_season_weighted_ppg"][0]["total_points"])]),
        (17, results[17], [(r["games_played"],) for r in c["top_scorers_2017"] if r["player_name"] == "LeBron James"]),
        (21, results[21], [(r["player_name"], round(r["field_goal_pct"], 3)) for r in c["field_goal_leaders_2017"]]),
        (25, results[25], [(c["points_per_game_leaders_2017_min20"][0]["player_name"], round(c["points_per_game_leaders_2017_min20"][0]["points_per_game"], 2))]),
        (27, results[27], [(c["double_double_leaders_2017"][0]["player_name"], c["double_double_leaders_2017"][0]["double_double_games"])]),
    ]
    abbreviation = dict(con.execute("SELECT TEAM_ID, ABBREVIATION FROM RAW.raw_teams").fetchall())
    top_team = c["team_win_leaders_2017"][0]
    checks.append((35, results[35], [(abbreviation[top_team["team_id"]], top_team["wins"])]))
    for qid, got, expected in checks:
        ok = len(got) == len(expected) and all(tuple(a) == tuple(b) for a, b in zip(got, expected))
        print(f"  q{qid}: {'MATCH' if ok else 'DIFFERS'} gold={got} oracle={expected}")
        if not ok:
            problems.append((qid, "differs from oracle"))
    print("\nProblems:", problems or "none")
    out = ROOT / "results" / "nba" / "gold-check.json"
    out.write_text(json.dumps({str(k): [list(map(str, r)) for r in v] for k, v in results.items()}, indent=1) + "\n")


if __name__ == "__main__":
    main()

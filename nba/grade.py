"""Grade one arm's SQL on the NBA DuckDB copy, the way wwi/grade.py grades WWI.

    work/nba/.venv/bin/python -I nba/grade.py --arm <predictions.jsonl> --out <graded.json>

Strict: run gold and prediction on the same read-only database, then
`set(gold) == set(pred)` on raw rows (NVIDIA's exec_match rule; a prediction
that doesn't run scores zero). Shape ("right in substance"): every column of
the smaller result is in the larger one row for row, numbers equal to 1e-6,
column order and extra columns ignored. The functions are copied from
wwi/grade.py unchanged; only the database driver differs.

Each graded row also records which layer the answer read its facts from and,
for ZLens arms, whether the tables it needs were in front of the drafter
(from the run's "Chose the tables" / "Showed the whole schema" step).
"""

import argparse
import collections
import datetime
import decimal
import json
import os
import re
import sys
import threading
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "work" / "nba" / "source" / "nba_analysis.duckdb"
# Q5: an arm on its own warehouse (DX: the NBA tables plus decoys) is graded on it, by the name its SQL uses.
if os.environ.get("BENCH_DB"):
    DB = Path(os.environ["BENCH_DB"])
# F1: BENCH_MODEL_PROJECT is the arm's project, to know which tables "the whole model" showed.
MODEL_PROJECT = os.environ.get("BENCH_MODEL_PROJECT")
# P6: BENCH_QUESTIONS points at another question file (nba/questions-p6.json).
QUESTIONS = Path(os.environ["BENCH_QUESTIONS"]) if os.environ.get("BENCH_QUESTIONS") else ROOT / "nba" / "questions.json"
TIMEOUT_S = 30.0
TOLERANCE_DIGITS = 6

_con = {}


def connection():
    if "c" not in _con:
        _con["c"] = duckdb.connect(str(DB), read_only=True)
        _con["c"].execute("SET enable_external_access = false")
    return _con["c"]


def run(sql):
    con = connection()
    out = {}

    def go():
        try:
            cursor = con.execute(sql)
            out["rows"] = cursor.fetchall()
            out["columns"] = [d[0] for d in cursor.description or []]
        except Exception as error:  # the error text is the result
            out["error"] = f"error: {error}".split("\n")[0][:200]

    worker = threading.Thread(target=go, daemon=True)
    worker.start()
    worker.join(TIMEOUT_S)
    if worker.is_alive():
        con.interrupt()
        worker.join(5)
        return None, None, "timeout"
    if "error" in out:
        return None, None, out["error"]
    return out["rows"], out["columns"], ""


def strict_match(gold, pred):
    try:
        return set(gold) == set(pred)
    except TypeError:
        try:
            return sorted(map(repr, gold)) == sorted(map(repr, pred))
        except Exception:
            return False


def normal(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return f"bool:{value}"
    if isinstance(value, (int, float, decimal.Decimal)):
        return f"num:{round(float(value), TOLERANCE_DIGITS) + 0.0}"
    if isinstance(value, datetime.datetime):
        if value.time() == datetime.time(0, 0):
            return f"date:{value.date()}"
        return f"ts:{value.replace(tzinfo=None).isoformat()}"
    if isinstance(value, datetime.date):
        return f"date:{value}"
    return f"str:{str(value).strip()}"


def form_match(gold, pred, norm=None):
    norm = norm or normal
    if not gold:
        return not pred
    if not pred or len(pred[0]) < len(gold[0]):
        return False
    gold_rows = [tuple(norm(v) for v in row) for row in gold]
    pred_rows = [tuple(norm(v) for v in row) for row in pred]
    if set(gold_rows) == set(pred_rows):
        return True
    wanted = collections.Counter(gold_rows)
    columns = [sorted(col) for col in zip(*gold_rows)]
    pred_columns = [sorted(col) for col in zip(*pred_rows)]
    choices = [[j for j, col in enumerate(pred_columns) if set(col) == set(gold_col)] for gold_col in columns]

    def assign(index, used):
        if index == len(choices):
            picked = collections.Counter(tuple(row[j] for j in used) for row in pred_rows)
            return set(picked) == set(wanted)
        return any(assign(index + 1, used + [j]) for j in choices[index] if j not in used)

    return assign(0, [])


def shape_match(gold, pred, norm=None):
    if form_match(gold, pred, norm):
        return True
    return bool(gold) and bool(pred) and len(pred[0]) < len(gold[0]) and form_match(pred, gold, norm)


# ------------------------------------------------------------------ the same thing by another name
# P7: "right in substance" compared names word for word, so an answer naming the
# Rockets by team_id where the gold wrote HOU, or the 2006 season where the gold
# wrote "2006-07", scored wrong with every number right. This second measure maps
# each cell to what it names before the same comparison: a team by its id,
# abbreviation, nickname, full name or (when only one team has it) city; a
# player by name (when only one player has it); a season label by its start
# year; a "YYYY-MM" month by its first day. Player ids stay numbers: they could
# be a points total. Reported beside the plain measure, for every arm alike.
_ALIASES = {}


def aliases():
    if _ALIASES:
        return _ALIASES
    con = connection()
    try:
        teams = con.execute("SELECT team_id, team_abbreviation, team_nickname, city FROM TRANSFORMED.dim_teams_cleansed").fetchall()
        players = con.execute("SELECT player_id, MIN(player_name) FROM TRANSFORMED.local_player_season_facts GROUP BY player_id").fetchall()
    except Exception:
        _ALIASES["none"] = None
        return _ALIASES
    cities = collections.Counter(str(city).strip().lower() for _, _, _, city in teams)
    for team_id, abbreviation, nickname, city in teams:
        token = f"team:{team_id}"
        _ALIASES[f"id:{team_id}"] = token
        for name in [abbreviation, nickname, f"{city} {nickname}"] + ([city] if cities[str(city).strip().lower()] == 1 else []):
            if name:
                _ALIASES[str(name).strip().lower()] = token
    names = collections.Counter(str(name).strip().lower() for _, name in players)
    for player_id, name in players:
        if name and names[str(name).strip().lower()] == 1:
            _ALIASES.setdefault(str(name).strip().lower(), f"player:{player_id}")
    return _ALIASES


def entity_normal(value):
    table = aliases()
    if isinstance(value, str):
        text = value.strip()
        label = re.fullmatch(r"(\d{4})-(\d{2})", text)
        if label:
            start, end = int(label.group(1)), int(label.group(2))
            if end == (start + 1) % 100:
                return f"num:{float(start)}"
            if 1 <= end <= 12:
                return f"date:{start:04d}-{end:02d}-01"
        if text.isdigit() and f"id:{text}" in table:
            return table[f"id:{text}"]
        if text.lower() in table:
            return table[text.lower()]
    if isinstance(value, (int, float, decimal.Decimal)) and not isinstance(value, bool) and float(value).is_integer() and f"id:{int(value)}" in table:
        return table[f"id:{int(value)}"]
    return normal(value)


def extract_sql(text):
    if not text:
        return "SELECT 1", False
    matches = re.findall(r"(?:```sql)(.*?[a-zA-Z].*?)(?:```)", text, flags=re.DOTALL)
    if not matches:
        return "SELECT 1", False
    block = matches[-1]
    answer = re.sub(r"--.*?$|/\*.*?\*/", "", block, flags=re.DOTALL)
    cut = len(re.sub(r"\s+", " ", answer)) < len(re.sub(r"\s+", " ", block)) and "--" in block
    answer = re.sub(r"\s+", " ", answer)
    return re.sub(r"^\*\*.*\*\*", "", answer).strip(), cut


# ------------------------------------------------------------------ layers
RELATION = re.compile(r'\b(?:from|join)\s+((?:"?[A-Za-z0-9_]+"?\.){0,2}"?[A-Za-z0-9_]+"?)', re.I)
QUOTED = re.compile(r'"?([A-Za-z0-9_]+)"?\."?([A-Za-z0-9_]+)"?\."?([A-Za-z0-9_]+)"?')
LOOKUPS = {"raw_teams", "dim_teams_cleansed", "src_teams", "scd_raw_teams", "dim_seasons"}


def tables_in(sql):
    """schema.table names an SQL statement reads (CTE names drop out: they have no schema)."""
    found = set()
    for name in RELATION.findall(sql or ""):
        parts = [part.strip('"').lower() for part in name.split(".")]
        if len(parts) >= 2:
            found.add(".".join(parts[-2:]))
    return found


def layer_of(table):
    name = table.split(".")[-1]
    for prefix in ("local_", "fct_", "int_", "src_", "stg_", "raw_", "dim_", "scd_"):
        if name.startswith(prefix):
            return prefix.rstrip("_")
    return "other"


def fact_layers(sql):
    """The layers an answer read its facts from: every table but the team and season lookups."""
    return sorted({layer_of(t) for t in tables_in(sql) if t.split(".")[-1] not in LOOKUPS})


def chosen_tables(title):
    """Tables named in the run's schema step, as schema.table."""
    return {f"{schema.lower()}.{table.lower()}" for _db, schema, table in QUOTED.findall(title or "")}


def recalled(needs, chosen, whole):
    if whole:
        return True
    names = {table.split(".")[-1] for table in chosen}
    return all(any(option in chosen or option.split(".")[-1] in names for option in group) for group in needs)


def model_tables(project):
    """F1 (RFC 0012): the tables a model answers from, when Ask showed "the whole model":
    its entities' tables, less deprecated ones and drafted look-alikes (use_instead)."""
    import yaml
    tables = set()
    for path in Path(project).glob("domains/**/modeling/**/*.yaml"):
        document = yaml.safe_load(path.read_text()) or {}
        for entity in document.get("entities") or []:
            if entity.get("status") == "deprecated" or entity.get("use_instead"):
                continue
            bound = entity.get("dbt_model") or entity.get("relation") or ""
            if bound:
                tables.add(bound.split(".")[-1].lower())
    return tables


def grade(path, out):
    predictions = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            predictions[record["question_id"]] = record
    results = []
    for case in json.loads(QUESTIONS.read_text()):
        qid = case["question_id"]
        gold_rows, _gold_columns, gold_status = run(case["SQL"])
        if gold_rows is None:
            results.append({"question_id": qid, "excluded": gold_status})
            continue
        record = predictions.get(qid)
        sql = (record or {}).get("sql")
        comment_cut = False
        if record and record.get("reply"):
            sql, comment_cut = extract_sql(record["reply"])
        failure = (record or {}).get("failure") or ("no_model_output" if record is None else None)
        title = (record or {}).get("schemaTitle")
        whole = bool(title and title.startswith("Showed the whole schema"))
        if title and title.startswith("Showed the whole model") and MODEL_PROJECT:
            # The model's tables were all shown, plus any the question named (not listed).
            title = title + " " + " ".join(f'"db"."m"."{table}"' for table in sorted(model_tables(MODEL_PROJECT)))
        chosen = chosen_tables(title)
        item = {
            "question_id": qid,
            "category": case["category"],
            "question": case["question"],
            "gold_rows": len(gold_rows),
            "strict": False,
            "form": False,
            "shape": False,
            "entities": False,
            "failure_reason": failure,
            "sql": sql,
            "comment_cut": comment_cut,
            "route": (record or {}).get("route"),
            "trust": (record or {}).get("trust"),
            "fact_layers": fact_layers(sql) if sql and sql != "SELECT 1" else [],
            "tables": sorted(tables_in(sql)) if sql else [],
            "schema_path": None if title is None else ("whole" if whole else "index" if "one-line index" in ((record or {}).get("schemaDetail") or "") else "chosen"),
            "chosen": sorted(chosen),
            "recalled": recalled(case["needs"], chosen, whole) if title is not None else None,
            "local_offered": (whole or any(t.split(".")[-1].startswith("local_") for t in chosen)) if title is not None else None,
            "drafted_notes": (record or {}).get("draftedNotes") or [],
        }
        if sql:
            rows, _columns, status = run(sql)
            if rows is None:
                item["failure_reason"] = "execution_timeout" if status == "timeout" else "execution_error"
                item["error"] = status
            else:
                item["strict"] = strict_match(gold_rows, rows)
                item["form"] = form_match(gold_rows, rows)
                item["shape"] = shape_match(gold_rows, rows)
                item["entities"] = item["shape"] or shape_match(gold_rows, rows, entity_normal)
                item["pred_rows"] = len(rows)
                item["pred_sample"] = [list(map(str, r)) for r in rows[:3]]
                item["failure_reason"] = None if item["strict"] else "wrong_result"
        elif not failure:
            item["failure_reason"] = "no_sql_extracted"
        results.append(item)
    Path(out).write_text(json.dumps(results, indent=2, default=str) + "\n")
    scored = [r for r in results if "excluded" not in r]
    print(f"{Path(path).parent.parent.name}: strict {sum(r['strict'] for r in scored)}/{len(scored)}, shape {sum(r['shape'] for r in scored)}/{len(scored)}, any name {sum(bool(r.get('entities')) for r in scored)}/{len(scored)}")
    print("  ", dict(collections.Counter(r["failure_reason"] for r in scored if not r["strict"])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    grade(args.arm, args.out)


if __name__ == "__main__":
    sys.exit(main())

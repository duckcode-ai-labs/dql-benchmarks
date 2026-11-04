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
DB = ROOT / "work" / "postcard" / "source" / "datamart.duckdb"
# F1: BENCH_MODEL_PROJECT is the arm's project, to know which tables "the whole model" showed.
MODEL_PROJECT = os.environ.get("BENCH_MODEL_PROJECT")
# P6: BENCH_QUESTIONS points at another question file (nba/questions-p6.json).
QUESTIONS = Path(os.environ["BENCH_QUESTIONS"]) if os.environ.get("BENCH_QUESTIONS") else ROOT / "postcard" / "questions.json"
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


def form_match(gold, pred):
    if not gold:
        return not pred
    if not pred or len(pred[0]) < len(gold[0]):
        return False
    gold_rows = [tuple(normal(v) for v in row) for row in gold]
    pred_rows = [tuple(normal(v) for v in row) for row in pred]
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


def shape_match(gold, pred):
    if form_match(gold, pred):
        return True
    return bool(gold) and bool(pred) and len(pred[0]) < len(gold[0]) and form_match(pred, gold)


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
                item["pred_rows"] = len(rows)
                item["pred_sample"] = [list(map(str, r)) for r in rows[:3]]
                item["failure_reason"] = None if item["strict"] else "wrong_result"
        elif not failure:
            item["failure_reason"] = "no_sql_extracted"
        results.append(item)
    Path(out).write_text(json.dumps(results, indent=2, default=str) + "\n")
    scored = [r for r in results if "excluded" not in r]
    print(f"{Path(path).parent.parent.name}: strict {sum(r['strict'] for r in scored)}/{len(scored)}, shape {sum(r['shape'] for r in scored)}/{len(scored)}")
    print("  ", dict(collections.Counter(r["failure_reason"] for r in scored if not r["strict"])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    grade(args.arm, args.out)


if __name__ == "__main__":
    sys.exit(main())

"""Grade one arm's SQL on WideWorldImporters with NVIDIA's rule.

    uv run --with 'psycopg[binary]' python wwi/grade.py --gold
    uv run --with 'psycopg[binary]' python wwi/grade.py --arm <predictions.jsonl> --out <graded.json>

The strict score is a port of ontology_sql_eval/gym/exec_match.py from
NVIDIA/ontology-sql-eval: run gold and the prediction on the same database with
psycopg, then `set(gold) == set(pred)` on raw rows. A gold query that does not
run takes the question out of the denominator. A prediction that does not run
scores zero. Row order is ignored, duplicates collapse, and an extra column or a
float against a Decimal is a miss.

The form score is ours, and only a diagnostic. It uses lib/row-match.mjs's idea:
column order and extra columns are ignored, and numbers are equal to 1e-6. It
separates "wrong answer" from "right answer, different shape". The headline is
always the strict score.

Each predictions line: {"question_id": 1, "sql": "...", "failure": null}
`failure` says why there is no SQL: "no_model_output" and "unknown_error" count
towards the broken-run gate, as in NVIDIA's compare.py; "refused" does not.
"""

import argparse
import collections
import datetime
import decimal
import json
import re
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path

import psycopg

DSN = "host=127.0.0.1 port=55432 user=wwi_reader dbname=wideworldimporters"
GOLD = Path(__file__).resolve().parent.parent / "work" / "wwi" / "dataset" / "evaluation.json"
TIMEOUT_S = 30.0  # PostgresExecutor's default
TOLERANCE_DIGITS = 6


def run(sql):
    """_run_postgres, plus the cap PostgresExecutor puts around it."""

    def go():
        with psycopg.connect(DSN) as conn, conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall(), [d.name for d in cur.description]

    pool = ThreadPoolExecutor(max_workers=1)
    try:
        return (*pool.submit(go).result(timeout=TIMEOUT_S), "")
    except FutureTimeout:
        return None, None, "timeout"
    except Exception as error:
        return None, None, f"error: {error}".split("\n")[0][:200]
    finally:
        pool.shutdown(wait=False)


def strict_match(gold, pred):
    """result_sets_match, unchanged."""
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
    """True when every gold column is in the prediction, row for row."""
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


def extract_sql(text):
    """extract_sql from exec_match.py, quirks included: the last block wins, and a
    `--` comment removes everything after it. Returns the SQL, and whether that
    quirk cut anything, so a run can show what it cost the control arm."""
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


def gold_cases():
    return json.loads(GOLD.read_text())


def check_gold():
    usable = 0
    empty = []
    slow = []
    for case in gold_cases():
        started = time.monotonic()
        rows, _columns, status = run(case["SQL"])
        seconds = time.monotonic() - started
        if rows is None:
            print(f"q{case['question_id']}: GOLD FAILED ({status}): {case['question'][:70]}")
            continue
        usable += 1
        if not rows:
            empty.append(case["question_id"])
        if seconds > 5:
            slow.append((case["question_id"], round(seconds, 1)))
    print(f"gold ran: {usable} of {len(gold_cases())}")
    print(f"empty gold: {empty}")
    print(f"slow (over 5 s): {slow}")


def grade(path, out):
    predictions = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            predictions[record["question_id"]] = record
    results = []
    for case in gold_cases():
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
        item = {
            "question_id": qid,
            "question": case["question"],
            "gold_result": "nonempty_gold" if gold_rows else "empty_gold",
            "gold_rows": len(gold_rows),
            "strict": False,
            "form": False,
            "failure_reason": failure,
            "sql": sql,
            "comment_cut": comment_cut,
            "route": (record or {}).get("route"),
            "trust": (record or {}).get("trust"),
        }
        if sql:
            rows, _columns, status = run(sql)
            if rows is None:
                item["failure_reason"] = "execution_timeout" if status == "timeout" else "execution_error"
                item["error"] = status
            else:
                item["strict"] = strict_match(gold_rows, rows)
                item["form"] = form_match(gold_rows, rows)
                item["pred_rows"] = len(rows)
                item["failure_reason"] = None if item["strict"] else "wrong_result"
        elif not failure:
            item["failure_reason"] = "no_sql_extracted"
        results.append(item)
    Path(out).write_text(json.dumps(results, indent=2, default=str) + "\n")
    scored = [r for r in results if "excluded" not in r]
    print(f"{Path(path).name}: strict {sum(r['strict'] for r in scored)}/{len(scored)}, form {sum(r['form'] for r in scored)}/{len(scored)}")
    print(dict(collections.Counter(r["failure_reason"] for r in scored if not r["strict"])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", action="store_true")
    parser.add_argument("--arm")
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.gold:
        check_gold()
    elif args.arm and args.out:
        grade(args.arm, args.out)
    else:
        parser.error("--gold, or --arm with --out")


if __name__ == "__main__":
    sys.exit(main())

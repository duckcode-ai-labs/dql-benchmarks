"""Do the NBA tables on Snowflake hold the same data as the DuckDB file? A numbers-match receipt.

    work/nba/.venv/bin/python -I nba/snowflake/parity.py --against snowflake      # needs SNOWFLAKE_* env
    work/nba/.venv/bin/python -I nba/snowflake/parity.py --against duckdb:<path>  # self-check of this script

For every table and view of the DuckDB file (26), on both engines: the row
count, and per column COUNT, COUNT(DISTINCT), MIN, MAX, and SUM for numbers.
Numbers agree within 1e-6 (relative, or absolute near zero): Snowflake divides
integers to 6 decimals where DuckDB uses doubles. Columns a snapshot stamps at
build time are left out. Writes work/nba/snowflake/parity.json and exits 1 on
any difference.
"""
import argparse
import datetime
import decimal
import json
import math
import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work" / "nba" / "source" / "nba_analysis.duckdb"
OUT = ROOT / "work" / "nba" / "snowflake" / "parity.json"
NUMERIC = ("BIGINT", "INTEGER", "SMALLINT", "TINYINT", "HUGEINT", "DOUBLE", "FLOAT", "REAL", "DECIMAL", "UBIGINT", "UINTEGER")
# Stamped when a snapshot runs, never the same on two engines.
BUILD_STAMPED = {"dbt_scd_id", "dbt_updated_at", "dbt_valid_from", "dbt_valid_to", "version_id", "valid_from", "valid_to", "is_current"}


def relations(con):
    rows = con.execute("""
        SELECT schema_name, table_name, 'table' FROM duckdb_tables() WHERE NOT internal
        UNION ALL SELECT schema_name, view_name, 'view' FROM duckdb_views() WHERE NOT internal
        ORDER BY 1, 2""").fetchall()
    out = []
    for schema, name, kind in rows:
        cols = con.execute("SELECT column_name, data_type FROM duckdb_columns() WHERE schema_name = ? AND table_name = ? ORDER BY column_index", [schema, name]).fetchall()
        out.append({"schema": schema, "name": name, "kind": kind, "columns": [(c, t) for c, t in cols if c.lower() not in BUILD_STAMPED]})
    return out


def profile_sql(relation, table_ref, quote):
    parts = ["COUNT(*) AS n"]
    for index, (column, dtype) in enumerate(relation["columns"]):
        q = quote(column)
        parts += [f"COUNT({q}) AS c{index}", f"COUNT(DISTINCT {q}) AS d{index}", f"MIN({q}) AS lo{index}", f"MAX({q}) AS hi{index}"]
        if dtype.startswith(NUMERIC):
            parts.append(f"SUM({q}) AS s{index}")
    return f"SELECT {', '.join(parts)} FROM {table_ref}"


def normal(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, bool):
        return int(value)
    return value


def same(a, b):
    a, b = normal(a), normal(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)
    return a == b


class DuckDB:
    def __init__(self, path):
        self.con = duckdb.connect(str(path), read_only=True)

    def profile(self, relation):
        sql = profile_sql(relation, f'"{relation["schema"]}"."{relation["name"]}"', lambda c: f'"{c}"')
        cur = self.con.execute(sql)
        return dict(zip([d[0].lower() for d in cur.description], cur.fetchone()))


class Snowflake:
    def __init__(self):
        import snowflake.connector  # pip install snowflake-connector-python
        self.con = snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ.get("SNOWFLAKE_USER", "ZLENS_BENCH_SVC"),
            authenticator="SNOWFLAKE_JWT",
            private_key_file=os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
            role=os.environ.get("SNOWFLAKE_ROLE", "ZLENS_BENCH_LOADER"),
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "ZLENS_BENCH_WH"),
            database="NBA",
            session_parameters={"QUERY_TAG": "zlens-bench-parity"},
        )

    def profile(self, relation):
        # Unquoted names: Snowflake upper-cases them, as the tables were made.
        sql = profile_sql(relation, f'NBA.{relation["schema"]}.{relation["name"]}', lambda c: c.upper())
        cur = self.con.cursor()
        cur.execute(sql)
        return dict(zip([d[0].lower() for d in cur.description], cur.fetchone()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--against", required=True, help="snowflake, or duckdb:<path> to check this script")
    args = parser.parse_args()
    base = DuckDB(SOURCE)
    other = Snowflake() if args.against == "snowflake" else DuckDB(Path(args.against.split(":", 1)[1]))
    report = {"against": args.against, "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(), "relations": []}
    failed = 0
    for relation in relations(base.con):
        label = f'{relation["schema"]}.{relation["name"]}'
        try:
            left, right = base.profile(relation), other.profile(relation)
            diffs = [f"{k}: {normal(left[k])!r} vs {normal(right.get(k))!r}" for k in left if not same(left[k], right.get(k))]
        except Exception as error:  # a missing table or column is a difference
            diffs = [f"could not compare: {str(error).splitlines()[0][:200]}"]
        report["relations"].append({"relation": label, "kind": relation["kind"], "rows": normal(left.get("n")) if not diffs or "could not" not in diffs[0] else None, "columns": len(relation["columns"]), "differences": diffs[:20]})
        status = "same" if not diffs else f"{len(diffs)} differences"
        failed += bool(diffs)
        print(f"{'✓' if not diffs else '✗'} {label:40} {relation['kind']:5} {status}")
        for diff in diffs[:5]:
            print(f"    {diff}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str))
    print(f"{len(report['relations']) - failed} of {len(report['relations'])} relations hold the same data -> {OUT.relative_to(ROOT)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

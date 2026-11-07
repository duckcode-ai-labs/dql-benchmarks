"""Load the NBA raw tables into Snowflake: PUT the Parquet files, then run raw_tables.sql.

    SNOWFLAKE_ACCOUNT=<orgname-accountname> SNOWFLAKE_PRIVATE_KEY_PATH=~/.zlens-bench/snowflake/loader.p8 \
      work/nba/.venv/bin/python -I nba/snowflake/load.py

Runs as ZLENS_BENCH_SVC / ZLENS_BENCH_LOADER (setup.sql). export_raw.py first.
Every statement carries the query tag zlens-bench-load, so its cost is visible
in QUERY_HISTORY. Prints each table's loaded row count against the DuckDB file's.
"""
import os
import sys
from pathlib import Path

import snowflake.connector  # pip install snowflake-connector-python

ROOT = Path(__file__).resolve().parents[2]
PARQUET = ROOT / "work" / "nba" / "snowflake" / "parquet"
SQL = Path(__file__).resolve().parent / "raw_tables.sql"


def main() -> None:
    files = sorted(PARQUET.glob("*.parquet"))
    if not files or not SQL.exists():
        sys.exit("run nba/snowflake/export_raw.py first")
    con = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ.get("SNOWFLAKE_USER", "ZLENS_BENCH_SVC"),
        authenticator="SNOWFLAKE_JWT",
        private_key_file=os.path.expanduser(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]),
        role="ZLENS_BENCH_LOADER",
        warehouse="ZLENS_BENCH_WH",
        database="NBA",
        schema="RAW",
        session_parameters={"QUERY_TAG": "zlens-bench-load"},
    )
    cur = con.cursor()
    for path in files:
        cur.execute(f"PUT 'file://{path}' @NBA.RAW.NBA_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE")
        print(f"put {path.name}: {cur.fetchone()[6]}")
    for cursor in con.execute_string(SQL.read_text()):
        row = cursor.fetchone() if cursor.description else None
        if row and cursor.description[0][0].upper() == "TABLE_NAME":
            print(f"{row[0]}: {'all rows loaded' if row[1] else 'ROW COUNT DIFFERS'}")
            if not row[1]:
                sys.exit(1)
    con.close()


if __name__ == "__main__":
    main()

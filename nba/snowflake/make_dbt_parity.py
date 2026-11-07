"""Make the Snowflake copy of the NBA dbt project that builds the same data as DuckDB.

    python3 nba/snowflake/make_dbt_parity.py

The NBA project was written for Snowflake (`NBA_GAMES.RAW.GAMES` ...) and later
given a DuckDB branch for the benchmark. The two branches build different data:
on Snowflake `src_players.player_id` is a ROW_NUMBER, `fct_player_performance`
joins player bios by name only (rows can repeat), `int_player_stats` keeps one
game per season row, and the four `local_*` tables the 40 gold answers read are
DuckDB-only. To score ZLens on Snowflake against the same gold, Snowflake must
hold the same tables with the same rows.

This copies work/nba/dbt to work/nba/dbt-snowflake and adds one dbt target,
`snowflake_parity`, that takes the DuckDB branch of every model and source
(the RAW tables keep their DuckDB names, loaded by export_raw.py into NBA.RAW).
Every other target, and the owner's own repo, are left exactly as they were.
Engine-specific macros keep their engine: DuckDB's `try_strptime` becomes
Snowflake's TRY_TO_DATE (not TO_DATE, which fails a run on one bad date where
DuckDB returns NULL).
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work" / "nba" / "dbt"
TARGET = ROOT / "work" / "nba" / "dbt-snowflake"
LIKE_DUCKDB = "(target.type == 'duckdb' or target.name == 'snowflake_parity')"

PROFILES = """nba_analysis:
  target: snowflake_parity
  outputs:
    # The benchmark's Snowflake copy: same tables and rows as the DuckDB file.
    snowflake_parity:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER', 'ZLENS_BENCH_SVC') }}"
      authenticator: snowflake_jwt
      private_key_path: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PATH') }}"
      role: ZLENS_BENCH_LOADER
      warehouse: ZLENS_BENCH_WH
      database: NBA
      schema: TRANSFORMED
      threads: 4
      query_tag: zlens-bench-dbt
"""


def rewrite(text: str) -> str:
    text = text.replace("target.type == 'duckdb'", LIKE_DUCKDB)
    text = text.replace("target.type != 'duckdb'", f"not {LIKE_DUCKDB}")
    # The raw tables live in the target database (NBA), not the original NBA_GAMES.
    text = text.replace("{% if target.type == 'snowflake' %}NBA_GAMES",
                        "{% if target.type == 'snowflake' and target.name != 'snowflake_parity' %}NBA_GAMES")
    return text


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET, ignore=shutil.ignore_patterns("*.duckdb", "*.duckdb.wal", "target", "logs", "dbt_packages"))
    changed = []
    for path in [*TARGET.glob("models/**/*.sql"), *TARGET.glob("models/**/*.yml"), *TARGET.glob("snapshots/**/*.yml"), *TARGET.glob("snapshots/**/*.sql")]:
        before = path.read_text()
        after = rewrite(before)
        if after != before:
            path.write_text(after)
            changed.append(path.relative_to(TARGET))
    macros = TARGET / "macros" / "nba_portability.sql"
    text = macros.read_text()
    # Parity: a bad date is NULL on both engines.
    text, n = re.subn(r"\{% else %\}\s*\n(\s*)TO_DATE\(", r"{% else %}\n\1TRY_TO_DATE(", text, count=1)
    if n != 1:
        raise SystemExit("nba_parse_date no longer has a TO_DATE branch: check the macro")
    macros.write_text(text)
    (TARGET / "profiles.yml").write_text(PROFILES)
    print(f"{TARGET.relative_to(ROOT)}: {len(changed)} files take the DuckDB branch on target snowflake_parity; nba_parse_date uses TRY_TO_DATE")
    for path in sorted(changed):
        print(f"  {path}")


if __name__ == "__main__":
    main()

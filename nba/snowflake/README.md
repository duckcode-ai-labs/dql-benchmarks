# The NBA benchmark on Snowflake

One dataset, hosted the way a Snowflake customer runs it, so ZLens's measured numbers can be re-measured on Snowflake against the same gold answers (Snowflake plan, phase 1: live proof).

## Why NBA

- It is ZLens's most-quoted benchmark: 40 questions with gold SQL and answers, the "auto ontology" draft (31 of 40), dbt-first and warehouse-first arms.
- **It was a Snowflake project to begin with.** `models/src/sources.yml` reads `NBA_GAMES.RAW.GAMES`, `GAMES_DETAILS`, `PLAYERS`, … on Snowflake; `macros/nba_portability.sql` switches date parsing and regular expressions per engine. Hosting it on Snowflake is going home, not porting.
- It is small: 6 raw tables, 913,330 rows, 10.6 MB of Parquet; with dbt's tables, views and snapshots, 26 relations and about 2.1 million rows. Loading and building take minutes on an X-Small warehouse: well under one credit.

## What the review found

1. **The Snowflake and DuckDB branches of the dbt project do not build the same data.** On Snowflake, `src_players.player_id` is a `ROW_NUMBER()`; `fct_player_performance` joins player bios on name only (rows can repeat); `int_player_stats` keeps one game per season row; the four `local_*` tables are DuckDB-only. The DuckDB branches are the corrected ones the benchmark was scored on.
2. **All 40 gold answers read the DuckDB-only tables**: `TRANSFORMED.local_player_season_facts` (16), `local_team_game_facts` (7), `local_team_season_facts` (7), `local_player_game_facts` (6), and `RAW.raw_teams` (13).
3. **The gold SQL itself is portable**: only `LIMIT`, `ROUND` and one `::INT`, no quoted names.
4. **Names**: the `local_*` tables have lower-case columns. Unquoted, Snowflake upper-cases them and the gold SQL resolves; a table made with `INFER_SCHEMA` keeps them quoted lower-case and every gold query would fail. So tables are created from explicit DDL.
5. **Numbers**: Snowflake divides integers to 6 decimals, DuckDB in doubles (`points / games` = 2.333333 vs 2.3333333333). Grading is unaffected (gold and prediction run on the same engine); the parity check compares within 1e-6.
6. `nba_parse_date` used `TO_DATE` on Snowflake, which stops a run at one bad date; DuckDB's `try_strptime` returns NULL. Parity uses `TRY_TO_DATE`.

## The setup

| Piece | What it does |
|---|---|
| `setup.sql` | Run once as ACCOUNTADMIN: X-Small warehouse with a 25-credit monthly monitor, database `NBA` (`RAW`, `TRANSFORMED`, `DEV`), a loader role and a **read-only `ZLENS_READER` role**, two key-pair service users (`ZLENS_BENCH_SVC` loads, `ZLENS_APP_SVC` is what ZLens and the grader use). No passwords. |
| `export_raw.py` | DuckDB → one Parquet file per RAW table, and `raw_tables.sql` (explicit DDL + `COPY INTO … MATCH_BY_COLUMN_NAME`) with each table's expected row count. |
| `load.py` | PUTs the Parquet files and runs `raw_tables.sql`; fails if a row count differs. |
| `make_dbt_parity.py` | Copies the dbt project to `work/nba/dbt-snowflake` with one new target, `snowflake_parity`, that takes the DuckDB branch everywhere (10 files) and `TRY_TO_DATE`. Other targets, and the owner's own repo, are unchanged. Parses on dbt-snowflake 1.10: all 18 models and 2 snapshots enabled, sources at `NBA.RAW.raw_*`. |
| `parity.py` | The numbers-match receipt: all 26 relations, row counts and per-column count, distinct count, min, max, sum, DuckDB vs Snowflake. Self-checked: an identical copy gives 26 of 26; one changed number is caught. |
| `nba/grade.py` | `BENCH_ENGINE=snowflake` grades gold and predictions on Snowflake as `ZLENS_READER`, with a server-side timeout. DuckDB stays the default. |

## Steps

| # | Who | Step | Proves |
|---|---|---|---|
| 1 | Owner | Start a Snowflake trial: **Enterprise edition** (row access and masking policies need it), **AWS us-east-1** (where ZLens Enterprise runs). | |
| 2 | Owner | Paste `~/.zlens-bench/snowflake/loader.pub` and `reader.pub` (made on this Mac, private keys stay here) into `setup.sql`, run it, and send the account identifier (`orgname-accountname`). | Least-privilege setup works |
| 3 | Agent | `export_raw.py`, `load.py` | 913,330 rows loaded, each table's count checked |
| 4 | Agent | `make_dbt_parity.py`, then in `work/nba/dbt-snowflake`: `dbt snapshot && dbt run` (key pair, query tag `zlens-bench-dbt`) | The dbt project builds on Snowflake |
| 5 | Agent | `parity.py --against snowflake` | Same data on both engines: the receipt |
| 6 | Agent | ZLens projects on Snowflake as `ZLENS_APP_SVC`: dbt-first (D0) and warehouse-first (W0); `zlens sync warehouse`, `zlens doctor`, Draft my models | The driver, sync (keys, comments, query history) and the draft work live |
| 7 | Agent | The 40 questions on the D0 and DA arms with `BENCH_ENGINE=snowflake`; scores beside the DuckDB runs | ZLens's numbers hold on Snowflake, or what breaks |

Cost: steps 3 to 7 are a few X-Small warehouse-minutes each plus the AI provider's tokens; the trial's credits cover them many times over. The monitor suspends the warehouse at 25 credits a month.

Nothing here writes to the owner's `nba_analysis` repo or to ZLens main.

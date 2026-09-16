# Spider 2.0-DBT

[Spider 2.0](https://spider2-sql.github.io/) (ICLR 2025) is an enterprise text-to-SQL benchmark. Its **DBT** setting has 68 repository-level tasks: each is a half-built dbt project with a DuckDB database and a plain-English instruction. The agent must finish the project so that, after `dbt run`, the database matches a golden one. The publisher's `evaluate.py` compares the tables row by row.

Leaderboard as of September 2026: SignalPilot 65.6%, JetBrains Databao 60.29%, GPT-5 baseline 41.18%.

## Conditions

| Condition | Tools the agent gets |
|---|---|
| `bare` (baseline) | list/read/write files in the task, `dbt run/compile/test`, read-only DuckDB SQL |
| `dql-tools` | the same, plus DQL's metadata search, table schema, relationship proofs and SQL validation |

Both run every task with the same model, budget and recordings policy (see [methodology](../docs/methodology.md)).

## Status

| Step | State |
|---|---|
| Download and set-up scripts | written, not yet run |
| Task importer (task → DQL project) | to do |
| DQL `dbt-task` agent command | to do, in the core DQL repo |
| Submission writer and local pre-check with `evaluate.py` | to do |
| Baseline reproduces the published GPT-5 number | to do |

## Running

```bash
./spider2-dbt/download.sh    # clones the publisher's repo into data/ and fetches the task data
./spider2-dbt/setup.sh       # Python environment with dbt-duckdb and the grader's requirements
```

Downloaded data lives under `data/spider2-dbt/` and is never committed.

## Budgets per task

20 minutes wall clock, 40 AI calls, 120 tool calls, 12 `dbt run`s, 200 rows per SQL query. A report records which budget stopped a task.

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
| Download and set-up scripts | done (upstream `cafb867`) |
| Task inventory (`manifest.json`) | done: 68 graded tasks |
| Submission writer and pre-check with the publisher's `evaluate.py` | done; untouched starting databases score 9/68 |
| Task importer (task → DQL project) | done; `playbook001` imports, `dql doctor` passes, DQL queries the task database |
| DQL `dbt-task` agent command | to do, in the core DQL repo |
| Baseline reproduces the published GPT-5 number | to do |

**Read [FINDINGS.md](FINDINGS.md) first:** only 61 of the 68 graded tasks can pass with the published grader, and 9 pass with no work at all.

## Running

```bash
./spider2-dbt/setup.sh                 # Python environment: dbt-duckdb and the grader's requirements
./spider2-dbt/download.sh              # publisher's repo and task data into data/
npm run connectors:install             # DuckDB driver DQL loads, shared by every task
node spider2-dbt/inventory.mjs         # record the task set in manifest.json
node spider2-dbt/pipe-check.mjs        # score untouched starting databases with evaluate.py
node spider2-dbt/import-task.mjs playbook001   # one task → a DQL project under work/
```

Downloaded data lives under `data/spider2-dbt/` and is never committed.

## Budgets per task

20 minutes wall clock, 40 AI calls, 120 tool calls, 12 `dbt run`s, 200 rows per SQL query. A report records which budget stopped a task.

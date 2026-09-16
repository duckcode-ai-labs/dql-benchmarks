# Spider 2.0-DBT: what the published task set actually contains

Checked on 2026-09-16 against upstream commit `cafb867313aab4e674652054198f383cf4018943` of [xlang-ai/Spider2](https://github.com/xlang-ai/Spider2). Reproduce with `node spider2-dbt/inventory.mjs` and `node spider2-dbt/pipe-check.mjs`.

## 1. 68 graded tasks, but only 61 can pass

The grader (`evaluation_suite/evaluate.py`) scores 68 tasks, all with `duckdb_match`.

| Problem | Tasks | Effect |
|---|---|---|
| Gold database not in the published archive | airbnb002, biketheft001, gitcoin001, google_ads001 | scores 0 for every entrant |
| Gold database present under a name the grader does not read | social_media001 (grader wants `social_media_reporting__rollup_report.duckdb`, folder has `social_media.duckdb`); xero_new001, xero_new002 (want `xero.duckdb`, folder has `xero_new.duckdb`) | scores 0 for every entrant |
| No starting database | gitcoin001 | the task cannot be attempted |
| Task folder the grader ignores | danish_democracy_data001 | not scored |

With the published grader, the best possible score is **61/68 (89.7%)**.

## 2. Nine tasks pass with no work at all

Submitting every task's starting database untouched scores **9/68 (13.2%)**: divvy001, f1003, mrr001, mrr002, playbook001, quickbooks003, retail001, salesforce001, superstore001. In these tasks the tables the grader checks already exist in the starting database with the graded values. For example, `playbook001` is graded on `attribution_touches`, which the starting database already holds (39 rows).

## 3. The grader's denominator is the submission, not the task set

`evaluate.py` scores only the instances listed in `results_metadata.jsonl` and divides by that count. A submission that leaves out tasks it cannot solve therefore reports a higher percentage. Our pre-check refuses any submission that does not list all 68 graded tasks.

## 4. The grader compares columns, not rows

`compare_pandas_table` checks that each gold column matches *some* result column within 0.01, and with `ignore_order` it sorts each column on its own. A result whose rows are scrambled across columns can still pass. We report the publisher's score as the score of record, and run our stricter row matcher beside it as a cross-check.

## What this means for reported numbers

- The leaderboard's top score (65.6%) sits above a 13.2% do-nothing floor and below an 89.7% ceiling.
- We report three numbers: over all 68 tasks (comparable to the leaderboard), over the 61 tasks the grader can pass, and over the tasks our answer-key audit accepts. The 16 tasks above are recorded as disputed in `gold-audit.jsonl`.
- These findings will be reported to the publisher before we publish.

# Insurance benchmarks: data.world and dbt Labs

Two public benchmarks on the same insurance data measure what modeling adds over raw AI-written SQL.

- **data.world** ([arXiv 2311.07509](https://arxiv.org/abs/2311.07509), data at [datadotworld/cwd-benchmark-data](https://github.com/datadotworld/cwd-benchmark-data)): 43 questions over a 13-table property-and-casualty schema, split by question complexity and schema complexity. GPT-4 scored 16.7% on the SQL schema and 54.2% with an ontology; on the complex-schema questions, SQL scored 0%.
- **dbt Labs** ([2026 update](https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026), code at [dbt-labs/dbt-llm-sl-bench](https://github.com/dbt-labs/dbt-llm-sl-bench)): 11 questions, 20 runs each, dbt + MetricFlow + DuckDB. With modeled data, text-to-SQL reached 84–90% and the semantic layer 98–100%.

## Layers

Each layer is a copy of dbt Labs' dbt project with one more DQL layer (see [../docs/methodology.md](../docs/methodology.md)):

| Layer | Project contents |
|---|---|
| L0 | dbt project only |
| L1 | + DQL modeling, written from the schema documents and ontology only |
| L2 | + dbt Labs' MetricFlow semantic models |
| L3 | + DQL skills, written from documentation only |

## Files

| File | Purpose |
|---|---|
| `download.sh` | fetches the three sources at pinned commits |
| `questions.mjs` | reads the 43 questions, their correct SQL and quadrant |
| `build.mjs` | builds one layer's project and warehouse, verifies row counts, computes correct answers |
| `checks/publisher-answers.mjs` | checks our warehouse against dbt Labs' published graded answers |
| `run.mjs` | asks a question set through Ask and scores it |
| `gold-audit.jsonl` | answer-key audit, one line per question |
| `dev-questions.json` | questions looked at while building; reported separately |
| `layers/` | files written for L1 and L3 (not yet written) |
| [`REPORT.md`](REPORT.md) | what we did, step by step, and the results |

## Status

See [REPORT.md](REPORT.md#progress).

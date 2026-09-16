# Insurance benchmarks: data.world and dbt Labs

Two public benchmarks on the same insurance data measure what modeling adds over raw AI-written SQL.

- **data.world** ([arXiv 2311.07509](https://arxiv.org/abs/2311.07509), data at [datadotworld/cwd-benchmark-data](https://github.com/datadotworld/cwd-benchmark-data)): 43 questions over a 13-table property-and-casualty schema, split by question complexity and schema complexity. GPT-4 scored 16.7% on the SQL schema and 54.2% with an ontology; on the complex-schema questions, SQL scored 0%.
- **dbt Labs** ([2026 update](https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026), code at [dbt-labs/dbt-llm-sl-bench](https://github.com/dbt-labs/dbt-llm-sl-bench)): 11 questions, 20 runs each, dbt + MetricFlow + DuckDB. With modeled data, text-to-SQL reached 84–90% and the semantic layer 98–100%.

## Conditions

1. `raw`: AI-written SQL over the 13 tables.
2. `modeling`: + DQL domain, entities and relationships with certified joins.
3. `semantic`: + the dbt semantic layer.
4. `skills`: + business rules as DQL skills.

DQL also runs as an extra strategy inside dbt Labs' own runner (through `dql mcp`), so the result appears in their report format with their cost and latency columns.

## Status

| Step | State |
|---|---|
| Download script | written, not yet run |
| DQL projects for both datasets, modeling files | to do |
| Question adapters and gold-answer audit | to do |
| DQL strategy for dbt Labs' runner | to do |
| Baseline reproduces dbt Labs' text-to-SQL numbers | to do |

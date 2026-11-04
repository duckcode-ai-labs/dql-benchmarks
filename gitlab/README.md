# GitLab analytics: domain truth set (model-at-scale design, Q0)

GitLab's public analytics dbt project (MIT; `gitlab-data/analytics`, `transform/snowflake-dbt`,
manifest of 2025-11-30) is the 4,000-model test bed. Work only on a scratch copy of its
`models/` and `target/manifest.json`; never run dbt or Snowflake against it.

- `extract.py <manifest> tables.json`: the 442 business tables (dim/fct/bdg/mart/rpt/map/pump, or
  common*/marts folders minus prep and staging).
- `truth.json`: one domain and subject area per table, labelled from what the table is about by an
  agent that never saw ZLens; 24 spot-checked. Taxonomy: sales_and_marketing (sales, marketing),
  product_and_engineering (product_usage, engineering), finance (revenue_and_billing,
  costs_and_accounting), people, customer_success, support, shared, platform.
- `score_domains.mjs <dql-core dist index.js> <dbt project dir>`: scores `discoverDbtDomains`.
  Proposed names map to true ones by majority; unplaced counts as wrong.

Results (2026-11-04): main 22cbe070 32.6% domains / 30.1% areas / 287 placed / 53 proposals;
zlens#257 78.1% / 66.7% / 439 / 25.

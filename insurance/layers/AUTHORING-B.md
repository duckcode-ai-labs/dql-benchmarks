# How the insurance business layer (B) is written and verified

Layer **B** is what a data team builds when it deploys DQL for an insurance business: the KPIs the business runs on, defined once and governed, the standard reports as blocks, the business rules as skills, and the model underneath. It is written **from the business and the data**, never from the benchmark's questions or answers.

It is used by two test arms that answer the same questions:

| Arm | Project |
|---|---|
| **LB** (with dbt) | dbt Labs' dbt project + B's dbt semantic models and metrics (MetricFlow) + B's DQL files |
| **WB** (without dbt) | the warehouse only + B's metrics converted to DQL native metrics (`dql semantic import`) + B's DQL files |

## Three roles, three separate agents

| Role | Reads | Produces |
|---|---|---|
| **Author** | the working folder below, DQL's documentation and source | the business brief, then layer B, then its log |
| **Verifier** (a different agent) | the author's files, the working folder, DQL's documentation and source | a check of every metric, join and block against the data and the brief; defects go back to the author; a sign-off |
| **Test** (fresh DQL agents, one per question) | the frozen project and one question | the answers that are scored |

The session that built the harness has read the questions and answers, so it writes none of B. After the verifier signs off, B is frozen: its hash is recorded in `insurance/layers/B/FROZEN.json` before any test runs. Later changes to B are not allowed; changes to DQL itself are logged with the build identity of each run.

## What the author and verifier may read

- The working folder `work/insurance/authoring-b/`:
  - `project/`: dbt Labs' insurance dbt project (models only, no semantic layer) with its DuckDB warehouse `acme_insurance.duckdb` (read-only queries: schema, sample rows, counts, distinct values);
  - `docs/`: the published schema documents: `ACME_small.ddl`, data.world's insurance ontology `insurance.ttl` and its mapping `data.world_P&C_Insurance_Ontology_V1.r2rml`;
  - `prior-layers/`: the team's existing DQL modeling (L1) and skills (L3), written earlier by another author under the same rules.
- DQL's documentation and source code (to learn file formats).
- General knowledge of how property-and-casualty insurers measure their business.

## What the author and verifier must not read

Anything that contains the benchmark's questions or answers, or results of runs:
- `data/`, `insurance/` (except this file and `insurance/layers/B/`), `spider2/`, `private/`, `work/` except `work/insurance/authoring-b/`;
- any file named `*benchmark*`, `*question*`, `*gold*`, `*heldout*`, `*unanswerable*`, `report.json`, or any `investigation/` or `hex_notebook/` folder;
- `~/.claude/` and any other session's notes or memory;
- the `duckcode-private` repository.

## What the author produces

All files under `insurance/layers/B/`:

1. **`BUSINESS-BRIEF.md`, written first.** The KPIs and standard reports an insurance carrier of this kind runs its business on, from industry practice and what this data holds: each KPI's business definition, its grain, the dimensions it is cut by, and what the data can and cannot support. Written before any metric or block.
2. **`dbt/models/business_semantics/`**: dbt semantic models and metrics (MetricFlow YAML, plus a time spine model in DuckDB SQL) for every KPI in the brief the data supports. They sit on the dbt project's models (`models/omg_models/`). `dbt parse` must pass.
3. **`dql/`**: files laid out as they sit in a DQL project root, copied on top of the project:
   - modeling: the domain, entities (grain, keys), relationships with keys and cardinality; a relationship is certified only when the data proves it (keys match, cardinality holds, rows join), otherwise it stays a draft with the reason. Start from `prior-layers/L1` and correct or extend it;
   - skills (`skills/*.skill.md`): business definitions and rules, each grounded in rows looked at. Start from `prior-layers/L3`;
   - blocks: the **standard reports** named in the brief (a handful, not one per possible question), each built on the governed metrics where one exists. Blocks are written in draft or review status. **The author never marks a block certified**; a person certifies it or it is reported as not human-certified.
   - `dql model validate` must pass on the project.
4. **`AUTHORING-LOG.md`**: start and end time, every file read outside the working folder, every query run against the warehouse (summarised), and the decisions made (what was certified, what stayed a draft, and why; which KPIs the data cannot support).

## What the verifier produces

`insurance/layers/B/VERIFICATION.md`: for every metric, relationship and block, the check run on the data and its result (pass, or the defect found); defects returned to the author and how each was resolved; and a sign-off line. The verifier does not edit B's files itself.

## Labels in results

Until a person certifies the blocks, results for LB and WB are labelled **"AI-authored, independently AI-verified, not human-certified"**.

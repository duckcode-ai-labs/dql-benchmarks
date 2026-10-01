# Data, question sets and licences

## Sources (fetched by `insurance/download.sh` at pinned commits; not redistributed)

| Source | Commit | Used for |
|---|---|---|
| [datadotworld/cwd-benchmark-data](https://github.com/datadotworld/cwd-benchmark-data) (Apache-2.0) | `0b75eb62` | ACME insurance schema, data, ontology and the 43 published questions (development set) |
| [dbt-labs/dbt-llm-sl-bench](https://github.com/dbt-labs/dbt-llm-sl-bench) | `a29f2429` | dbt project and MetricFlow semantic models over the same data |
| [dbt-labs/semantic-layer-llm-benchmarking](https://github.com/dbt-labs/semantic-layer-llm-benchmarking) | `ac20c929` | dbt Labs' published graded answers, used to check our warehouse |

Check each source's licence before redistributing its files.

## Question sets

| Set | Size | Written by | Status |
|---|---|---|---|
| Development (`insurance/questions.mjs`) | 41 of the 43 published questions | data.world | public; used to diagnose and fix |
| Set 2 (`insurance/heldout/questions-2.json`) | | Claude agent | spent before the paper; not reported |
| Set 3 (`insurance/heldout/questions-3.json`) | 40 + 10 unanswerable | Claude agent | spent (see the paper, section 4.2); reported |
| Set 4 | 200 + 50 unanswerable | Claude agent (Opus 5.5) | sealed until the paper is posted |
| Set 5 | 200 + 50 unanswerable | GPT-6 Sol (Codex, isolated) | sealed until its pre-registered run is reported |

Each writer saw only a copy of the warehouse and a format specification (for set 5:
`insurance/set5-writer/`). Reference rows come from executing the writer's SQL
(`node insurance/heldout.mjs --number N gold`).

## Audits

- Development set: `insurance/gold-audit.jsonl` (three disputed references, with reasons).
- Set 4: a random 25% sample (100 answerable, 25 per quadrant, and 20 unanswerable; seed 20260930;
  `insurance/audit/make_audit_sheet.py`) checked by a person against `insurance/audit/AUDIT-INSTRUCTIONS.md`.
  The completed verdicts are published with set 4.

## What is never committed

Downloaded data, built projects and warehouses, run stores, model logs and Python environments
(`work/`, `data/`, `.venv*/`, see `.gitignore`). Sealed question files and their reports are ignored
explicitly until their release.

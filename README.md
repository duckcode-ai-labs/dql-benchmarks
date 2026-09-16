# DQL Benchmarks

Reproducible public benchmarks for [DQL](https://github.com/duckcode-ai/dql), DuckCode's governed analytics layer for dbt teams.

**What is measured:** DQL's Ask AI answering business questions in plain English over a dbt project — text-to-SQL, the way a DQL customer uses it. Each benchmark measures how much each DQL layer (modeling, semantic layer, skills) adds on top of a plain dbt project.

Every number here is produced by a **pinned, released DQL version** (see `dql.json`), graded against the benchmark publisher's own answers, and ships with the recorded AI calls needed to replay it without an API key.

## Benchmarks

| Benchmark | What it is | Status |
|---|---|---|
| [Insurance](insurance/) | data.world's 43 enterprise questions and dbt Labs' 11, on dbt Labs' insurance dbt project | in progress — see [insurance/REPORT.md](insurance/REPORT.md) |
| BIRD mini-dev | 500 questions over 11 databases; the best-known text-to-SQL leaderboard | planned |
| Spider 2.0-Lite / Snow | enterprise databases (SQLite, BigQuery, Snowflake) | planned |

## How results are reported

See [docs/methodology.md](docs/methodology.md). In short:

1. **DQL as customers use it.** A dbt project, DQL initialised on it, questions asked through Ask.
2. **Paired comparisons only.** DQL layer by layer on the same questions, the same grader, an exact McNemar test and Wilson 95% confidence intervals.
3. **Provenance.** Only runs recorded from a real AI provider count. Every report names the repository commit, the DQL version, the model and the data.
4. **The answer key is audited.** Disputed answers are logged with a reason, and accuracy is reported on all questions and on the accepted subset.
5. **Trust labels are scored.** A wrong answer DQL labels `certified` is counted separately; the target is zero.
6. **No tuning on the test set.** DQL runs as released; modeling and skills are written from documentation, never from the questions or answers.
7. **Cost and latency sit beside accuracy.** Cost is reported only when measured, never estimated.

## Layout

```
dql.json              pinned DQL version (npm release, or a local build while developing)
pricing.json          dated model list prices; null means "not measured"
lib/                  DQL resolver, runtime launcher, identity stamp, row matching, statistics, answer-key audit
paired/               paired comparison scorer
insurance/            insurance benchmark: download, build, questions, runs, report
scripts/              installers for DQL, the DuckDB driver and the Python/dbt environment
docs/                 methodology
```

Downloaded data, working copies, Python environments and database files are never committed (see `.gitignore`).

## Quick start

```bash
npm test                          # unit tests for the scorer and helpers
./scripts/setup-python.sh         # dbt 1.9 with the DuckDB adapter, in .venv/
npm run dql:install               # the DQL version pinned in dql.json, in .dql-cli/
npm run connectors:install        # the DuckDB driver DQL loads, in .connectors/
npm run compare -- a.json b.json  # paired comparison of two eval reports
```

## Using a local DQL build while developing

Set `"source": "local"` and `"path"` in `dql.json` to a DQL checkout's `apps/cli/dist/index.js`, or export `DQL_CLI=/path/to/apps/cli/dist/index.js`. Reports record the source and that build's commit, and a report made from a development build is never published.

## History

This repository first held a harness for Spider 2.0-DBT, which tests an agent writing dbt models rather than answering questions. It was removed on 2026-09-16 when the focus was set on Ask text-to-SQL; the git history keeps it.

## License

Code in this repository is Apache-2.0. Benchmark datasets are downloaded from their publishers and remain under their own licenses; they are not redistributed here.

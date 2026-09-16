# DQL Benchmarks

Reproducible public benchmarks for [DQL](https://github.com/duckcode-ai/dql), the governed analytics layer from DuckCode.

Every number in this repository is produced by a **pinned, released DQL version** (see `dql.json`), runs against the benchmark publisher's own data and grader, and ships with the recorded AI calls needed to replay it without an API key.

## What we measure

| Benchmark | Question it answers | Status |
|---|---|---|
| [Spider 2.0-DBT](spider2-dbt/) | Can an agent finish a real, half-built dbt project so its tables match a golden database? | harness in progress |
| [dbt Labs semantic-layer bench + data.world insurance set](dbt-sl-bench/) | How much does modeling (domains, relationships, certified joins, semantic layer, skills) add over raw AI-written SQL? | planned |

## How results are reported

See [docs/methodology.md](docs/methodology.md). In short:

1. **Paired comparisons only.** Two conditions, the same questions, the same grader, an exact McNemar test and Wilson 95% confidence intervals. Never a lone percentage.
2. **Provenance.** Only runs whose AI calls were recorded from a real provider count. Every report carries the benchmark repo commit, the DQL version and where it came from, the model, and a content fingerprint.
3. **The answer key is audited.** Public gold sets contain many wrong answers. Every disputed case is logged with a reason, and accuracy is reported on the full set and on the accepted subset.
4. **Trust labels are scored.** A wrong answer that DQL labels `certified` is counted separately; the target is zero.
5. **Cost and latency sit beside accuracy.** Cost is reported only when measured, never estimated.

## Layout

```
dql.json              pinned DQL version (npm release, or a local build while developing)
pricing.json          dated model list prices; null means "not measured"
lib/                  shared helpers: DQL resolver, runtime launcher, identity stamp, row matching, statistics, gold audit
paired/               paired comparison scorer
spider2-dbt/          Spider 2.0-DBT adapter
dbt-sl-bench/         dbt Labs + data.world adapter
docs/                 methodology and published write-ups
```

Downloaded benchmark data, working copies, Python environments and DuckDB files are never committed (see `.gitignore`).

## Quick start

```bash
npm test                      # unit tests for the scorer and helpers
npm run dql:install           # installs the DQL version pinned in dql.json into .dql-cli/
npm run compare -- a.json b.json   # paired comparison of two eval reports
```

## Using a local DQL build while developing

Set `"source": "local"` and `"path"` in `dql.json` to a DQL checkout's `apps/cli/dist/index.js`, or export `DQL_CLI=/path/to/apps/cli/dist/index.js`. Reports record the source, and a report made from a local build is never published.

## License

Code in this repository is Apache-2.0. Benchmark datasets are downloaded from their publishers and remain under their own licenses; they are not redistributed here.

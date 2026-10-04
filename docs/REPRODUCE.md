# Reproducing the insurance results

There are three levels of reproduction, from minutes to days.

## 1. Check the numbers from the committed reports (minutes, no model calls)

Every run behind the paper is in `results/insurance/<run>/<condition>/<set>/report.json`. Each answer
records the question, the SQL, the trust label (`answer.trustState`), whether it matched the reference
rows (`executionMatched`) or stopped correctly on an unanswerable question (`passed`), the model calls
and the timing. `identity` records the DQL build, model identifier, CLI version and run settings.

| Run id | Model | Contents |
|---|---|---|
| `fl-opus`, `fl-sonnet55`, `fl-sonnet`, `fl-qwen`, `fl-luna`, `fl-sol`, `fl-terra` | Claude Opus 5.5, Claude Sonnet 5.5, Claude Sonnet 5, Qwen 3.8 27B, GPT-6 Luna, GPT-6 Sol, GPT-5.6 Terra | one-shot SQL (`baseline-full`, `baseline-small`) and DQL levels L0–WB on the development set (`all`) and set 3 |
| `ag-opus`, `ag-sonnet55` | Claude Opus 5.5, Claude Sonnet 5.5 | agent baseline (`agent-ddl`) on set 3 |
| `fl4-sonnet55`, `ag4-sonnet55`, `ag4m-sonnet55` | Claude Sonnet 5.5 | set 4: added on release day |

Reports flagged `"invalid": true` are kept for the record but excluded from every figure. LB and WB
count only on DQL build `627009a1`.

## 2. Recompute the statistics and the paper (minutes, needs the run archive)

The strict/lenient re-grade reads the rows each DQL answer showed from its run store
(`project/.dql/local/agent-runs.sqlite`) and re-runs baseline SQL on a read-only copy of the warehouse.
Those stores and project copies are in the release archive (see the release checklist), not in git.
Extract it to `work/insurance/runs/`, build the warehouses (step 3, `build.mjs` only), then:

```bash
python3 analysis/insurance-2026-09-29/paper/stats_v2/stats_v2.py   # writes stats_v2.json / .md
python3 analysis/insurance-2026-09-29/paper/paper_numbers.py > analysis/insurance-2026-09-29/paper/paper_numbers.json
python3 analysis/insurance-2026-09-29/paper/paper_docx.py           # writes paper.docx, fig1, fig2
```

`stats_v2.py` uses only the Python standard library plus the DuckDB helper in `lib/`; the bootstrap
seed is 20260930, so the output is identical on every run.

## 3. Re-run a model's round from scratch (hours to days, model calls)

1. Install: Node 20+, Python 3.11+, then `./scripts/setup-python.sh` (dbt 1.9 + DuckDB adapter,
   MetricFlow) and `npm run connectors:install`.
2. Fetch the data at pinned commits: `./insurance/download.sh`.
3. Build DQL twice from [duckcode-ai/dql](https://github.com/duckcode-ai-labs/dql): at `49c0e1cb` (all
   levels but LB and WB) and at `627009a1` (LB and WB). Both are development builds of 1.17.3.
4. Run a round, for example Claude Sonnet 5.5 through the Claude Code CLI:

```bash
DQL_CLI_MAIN=/path/to/dql-49c0e1cb/apps/cli/dist/index.js \
DQL_CLI_FIXED=/path/to/dql-627009a1/apps/cli/dist/index.js \
scripts/run-insurance-round.sh my-sonnet55 claude-code claude-sonnet-5-5
```

For GPT models through the Codex CLI, pass the reasoning level and an isolated Codex home (no
`AGENTS.md`, `[features] memories = false`, no plugins or MCP servers; `run.mjs` refuses any other):

```bash
CODEX_BENCH_HOME=$HOME/.codex-bench DQL_AGENT_DEADLINE_SCALE=20 DQL_SUBSCRIPTION_CLI_TIMEOUT_MS=300000 \
DQL_CLI_MAIN=... DQL_CLI_FIXED=... scripts/run-insurance-round.sh my-sol codex gpt-6-sol medium
```

Agent baselines:

```bash
node insurance/baseline-agent.mjs --run my-agent --set heldout-3 --context ddl --provider claude-code --model claude-sonnet-5-5 --effort high
node insurance/baseline-agent.mjs --run my-agent-m --set heldout-3 --context modeling --level W2 --provider claude-code --model claude-sonnet-5-5 --effort high
```

Every question runs in a new conversation on a fresh copy of the project with DQL's caches, memory and
run history removed. Expect differences of a few questions between runs of the same model
(earlier repeats moved single levels by up to 4 of 40).

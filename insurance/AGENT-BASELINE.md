# Agentic text-to-SQL baseline (A)

The one-shot baseline **P** (`baseline-text2sql.mjs`) gives the model the schema and one chance to write SQL. A reader can fairly ask whether DQL beats only that weak opponent, or also a model that can explore the database itself. **A** is that opponent: the same model, the same warehouse and no DQL, but it can list tables, look at columns and rows, run queries, see its errors and try again before it commits to an answer.

Code: [`baseline-agent.mjs`](baseline-agent.mjs) (loop, providers, scoring, report) and [`agent_tools.py`](agent_tools.py) (the database tools). Tests: [`baseline-agent.test.mjs`](baseline-agent.test.mjs), with the scripted fixture [`fixtures/agent-fake-transcripts.json`](fixtures/agent-fake-transcripts.json).

**Status:** built and tested with a scripted fake provider only. No model has been run through it.

## Design goals

1. **The same inputs as DQL's L0 and W0.** A reads the warehouse of the level it is given (`--level L0` or `W0`). Before each run it copies that level's `acme_insurance.duckdb` into the run folder and opens the copy read-only. There is no business layer and no DQL. `--context` sets what A is told before it starts:
   - `none`: the question only. A finds everything else with its tools, as DQL W0 finds it from the warehouse catalog.
   - `ddl` (the default): the CREATE TABLE text for every relation in `main`. This is byte-for-byte P's `--ddl full` text (`work/insurance/ACME_full.ddl`, checked when this was built), so A and P start from the same page.
   - `dbt-docs`: what L0's dbt project documents, read as DQL L0 reads it (`target/manifest.json` and `catalog.json`). For each model it gives the description, the model it is built from, and the columns with their types and descriptions. It needs `--level L0`. **This dbt project ships no schema yml**, so every description is empty. The text says `description: (none)` rather than hiding the gap. On this dataset `dbt-docs` therefore adds only model lineage to `ddl`. It is kept because the same harness applies unchanged to a documented project.
2. **The loop.** A can call four tools, then must finish:
   - `list_tables`: every table and view in `main`, with its type and column count.
   - `describe_table(table)`: the columns, types and nullability.
   - `sample_rows(table, n)`: at most 5 rows.
   - `run_sql(sql)`: runs any read-only statement and shows at most 50 rows. Longer results are marked as truncated. Each cell is cut at 200 characters, and a statement is stopped after 30 seconds.
   - To finish, A sends `final_sql(sql)`, or `cannot_answer(reason)`. A reply that starts with `CANNOT_ANSWER: <reason>` also counts as `cannot_answer`.
   - The harness test-runs `final_sql` under the same limits first. If the SQL fails and replies remain, A is shown the error and may correct it, as a human analyst would. On the last reply, a failing final query stands and is graded as SQL that did not run.
   - A reply that is not one valid action is sent back as an error. It uses up a turn and is counted in `protocolErrors`.
   - **Budgets** (all are flags):
     - `--max-turns 12`: model calls per question.
     - `--max-tool-calls 20`: tools actually executed. Once they are spent, A is told so and must finish.
     - `--max-wall-s 900`: checked before each call.
     - `--call-timeout-s 300`: one model call, as in P.
     - `--statement-timeout-s 30`.

     Every turn tells A how many replies and tool calls it has left. The last turn says it must finish. A question that runs out of budget gets **no answer**. It is scored wrong on an answerable set and is **not** a correct stop on an unanswerable set: running out of budget is not a decision.
3. **Providers.** The loop is written against one interface: `provider.turn(state) → reply`. The providers differ in how they carry the conversation:
   - **Subscription CLIs** (`claude-code`, `codex`) are single-shot, so they use a **text protocol**. The model replies with one JSON action per turn, the harness executes it, and the next turn is a **fresh call carrying the whole transcript so far**: fixed instructions, question, context, then every earlier reply and its result. **Input cost therefore grows with every turn, roughly with the square of the number of turns.** There is no conversation state for the CLI to cache or reuse.
     - Claude uses exactly P's invocation: an empty temporary cwd, `--tools ''`, `--max-turns 1`, `--strict-mcp-config` and `--no-session-persistence`, with `--model` and `--effort`.
     - Codex also uses P's invocation: `exec -`, `--sandbox read-only`, `--ephemeral` and an empty `--cd`, with `-c model_reasoning_effort="<effort>"`. `--codex-home <dir>` goes through `run.mjs`'s `useIsolatedCodexHome`, which means no AGENTS.md, plugins, MCP or memories.
   - `ollama` uses the same text protocol, sent as alternating chat messages. The context window is sized to the transcript, as in P.
   - `anthropic` uses Messages API **native tool use** behind the same interface: the six actions become six tools, and results go back as `tool_result` blocks. **It has not been run.** Treat it as untested until a first checkpoint run.
   - `fake` returns scripted replies for tests.
4. **Scoring and report.** Grading is the same as P's:
   - The final SQL is run in full on the warehouse copy with `lib/duckdb_query.py`.
   - Rows are compared with `lib/row-match.mjs`, with extra columns allowed.
   - `cannot_answer` is right only on an unanswerable set (`unanswerable`, `heldout-N-unanswerable`), and wrong on an answerable one.

   `report.json` has P's shape and identity fields:
   - The condition is `agent-<context>`, and `run.layer` is the same name.
   - `run.warehouse` is the level.
   - `method` records the full system prompt, its SHA-256, a hash of the context text and the limits.

   Each result keeps P's fields (`passed`, `executionMatched`, `durationMs`, `providerDispatchCount` = model calls, `kind`, `answer.trustState`, `usage`, `costUsd`) and adds:
   - `turns`, `toolCalls`, `sqlStatementsRun` (`run_sql` calls plus final-query checks), `protocolErrors`, `totalMs`, `modelMs`, `finalSql` and `stop` (`final_sql`, `cannot_answer`, `turns` or `wall`).

   `score.mjs`, `repeats.mjs` and `paired/paired-compare.mjs` read the report unchanged. This was checked on the fake run.
5. **Resume after refusals, as P does.**
   - Every finished question is written to `transcripts.json` at once, with every reply, action and result.
   - If a provider call fails (a usage or rate limit, sign-in, timeout or empty reply), the run stops with **exit code 3** and writes no report. The attempt is logged to `refused-attempts.jsonl`.
   - Running the same command again keeps the finished questions and asks the refused question **again from its first turn**. A partial conversation is never continued.
   - `transcripts.json` stores the run's settings (provider, model, effort, context, level, limits and prompt hash). A resume with different settings is refused.
   - `--replay` grades the saved transcripts again without calling anyone.
6. **Isolation.**
   - Each question is a new conversation. Nothing carries over between questions: no memory, no hints, no earlier SQL and no results.
   - The model sees only the fixed system prompt below, the question (plus the `--context` text) and what its own actions returned.
   - It never sees the correct SQL, the correct rows, the question set, other questions or anything from DQL. The warehouse copy is deleted when the run ends.

## The system prompt (text protocol, default limits)

This is fixed for every question of a run. The native-tool version replaces the action list with the tool list and drops the last rule.

```
You are a data analyst. You answer one business question by writing one SQL query against a DuckDB database. You cannot see the database: you explore it through the actions below, and after each reply you are shown what your action returned.

Actions (reply with exactly one JSON object per reply, and nothing else):
{"action": "list_tables"}                             every table and view you can query
{"action": "describe_table", "table": "<name>"}       the table's columns and types
{"action": "sample_rows", "table": "<name>", "n": 3}  up to 5 rows of the table
{"action": "run_sql", "sql": "<query>"}               run one read-only query; you see at most 50 rows
Finish with exactly one of:
{"action": "final_sql", "sql": "<query>"}             the query whose full result answers the question
{"action": "cannot_answer", "reason": "<why>"}        the data does not hold what the question needs
(A reply that starts with CANNOT_ANSWER: <reason> also finishes with cannot_answer.)

Rules:
- The database is DuckDB and read-only.
- Your final query's full result is the answer, and it is checked by its values: return the columns and rows the question asks for, not a preview. The 50-row limit applies only to what you are shown while exploring.
- If a query fails, you are shown the error and may try again. If your final query fails to run, you are shown the error and may send a corrected final_sql.
- Use cannot_answer only when the data does not hold what the question needs (a missing measure, attribute, entity or period). Do not substitute a different measure.
- You have at most 12 replies and 20 tool calls for this question. A question left without final_sql or cannot_answer when they run out gets no answer.
- Reply with one JSON object only: no prose, no Markdown.
```

The first user message is `Question: <question>`, followed for `ddl` and `dbt-docs` by `Schema you were given:` and the context text. Each later turn appends `Your reply k: <reply>` / `Result: <JSON>` pairs, then a line such as `Reply 4 of 12; tool calls left: 17.`

**The prompt is frozen before any scored run.** It was written without reading any benchmark question except the declared development questions, and it names no insurance concept. A change to it after a held-out run spends that set, exactly as a DQL change does.

## Fairness

**Why this is the strongest reasonable opponent without DQL.** It is how a capable general-purpose agent answers a data question today, in the way Claude Code or Codex does with a database connection:
- It explores the schema and looks at real values.
- It runs trial queries and recovers from its own errors.
- It verifies that the final query runs.
- It may decline.

It runs on the same frontier model and effort as DQL. Its budgets are generous: 12 calls is more than DQL's typical Ask run.

**What A gets that P does not:**
- exploration: sample values, which reveal code values such as `AG`, date encodings and empty tables;
- retries after errors;
- a checked final query;
- the option to stop.

**What A lacks compared with DQL:**
- no governed definitions: no L1 modeling, no certified joins or metrics, no skills;
- no business glossary;
- no trust labels.

A is also not told which tables a concept lives in, beyond what it can find. That is the gap DQL's layers are meant to close. A's win on L0/W0-style exploration is A's own.

**What A sees of the data.** A sees result rows, at most 50 per query. DQL's default sends the model no result rows. The report's `egress` field is absent for A, and the paper says so: A's accuracy depends on showing data to the model.

**Trust.** A has no trust labels, so every answer is `trustState: none`. `paired-compare.mjs` counts every wrong answer A gives as "wrong, shown as trustworthy" (unlabelled). Report it with its denominator, for example "A: 14 of 41 answers wrong with no warning".

**Codex's sandbox can read files.** `--sandbox read-only` stops writes, not reads, so in principle Codex could open a file on disk instead of using A's actions. P's Codex runs have the same exposure. A keeps the last 2 kB of Codex's own log for each turn (`steps[].codexLogTail` in `transcripts.json`), so an audit can confirm that no command ran. Claude runs with `--tools ''` and has no such path.

## Cost and latency (estimates to be replaced by measurement)

The data is tiny, so tool results are small:
- `list_tables` is about 1.5 kB and `describe_table` 0.2–0.8 kB.
- A 50-row result is 1–3 kB.
- The system prompt is 1.8 kB and the DDL 5.8 kB.

A typical question should take 4–8 model calls: list or describe, one or two samples or probes, then the final query. Multi-table loss questions will take more.

| | P (one-shot) | A, `--context ddl` |
|---|---|---|
| Model calls per question | 1 | ~4–8 (cap 12) |
| Input tokens per question | ~2k | ~12–25k (transcript re-sent each turn) |
| Claude Code, Opus 5.5 | 4–9 s | ~0.5–2 min (CLI start ~3 s per call) |
| Codex, gpt-6-sol medium | 6–18 s | ~1.5–4 min |
| Ollama, qwen3.8:27b (local) | 5–150 s | ~3–15 min |
| API cost, Opus 5 list price | ~$0.02 | ~$0.10–0.20 (reasoning output extra) |

A 41-question run will take about 30–80 minutes on Claude Code and about 1.5–3 hours on Codex. A run on a subscription uses about 5–8 times the calls of P, so expect usage limits: resume handles them.

## How results are reported

A appears next to P and every DQL level, on the same questions, runs and model:
- **Accuracy** with a Wilson 95% interval.
- **Paired exact McNemar** per question against P and against each DQL level (`node paired/paired-compare.mjs P.json A.json L0.json … L3.json`). The paper states the discordant counts, not only p.
- **Stops:** stopped correctly on the unanswerable sets, and stopped wrongly (`cannot_answer` or out of budget) on answerable ones.
- **Trust:** wrong answers shown with no warning (all of A's wrong answers), next to DQL's wrong-certified and wrong-governed counts, each with its denominator.
- **Cost and latency:** p50 and p95 time, model calls per question, and tokens and cost where the API route measures them. On a subscription route, tokens are reported as the CLI reports them and cost is not claimed.
- **Stability:** three repeats as separate run ids, read with `repeats.mjs`.
- **Held-out:** the sealed set 3 decides, with totals only. A is not tuned on the headline set either: only the two declared development questions were used, and only by the fake fixture.

## Running it

```sh
# Claude Code subscription, Opus 5.5, the same effort as the P run it is paired with (fl-opus: high)
node insurance/baseline-agent.mjs --run ag-opus-1 --set all --context ddl --provider claude-code --model claude-opus-5-5 --effort high
node insurance/baseline-agent.mjs --run ag-opus-1 --set heldout-3 --context ddl --provider claude-code --model claude-opus-5-5 --effort high
node insurance/baseline-agent.mjs --run ag-opus-1 --set heldout-3-unanswerable --context ddl --provider claude-code --model claude-opus-5-5 --effort high

# Codex (ChatGPT subscription), gpt-6-sol at medium, from the isolated benchmark home
node insurance/baseline-agent.mjs --run ag-sol-1 --set all --context ddl --provider codex --model gpt-6-sol --effort medium --codex-home ~/.codex-bench

# Local Ollama, qwen3.8:27b: accuracy, not speed, so longer limits
node insurance/baseline-agent.mjs --run ag-qwen-1 --set heldout-3 --context ddl --provider ollama --model qwen3.8:27b --call-timeout-s 900 --max-wall-s 3600

# Variants: warehouse only (as W0) or dbt docs (as L0)
node insurance/baseline-agent.mjs --run ag-opus-1 --set all --context none --level W0 --provider claude-code --model claude-opus-5-5 --effort high
node insurance/baseline-agent.mjs --run ag-opus-1 --set all --context dbt-docs --level L0 --provider claude-code --model claude-opus-5-5 --effort high

# After exit code 3 (a usage limit), wait and run the same command again. Then score:
node insurance/score.mjs work/insurance/runs/ag-opus-1/agent-ddl/all/report.json
```

Output goes to `work/insurance/runs/<run>/agent-<context>/<set>/`: `report.json`, `transcripts.json` and, if a call was refused, `refused-attempts.jsonl`. `--out <dir>` overrides the folder, and the tests use it. Run the levels (`--level`) of one context under different run ids: a folder records one level, and a resume with another level is refused.

## Testing without a model

```sh
node --test insurance/*.test.mjs
node insurance/baseline-agent.mjs --run t --set dev --provider fake --fixture insurance/fixtures/agent-fake-transcripts.json --out /tmp/agent-t
```

The fake provider renders the same text prompt the CLIs get and keeps it in the transcript. The tests cover:
- reading replies: fences, surrounding prose, CANNOT_ANSWER and invalid actions;
- native tool-call mapping and message pairing;
- the tools on a read-only copy: the 50-row cap, unknown tables and refused writes;
- the turn and tool budgets, including the last-turn notice;
- scoring rules for stops and spent budgets;
- the dbt-docs text;
- end to end on the two development questions: a scripted refusal (exit 3), a resume that re-asks the refused question from turn 1, a transcript that carries earlier errors and the DDL, grading, the report shape, replay, and refusal of a resume with other settings;
- end to end on one unanswerable question on W0 with no context.

The end-to-end tests skip on a clone without `work/`.

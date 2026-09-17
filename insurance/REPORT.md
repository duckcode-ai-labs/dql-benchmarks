# Insurance benchmark: how we test DQL's Ask, step by step

*Living document. Every step we take is written here as we take it, including what went wrong. Last updated 2026-09-16.*

---

## The short version

**Question we are answering.** When a business user asks a question in plain English, how often does DQL's Ask return the right rows? And how much does each DQL layer add: modeling, the semantic layer, skills?

**Where we test it.** On a public benchmark that two other teams already used, so our numbers sit next to theirs:

- **data.world (2023):** 43 insurance questions. The paper showed GPT-4 got 16.7% right writing SQL on raw tables, and 54.2% with a knowledge graph.
- **dbt Labs (2026):** the same questions and data, rebuilt as a dbt project. They ran 11 of the questions many times per model. For Claude Sonnet 5, text-to-SQL scored 78–91% and the semantic layer 87–95%, depending on reasoning effort.

**How we test it.** We use the setup a DQL customer would have:

1. Build dbt Labs' own dbt project into a DuckDB warehouse.
2. Run `dql init` on it.
3. Ask each question through Ask.
4. Compare the rows Ask returns with the rows of the benchmark's correct SQL.

We repeat this on four copies of the project. Each copy adds one DQL layer:

| Layer | What the project has |
|---|---|
| L0 | the dbt project only |
| L1 | + DQL modeling (domain, entities, relationships, certified joins) |
| L2 | + the dbt semantic layer (MetricFlow) |
| L3 | + DQL skills (business definitions) |

**Honesty rules we hold ourselves to**
- DQL is not changed for this benchmark.
- Modeling and skills are written from documentation, never from the questions.
- The correct answers live outside the project Ask works in.
- Every AI call is recorded, so the run can be replayed.
- We report the questions we looked at while building, separately from the headline numbers.

**Where we are** (see [Progress](#progress)): the warehouse is built and verified against dbt Labs' own graded answers. All 43 correct answers run. The harness works end to end. The first full L0 run stopped on a timeout, and tracing it found a DQL defect: since September 5, Ask has not told the AI model how hard to think, so on the Claude subscription one step took 80–120 seconds. The fix is written and is being checked against DQL's own golden question suites before any benchmark run uses it (see [Step 8](#step-8-why-the-first-run-timed-out-and-the-dql-defect-it-found)).

---

## Progress

| # | Step | State |
|---|---|---|
| 1 | Answer scoring inside `dql agent eval` (DQL core repo) | done, DQL commit `62258981` (local, not released) |
| 2 | Download the sources, pinned | done |
| 3 | Read the questions and pick the question set | done |
| 4 | Build the dbt project into DuckDB and verify it | done |
| 5 | Compute and check the correct answers | done |
| 6 | Audit the answer key | first pass done; owner review pending |
| 7 | Harness: ask, score, record, stamp identity | done; smoke-tested on 1 declared dev question |
| 8 | First L0 run | stopped on a timeout; cause traced to a DQL defect (Step 8) |
| 8a | Fix the defect in DQL and re-check DQL's golden suites | done: DQL `0a23c4d9`; golden jaffle 83/83, NBA 25/25, office 8/8 on fresh live recordings |
| 8b | L0 run on the fixed build, 41 headline questions | done: 8/41 right (Step 9) |
| 9 | Write L1 modeling and L3 skills from documentation only | to do (by a separate agent that has not seen the questions) |
| 10 | L1, L2, L3 runs; repeats; paired comparison | to do |
| 11 | Same runs on the Anthropic API (with cost), then other model families | to do |

---

## Step 1: teaching `dql agent eval` to grade against a benchmark

DQL already had a batch evaluator, `dql agent eval`. It could only compare an answer with rows written in DQL's own column names. Benchmarks name their columns their own way: dbt Labs' `NoOfPolicies` is Ask's `policy_count`. So we added a comparator that matches on values:

- column names and column order are ignored;
- numbers are equal within 1e-6;
- a date equals a midnight timestamp of the same day;
- duplicate rows must appear the same number of times;
- row order is ignored unless the question asks for an order;
- optionally, the answer may carry extra columns, as long as every correct column is present. This is the rule dbt Labs' grader uses, and we use it too.

Each graded answer also records:
- the trust label Ask showed (`certified`, `governed` or `review_required`);
- which path produced the answer;
- the proofs, the SQL and the row count.

A refusal is never counted as a match.

This change affects only how answers are graded, not how Ask answers. (Step 8 describes the one later DQL change that does affect Ask, and why.) It is commit `62258981` in the DQL repo (`apps/cli/src/commands/eval-row-match.ts`), with 10 new unit tests; the CLI suite passes (1,388 tests).

## Step 2: the sources

| Source | What we use from it | Commit |
|---|---|---|
| [datadotworld/cwd-benchmark-data](https://github.com/datadotworld/cwd-benchmark-data) | the original question file, schema (DDL) and ontology | `0b75eb6` |
| [dbt-labs/dbt-llm-sl-bench](https://github.com/dbt-labs/dbt-llm-sl-bench) | the corrected question file, the 11-question selection, the grader's rules, the published graded answers | `a29f242` |
| [dbt-labs/semantic-layer-llm-benchmarking](https://github.com/dbt-labs/semantic-layer-llm-benchmarking) | the dbt project: 29 seed CSVs, 29 models, MetricFlow semantic models | `ac20c92` (main) |

All three are Apache-2.0. `insurance/download.sh` fetches exactly these commits. Nothing from them is copied into this repository.

## Step 3: the questions

Both question files are RDF (Turtle). Each question is stored with its correct SQL, and its title starts with the paper's complexity quadrant. For example, `HQLS` means high question complexity, low schema complexity. We wrote a small reader (`lib/turtle.mjs`) instead of adding an RDF library. It refuses anything outside the simple format these files use. `insurance/questions.mjs` extracts the questions the same way dbt Labs' loader does.

**The two files differ.** We compared them:

- data.world's file has 45 SQL entries for 44 questions. dbt Labs' file has 43, which matches the paper's count.
- dbt Labs dropped one duplicate and the question "Return all the claims by claim number that were closed in 2019", which the paper also leaves out.
- dbt Labs **fixed two correct answers:**
  - "average time to settle a claim" had its date difference reversed;
  - "total premiums a policy holder has paid, by policy number" returned an extra policy-holder column.

**Decision:** we use dbt Labs' 43-question file. It is the corrected version, and dbt Labs' published numbers were graded with it.

The 43 questions split into LQLS 12, HQLS 11, LQHS 10, HQHS 10 (L/H = low/high, Q = question complexity, S = schema complexity). All 11 of dbt Labs' questions (listed in their `config/base.py`) are in the file; we report them as their own set.

## Step 4: building the warehouse

`insurance/build.mjs --layer L0` does the following, and records every step in `work/insurance/build-L0.json`:

1. **Copies only the dbt project:** `dbt_project.yml`, `models/`, the seed CSVs, and the empty `macros/`, `analyses/`, `snapshots/`, `tests/` folders. Everything else is left out on purpose:
   - `ACME_Insurance/investigation/` and `hex_notebook/` contain the questions with their correct SQL. If they were in the project, Ask could find the answers.
   - `DDL/`, `ontology/` and the R2RML mapping are schema documents. They are inputs for writing L1, not part of a dbt project.
   - For L0, `models/omg_semantics/` (the MetricFlow definitions) is removed as well; it returns in L2.
2. **Writes a dbt profile** pointing at `acme_insurance.duckdb` inside the project.
3. **Runs** `dbt seed`, `dbt run` and `dbt docs generate` (dbt-core 1.9.11, dbt-duckdb 1.9.6, DuckDB 1.5.5).
4. **Checks row counts.** All 29 seed tables have exactly the rows of their CSV files, and all 29 models have the rows of their seed.
5. **Runs `dql init`.** It detected the dbt project and the DuckDB file on its own (`connections.default = duckdb`, `dbt.manifestPath = target/manifest.json`, `modeling.mode = dbt-first`). The DuckDB driver DQL loads (duckdb 1.1.3, the version DQL's CI uses) is linked into `.dql/connectors`.

**Deviation 1 (numeric type).** `dbt seed` first failed: `Policy.Policy_Number` holds values like 31003000336, too large for the 32-bit integer dbt-duckdb picked from a sample of rows. dbt Labs built on a cloud warehouse, where numbers are wider. The build now scans every CSV and declares any whole-number column outside the 32-bit range as `bigint` in the project's seed config. The rule looks only at the data. It changed one column.

**The data is very small.** The benchmark measures schema difficulty, not data volume: 2 policies, 2 claims, 6 premium rows. Most correct answers have 1–6 rows. The drawback is that a wrong query can return the right numbers by chance: "how many policies" and "how many claims" both answer 2. The value-based grader cannot tell those apart, and neither can dbt Labs' grader. We will add a second check that reviews which tables each answer used, and report both.

## Step 5: the correct answers

The build runs each question's correct SQL against the finished warehouse (read-only, file access off). It saves the rows to `work/insurance/gold/answers.json`, outside every DQL project.

**Deviation 2 (SQL dialect).** One correct query, "average time to settle a claim by policy number", uses Snowflake's `DATEDIFF("day", …)`. DuckDB reads `"day"` as a column name. The build rewrites it to `DATEDIFF('day', …)`, which means the same thing. It records the published SQL, the SQL it ran and why (`DIALECT_PORTS` in `build.mjs`). After this, **all 43 correct answers run and none is empty.**

**Cross-check against dbt Labs' own grading** (`insurance/checks/publisher-answers.mjs`). dbt Labs published every text-to-SQL answer their runs produced, with their grader's verdict. We ran each distinct answer on our warehouse and graded it with our rules:

| dbt Labs' verdict | agrees with ours | disagrees | does not run on DuckDB |
|---|---|---|---|
| correct | 232 | 0 | 609 |
| wrong | 303 | 4 | 263 |

Every answer dbt Labs marked correct that runs on DuckDB is also correct on our warehouse. The four disagreements are all old GPT-4 runs of one question, graded against the earlier answer key that had the extra policy-holder column (their stored error reads `['PARTY_IDENTIFIER'] not in index`). Our build and our grader therefore agree with dbt Labs on every answer graded with the current key. The "does not run" answers use Snowflake-only syntax and say nothing about our build.

## Step 6: auditing the answer key

Public answer keys contain mistakes, so every question gets a line in `insurance/gold-audit.jsonl`. A first pass read all 43 questions against their correct SQL and results:

- **43 accepted.** No answer looked wrong.
- **6 accepted with a note about ambiguity:**
  - Four questions ask for "premium amount paid" next to claims. The correct answer uses the premium of the coverage year the claim was made against (20,000), not the policy's total premium (86,000).
  - Two loss-ratio questions divide by that same coverage-year premium.

  Other readings are reasonable, and we will report how often Ask chose one.
- One correct query labels a policy-holder column "AgentID". Labels are not graded, so it does not matter.

The first pass was done by the AI assistant building this harness. **The owner's review is still pending**, and the audit file says so.

## Step 7: the harness

`insurance/run.mjs --layer L0 --set all --run <id>`:

1. Picks the questions:
   - `all` is the 43 minus declared development questions;
   - `dbt-labs` is the 11;
   - `dev` is the declared development questions only.

   It refuses to start if any question lacks an audit line or its correct answer failed.
2. Writes the eval file (question, correct rows, correct SQL) into the run folder, outside the project.
3. Selects the AI provider in the project's own settings file. For the first runs this is the **Claude subscription through the `claude` command** with model **`claude-sonnet-5`**. No API key is involved, and nothing is copied from anyone's workspace.
4. Starts a DQL server on the project, recording every AI call.
5. Runs `dql agent eval --via runtime` and saves DQL's JSON report, stamped with:
   - **identity:** this repo's commit, the DQL version and build commit, model, data hash, dbt/DuckDB versions;
   - **provenance:** every recorded AI call must come from a real provider.

**Development question (declared).** One question was used to prove the pipe works before any scored run: "Return all the policies we have by policy number, effective date and expiration date?" It is listed in `insurance/dev-questions.json`, excluded from the headline sets and reported separately. On L0, Ask answered it correctly:
- 23 seconds, 2 AI calls;
- labelled `review_required` (the exploratory path, which is expected when a project has no modeling).

**Why the answer-key audit changes who writes L1 and L3.** Auditing meant reading every question and its correct SQL. Whoever did that cannot also write the modeling and skills without the questions leaking in. So L1 and L3 will be written by a separate agent. It will see only the dbt project, the published DDL and the ontology, and will be told not to open the question files, the notebook export or the answers. Its instructions and the files it read will be published here.

## Step 8: why the first run timed out, and the DQL defect it found

**What happened.** The first L0 run (42 questions) stopped on its second scored question. Its trace showed:
1. DQL's first AI call, which reads the question, got no reply within DQL's 90-second limit for a `claude` CLI call.
2. DQL retried that call.
3. After 120 seconds, `dql agent eval`'s own per-question limit stopped the whole suite.

**Two harness fixes** (they change grading, not Ask):
- `dql agent eval` now records a question that gets no answer as failed, with the reason, and carries on. It is never counted as a correct answer or as a refusal (DQL commit `afa6f908`). The harness allows 15 minutes per question, so only Ask's own limits apply.
- Each run now works on a fresh copy of the project, so nothing a run leaves in DQL's local state can reach another run.

**Diagnosis.** We ran the question that timed out three more times with DQL's CLI debug output on. We then replayed the exact CLI call outside DQL. Because we looked at its runs, this question is now a declared development question. The debug numbers:

| | first call | retry | result |
|---|---|---|---|
| debug run 1 | stopped at 90 s (84 s of model time, 8.8k output tokens, 3 turns) | stopped at 90 s | no answer after 182 s |
| debug run 2 | stopped at 90 s | 88 s, 8.3k output tokens, 3 turns | no answer after 181 s |
| debug run 3 | stopped at 90 s (75 s of model time, 4 turns) | 82 s, 3 turns | an answer after 184 s |

In the same questions, the AI calls that wrote SQL took 1.7–2.9 s. Direct `claude` calls with a one-word prompt took 2–3 s. So the CLI and the subscription were healthy; only this step was slow.

**Cause 1 (DQL defect): no reasoning effort was sent.** DQL is designed to tell the model how hard to think: `medium` for an Ask answer, `high` for research, one level up on a repair, capped by the provider's Settings. That wiring was deleted on 2026-09-05, when DQL's previous Ask runtime was removed (commit `b3e297ee`). Since then, every Ask call has run at the provider's default effort, on every provider. On the Claude subscription this meant long hidden thinking: 8–12k output tokens around an answer of about 300 tokens. The same captured call, replayed with an explicit effort:

| effort | time | output tokens |
|---|---|---|
| none sent (DQL today) | 82–122 s | 8.3k–11.9k |
| `medium` | 27 s | 2.6k |
| `low` | 20 s | 1.6k |

**Cause 2 (in the Claude Code CLI, outside DQL): a wasted first turn.** Every time, the model's first structured answer came back wrapped as `{"$PARAMETER_VALUE": "<the JSON as a string>"}`. The CLI's schema check rejects that and asks again, which costs a full extra turn at every effort level. We will report it to the Claude Code team; DQL cannot change it.

**The fix** (DQL, not yet committed at the time of writing): the server again attaches a reasoning effort to every Ask AI call, using the rule above. It does not look at any benchmark question. Tests check the rule, the Settings cap, and that a real Ask request sends it; the end-to-end test fails without the fix.

**Why DQL's golden suites must be re-recorded.** DQL's own golden question suites replay recorded AI calls, and a recording's key includes the effort. The 69 golden cases (jaffle, NBA, office) are being re-recorded live with Claude Sonnet 5 through the subscription. Their pass rate at the restored effort decides whether the fix is accepted. The fix changes how Ask behaves, so it will be released as its own DQL version, and benchmark numbers will come from that version.

**Other settings pinned during the diagnosis**
- **Embeddings.** When a machine runs Ollama, DQL switches to Ollama embeddings on its own, in the background after the server starts. Results could then depend on the machine and on timing. Scored runs set `DQL_EMBEDDINGS_AUTODETECT=off`, which is what a machine without Ollama gets, and record it.
- **Starter content.** `dql init` adds a starter business term ("Customer") and four starter skills (block authoring, domain rules, metrics glossary, SQL conventions) to every project. L0 keeps them, because a new customer project has them too.
- **Timing we saw.** "How many claims do we have?" stays in the headline set. We saw its timing while diagnosing (16 s, 2 AI calls) but not its answer; `dev-questions.json` records this.

## Step 9: results

### L0 (dbt project only), Claude subscription, run `sub-L0-r2`

Full scorecard: [results/L0-subscription-r2.md](results/L0-subscription-r2.md). This run is **not publishable**: DQL came from the development build (`d0c91022`), and the harness had an uncommitted documentation edit when it started. It is one run; repeats come next.

| | Right | Accuracy (95% CI) |
|---|---:|---|
| All 41 headline questions | 8 | 19.5% (10.2–34.0%) |
| dbt Labs' 11 | 2 | 18.2% (5.1–47.7%) |
| Low question, low schema complexity | 5/10 | 50% |
| Low question, high schema complexity | 1/10 | 10% |
| High question, low schema complexity | 2/11 | 18% |
| High question, high schema complexity | 0/10 | 0% |

- **Where this sits.** It is close to the paper's GPT-4 result on the raw tables (16.7%). It is far below dbt Labs' published Sonnet 5 text-to-SQL results (78–91%), but those runs gave the model a hand-written schema plus three extra models dbt Labs built for the questions; L0 gives it neither.
- **What the answers were:**
  - 8 right;
  - 13 wrong, all labelled `review_required`;
  - 13 declined and 7 asked a clarifying question, 20 with no answer in total.
- **Trust.** No wrong answer was labelled certified. No result rows were sent to the AI model (104 AI calls recorded).
- **Speed.** Median 53 s, 95th percentile 170 s, 2.5 AI calls per question.
- **Chance matches.** 6 of the 8 right answers read exactly the correct query's tables. The other 2 read extra tables and missed none.

**Why L0 got questions wrong** (a reading of the failures, used to decide what L1 must describe, not to change DQL):
- **Wrong join paths.** For example, it reached a claim's policy through the insured object instead of through claim coverage.
- **Missing type rules.** Premiums are the policy amounts that have a premium record; losses, reserves and expenses are claim amounts told apart by their subtype tables. L0 contains nothing that says so.
- **Party roles.** Agents and policy holders are parties with role codes `AG` and `PH` on the agreement; L0 does not say this.
- **One strict case.** "Total premiums a policy holder has paid" was answered without the policy holder's id, which the correct answer (and dbt Labs' grader) requires.

**Why it declined or asked back.** In most of the 20 cases Ask named the missing knowledge instead of guessing. For example: "Which party-role column identifies the selling agent?", and "Should total loss be all claim amounts, or only those in the loss and expense subtype tables?" That is the behaviour a governed product should show, and it is exactly what L1 supplies.

**Two things in DQL to look at.** They are recorded here and will be fixed only as general fixes, checked on DQL's own suites, and disclosed:
- One question stopped because the run's time budget was nearly spent after 197 s.
- In two questions, Ask said the loss and expense subtype tables share no key with claims, although they join through the claim amount table.

### Writing L1 and L3

A separate agent, which had not seen the benchmark, wrote both layers under the rules in [layers/AUTHORING.md](layers/AUTHORING.md). It took **about 11 minutes** (01:53–02:04 UTC); its full log is [layers/AUTHORING-LOG.md](layers/AUTHORING-LOG.md). It produced:

- **L1: one `insurance` domain.** All 29 dbt models are bound as entities, with their grain and keys, and there are 36 relationships:
  - **31 certified.** Each passed DQL's own relationship check against the warehouse.
  - **5 left as drafts.** One is true in the data, but the `agreement` model names its id column `Agreement_Type_Code`. The other four are keys from the schema document that are empty in every row.
- **L3: five skills.** Policies and parties, coverage and premium, claims (reserves and payments), locations, and what the data does and does not cover.
- **The unanswerable set:** 15 questions this data cannot answer, each with the reason ([unanswerable.json](unanswerable.json)).
- **What DQL's own `dql model discover` proposed:** one domain holding all 29 models, with no relationships. The author used it only as a cross-check.

**What the author found in DQL:**
- **No command writes certification evidence.** The warehouse evidence that certification needs had to be produced with a small script that calls DQL's own validation code.
- **Empty-key joins pass the check.** DQL's relationship check reports "passed" for a join whose keys are empty in every row (0 rows joined), so a join could be certified on no evidence. The author kept those as drafts; the check itself needs a fix.
- **Two things the modeling format cannot say:** "a party is an agent when its role code is AG" (a relationship with a role filter; it went into descriptions and skills instead), and "a premium is a kind of policy amount".

**How the layers are built:** `dql init` runs on the dbt project first, then the layer's files are added and `dql model validate` must pass, the order a team would follow. An earlier build ran `dql init` after adding the files, which added an extra generated domain skill to L1; that was fixed before any L1 run.

**Deviation 3 (SQL dialect).** dbt Labs' MetricFlow time spine (L2 and L3 only) uses Snowflake's `to_date('01/01/2000','mm/dd/yyyy')`; it is built with the DATE literal `DATE '2000-01-01'` instead (`MODEL_PORTS` in `build.mjs`).

**Next:** L1, L2 and L3 are run on the 41 headline questions and compared with L0, then repeated; the unanswerable set is run on L0 and L3.

## Reproduce

```bash
./scripts/setup-python.sh                 # dbt 1.9 + DuckDB in .venv
npm run connectors:install                # DuckDB driver for DQL
./insurance/download.sh                   # pinned sources
export DQL_CLI=/path/to/dql/apps/cli/dist/index.js   # until the scoring change is released
node insurance/build.mjs --layer L0
node insurance/checks/publisher-answers.mjs
claude /login                             # the subscription provider uses this login
node insurance/run.mjs --layer L0 --set all --run my-run
```

Replaying a recorded run: `node insurance/run.mjs --layer L0 --set all --run <same id> --cassette replay`.

## Change log

- 2026-09-16: Spider 2.0-DBT harness removed (it tests writing dbt models, not answering questions). Step 1 committed in DQL (`62258981`). Steps 2–7 done. L0 run started.
- 2026-09-16: The L0 run stopped on a timeout. Grading fix `afa6f908`. Diagnosis found the missing reasoning effort (Step 8); fix written, golden suites being re-recorded. A second development question was declared.

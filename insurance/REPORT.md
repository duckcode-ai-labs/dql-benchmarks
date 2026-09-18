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

**Where we are** (see [Step 9](#step-9-results)): latest run `sub-r6`, on DQL's development build `f064f023`, Claude Sonnet 5 through the subscription, one run per layer:

| | Right | Wrong, flagged for review | **Wrong, shown as trustworthy** | Stopped | Median time |
|---|---:|---:|---:|---:|---:|
| Plain text-to-SQL (dbt Labs' prompt, 13 hand-picked tables with keys) | 19/41 (46%) | 0 | **22** | 0 | 6 s |
| DQL L0: dbt project only | 14/41 (34%) | 9 | **0** | 18 | 47 s |
| DQL L1: + modeling | 17/41 (41%) | 13 | **0** | 11 | 38 s |
| DQL L2: + dbt Labs' semantic layer | 22/41 (54%) | 15 | **0** | 4 | 36 s |
| DQL L3: + skills | 26/41 (63%) | 12 | **0** | 3 | 33 s |

- **L3 is significantly more accurate than plain text-to-SQL:** +17 points, 95% CI +4 to +30, exact McNemar p = 0.04. L3 was right on 8 questions that text-to-SQL missed, and text-to-SQL on 1 that L3 missed.
- **L3 against L0:** +29 points, p = 0.0005, with no question lost.
- **The hardest quadrant** (complex questions over the complex schema): L3 answered 7 of 10. The 2023 paper reported 0% for SQL and 36–39% with a knowledge graph there, using GPT-4, so this is context, not a head-to-head result.
- **dbt Labs' 11 questions:** 10 right.
- **No DQL layer showed a wrong answer as trustworthy.** Plain text-to-SQL showed 22.
- **Single runs swing by about ±4 questions** (L1 was 20 in `sub-r5` and 17 here), so none of this is final. Repeat runs come next. These results are **not published**: a development build, single runs, and answers still slower than we want.

---|---:|---:|---:|---:|---:|
| Plain text-to-SQL (dbt Labs' prompt, 13 hand-picked tables with keys) | 19/41 (46%) | 0 | **22** | 0 | 6 s |
| DQL L0: dbt project only | 10/41 (24%) | 6 | **0** | 25 | 46 s |
| DQL L1: + modeling | 20/41 (49%) | 7 | **0** | 14 | 42 s |
| DQL L2: + dbt Labs' semantic layer | 21/41 (51%) | 13 | **1** | 6 | 39 s |
| DQL L3: + skills | 23/41 (56%) | 11 | **1** | 6 | 36 s |

- **Against L0, each layer's gain is statistically significant** (L1 +24 points, p = 0.002; L3 +32 points, p = 0.0002). No question that L0 answered correctly was lost.
- **Against plain text-to-SQL, the accuracy differences are not significant yet** (L3 +10 points, p = 0.34). Plain text-to-SQL is about six times faster.
- **Plain text-to-SQL showed 22 wrong numbers with no warning; DQL showed at most one.** That one (L2 and L3) is a borderline answer key: the right total without the policy-holder column the question implies.
- **On dbt Labs' 11 questions, L3 answered 10.** dbt Labs published 78–91% for Sonnet 5 text-to-SQL with its enhanced schema. Our runs are single runs on our own warehouse, so this is context, not a head-to-head result.
- **These runs are not publishable:** DQL is a development build, and each condition has one run. Repeats and a DQL release come next.

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

**Why DQL's golden suites had to be re-recorded.** DQL's own golden question suites replay recorded AI calls, and a recording's key includes the effort. The golden cases (jaffle, NBA, office) were re-recorded live with Claude Sonnet 5 through the subscription, and their pass rate at the restored effort decided whether the fix was accepted. At `medium` for every call, one jaffle case (gross margin) wrote SQL that counted each order's cost once per item whenever it ran inside the full suite (2 of 2 runs; 3 of 3 alone passed). So SQL writing uses DQL's SQL-authoring effort (`high`), as DQL's original effort design intended. With that, every golden case passed (DQL `0a23c4d9`). The fix changes how Ask behaves, so it will be released as its own DQL version, and benchmark numbers will come from that version.

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

### Run `sub-r3`: L1, L2, L3 and the unanswerable set

| Layer | Right | Accuracy (95% CI) | dbt Labs' 11 | Wrong | Declined / asked back | Wrong but certified | Median time |
|---|---:|---|---:|---:|---:|---:|---:|
| L0 (run `sub-L0-r2`) | 8 | 19.5% (10.2–34.0%) | 2 | 13 | 20 | 0 | 53 s |
| L1 | 11 | 26.8% (15.7–41.9%) | 5 | 9 | 21 | 0 | 45 s |
| L2 *(invalid, see below)* | 11 | 26.8% | 6 | 6 | 24 | 0 | 45 s |
| L3 *(invalid, see below)* | 10 | 24.4% | 6 | 9 | 22 | 0 | 46 s |

- **L1 against L0:** +7.3 points (95% CI −6.8 to +21.5). 6 questions became right and 3 became wrong; exact McNemar p = 0.51, so **not a significant difference on one run**.
- **Where L1 helped:** the hardest quadrant (complex questions over the complex schema) went from 0/10 to 3/10.
- **Why many questions are still declined with L1:** Ask said, for example, "no listed column links claim to policy". L1 describes exactly that link as a certified relationship through the coverage tables. So when DQL writes SQL itself, the certified relationships and bridge tables do not reach that step. This is a DQL product gap. It will be fixed as a general change, checked on DQL's own suites, and disclosed.
- **L2 and L3 are invalid as semantic-layer measurements.** DQL used the machine's own MetricFlow (`mf` on the PATH, version 0.14.0), which lacks the DuckDB adapter, so every semantic compile failed and Ask fell back to AI-written SQL. The harness now installs its own MetricFlow with the DuckDB adapter (`.venv-mf`, dbt-metricflow 0.8.2 on dbt-core 1.9.11), passes it to DQL as `DQL_METRICFLOW_BIN`, and records its version. L2 and L3 are re-run.
- **This exposed two more DQL gaps:**
  - DQL treats MetricFlow as ready when `mf --version` works, without checking the adapter.
  - When MetricFlow fails, Ask does not try DQL's native semantic engine.
- **Unanswerable questions** ([results](results/L0-unanswerable-r3.md)):
  - L0 stopped correctly on 14 of 15; L3 (invalid run) on 13 of 15.
  - None of the answers it gave anyway was labelled certified.
- **In every run**, no result rows were sent to the AI model.
- **About the "harness had uncommitted changes" flag on these runs:** the harness was being edited while they ran. From the next runs on, no tracked file is edited during a run.

### Three repeat runs on DQL 1.17.3 (the released fixes)

The same 41 questions, three times per layer, each run on a fresh copy of the project with nothing carried over. Summaries: [L0](results/repeats-v1.17.3-L0.md) · [L1](results/repeats-v1.17.3-L1.md) · [L2](results/repeats-v1.17.3-L2.md) · [L3](results/repeats-v1.17.3-L3.md) · unanswerable: [L0](results/L0-unanswerable-v1.17.3.md), [L3](results/L3-unanswerable-v1.17.3.md).

| Layer | Runs | Average right | Pooled 95% CI | Same outcome in every run | Wrong, shown as trustworthy (of 123 answers) |
|---|---|---:|---|---:|---:|
| L0 | 10, 12, 10 | **26.0%** | 19.1–34.4% | 61% | 0 |
| L1 | 19, 17, 19 | **44.7%** | 36.2–53.5% | 63% | 0 |
| L2 | 20, 20, 21 | **49.6%** | 40.9–58.3% | 78% | 3 |
| L3 | 23, 20, 23 | **53.7%** | 44.9–62.2% | 73% | 4 |

What the repeats change:

- **The single best runs overstated the result.** `sub-r6` put L3 at 63%; the average on the released code is 54%. The order of the layers holds (L0 < L1 < L2 < L3), and every step up is visible in every run.
- **Stability is well short of where it should be:** 61–78% of questions came out the same way in all three runs. Too many answers depend on how the model happened to read the question that time.
- **Governed answers are not always right.** Across the six L2 and L3 runs, 7 wrong answers carried the `governed` label:
  - 4 are the borderline "total premiums a policy holder has paid": the right total, without the policy-holder id the answer key requires;
  - **3 are real defects:**
    - a list of premiums collapsed into one total;
    - a breakdown missing one of the columns asked for;
    - an average policy size computed wrongly.

  A governed answer must cover everything the question asks for, or not carry the label. This is the most important DQL defect found so far (17), because the product's claim rests on that label.
- **Unanswerable questions:** L0 stopped correctly on 14 of 15, L3 on 13 of 15, none shown as trustworthy.
- **The plain text-to-SQL baseline, three times** ([summary](results/repeats-baseline.md)): the same model, given the warehouse schema and asked for one SQL statement, averaged **44.7%** (19, 17, 19 of 41; pooled 95% CI 36.2–53.5%) and gave the same outcome in every run for **90%** of questions.
  - **L3 is 9 points higher, and that is not yet significant.** Paired over the 123 question-and-run pairs, L3 was right where the baseline was wrong 22 times, and the reverse 11 times (exact McNemar p = 0.08).
  - **The baseline is more stable than DQL** (90% against 73%). One prompt and one statement vary less than a pipeline that reads the question, chooses tables and then writes SQL. Most of DQL's run-to-run changes are in the SQL it writes itself on the multi-table loss questions (see defect 18).
  - **Where DQL is already clearly ahead is trust.** The baseline gave 68 wrong answers over its three runs, each as a plain answer, with nothing to tell the reader to check it. DQL's wrong answers carried `review_required` except the 7 governed ones above.

### Run `sub-r6`: all layers on DQL `f064f023` (marker tables and wide questions)

Scorecards: [L0](results/L0-subscription-r6.md) · [L1](results/L1-subscription-r6.md) · [L2](results/L2-subscription-r6.md) · [L3](results/L3-subscription-r6.md) · paired: [against plain text-to-SQL](results/paired-r6-vs-baseline.md), [between layers](results/paired-r6-layers.md) · unanswerable: [L0](results/L0-unanswerable-r6.md), [L3](results/L3-unanswerable-r6.md) (each stopped correctly on 14 of 15).

**What changed against `sub-r5`:**
- L0 10 → 14, L1 20 → 17, L2 21 → 22, L3 23 → 26.
- Stops fell again: L3 from 6 to 3.

**Reading the L1 drop question by question:**
- Four of the five questions L1 lost were the model writing different SQL for the same reading: a guessed role code, an average per amount row instead of per claim, the parts of a total without the total.
- **The fifth was a DQL side effect of the wide-question change.** More tables were named, the warehouse is asked about at most five tables per call, and the bridge tables the Modeling map had added were left without columns and dropped. DQL now asks in batches, bridge tables first (defect 16).

### Run `sub-r5`: all layers on DQL `629db0f9` (the benchmark's fixes)

Scorecards: [L0](results/L0-subscription-r5.md) · [L1](results/L1-subscription-r5.md) · [L2](results/L2-subscription-r5.md) · [L3](results/L3-subscription-r5.md) · paired: [against plain text-to-SQL](results/paired-r5-vs-baseline.md), [between layers](results/paired-r5-layers.md) · unanswerable: [L0](results/L0-unanswerable-r5.md), [L3](results/L3-unanswerable-r5.md).

| Layer | Right | dbt Labs' 11 | Hard questions over the complex schema | Stopped | Governed answers (right / wrong) | Median / 95th pct time |
|---|---:|---:|---:|---:|---:|---:|
| L0 | 10 (24.4%) | 4 | 1/10 | 25 | 0 / 0 | 46 / 178 s |
| L1 | 20 (48.8%) | 9 | 3/10 | 14 | 0 / 0 | 42 / 187 s |
| L2 | 21 (51.2%) | 9 | 4/10 | 6 | 3 / 1 | 39 / 104 s |
| L3 | 23 (56.1%) | 10 | 3/10 | 6 | 3 / 1 | 36 / 117 s |

- **The semantic layer ran this time.** L2 and L3 each answered 4 questions from dbt Labs' metrics, labelled `governed`. Three were right.
- **The fourth governed answer is the "wrong, shown as trustworthy" case.** "What is the total amount of premiums that a policy holder has paid?" was answered with the right total (98,000) but without the policy-holder id the answer key requires. It counts as wrong, and it is the only such case in any DQL layer.
- **Chance-match review.** Some right answers summed every claim amount rather than only the loss and expense subtypes. That is the same total only because every claim amount in this data belongs to one of those four subtypes; on real data it would be wrong. The scorecards list each case (right answers that left out a table the correct query reads). Reviewing them by hand, and reporting accuracy with and without them, is part of the publication step.
- **Unanswerable questions.** L0 stopped correctly on 14 of 15 and L3 on 13 of 15. None of the answers given anyway was labelled trustworthy.
- **No result rows were sent to the AI model in any run.**
- **What changed since `sub-r3`:** the DQL fixes in Step 10 (#3–#7) and a working MetricFlow. The same question set, model and layers were used. Because these fixes came from reading failures on this benchmark, the next confirmation must come from a benchmark DQL was not tuned on (the Trust Benchmark design).

### Run `sub-r4`: plain text-to-SQL baseline, and L2/L3 again

**Plain text-to-SQL baseline** ([scorecard](results/baseline-text2sql-small-r4.md)): dbt Labs' own prompt and schema file (13 hand-picked tables with 25 foreign keys), Claude Sonnet 5 at medium effort, one call per question, on our warehouse. **19/41 right (46.3%, 95% CI 32.1–61.3%)**; dbt Labs' 11: 7/11. Median 6 s per question. Every reply ran on DuckDB.

**The comparison that matters commercially** (all 41 questions are answerable, so every stop is an unnecessary stop):

| | Right | Wrong, flagged | **Wrong, shown as a plain answer** | Unnecessary stop | Median time |
|---|---:|---:|---:|---:|---:|
| Plain text-to-SQL (13 curated tables + keys) | 19 (46%) | 0 | **22 (54%)** | 0 | 6 s |
| DQL L0 (dbt project only) | 8 (20%) | 13 | **0** | 20 (49%) | 53 s |
| DQL L1 (+ modeling) | 11 (27%) | 9 | **0** | 21 (51%) | 45 s |
| DQL L3 (+ skills; semantic layer not running, see below) | 12 (29%) | 7 | **0** | 22 (54%) | 49 s |

What this says, plainly:

- **Plain text-to-SQL is right more often (46% against 20–29%) and about eight times faster.** It was also given a hand-picked schema of the 13 tables the questions need, with their keys; DQL was given the whole project.
- **More than half of plain text-to-SQL's answers are wrong numbers with no warning.** DQL gave no wrong answer without flagging it, in any layer.
- **DQL's weakness is stopping too often.** It declined or asked back on about half of questions it could have answered. A tool that is never silently wrong but answers half the time does not win a buyer either. Cutting unnecessary stops while keeping silent-wrong at zero is the product goal these numbers set.
- **Latency is DQL's other gap:** 45–53 s median against 6 s. The Claude subscription CLI accounts for part of it (a rejected first structured reply on every question-reading call).

**L2 and L3 are invalid again as semantic-layer measurements.** With the harness's MetricFlow (0.8.2 at the time), DQL called `mf query --compile`, which that version does not have. DQL picks the flag from the MetricFlow version (`--explain` from 0.13 on), and DQL's own installer installs 0.13. The harness now installs exactly DQL's range (`dbt-metricflow[dbt-duckdb]>=0.13,<0.14`, currently 0.13.0), which compiles dbt Labs' metrics on this project. L2 and L3 are run again with it.

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

## Step 10: DQL defects the benchmark found, and their fixes

Every fix below is general: it names no benchmark table, column or question. Each is checked on DQL's own golden question suites (jaffle, NBA, office), and every benchmark number reports the DQL build it ran on.

| # | Defect | Found by | Fix | State |
|---|---|---|---|---|
| 1 | Ask never sent a reasoning effort to the AI model (lost when the previous runtime was removed on 2026-09-05); on the Claude subscription one step took 80–120 s and often timed out | first L0 run | effort again set per call: reading at the route effort, SQL writing at the SQL-authoring effort, repairs one level up, capped by Settings | DQL `0a23c4d9` |
| 2 | `dql agent eval` stopped the whole suite when one question timed out | first L0 run | the question is recorded as failed, never as a refusal; `--case-timeout-ms` | DQL `afa6f908` |
| 3 | When Ask writes SQL itself, the tables *between* the question's tables (bridge tables) were never chosen, so modeled joins could not be used ("no column links claim to policy") | L1 run | the cheapest route over the Modeling map (certified joins first, up to 3 hops) adds its bridge tables and shows each hop as a join hint | DQL `629db0f9` |
| 4 | Skills never reached the SQL writer, and the question reader sees only their first 300 characters | L3 run | the two skills sharing the most words with the question and tables are given to the SQL writer, up to 1,500 characters each | DQL `629db0f9` |
| 5 | Tables that only share a column name with the question's tables (look-alikes) were ranked like connected ones, and joins through them returned no rows | L1/L3 runs | on a modeled project, a table on the Modeling map ranks by whether a modeled route (two hops at most) reaches the question's tables | DQL `629db0f9` |
| 6 | An absolute machine path appeared in an answer summary and the next AI prompt ("MetricFlow is installed but /var/…/semantic_manifest.json was not found") | re-recording DQL's golden suites | the path is shown relative to the project | DQL `ebf7455e` |
| 7 | DQL's golden suite used whichever MetricFlow the developer had installed, so recordings made on one machine did not replay | same | the suite pins the native semantic engine, as CI has no MetricFlow | DQL `ebf7455e` |
| 8 | MetricFlow counted as ready when `mf --version` works, even without the warehouse adapter; no fallback to DQL's native semantic engine when MetricFlow fails | L2 run | to do | open |
| 9 | Certification check passes a join whose keys are empty in every row (0 rows joined) | L1 authoring | to do | open |
| 10 | No CLI command writes the warehouse evidence certification needs | L1 authoring | to do | open |
| 11 | The Claude Code CLI rejects the model's first structured answer to DQL's reading schema about 60% of the time (one wasted turn per question) | timeout diagnosis | measure answering without the CLI's schema feature | open (separate task) |
| 12 | Ask stops on about half of answerable questions | every run | defects 3–5 cut stops from 25 to 6 (run `sub-r5`) | partly fixed |
| 13 | A table that only marks rows of another (a `loss_payment` row marks a claim amount) was not understood: drafts summed every claim amount, or stopped because "no table holds loss reserve amounts" | `sub-r5` L3 misses | a key-only side of a modeled one-to-one relationship is described to the SQL writer as a marker, and its base table is added | DQL `f064f023` |
| 14 | Wide questions lost tables: "loss reserves" did not name `loss_reserve`, and tables named in a metric's definition were not included | `sub-r5` L3 misses | question words match table names; a metric brings the tables its definition names; larger table budget | DQL `f064f023` |
| 15 | The question-reading step can stop with a question back before any answer path is tried | `sub-r5` L3 misses | a first fix (send such readings straight to AI SQL) was dropped: DQL's golden suite showed it lost a follow-up's inherited limit and skipped a certified answer. It needs a design that tries certified and semantic answers first | open |
| 16 | Bridge tables added from the Modeling map were dropped on wide questions (columns are described five tables per call, and the bridges came last) | `sub-r6` L1 | columns described in batches of five, bridge tables first | written, being verified |
| 17 | A governed (semantic-layer) answer can drop a breakdown or grain the question asked for and still carry the `governed` label: a list of premiums collapsed into one total, a breakdown missing a column | 1.17.3 repeats | a governed answer must cover every measure, breakdown and grain the reading asks for, or be downgraded to review-required | **split on diagnosis.** (b) *Code:* a question grouped by two dates bound only the last one, because each time grouping overwrote the request's single time dimension. Fixed in DQL 73295860 (unreleased): the second date at day grain is grouped too; at another grain, or whenever any grouping would be lost, the semantic tier refuses and the question falls through to a review-required answer. (a) and (c) *Reading:* the reading turned "all the premiums paid" into one total; and for "average policy size … total amount of premium" it divided every policy amount (5,698,000) by 2 policies instead of premium amounts only (98,000). The semantic model documents the `has_premium` flag for exactly this. These are reading errors, not binding errors; they count against accuracy and stay open under stability/reading work |
| 18 | AI-written SQL related two tables through a parent they both only reference (claims and coverage details each name the insured object), instead of the bridge the team modeled. Every claim then met every coverage on that object, and totals landed on the wrong policies. The route search ignored which way each relationship runs, so the two 3-hop routes tied. On this small warehouse no key repeats, so DQL's row-count probe could not see it | L3 repeats (stability) | the route search knows each relationship's direction: a route that climbs to a table and comes back down is a last resort. A new check fails AI-written SQL that relates two tables through a shared parent when the Modeling map connects them by certified or validated direct links, and names the route to use. Over the 105 AI-written L3 answers in the three 1.17.3 runs, it flags 20 of the 48 wrong answers and none of the 57 right ones | DQL `953067e7` (unreleased) |

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

## Speed: where a question's time goes

On the Claude subscription route, L1–L3 take a median of 34–41 s per question, and L0 52–58 s. The target is 15 s. Timed from the run store of a clean L3 run (`v1173-c`), average per question:

| Step | Time |
|---|---:|
| Reading the question against the governed vocabulary (one AI call, sometimes a correction) | **27 s** |
| Writing the SQL (one AI call) | 7–11 s |
| Searching every table for a field the reading missed (when it happens, 9 of 41) | 21 s |
| Everything DQL does itself: context, grounding, the semantic-layer compile, checks, running the query | about 2 s |

- **Almost all the time is in the AI calls.** DQL's own work is about 2 s, most of it the MetricFlow compile.
- **The reading call is the slow one.** It goes through the `claude` command line with a structured-output schema. An earlier DQL experiment put the schema in the prompt instead: 2–3 times faster, but it lost accuracy on DQL's own golden suite (10 of 15 against 15 of 15). So there is no free speed-up on this route.
- **The next measurement is the Anthropic API route.** It has no command-line start-up and supports prompt caching, and it also gives the cost figures. It needs an API key from the owner.

**One run's speed is partly invalid.** The L3 run of `v1173-b` was started twice. Recording reuses any recording it finds, so 8 of its 41 answers replayed the first attempt's recordings: no AI call, about 3 s each.
- Their answers are real model output from the same build, so accuracy stands.
- Their times are not real, so speed figures leave them out; that run's median over the other 33 questions is 37 s.
- The harness now refuses to record into a run that already holds recordings.

## Held-out questions

Every fix in Step 10 came from reading failures on the 41 questions, so a gain on them may not carry over to other questions. A second, sealed set answers that:

- **Who wrote it:** a separate agent that saw only the warehouse (its schema, sample values and a read-only query tool). It never saw the 41 questions, any result or DQL. It was also told not to recall any published question set for this data.
- **What it holds:** 44 answerable questions (LQLS 12, HQLS 11, LQHS 10, HQHS 11), covering single numbers, lists, breakdowns, rankings, ratios and trends. There are also 9 questions the data cannot answer. Every correct query was run and returns rows.
- **The rules:**
  - DQL is never changed because of a held-out failure;
  - the set runs at release checkpoints (`--set heldout`, `--set heldout-unanswerable`);
  - its scorecards, regrades and repeat summaries print totals only, never a question.
- **The answer key is not yet reviewed.** It needs an owner review, like the main set's, before a held-out number is published. The author noted that the data is very small (most tables have 2–12 rows), and that some joins rest on conventions the schema doesn't state; those choices are recorded in each question's notes.

File: [heldout/questions.json](heldout/questions.json) · tool: `insurance/heldout.mjs`.

## Change log

- 2026-09-16: Spider 2.0-DBT harness removed (it tests writing dbt models, not answering questions). Step 1 committed in DQL (`62258981`). Steps 2–7 done. L0 run started.
- 2026-09-16: The L0 run stopped on a timeout. Grading fix `afa6f908`. Diagnosis found the missing reasoning effort (Step 8); fix written, golden suites being re-recorded. A second development question was declared.

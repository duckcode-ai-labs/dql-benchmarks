# Methodology

How every number in this repository is produced and reported. A result that does not follow these rules is not published.

## 1. Paired comparisons only

A claim always compares two **conditions** on **the same questions** scored by **the same grader**:

- per condition: correct / total, accuracy, and a **Wilson 95% confidence interval**;
- between conditions: the questions only one of them got right, an **exact two-sided McNemar test**, and the difference in accuracy with a 95% interval.

A single accuracy figure on its own is never published. The scorer is `paired/paired-compare.mjs`; it refuses reports that answer different questions.

## 2. What the conditions are

| Benchmark | Baseline | Challenger(s) |
|---|---|---|
| Spider 2.0-DBT | an agent with file, `dbt run` and read-only SQL tools | the same agent plus DQL's metadata, relationship-proof and SQL-validation tools |
| Insurance (data.world, dbt Labs) | AI-written SQL over the raw tables | + DQL domain modeling and relationships → + dbt semantic layer → + skills |

Each step adds exactly one layer, so the table shows what each layer is worth.

## 3. Provenance

- Runs are recorded once against a real AI provider and replayed from those recordings. Only recordings from a real provider count; test fixtures and synthetic recordings are refused by the scorer.
- Every report carries an identity block: this repository's commit and whether it had uncommitted changes, the DQL version and whether it came from an npm release, the provider and model, the recording mode, a fingerprint of the adapter code, and a hash of the downloaded data.
- Only runs of a **released** DQL version, from a **clean** checkout, with **recorded** AI calls are publishable.

## 4. The answer key is audited

Public answer keys contain many mistakes. A 2026 audit ([arXiv 2601.08778](https://arxiv.org/abs/2601.08778)) found 52.8% of BIRD mini-dev and 62.8% of Spider 2.0-Snow gold annotations wrong, enough to move agents up to nine places on a leaderboard.

So every scored case has a line in the benchmark's `gold-audit.jsonl`:

```json
{"caseId": "...", "status": "accepted", "reviewer": "...", "reviewedAt": "2026-09-16"}
{"caseId": "...", "status": "disputed", "reason": "gold counts refunds as revenue", "reviewer": "...", "reviewedAt": "..."}
{"caseId": "...", "status": "corrected", "reason": "...", "evidenceSql": "select ...", "reviewer": "...", "reviewedAt": "...", "upstreamIssue": "https://..."}
```

- Accuracy is reported on **all** cases and on the **accepted** subset, always side by side.
- A correction never replaces the publisher's answer. Our reference is scored as an alternative beside it, and the disagreement is reported to the publisher.
- A case with no audit line stops the scorer.

## 5. Trust labels are scored

DQL labels every answer `certified`, `governed` or `review_required`. Reports count **wrong answers labelled certified** as their own column. The target is zero; any other value is a product defect, reported as such.

When a benchmark includes questions the data cannot answer, a refusal counts as correct only when refusing was right.

## 6. Cost and latency

- Latency: median and 95th percentile per question.
- AI calls: mean and maximum per question, from DQL's run receipts.
- Cost: dollars per question at the provider's list price on the date in `pricing.json`. Cost is shown only when **every** question measured its token usage; otherwise the column reads "—". Cost is never estimated.

## 7. Matching answers

Where a benchmark ships its own grader (Spider 2.0-DBT's `evaluate.py`), that grader decides. Our own row matcher (`lib/row-match.mjs`) runs beside it as a cross-check, and any disagreement is reported.

Where we compare rows ourselves, column names and order are ignored, numbers compare within 1e-6, a date equals a midnight timestamp of the same day, and duplicate rows must appear the same number of times.

## 8. No tuning on the test set, and no path to the answers

- **The product is not tuned to benchmark tasks.** The agent's prompt names no task, table or schema, and its code has no task-specific branches. Changes made while building the harness fix general faults (a truncated file listing, a prose reply treated as finishing), never a task's content.
- **Development tasks are declared and kept out of scored runs.** Any task whose run was inspected while building the harness is listed in the benchmark's `dev-tasks.json` with the reason. `run.mjs --scored` refuses to include them, and any result on them is reported separately.
- **The agent code is frozen before a scored run.** The report records the DQL version and commit, and a scored run from a modified or unreleased build is not published.
- **The agent cannot reach the graded answers.** The answer databases live outside the task folder. The agent's file tools are confined to the task folder. Its SQL tool opens only the task database, with file access limited to the task folder and then locked (no reading other files, no `ATTACH`, no switching the restriction off). Model files that reference absolute paths, leave the folder with `..`, or use `ATTACH` are refused before dbt can run them, and each refusal is recorded in the result.

## 9. Before any number is trusted

- The baseline condition must reproduce the publisher's own reported baseline within a few points. If it does not, the harness is wrong and nothing is published.
- Replaying the recordings on a clean machine must reproduce the published accuracy columns exactly.

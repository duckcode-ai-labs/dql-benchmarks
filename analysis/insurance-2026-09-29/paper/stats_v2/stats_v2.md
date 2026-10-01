# Insurance benchmark — statistics v2

Generated 2026-10-01T01:18:15+00:00 by `stats_v2.py` in this folder (Python standard library; re-runnable; read-only on runs/, projects/, gold/ and insurance/; no model or network calls). Sealed sets: aggregates only.

## Method note

- **Bootstrap.** Question-level (cluster) percentile bootstrap: questions are resampled with replacement, 10,000 replicates, fixed seed `20260930` (one stream per set, `random.Random("<seed>:<set>")`). Every statistic on a set uses the same resamples, so paired differences are computed on identical question draws. For pooled measures all answers to a resampled question enter together (a question drawn twice contributes all its answers twice), which removes the pseudo-replication of counting the same question once per model and level as if it were an independent observation.
- **Wilson.** Score interval, z = 1.96, on the answer counts as before; for pooled measures it is shown only as the naive (pseudo-replicated) comparison.
- **Effective sample size.** `ESS_icc = answers / DEFF`, `DEFF = 1 + (n0 − 1)·ICC` with the one-way ANOVA ICC of the 0/1 outcome within question (clipped to [0, 1]); `ESS_boot = p(1 − p) / SE²_boot` (undefined when p is 0 or 1); `ESS_min = (Σ m_q)² / Σ m_q²`, the value if all answers to a question always agreed (ICC = 1).
- **Rule of three.** With zero wrong trusted answers, the one-sided 95% upper bound is `3/n` with **n = distinct questions that ever received a trusted answer**; the exact bound `1 − 0.05^(1/n)` is shown beside it. When some are wrong, the question-level rate (questions with ≥ 1 wrong trusted answer) gets an exact Clopper–Pearson one-sided bound.
- **Paired tests (set 4).** Exact two-sided McNemar on discordant questions; Holm–Bonferroni step-down within the family {L2, L3, W2, WB} vs A (4 tests) and separately vs P (4 tests).
- **Re-grade.** Strict = the run's own `executionMatched`, re-checked on the graded rows. Lenient = strict, or same row count and every gold *measure* (numeric) column matched by an answer column row by row (label/id columns may be missing or different). Lenient + rounding = lenient, or same row count and the answer's measure values equal the gold values **rounded to d decimals, d ∈ {0,…,4}** (one d per answer; only non-integer gold values are rounded; half-up on the exact binary value, decimal half-up and half-even are all accepted). The measure/label split and the error classes are a Python port of `regrade/regrade.mjs` (measure = computed in the gold projection, numeric-sounding name that is not an id/label, or fractional values). DQL rows are those the answer showed (copy of `agent-runs.sqlite`, all attempts); P and A rows come from re-running the recorded SQL on a read-only copy of the warehouse (L0).
- **Classes of strict-wrong answers** (first that applies): `abstained` (no SQL, asked to clarify, or stopped with SQL); `other` (SQL that fails on re-run, or rows that match although recorded wrong); `grain_or_shape` (row count differs); `missing_or_extra_columns` (same rows, measures right, a label column missing/substituted/re-formatted); `rounding_only` (measures equal the gold rounded to 0–4 decimals); `wrong_numbers` (measure values differ, or listing values differ).
- **Inclusion.** A report with `invalid` set is missing; LB and WB count only on DQL build `627009a1`. Trusted = `trustState` certified or governed; abstained = no recorded SQL.

**Excluded / partial cells:** luna L0 heldout-3-unanswerable (report flagged invalid); sol L2 heldout-3-unanswerable (report flagged invalid); sol LB heldout-3 (old DQL build 49c0e1cb (LB/WB count only on 627009a1)).

## 1. Accuracy per model × condition × set

Accuracy on answerable sets = strict execution match; on unanswerable sets = correct stops (`passed`). Bootstrap = question-level, 10k reps.

### heldout-3 (40 questions)

| Model | Condition | k/n | Accuracy | Wilson 95% | Bootstrap 95% |
|---|---|---:|---:|---|---|
| Claude Opus 5.5 | P (one-shot SQL) | 30/40 | 75.0% | 59.8–85.8% | 60.0–87.5% |
| Claude Opus 5.5 | A (agent) | 32/40 | 80.0% | 65.2–89.5% | 67.5–92.5% |
| Claude Opus 5.5 | L0 | 24/40 | 60.0% | 44.6–73.7% | 45.0–75.0% |
| Claude Opus 5.5 | L1 | 34/40 | 85.0% | 70.9–92.9% | 72.5–95.0% |
| Claude Opus 5.5 | L2 | 29/40 | 72.5% | 57.2–83.9% | 57.5–85.0% |
| Claude Opus 5.5 | L3 | 33/40 | 82.5% | 68.0–91.2% | 70.0–92.5% |
| Claude Opus 5.5 | LB | 29/40 | 72.5% | 57.2–83.9% | 57.5–85.0% |
| Claude Opus 5.5 | W0 | 33/40 | 82.5% | 68.0–91.2% | 70.0–92.5% |
| Claude Opus 5.5 | W1 | 32/40 | 80.0% | 65.2–89.5% | 67.5–92.5% |
| Claude Opus 5.5 | W2 | 36/40 | 90.0% | 77.0–96.0% | 80.0–97.5% |
| Claude Opus 5.5 | WB | 34/40 | 85.0% | 70.9–92.9% | 72.5–95.0% |
| Claude Sonnet 5.5 | P (one-shot SQL) | 27/40 | 67.5% | 52.0–79.9% | 52.5–82.5% |
| Claude Sonnet 5.5 | A (agent) | 33/40 | 82.5% | 68.0–91.2% | 70.0–92.5% |
| Claude Sonnet 5.5 | L0 | 24/40 | 60.0% | 44.6–73.7% | 45.0–75.0% |
| Claude Sonnet 5.5 | L1 | 32/40 | 80.0% | 65.2–89.5% | 67.5–92.5% |
| Claude Sonnet 5.5 | L2 | 35/40 | 87.5% | 73.9–94.5% | 77.5–97.5% |
| Claude Sonnet 5.5 | L3 | 33/40 | 82.5% | 68.0–91.2% | 70.0–92.5% |
| Claude Sonnet 5.5 | LB | 31/40 | 77.5% | 62.5–87.7% | 65.0–90.0% |
| Claude Sonnet 5.5 | W0 | 37/40 | 92.5% | 80.1–97.4% | 82.5–100.0% |
| Claude Sonnet 5.5 | W1 | 38/40 | 95.0% | 83.5–98.6% | 87.5–100.0% |
| Claude Sonnet 5.5 | W2 | 39/40 | 97.5% | 87.1–99.6% | 92.5–100.0% |
| Claude Sonnet 5.5 | WB | 38/40 | 95.0% | 83.5–98.6% | 87.5–100.0% |
| Claude Sonnet 5 | P (one-shot SQL) | 25/40 | 62.5% | 47.0–75.8% | 47.5–77.5% |
| Claude Sonnet 5 | L0 | 20/40 | 50.0% | 35.2–64.8% | 35.0–65.0% |
| Claude Sonnet 5 | L1 | 33/40 | 82.5% | 68.0–91.2% | 70.0–92.5% |
| Claude Sonnet 5 | L2 | 34/40 | 85.0% | 70.9–92.9% | 72.5–95.0% |
| Claude Sonnet 5 | L3 | 29/40 | 72.5% | 57.2–83.9% | 57.5–85.0% |
| Claude Sonnet 5 | LB | 29/40 | 72.5% | 57.2–83.9% | 57.5–85.0% |
| Claude Sonnet 5 | W0 | 29/40 | 72.5% | 57.2–83.9% | 57.5–85.0% |
| Claude Sonnet 5 | W1 | 35/40 | 87.5% | 73.9–94.5% | 77.5–97.5% |
| Claude Sonnet 5 | W2 | 36/40 | 90.0% | 77.0–96.0% | 80.0–97.5% |
| Claude Sonnet 5 | WB | 34/40 | 85.0% | 70.9–92.9% | 72.5–95.0% |
| Qwen 3.8 27B (local) | P (one-shot SQL) | 18/40 | 45.0% | 30.7–60.2% | 30.0–60.0% |
| Qwen 3.8 27B (local) | L0 | 10/40 | 25.0% | 14.2–40.2% | 12.5–40.0% |
| Qwen 3.8 27B (local) | L1 | 28/40 | 70.0% | 54.6–81.9% | 55.0–82.5% |
| Qwen 3.8 27B (local) | L2 | 27/40 | 67.5% | 52.0–79.9% | 52.5–82.5% |
| Qwen 3.8 27B (local) | L3 | 26/40 | 65.0% | 49.5–77.9% | 50.0–80.0% |
| Qwen 3.8 27B (local) | LB | 23/40 | 57.5% | 42.2–71.5% | 42.5–72.5% |
| Qwen 3.8 27B (local) | W0 | 23/40 | 57.5% | 42.2–71.5% | 42.5–72.5% |
| Qwen 3.8 27B (local) | W1 | 29/40 | 72.5% | 57.2–83.9% | 57.5–85.0% |
| Qwen 3.8 27B (local) | W2 | 27/40 | 67.5% | 52.0–79.9% | 52.5–82.5% |
| Qwen 3.8 27B (local) | WB | 31/40 | 77.5% | 62.5–87.7% | 65.0–90.0% |
| GPT-6 Luna (max) | P (one-shot SQL) | 25/40 | 62.5% | 47.0–75.8% | 47.5–77.5% |
| GPT-6 Luna (max) | L0 | 19/40 | 47.5% | 32.9–62.5% | 32.5–62.5% |
| GPT-6 Luna (max) | L1 | 32/40 | 80.0% | 65.2–89.5% | 67.5–92.5% |
| GPT-6 Luna (max) | L2 | 32/40 | 80.0% | 65.2–89.5% | 67.5–92.5% |
| GPT-6 Luna (max) | L3 | 32/40 | 80.0% | 65.2–89.5% | 67.5–92.5% |
| GPT-6 Luna (max) | W0 | 30/40 | 75.0% | 59.8–85.8% | 60.0–87.5% |
| GPT-6 Luna (max) | W1 | 34/40 | 85.0% | 70.9–92.9% | 72.5–95.0% |
| GPT-6 Luna (max) | W2 | 31/40 | 77.5% | 62.5–87.7% | 65.0–90.0% |
| GPT-6 Sol (medium) | P (one-shot SQL) | 26/40 | 65.0% | 49.5–77.9% | 50.0–80.0% |
| GPT-6 Sol (medium) | L0 | 20/40 | 50.0% | 35.2–64.8% | 35.0–65.0% |
| GPT-6 Sol (medium) | L1 | 30/40 | 75.0% | 59.8–85.8% | 60.0–87.5% |
| GPT-6 Sol (medium) | L2 | 31/40 | 77.5% | 62.5–87.7% | 65.0–90.0% |
| GPT-6 Sol (medium) | L3 | 33/40 | 82.5% | 68.0–91.2% | 70.0–92.5% |
| GPT-6 Sol (medium) | W0 | 30/40 | 75.0% | 59.8–85.8% | 60.0–87.5% |
| GPT-6 Sol (medium) | W1 | 32/40 | 80.0% | 65.2–89.5% | 67.5–92.5% |
| GPT-6 Sol (medium) | W2 | 35/40 | 87.5% | 73.9–94.5% | 77.5–97.5% |
| GPT-5.6 Terra (high) | P (one-shot SQL) | 26/40 | 65.0% | 49.5–77.9% | 50.0–80.0% |
| GPT-5.6 Terra (high) | L0 | 17/40 | 42.5% | 28.5–57.8% | 27.5–57.5% |
| GPT-5.6 Terra (high) | L1 | 30/40 | 75.0% | 59.8–85.8% | 60.0–87.5% |
| GPT-5.6 Terra (high) | L2 | 30/40 | 75.0% | 59.8–85.8% | 62.5–87.5% |
| GPT-5.6 Terra (high) | L3 | 31/40 | 77.5% | 62.5–87.7% | 65.0–90.0% |
| GPT-5.6 Terra (high) | LB | 30/40 | 75.0% | 59.8–85.8% | 60.0–87.5% |
| GPT-5.6 Terra (high) | W0 | 27/40 | 67.5% | 52.0–79.9% | 52.5–82.5% |
| GPT-5.6 Terra (high) | W1 | 31/40 | 77.5% | 62.5–87.7% | 65.0–90.0% |
| GPT-5.6 Terra (high) | W2 | 29/40 | 72.5% | 57.2–83.9% | 57.5–85.0% |
| GPT-5.6 Terra (high) | WB | 32/40 | 80.0% | 65.2–89.5% | 67.5–92.5% |

### heldout-3-unanswerable (10 questions)

| Model | Condition | k/n | Accuracy | Wilson 95% | Bootstrap 95% |
|---|---|---:|---:|---|---|
| Claude Opus 5.5 | A (agent) | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | L0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | L1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | L2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | L3 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | LB | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | W0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | W1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | W2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Opus 5.5 | WB | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | A (agent) | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | L0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | L1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | L2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | L3 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | LB | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | W0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | W1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | W2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5.5 | WB | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5 | L0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5 | L1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5 | L2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5 | L3 | 9/10 | 90.0% | 59.6–98.2% | 70.0–100.0% |
| Claude Sonnet 5 | LB | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5 | W0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5 | W1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5 | W2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Claude Sonnet 5 | WB | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | L0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | L1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | L2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | L3 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | LB | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | W0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | W1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | W2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| Qwen 3.8 27B (local) | WB | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| GPT-6 Sol (medium) | L0 | 9/10 | 90.0% | 59.6–98.2% | 70.0–100.0% |
| GPT-6 Sol (medium) | L1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| GPT-5.6 Terra (high) | L0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| GPT-5.6 Terra (high) | L1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| GPT-5.6 Terra (high) | L2 | 9/10 | 90.0% | 59.6–98.2% | 70.0–100.0% |
| GPT-5.6 Terra (high) | L3 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| GPT-5.6 Terra (high) | W0 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| GPT-5.6 Terra (high) | W1 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |
| GPT-5.6 Terra (high) | W2 | 10/10 | 100.0% | 72.2–100.0% | 100.0–100.0% |

### heldout-4 (200 questions)

| Model | Condition | k/n | Accuracy | Wilson 95% | Bootstrap 95% |
|---|---|---:|---:|---|---|
| Claude Sonnet 5.5 | P (one-shot SQL) | 126/200 | 63.0% | 56.1–69.4% | 56.0–69.5% |
| Claude Sonnet 5.5 | A (agent) | 156/200 | 78.0% | 71.8–83.2% | 72.0–83.5% |
| Claude Sonnet 5.5 | A-model (agent + DQL modeling context) | 168/200 | 84.0% | 78.3–88.4% | 78.5–89.0% |
| Claude Sonnet 5.5 | L2 | 142/200 | 71.0% | 64.4–76.8% | 64.5–77.0% |
| Claude Sonnet 5.5 | L3 | 147/200 | 73.5% | 67.0–79.1% | 67.5–79.5% |
| Claude Sonnet 5.5 | W2 | 171/200 | 85.5% | 80.0–89.7% | 80.5–90.0% |
| Claude Sonnet 5.5 | WB | 154/200 | 77.0% | 70.7–82.3% | 71.0–82.5% |

### heldout-4-unanswerable (50 questions)

| Model | Condition | k/n | Accuracy | Wilson 95% | Bootstrap 95% |
|---|---|---:|---:|---|---|
| Claude Sonnet 5.5 | A (agent) | 47/50 | 94.0% | 83.8–97.9% | 86.0–100.0% |
| Claude Sonnet 5.5 | A-model (agent + DQL modeling context) | 47/50 | 94.0% | 83.8–97.9% | 86.0–100.0% |
| Claude Sonnet 5.5 | L2 | 43/50 | 86.0% | 73.8–93.0% | 76.0–94.0% |
| Claude Sonnet 5.5 | L3 | 41/50 | 82.0% | 69.2–90.2% | 70.0–92.0% |
| Claude Sonnet 5.5 | W2 | 40/50 | 80.0% | 67.0–88.8% | 68.0–90.0% |
| Claude Sonnet 5.5 | WB | 42/50 | 84.0% | 71.5–91.7% | 72.0–94.0% |

## 2. Pooled measures corrected for pseudo-replication (set 3)

The same 40 (or 10) questions are answered by every model at every level, so pooled answers are not independent. The corrected interval resamples questions; the naive Wilson interval treats every answer as independent and is shown only for comparison. A percentile bootstrap collapses to a point when every pooled answer is right (or wrong); read the upper-bound column (rule of three on distinct questions) there.

### 2a. Trusted-answer precision, heldout-3

| Pool | Trusted answers | Wrong | Precision | Naive Wilson (answers) | Question-cluster bootstrap | Distinct questions (with wrong) | Answers/question mean (max) | ICC | ESS_icc | ESS_boot | ESS_min | Upper 95% wrong-rate |
|---|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|---|
| **L2_L3 pooled** (all models) | 49 | 0 | 100.0% | 92.7–100.0% | 100.0–100.0% | 4 (0) | 12.25 (14) | — | — | — | 3.8 | 3/4 = 75.0% (exact 52.7%; naive 3/49 = 6.1%) |
| L2_L3 · Claude Opus 5.5 | 8 | 0 | 100.0% | 67.6–100.0% | 100.0–100.0% | 4 (0) | 2.0 (2) | — | — | — | 4.0 | 3/4 = 75.0% (exact 52.7%; naive 3/8 = 37.5%) |
| L2_L3 · Claude Sonnet 5.5 | 6 | 0 | 100.0% | 61.0–100.0% | 100.0–100.0% | 3 (0) | 2.0 (2) | — | — | — | 3.0 | 3/3 = 100.0% (exact 63.2%; naive 3/6 = 50.0%) |
| L2_L3 · Claude Sonnet 5 | 6 | 0 | 100.0% | 61.0–100.0% | 100.0–100.0% | 3 (0) | 2.0 (2) | — | — | — | 3.0 | 3/3 = 100.0% (exact 63.2%; naive 3/6 = 50.0%) |
| L2_L3 · Qwen 3.8 27B (local) | 6 | 0 | 100.0% | 61.0–100.0% | 100.0–100.0% | 3 (0) | 2.0 (2) | — | — | — | 3.0 | 3/3 = 100.0% (exact 63.2%; naive 3/6 = 50.0%) |
| L2_L3 · GPT-6 Luna (max) | 8 | 0 | 100.0% | 67.6–100.0% | 100.0–100.0% | 4 (0) | 2.0 (2) | — | — | — | 4.0 | 3/4 = 75.0% (exact 52.7%; naive 3/8 = 37.5%) |
| L2_L3 · GPT-6 Sol (medium) | 8 | 0 | 100.0% | 67.6–100.0% | 100.0–100.0% | 4 (0) | 2.0 (2) | — | — | — | 4.0 | 3/4 = 75.0% (exact 52.7%; naive 3/8 = 37.5%) |
| L2_L3 · GPT-5.6 Terra (high) | 7 | 0 | 100.0% | 64.6–100.0% | 100.0–100.0% | 4 (0) | 1.75 (2) | — | — | — | 3.8 | 3/4 = 75.0% (exact 52.7%; naive 3/7 = 42.9%) |
| **W2 pooled** (all models) | 3 | 3 | 0.0% | 0.0–56.1% | 0.0–0.0% | 1 (1) | 3.0 (3) | — | — | — | 1.0 | question-level 1/1 wrong; exact upper 100.0% |
| W2 · Claude Opus 5.5 | 0 | 0 | — | — | — | 0 | — | — | — | — | — | not informative |
| W2 · Claude Sonnet 5.5 | 0 | 0 | — | — | — | 0 | — | — | — | — | — | not informative |
| W2 · Claude Sonnet 5 | 0 | 0 | — | — | — | 0 | — | — | — | — | — | not informative |
| W2 · Qwen 3.8 27B (local) | 1 | 1 | 0.0% | 0.0–79.3% | 0.0–0.0% | 1 (1) | 1.0 (1) | — | — | — | 1.0 | question-level 1/1 wrong; exact upper 100.0% |
| W2 · GPT-6 Luna (max) | 1 | 1 | 0.0% | 0.0–79.3% | 0.0–0.0% | 1 (1) | 1.0 (1) | — | — | — | 1.0 | question-level 1/1 wrong; exact upper 100.0% |
| W2 · GPT-6 Sol (medium) | 0 | 0 | — | — | — | 0 | — | — | — | — | — | not informative |
| W2 · GPT-5.6 Terra (high) | 1 | 1 | 0.0% | 0.0–79.3% | 0.0–0.0% | 1 (1) | 1.0 (1) | — | — | — | 1.0 | question-level 1/1 wrong; exact upper 100.0% |
| **LB pooled** (all models) | 50 | 15 | 70.0% | 56.2–80.9% | 41.9–91.1% | 15 (6) | 3.33 (5) | 1.0 | 15.3 | 13.4 | 12.1 | question-level 6/15 wrong; exact upper 64.0% |
| LB · Claude Opus 5.5 | 11 | 4 | 63.6% | 35.4–84.8% | 33.3–90.9% | 11 (4) | 1.0 (1) | — | — | 10.2 | 11.0 | question-level 4/11 wrong; exact upper 65.0% |
| LB · Claude Sonnet 5.5 | 9 | 3 | 66.7% | 35.4–87.9% | 33.3–100.0% | 9 (3) | 1.0 (1) | — | — | 8.2 | 9.0 | question-level 3/9 wrong; exact upper 65.5% |
| LB · Claude Sonnet 5 | 11 | 4 | 63.6% | 35.4–84.8% | 33.3–90.9% | 11 (4) | 1.0 (1) | — | — | 10.4 | 11.0 | question-level 4/11 wrong; exact upper 65.0% |
| LB · Qwen 3.8 27B (local) | 11 | 3 | 72.7% | 43.4–90.2% | 42.9–100.0% | 11 (3) | 1.0 (1) | — | — | 10.2 | 11.0 | question-level 3/11 wrong; exact upper 56.4% |
| LB · GPT-5.6 Terra (high) | 8 | 1 | 87.5% | 52.9–97.8% | 60.0–100.0% | 8 (1) | 1.0 (1) | — | — | 7.2 | 8.0 | question-level 1/8 wrong; exact upper 47.1% |
| **WB pooled** (all models) | 24 | 4 | 83.3% | 64.1–93.3% | 41.7–100.0% | 7 (3) | 3.43 (5) | 1.0 | 7.4 | 5.5 | 5.4 | question-level 3/7 wrong; exact upper 77.5% |
| WB · Claude Opus 5.5 | 5 | 1 | 80.0% | 37.5–96.4% | 33.3–100.0% | 5 (1) | 1.0 (1) | — | — | 3.9 | 5.0 | question-level 1/5 wrong; exact upper 65.7% |
| WB · Claude Sonnet 5.5 | 5 | 1 | 80.0% | 37.5–96.4% | 33.3–100.0% | 5 (1) | 1.0 (1) | — | — | 4.0 | 5.0 | question-level 1/5 wrong; exact upper 65.7% |
| WB · Claude Sonnet 5 | 4 | 0 | 100.0% | 51.0–100.0% | 100.0–100.0% | 4 (0) | 1.0 (1) | — | — | — | 4.0 | 3/4 = 75.0% (exact 52.7%; naive 3/4 = 75.0%) |
| WB · Qwen 3.8 27B (local) | 6 | 2 | 66.7% | 30.0–90.3% | 20.0–100.0% | 6 (2) | 1.0 (1) | — | — | 5.0 | 6.0 | question-level 2/6 wrong; exact upper 72.9% |
| WB · GPT-5.6 Terra (high) | 4 | 0 | 100.0% | 51.0–100.0% | 100.0–100.0% | 4 (0) | 1.0 (1) | — | — | — | 4.0 | 3/4 = 75.0% (exact 52.7%; naive 3/4 = 75.0%) |
| **all_DQL_levels pooled** (all models) | 126 | 22 | 82.5% | 75.0–88.2% | 56.6–95.0% | 16 (7) | 7.88 (24) | 1.0 | 17.1 | 14.1 | 8.2 | question-level 7/16 wrong; exact upper 66.7% |
| all_DQL_levels · Claude Opus 5.5 | 24 | 5 | 79.2% | 59.5–90.8% | 50.0–96.4% | 11 (4) | 2.18 (4) | 1.0 | 11.3 | 11.0 | 8.7 | question-level 4/11 wrong; exact upper 65.0% |
| all_DQL_levels · Claude Sonnet 5.5 | 20 | 4 | 80.0% | 58.4–91.9% | 46.2–100.0% | 9 (3) | 2.22 (4) | 1.0 | 9.3 | 8.6 | 7.1 | question-level 3/9 wrong; exact upper 65.5% |
| all_DQL_levels · Claude Sonnet 5 | 21 | 4 | 81.0% | 60.0–92.3% | 52.4–96.3% | 11 (4) | 1.91 (4) | 1.0 | 11.4 | 11.5 | 8.0 | question-level 4/11 wrong; exact upper 65.0% |
| all_DQL_levels · Qwen 3.8 27B (local) | 24 | 6 | 75.0% | 55.1–88.0% | 45.5–93.5% | 13 (5) | 1.85 (4) | 1.0 | 13.4 | 12.0 | 9.6 | question-level 5/13 wrong; exact upper 64.5% |
| all_DQL_levels · GPT-6 Luna (max) | 9 | 1 | 88.9% | 56.5–98.0% | 50.0–100.0% | 5 (1) | 1.8 (2) | 1.0 | 5.1 | 4.1 | 4.8 | question-level 1/5 wrong; exact upper 65.7% |
| all_DQL_levels · GPT-6 Sol (medium) | 8 | 0 | 100.0% | 67.6–100.0% | 100.0–100.0% | 4 (0) | 2.0 (2) | — | — | — | 4.0 | 3/4 = 75.0% (exact 52.7%; naive 3/8 = 37.5%) |
| all_DQL_levels · GPT-5.6 Terra (high) | 20 | 2 | 90.0% | 69.9–97.2% | 66.7–100.0% | 9 (2) | 2.22 (4) | 1.0 | 9.3 | 10.7 | 7.1 | question-level 2/9 wrong; exact upper 55.0% |

### 2b. Correct-stop rate, heldout-3-unanswerable (DQL levels)

| Pool | Answers | Correct stops | Rate | Naive Wilson (answers) | Question-cluster bootstrap | Distinct questions | Answers/question mean (max) | ICC | ESS_icc | ESS_boot | ESS_min |
|---|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|
| **All DQL levels × models, pooled** | 450 | 447 | 99.3% | 98.1–99.8% | 98.4–100.0% | 10 | 45.0 (45) | 0.0119 | 295.4 | 328.5 | 10.0 |
| Claude Opus 5.5 (all its DQL levels) | 90 | 90 | 100.0% | 95.9–100.0% | 100.0–100.0% | 10 | 9.0 (9) | — | — | — | 10.0 |
| Claude Sonnet 5.5 (all its DQL levels) | 90 | 90 | 100.0% | 95.9–100.0% | 100.0–100.0% | 10 | 9.0 (9) | — | — | — | 10.0 |
| Claude Sonnet 5 (all its DQL levels) | 90 | 89 | 98.9% | 94.0–99.8% | 96.7–100.0% | 10 | 9.0 (9) | 0.0 | 90.0 | 99.3 | 10.0 |
| Qwen 3.8 27B (local) (all its DQL levels) | 90 | 90 | 100.0% | 95.9–100.0% | 100.0–100.0% | 10 | 9.0 (9) | — | — | — | 10.0 |
| GPT-6 Sol (medium) (all its DQL levels) | 20 | 19 | 95.0% | 76.4–99.1% | 85.0–100.0% | 10 | 2.0 (2) | 0.0 | 20.0 | 21.2 | 10.0 |
| GPT-5.6 Terra (high) (all its DQL levels) | 70 | 69 | 98.6% | 92.3–99.8% | 95.7–100.0% | 10 | 7.0 (7) | 0.0 | 70.0 | 75.8 | 10.0 |
| Level L0 (all models) | 60 | 59 | 98.3% | 91.1–99.7% | 95.0–100.0% | 10 | 6.0 (6) | 0.0 | 60.0 | 65.7 | 10.0 |
| Level L1 (all models) | 60 | 60 | 100.0% | 94.0–100.0% | 100.0–100.0% | 10 | 6.0 (6) | — | — | — | 10.0 |
| Level L2 (all models) | 50 | 49 | 98.0% | 89.5–99.7% | 94.0–100.0% | 10 | 5.0 (5) | 0.0 | 50.0 | 53.8 | 10.0 |
| Level L3 (all models) | 50 | 49 | 98.0% | 89.5–99.7% | 94.0–100.0% | 10 | 5.0 (5) | 0.0 | 50.0 | 54.6 | 10.0 |
| Level LB (all models) | 40 | 40 | 100.0% | 91.2–100.0% | 100.0–100.0% | 10 | 4.0 (4) | — | — | — | 10.0 |
| Level W0 (all models) | 50 | 50 | 100.0% | 92.9–100.0% | 100.0–100.0% | 10 | 5.0 (5) | — | — | — | 10.0 |
| Level W1 (all models) | 50 | 50 | 100.0% | 92.9–100.0% | 100.0–100.0% | 10 | 5.0 (5) | — | — | — | 10.0 |
| Level W2 (all models) | 50 | 50 | 100.0% | 92.9–100.0% | 100.0–100.0% | 10 | 5.0 (5) | — | — | — | 10.0 |
| Level WB (all models) | 40 | 40 | 100.0% | 91.2–100.0% | 100.0–100.0% | 10 | 4.0 (4) | — | — | — | 10.0 |
| Agent A · Claude Opus 5.5 | 10 | 10 | 100.0% | 72.2–100.0% | 100.0–100.0% | 10 | 1.0 (1) | — | — | — | 10.0 |
| Agent A · Claude Sonnet 5.5 | 10 | 10 | 100.0% | 72.2–100.0% | 100.0–100.0% | 10 | 1.0 (1) | — | — | — | 10.0 |

Set 4 (Sonnet 5.5) for reference:

| Pool | Answers | Correct stops | Rate | Naive Wilson (answers) | Question-cluster bootstrap | Distinct questions | Answers/question mean (max) | ICC | ESS_icc | ESS_boot | ESS_min |
|---|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|
| heldout-4-unanswerable, L2+L3+W2+WB pooled | 200 | 166 | 83.0% | 77.2–87.6% | 73.0–91.5% | 50 | 4.0 (4) | 0.6976 | 64.7 | 64.7 | 50.0 |

| Pool | Trusted answers | Wrong | Precision | Naive Wilson (answers) | Question-cluster bootstrap | Distinct questions (with wrong) | Answers/question mean (max) | ICC | ESS_icc | ESS_boot | ESS_min | Upper 95% wrong-rate |
|---|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|---|
| heldout-4 L2_L3 | 28 | 3 | 89.3% | 72.8–96.3% | 71.4–100.0% | 18 (2) | 1.56 (2) | 1.0 | 18.1 | 15.9 | 16.3 | question-level 2/18 wrong; exact upper 31.0% |
| heldout-4 all_DQL_levels | 54 | 16 | 70.4% | 57.2–80.9% | 54.0–85.1% | 39 (13) | 1.38 (3) | 1.0 | 39.2 | 33.8 | 32.4 | question-level 13/39 wrong; exact upper 47.7% |

## 3. Set 4 (Claude Sonnet 5.5, 200 questions): paired tests

Gained = the level right and the reference wrong; lost = the reverse. Holm adjusts within each family of 4 tests.

| Comparison | Level k/n | Ref k/n | Δ accuracy | Paired bootstrap 95% (Δ) | Gained / lost | McNemar p (raw) | Holm-adjusted p |
|---|---:|---:|---:|---|---|---:|---:|
| L2 − A (agent) | 142/200 | 156/200 | -7.0 pts | -14.0–0.0% | 19 / 33 | 0.0704 | 0.2112 |
| L3 − A (agent) | 147/200 | 156/200 | -4.5 pts | -11.5–2.5% | 21 / 30 | 0.2624 | 0.5249 |
| W2 − A (agent) | 171/200 | 156/200 | +7.5 pts | 1.0–14.0% | 29 / 14 | 0.0315 | 0.1262 |
| WB − A (agent) | 154/200 | 156/200 | -1.0 pts | -7.5–5.5% | 21 / 23 | 0.8804 | 0.8804 |
| L2 − P (one-shot SQL) | 142/200 | 126/200 | +8.0 pts | 0.5–15.5% | 39 / 23 | 0.0559 | 0.0559 |
| L3 − P (one-shot SQL) | 147/200 | 126/200 | +10.5 pts | 3.5–17.5% | 37 / 16 | 0.0055 | 0.0110 |
| W2 − P (one-shot SQL) | 171/200 | 126/200 | +22.5 pts | 15.5–29.5% | 52 / 7 | 1.4e-09 | 5.4e-09 |
| WB − P (one-shot SQL) | 154/200 | 126/200 | +14.0 pts | 6.5–21.5% | 44 / 16 | 0.0004 | 0.0012 |
| P − A (not in a family) | 126/200 | 156/200 | -15.0 pts | -20.5–-9.5% | 3 / 33 | 2.3e-07 | — |
| W2 − A-model (exploratory) | 171/200 | 168/200 | +1.5 pts | -4.0–7.0% | 18 / 15 | 0.7283 | — |
| A-model − A (exploratory) | 168/200 | 156/200 | +6.0 pts | 2.0–10.0% | 15 / 3 | 0.0075 | — |

**Sensitivity: the same tests under the lenient grades** (section 5). The agent and one-shot SQL lose many more answers to label columns than DQL does, so the comparison with A depends on the grading rule.

*Lenient*

| Comparison | Level k/n | Ref k/n | Δ accuracy | Paired bootstrap 95% (Δ) | Gained / lost | McNemar p (raw) | Holm-adjusted p |
|---|---:|---:|---:|---|---|---:|---:|
| L2 − A (agent) | 149/200 | 182/200 | -16.5 pts | -22.5–-11.0% | 4 / 37 | 1.0e-07 | 4.1e-07 |
| L3 − A (agent) | 152/200 | 182/200 | -15.0 pts | -20.5–-9.5% | 3 / 33 | 2.3e-07 | 6.8e-07 |
| W2 − A (agent) | 177/200 | 182/200 | -2.5 pts | -7.0–1.5% | 7 / 12 | 0.3593 | 0.3593 |
| WB − A (agent) | 159/200 | 182/200 | -11.5 pts | -17.0–-6.0% | 5 / 28 | 6.6e-05 | 0.0001 |
| L2 − P (one-shot SQL) | 149/200 | 152/200 | -1.5 pts | -8.5–5.5% | 24 / 27 | 0.7798 | 1.0000 |
| L3 − P (one-shot SQL) | 152/200 | 152/200 | +0.0 pts | -6.0–6.0% | 20 / 20 | 1.0000 | 1.0000 |
| W2 − P (one-shot SQL) | 177/200 | 152/200 | +12.5 pts | 7.0–18.5% | 32 / 7 | 7.0e-05 | 0.0003 |
| WB − P (one-shot SQL) | 159/200 | 152/200 | +3.5 pts | -3.5–10.5% | 28 / 21 | 0.3916 | 1.0000 |
| P − A (not in a family) | 152/200 | 182/200 | -15.0 pts | -20.5–-10.0% | 2 / 32 | 6.9e-08 | — |
| W2 − A-model (exploratory) | 177/200 | 183/200 | -3.0 pts | -7.5–1.5% | 7 / 13 | 0.2632 | — |
| A-model − A (exploratory) | 183/200 | 182/200 | +0.5 pts | -2.0–3.0% | 4 / 3 | 1.0000 | — |

*Lenient + rounding*

| Comparison | Level k/n | Ref k/n | Δ accuracy | Paired bootstrap 95% (Δ) | Gained / lost | McNemar p (raw) | Holm-adjusted p |
|---|---:|---:|---:|---|---|---:|---:|
| L2 − A (agent) | 149/200 | 183/200 | -17.0 pts | -23.0–-11.5% | 3 / 37 | 1.9e-08 | 7.8e-08 |
| L3 − A (agent) | 152/200 | 183/200 | -15.5 pts | -21.0–-10.5% | 2 / 33 | 3.7e-08 | 1.1e-07 |
| W2 − A (agent) | 177/200 | 183/200 | -3.0 pts | -7.0–1.0% | 6 / 12 | 0.2379 | 0.2379 |
| WB − A (agent) | 159/200 | 183/200 | -12.0 pts | -17.5–-7.0% | 4 / 28 | 1.9e-05 | 3.9e-05 |
| L2 − P (one-shot SQL) | 149/200 | 152/200 | -1.5 pts | -8.5–5.5% | 24 / 27 | 0.7798 | 1.0000 |
| L3 − P (one-shot SQL) | 152/200 | 152/200 | +0.0 pts | -6.0–6.0% | 20 / 20 | 1.0000 | 1.0000 |
| W2 − P (one-shot SQL) | 177/200 | 152/200 | +12.5 pts | 7.0–18.5% | 32 / 7 | 7.0e-05 | 0.0003 |
| WB − P (one-shot SQL) | 159/200 | 152/200 | +3.5 pts | -3.5–10.5% | 28 / 21 | 0.3916 | 1.0000 |
| P − A (not in a family) | 152/200 | 183/200 | -15.5 pts | -21.0–-10.5% | 1 / 32 | 7.9e-09 | — |
| W2 − A-model (exploratory) | 177/200 | 185/200 | -4.0 pts | -8.0–0.0% | 5 / 13 | 0.0963 | — |
| A-model − A (exploratory) | 185/200 | 183/200 | +1.0 pts | -1.5–3.5% | 4 / 2 | 0.6875 | — |

## 4. Trust metrics per level

T = answers labelled certified/governed; W_T = of those, strict-wrong; precision π = (T − W_T)/T with Wilson 95%; trusted coverage κ = T/n; silent-error rate σ = W_T/n for DQL, (n − k)/n for P and A (no labels, every wrong answer is silent). W_T (lenient+rounding) re-counts W_T under the lenient + rounding grade.

### Set 4 (Sonnet 5.5)

| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| P (one-shot SQL) | 200 | — (no labels) | — | — | — | — | — | 37.0% | — |
| A (agent) | 200 | — (no labels) | — | — | — | — | — | 22.0% | 47/50 / 0 |
| A-model (agent + DQL modeling context) | 200 | — (no labels) | — | — | — | — | — | 16.0% | 47/50 / 0 |
| L2 | 200 | 14 | 1 | 0 | 92.9% | 68.5–98.7% | 7.0% | 0.5% | 43/50 / 2 |
| L3 | 200 | 14 | 2 | 1 | 85.7% | 60.1–96.0% | 7.0% | 1.0% | 41/50 / 2 |
| W2 | 200 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 40/50 / 1 |
| WB | 200 | 26 | 13 | 12 | 50.0% | 32.1–67.9% | 13.0% | 6.5% | 42/50 / 1 |

### Set 3, pooled across models per level (precision CI = question-cluster bootstrap)

| Level | Answers | T | W_T | Precision π | Naive Wilson | Cluster bootstrap | Distinct questions trusted (with wrong) | κ | σ |
|---|---:|---:|---:|---:|---|---|---:|---:|---|
| L0 | 280 | 0 | 0 | — | — | — | 0 (0) | 0.0% | 0.0% — not informative (no trusted answers) |
| L1 | 280 | 0 | 0 | — | — | — | 0 (0) | 0.0% | 0.0% — not informative (no trusted answers) |
| L2 | 280 | 24 | 0 | 100.0% | 86.2–100.0% | 100.0–100.0% | 4 (0) | 8.6% | 0.0% |
| L3 | 280 | 25 | 0 | 100.0% | 86.7–100.0% | 100.0–100.0% | 4 (0) | 8.9% | 0.0% |
| LB | 200 | 50 | 15 | 70.0% | 56.2–80.9% | 41.9–91.1% | 15 (6) | 25.0% | 7.5% |
| W0 | 280 | 0 | 0 | — | — | — | 0 (0) | 0.0% | 0.0% — not informative (no trusted answers) |
| W1 | 280 | 0 | 0 | — | — | — | 0 (0) | 0.0% | 0.0% — not informative (no trusted answers) |
| W2 | 280 | 3 | 3 | 0.0% | 0.0–56.1% | 0.0–0.0% | 1 (1) | 1.1% | 1.1% |
| WB | 200 | 24 | 4 | 83.3% | 64.1–93.3% | 41.7–100.0% | 7 (3) | 12.0% | 2.0% |

### Set 3, per model

**Claude Opus 5.5**

| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| P (one-shot SQL) | 40 | — (no labels) | — | — | — | — | — | 25.0% | — |
| A (agent) | 40 | — (no labels) | — | — | — | — | — | 20.0% | 10/10 / 0 |
| L0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L2 | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | 10/10 / 0 |
| L3 | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | 10/10 / 0 |
| LB | 40 | 11 | 4 | 4 | 63.6% | 35.4–84.8% | 27.5% | 10.0% | 10/10 / 0 |
| W0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W2 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| WB | 40 | 5 | 1 | 1 | 80.0% | 37.5–96.4% | 12.5% | 2.5% | 10/10 / 0 |

**Claude Sonnet 5.5**

| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| P (one-shot SQL) | 40 | — (no labels) | — | — | — | — | — | 32.5% | — |
| A (agent) | 40 | — (no labels) | — | — | — | — | — | 17.5% | 10/10 / 0 |
| L0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L2 | 40 | 3 | 0 | 0 | 100.0% | 43.9–100.0% | 7.5% | 0.0% | 10/10 / 0 |
| L3 | 40 | 3 | 0 | 0 | 100.0% | 43.9–100.0% | 7.5% | 0.0% | 10/10 / 0 |
| LB | 40 | 9 | 3 | 3 | 66.7% | 35.4–87.9% | 22.5% | 7.5% | 10/10 / 0 |
| W0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W2 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| WB | 40 | 5 | 1 | 1 | 80.0% | 37.5–96.4% | 12.5% | 2.5% | 10/10 / 0 |

**Claude Sonnet 5**

| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| P (one-shot SQL) | 40 | — (no labels) | — | — | — | — | — | 37.5% | — |
| L0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L2 | 40 | 3 | 0 | 0 | 100.0% | 43.9–100.0% | 7.5% | 0.0% | 10/10 / 0 |
| L3 | 40 | 3 | 0 | 0 | 100.0% | 43.9–100.0% | 7.5% | 0.0% | 9/10 / 0 |
| LB | 40 | 11 | 4 | 4 | 63.6% | 35.4–84.8% | 27.5% | 10.0% | 10/10 / 0 |
| W0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W2 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| WB | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | 10/10 / 0 |

**Qwen 3.8 27B (local)**

| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| P (one-shot SQL) | 40 | — (no labels) | — | — | — | — | — | 55.0% | — |
| L0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L2 | 40 | 3 | 0 | 0 | 100.0% | 43.9–100.0% | 7.5% | 0.0% | 10/10 / 0 |
| L3 | 40 | 3 | 0 | 0 | 100.0% | 43.9–100.0% | 7.5% | 0.0% | 10/10 / 0 |
| LB | 40 | 11 | 3 | 3 | 72.7% | 43.4–90.2% | 27.5% | 7.5% | 10/10 / 0 |
| W0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W2 | 40 | 1 | 1 | 1 | 0.0% | 0.0–79.3% | 2.5% | 2.5% | 10/10 / 0 |
| WB | 40 | 6 | 2 | 2 | 66.7% | 30.0–90.3% | 15.0% | 5.0% | 10/10 / 0 |

**GPT-6 Luna (max)**

| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| P (one-shot SQL) | 40 | — (no labels) | — | — | — | — | — | 37.5% | — |
| L0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | — |
| L1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | — |
| L2 | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | — |
| L3 | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | — |
| W0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | — |
| W1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | — |
| W2 | 40 | 1 | 1 | 1 | 0.0% | 0.0–79.3% | 2.5% | 2.5% | — |

**GPT-6 Sol (medium)**

| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| P (one-shot SQL) | 40 | — (no labels) | — | — | — | — | — | 35.0% | — |
| L0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 9/10 / 0 |
| L1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L2 | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | — |
| L3 | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | — |
| W0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | — |
| W1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | — |
| W2 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | — |

**GPT-5.6 Terra (high)**

| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| P (one-shot SQL) | 40 | — (no labels) | — | — | — | — | — | 35.0% | — |
| L0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| L2 | 40 | 3 | 0 | 0 | 100.0% | 43.9–100.0% | 7.5% | 0.0% | 9/10 / 0 |
| L3 | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | 10/10 / 0 |
| LB | 40 | 8 | 1 | 1 | 87.5% | 52.9–97.8% | 20.0% | 2.5% | — |
| W0 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W1 | 40 | 0 | 0 | 0 | — | — | 0.0% | 0.0% — not informative (no trusted answers) | 10/10 / 0 |
| W2 | 40 | 1 | 1 | 1 | 0.0% | 0.0–79.3% | 2.5% | 2.5% | 10/10 / 0 |
| WB | 40 | 4 | 0 | 0 | 100.0% | 51.0–100.0% | 10.0% | 0.0% | — |

## 5. Lenient and rounding re-grade (all conditions, both sets)

### Headline

| Scope | Answers | Strict | Lenient | Lenient + rounding | Strict-wrong | wrong_numbers | rounding_only | missing_or_extra_columns | grain_or_shape | abstained | other |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| heldout-3 · all conditions | 2720 | 2014 (74.0%) | 2086 (76.7%) | 2139 (78.6%) | 706 | 217 (30.7%) | 53 (7.5%) | 72 (10.2%) | 93 (13.2%) | 261 (37.0%) | 10 (1.4%) |
| heldout-3 · DQL levels | 2360 | 1772 (75.1%) | 1822 (77.2%) | 1861 (78.9%) | 588 | 179 (30.4%) | 39 (6.6%) | 50 (8.5%) | 59 (10.0%) | 261 (44.4%) | 0 (0.0%) |
| heldout-3 · P (one-shot) | 280 | 177 (63.2%) | 197 (70.4%) | 205 (73.2%) | 103 | 32 (31.1%) | 8 (7.8%) | 20 (19.4%) | 33 (32.0%) | 0 (0.0%) | 10 (9.7%) |
| heldout-3 · A (agent) | 80 | 65 (81.2%) | 67 (83.8%) | 73 (91.2%) | 15 | 6 (40.0%) | 6 (40.0%) | 2 (13.3%) | 1 (6.7%) | 0 (0.0%) | 0 (0.0%) |
| heldout-3 · Claude Opus 5.5 | 440 | 346 (78.6%) | 360 (81.8%) | 386 (87.7%) | 94 | 21 (22.3%) | 26 (27.7%) | 14 (14.9%) | 12 (12.8%) | 21 (22.3%) | 0 (0.0%) |
| heldout-3 · Claude Sonnet 5.5 | 440 | 367 (83.4%) | 380 (86.4%) | 383 (87.0%) | 73 | 22 (30.1%) | 3 (4.1%) | 13 (17.8%) | 14 (19.2%) | 21 (28.8%) | 0 (0.0%) |
| heldout-3 · Claude Sonnet 5 | 400 | 304 (76.0%) | 310 (77.5%) | 318 (79.5%) | 96 | 18 (18.8%) | 8 (8.3%) | 6 (6.2%) | 17 (17.7%) | 45 (46.9%) | 2 (2.1%) |
| heldout-3 · Qwen 3.8 27B (local) | 400 | 242 (60.5%) | 248 (62.0%) | 263 (65.8%) | 158 | 36 (22.8%) | 15 (9.5%) | 6 (3.8%) | 23 (14.6%) | 71 (44.9%) | 7 (4.4%) |
| heldout-3 · GPT-6 Luna (max) | 320 | 235 (73.4%) | 244 (76.2%) | 244 (76.2%) | 85 | 39 (45.9%) | 0 (0.0%) | 9 (10.6%) | 7 (8.2%) | 29 (34.1%) | 1 (1.2%) |
| heldout-3 · GPT-6 Sol (medium) | 320 | 237 (74.1%) | 247 (77.2%) | 248 (77.5%) | 83 | 39 (47.0%) | 1 (1.2%) | 10 (12.0%) | 6 (7.2%) | 27 (32.5%) | 0 (0.0%) |
| heldout-3 · GPT-5.6 Terra (high) | 400 | 283 (70.8%) | 297 (74.2%) | 297 (74.2%) | 117 | 42 (35.9%) | 0 (0.0%) | 14 (12.0%) | 14 (12.0%) | 47 (40.2%) | 0 (0.0%) |
| heldout-4 · all conditions | 1400 | 1064 (76.0%) | 1154 (82.4%) | 1157 (82.6%) | 336 | 144 (42.9%) | 3 (0.9%) | 90 (26.8%) | 46 (13.7%) | 51 (15.2%) | 2 (0.6%) |
| heldout-4 · DQL levels | 800 | 614 (76.8%) | 637 (79.6%) | 637 (79.6%) | 186 | 89 (47.8%) | 0 (0.0%) | 23 (12.4%) | 23 (12.4%) | 51 (27.4%) | 0 (0.0%) |
| heldout-4 · P (one-shot) | 200 | 126 (63.0%) | 152 (76.0%) | 152 (76.0%) | 74 | 25 (33.8%) | 0 (0.0%) | 26 (35.1%) | 21 (28.4%) | 0 (0.0%) | 2 (2.7%) |
| heldout-4 · A (agent) | 200 | 156 (78.0%) | 182 (91.0%) | 183 (91.5%) | 44 | 16 (36.4%) | 1 (2.3%) | 26 (59.1%) | 1 (2.3%) | 0 (0.0%) | 0 (0.0%) |
| heldout-4 · Claude Sonnet 5.5 | 1400 | 1064 (76.0%) | 1154 (82.4%) | 1157 (82.6%) | 336 | 144 (42.9%) | 3 (0.9%) | 90 (26.8%) | 46 (13.7%) | 51 (15.2%) | 2 (0.6%) |
| both sets · all conditions | 4120 | 3078 (74.7%) | 3240 (78.6%) | 3296 (80.0%) | 1042 | 361 (34.6%) | 56 (5.4%) | 162 (15.5%) | 139 (13.3%) | 312 (29.9%) | 12 (1.2%) |
| both sets · Sonnet 5.5 (all its conditions) | 1840 | 1431 (77.8%) | 1534 (83.4%) | 1540 (83.7%) | 409 | 166 (40.6%) | 6 (1.5%) | 103 (25.2%) | 60 (14.7%) | 72 (17.6%) | 2 (0.5%) |
| both sets · agent A (Opus 5.5 + Sonnet 5.5) | 280 | 221 (78.9%) | 249 (88.9%) | 256 (91.4%) | 59 | 22 (37.3%) | 7 (11.9%) | 28 (47.5%) | 2 (3.4%) | 0 (0.0%) | 0 (0.0%) |

Class cells = count (share of strict-wrong answers).

### Per condition, pooled over models

| Set | Condition | Answers | Strict | Lenient | Lenient + rounding | Strict-wrong | wrong_numbers | rounding_only | missing_or_extra_columns | grain_or_shape | abstained | other |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| heldout-3 | P (one-shot SQL) | 280 | 177 | 197 | 205 | 103 | 32 (31.1%) | 8 (7.8%) | 20 (19.4%) | 33 (32.0%) | 0 (0.0%) | 10 (9.7%) |
| heldout-3 | A (agent) | 80 | 65 | 67 | 73 | 15 | 6 (40.0%) | 6 (40.0%) | 2 (13.3%) | 1 (6.7%) | 0 (0.0%) | 0 (0.0%) |
| heldout-3 | L0 | 280 | 134 | 134 | 137 | 146 | 28 (19.2%) | 3 (2.1%) | 0 (0.0%) | 4 (2.7%) | 111 (76.0%) | 0 (0.0%) |
| heldout-3 | L1 | 280 | 219 | 231 | 234 | 61 | 18 (29.5%) | 3 (4.9%) | 12 (19.7%) | 5 (8.2%) | 23 (37.7%) | 0 (0.0%) |
| heldout-3 | L2 | 280 | 218 | 227 | 230 | 62 | 24 (38.7%) | 3 (4.8%) | 9 (14.5%) | 6 (9.7%) | 20 (32.3%) | 0 (0.0%) |
| heldout-3 | L3 | 280 | 217 | 224 | 228 | 63 | 20 (31.7%) | 4 (6.3%) | 7 (11.1%) | 7 (11.1%) | 25 (39.7%) | 0 (0.0%) |
| heldout-3 | LB | 200 | 142 | 148 | 148 | 58 | 15 (25.9%) | 0 (0.0%) | 6 (10.3%) | 10 (17.2%) | 27 (46.6%) | 0 (0.0%) |
| heldout-3 | W0 | 280 | 209 | 213 | 220 | 71 | 18 (25.4%) | 7 (9.9%) | 4 (5.6%) | 13 (18.3%) | 29 (40.8%) | 0 (0.0%) |
| heldout-3 | W1 | 280 | 231 | 235 | 245 | 49 | 20 (40.8%) | 10 (20.4%) | 4 (8.2%) | 7 (14.3%) | 8 (16.3%) | 0 (0.0%) |
| heldout-3 | W2 | 280 | 233 | 238 | 243 | 47 | 24 (51.1%) | 5 (10.6%) | 5 (10.6%) | 2 (4.3%) | 11 (23.4%) | 0 (0.0%) |
| heldout-3 | WB | 200 | 169 | 172 | 176 | 31 | 12 (38.7%) | 4 (12.9%) | 3 (9.7%) | 5 (16.1%) | 7 (22.6%) | 0 (0.0%) |
| heldout-4 | P (one-shot SQL) | 200 | 126 | 152 | 152 | 74 | 25 (33.8%) | 0 (0.0%) | 26 (35.1%) | 21 (28.4%) | 0 (0.0%) | 2 (2.7%) |
| heldout-4 | A (agent) | 200 | 156 | 182 | 183 | 44 | 16 (36.4%) | 1 (2.3%) | 26 (59.1%) | 1 (2.3%) | 0 (0.0%) | 0 (0.0%) |
| heldout-4 | A-model (agent + DQL modeling context) | 200 | 168 | 183 | 185 | 32 | 14 (43.8%) | 2 (6.2%) | 15 (46.9%) | 1 (3.1%) | 0 (0.0%) | 0 (0.0%) |
| heldout-4 | L2 | 200 | 142 | 149 | 149 | 58 | 24 (41.4%) | 0 (0.0%) | 7 (12.1%) | 6 (10.3%) | 21 (36.2%) | 0 (0.0%) |
| heldout-4 | L3 | 200 | 147 | 152 | 152 | 53 | 22 (41.5%) | 0 (0.0%) | 5 (9.4%) | 8 (15.1%) | 18 (34.0%) | 0 (0.0%) |
| heldout-4 | W2 | 200 | 171 | 177 | 177 | 29 | 13 (44.8%) | 0 (0.0%) | 6 (20.7%) | 2 (6.9%) | 8 (27.6%) | 0 (0.0%) |
| heldout-4 | WB | 200 | 154 | 159 | 159 | 46 | 30 (65.2%) | 0 (0.0%) | 5 (10.9%) | 7 (15.2%) | 4 (8.7%) | 0 (0.0%) |

### Per model × condition × set

| Set | Model | Condition | n | Strict | Lenient | +rounding | Strict-wrong | wrong_numbers / rounding_only / missing_or_extra_columns / grain_or_shape / abstained / other | Rows store / re-run / unrunnable | Re-check disagrees |
|---|---|---|---:|---:|---:|---:|---:|---|---|---:|
| heldout-3 | Claude Opus 5.5 | P (one-shot SQL) | 40 | 30 | 33 | 35 | 10 | 2 / 2 / 3 / 3 / 0 / 0 | 0 / 40 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | A (agent) | 40 | 32 | 33 | 37 | 8 | 2 / 4 / 1 / 1 / 0 / 0 | 0 / 40 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | L0 | 40 | 24 | 24 | 26 | 16 | 4 / 2 / 0 / 0 / 10 / 0 | 30 / 0 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | L1 | 40 | 34 | 36 | 38 | 6 | 1 / 2 / 2 / 0 / 1 / 0 | 39 / 0 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | L2 | 40 | 29 | 30 | 32 | 11 | 3 / 2 / 1 / 1 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | L3 | 40 | 33 | 34 | 36 | 7 | 1 / 2 / 1 / 1 / 2 / 0 | 38 / 0 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | LB | 40 | 29 | 31 | 31 | 11 | 3 / 0 / 2 / 2 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | W0 | 40 | 33 | 34 | 37 | 7 | 1 / 3 / 1 / 2 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | W1 | 40 | 32 | 33 | 38 | 8 | 1 / 5 / 1 / 1 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | W2 | 40 | 36 | 37 | 39 | 4 | 1 / 2 / 1 / 0 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | Claude Opus 5.5 | WB | 40 | 34 | 35 | 37 | 6 | 2 / 2 / 1 / 1 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | P (one-shot SQL) | 40 | 27 | 32 | 33 | 13 | 3 / 1 / 5 / 4 / 0 / 0 | 0 / 40 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | A (agent) | 40 | 33 | 34 | 36 | 7 | 4 / 2 / 1 / 0 / 0 / 0 | 0 / 40 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | L0 | 40 | 24 | 24 | 24 | 16 | 4 / 0 / 0 / 1 / 11 / 0 | 29 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | L1 | 40 | 32 | 35 | 35 | 8 | 2 / 0 / 3 / 1 / 2 / 0 | 38 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | L2 | 40 | 35 | 35 | 35 | 5 | 2 / 0 / 0 / 1 / 2 / 0 | 38 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | L3 | 40 | 33 | 34 | 34 | 7 | 2 / 0 / 1 / 2 / 2 / 0 | 38 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | LB | 40 | 31 | 31 | 31 | 9 | 2 / 0 / 0 / 3 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | W0 | 40 | 37 | 38 | 38 | 3 | 1 / 0 / 1 / 1 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | W1 | 40 | 38 | 39 | 39 | 2 | 1 / 0 / 1 / 0 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | W2 | 40 | 39 | 40 | 40 | 1 | 0 / 0 / 1 / 0 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5.5 | WB | 40 | 38 | 38 | 38 | 2 | 1 / 0 / 0 / 1 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | P (one-shot SQL) | 40 | 25 | 26 | 29 | 15 | 4 / 3 / 1 / 5 / 0 / 2 | 0 / 38 / 2 | 0 |
| heldout-3 | Claude Sonnet 5 | L0 | 40 | 20 | 20 | 20 | 20 | 3 / 0 / 0 / 1 / 16 / 0 | 24 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | L1 | 40 | 33 | 34 | 34 | 7 | 0 / 0 / 1 / 1 / 5 / 0 | 35 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | L2 | 40 | 34 | 34 | 34 | 6 | 2 / 0 / 0 / 1 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | L3 | 40 | 29 | 31 | 31 | 11 | 2 / 0 / 2 / 2 / 5 / 0 | 35 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | LB | 40 | 29 | 30 | 30 | 11 | 2 / 0 / 1 / 2 / 6 / 0 | 34 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | W0 | 40 | 29 | 29 | 31 | 11 | 1 / 2 / 0 / 2 / 6 / 0 | 34 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | W1 | 40 | 35 | 35 | 37 | 5 | 1 / 2 / 0 / 1 / 1 / 0 | 39 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | W2 | 40 | 36 | 36 | 37 | 4 | 1 / 1 / 0 / 1 / 1 / 0 | 39 / 0 / 0 | 0 |
| heldout-3 | Claude Sonnet 5 | WB | 40 | 34 | 35 | 35 | 6 | 2 / 0 / 1 / 1 / 2 / 0 | 38 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | P (one-shot SQL) | 40 | 18 | 20 | 21 | 22 | 6 / 1 / 2 / 6 / 0 / 7 | 0 / 33 / 7 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | L0 | 40 | 10 | 10 | 11 | 30 | 1 / 1 / 0 / 2 / 26 / 0 | 14 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | L1 | 40 | 28 | 29 | 30 | 12 | 5 / 1 / 1 / 1 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | L2 | 40 | 27 | 29 | 30 | 13 | 5 / 1 / 2 / 2 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | L3 | 40 | 26 | 27 | 29 | 14 | 1 / 2 / 1 / 2 / 8 / 0 | 32 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | LB | 40 | 23 | 23 | 23 | 17 | 4 / 0 / 0 / 3 / 10 / 0 | 30 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | W0 | 40 | 23 | 23 | 25 | 17 | 5 / 2 / 0 / 3 / 7 / 0 | 33 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | W1 | 40 | 29 | 29 | 32 | 11 | 2 / 3 / 0 / 2 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | W2 | 40 | 27 | 27 | 29 | 13 | 5 / 2 / 0 / 1 / 5 / 0 | 35 / 0 / 0 | 0 |
| heldout-3 | Qwen 3.8 27B (local) | WB | 40 | 31 | 31 | 33 | 9 | 2 / 2 / 0 / 1 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Luna (max) | P (one-shot SQL) | 40 | 25 | 28 | 28 | 15 | 7 / 0 / 3 / 4 / 0 / 1 | 0 / 39 / 1 | 0 |
| heldout-3 | GPT-6 Luna (max) | L0 | 40 | 19 | 19 | 19 | 21 | 6 / 0 / 0 / 0 / 15 / 0 | 25 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Luna (max) | L1 | 40 | 32 | 33 | 33 | 8 | 3 / 0 / 1 / 1 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Luna (max) | L2 | 40 | 32 | 34 | 34 | 8 | 4 / 0 / 2 / 0 / 2 / 0 | 38 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Luna (max) | L3 | 40 | 32 | 33 | 33 | 8 | 4 / 0 / 1 / 0 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Luna (max) | W0 | 40 | 30 | 30 | 30 | 10 | 4 / 0 / 0 / 1 / 5 / 0 | 35 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Luna (max) | W1 | 40 | 34 | 35 | 35 | 6 | 4 / 0 / 1 / 1 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Luna (max) | W2 | 40 | 31 | 32 | 32 | 9 | 7 / 0 / 1 / 0 / 1 / 0 | 39 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Sol (medium) | P (one-shot SQL) | 40 | 26 | 30 | 31 | 14 | 6 / 1 / 4 / 3 / 0 / 0 | 0 / 40 / 0 | 0 |
| heldout-3 | GPT-6 Sol (medium) | L0 | 40 | 20 | 20 | 20 | 20 | 6 / 0 / 0 / 0 / 14 / 0 | 26 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Sol (medium) | L1 | 40 | 30 | 32 | 32 | 10 | 4 / 0 / 2 / 0 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Sol (medium) | L2 | 40 | 31 | 33 | 33 | 9 | 4 / 0 / 2 / 0 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Sol (medium) | L3 | 40 | 33 | 33 | 33 | 7 | 5 / 0 / 0 / 0 / 2 / 0 | 38 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Sol (medium) | W0 | 40 | 30 | 31 | 31 | 10 | 3 / 0 / 1 / 2 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Sol (medium) | W1 | 40 | 32 | 32 | 32 | 8 | 7 / 0 / 0 / 1 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | GPT-6 Sol (medium) | W2 | 40 | 35 | 36 | 36 | 5 | 4 / 0 / 1 / 0 / 0 / 0 | 40 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | P (one-shot SQL) | 40 | 26 | 28 | 28 | 14 | 4 / 0 / 2 / 8 / 0 / 0 | 0 / 40 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | L0 | 40 | 17 | 17 | 17 | 23 | 4 / 0 / 0 / 0 / 19 / 0 | 21 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | L1 | 40 | 30 | 32 | 32 | 10 | 3 / 0 / 2 / 1 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | L2 | 40 | 30 | 32 | 32 | 10 | 4 / 0 / 2 / 1 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | L3 | 40 | 31 | 32 | 32 | 9 | 5 / 0 / 1 / 0 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | LB | 40 | 30 | 33 | 33 | 10 | 4 / 0 / 3 / 0 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | W0 | 40 | 27 | 28 | 28 | 13 | 3 / 0 / 1 / 2 / 7 / 0 | 33 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | W1 | 40 | 31 | 32 | 32 | 9 | 4 / 0 / 1 / 1 / 3 / 0 | 37 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | W2 | 40 | 29 | 30 | 30 | 11 | 6 / 0 / 1 / 0 / 4 / 0 | 36 / 0 / 0 | 0 |
| heldout-3 | GPT-5.6 Terra (high) | WB | 40 | 32 | 33 | 33 | 8 | 5 / 0 / 1 / 1 / 1 / 0 | 39 / 0 / 0 | 0 |
| heldout-4 | Claude Sonnet 5.5 | P (one-shot SQL) | 200 | 126 | 152 | 152 | 74 | 25 / 0 / 26 / 21 / 0 / 2 | 0 / 198 / 2 | 0 |
| heldout-4 | Claude Sonnet 5.5 | A (agent) | 200 | 156 | 182 | 183 | 44 | 16 / 1 / 26 / 1 / 0 / 0 | 0 / 200 / 0 | 0 |
| heldout-4 | Claude Sonnet 5.5 | A-model (agent + DQL modeling context) | 200 | 168 | 183 | 185 | 32 | 14 / 2 / 15 / 1 / 0 / 0 | 0 / 200 / 0 | 0 |
| heldout-4 | Claude Sonnet 5.5 | L2 | 200 | 142 | 149 | 149 | 58 | 24 / 0 / 7 / 6 / 21 / 0 | 179 / 0 / 0 | 0 |
| heldout-4 | Claude Sonnet 5.5 | L3 | 200 | 147 | 152 | 152 | 53 | 22 / 0 / 5 / 8 / 18 / 0 | 182 / 0 / 0 | 0 |
| heldout-4 | Claude Sonnet 5.5 | W2 | 200 | 171 | 177 | 177 | 29 | 13 / 0 / 6 / 2 / 8 / 0 | 192 / 0 / 0 | 0 |
| heldout-4 | Claude Sonnet 5.5 | WB | 200 | 154 | 159 | 159 | 46 | 30 / 0 / 5 / 7 / 4 / 0 | 196 / 0 / 0 | 0 |

### Sub-kinds, pooled (both sets, all conditions)

| Class:sub-kind | Count |
|---|---:|
| wrong_numbers:values_differ | 275 |
| abstained:no_sql | 244 |
| missing_or_extra_columns:label_column_substituted | 120 |
| wrong_numbers:listing_values_differ | 86 |
| abstained:asked_to_clarify | 68 |
| rounding_only:gold_rounded_0_to_4_decimals | 56 |
| grain_or_shape:empty_result | 50 |
| grain_or_shape:list_for_a_total | 38 |
| missing_or_extra_columns:label_case_or_format | 31 |
| grain_or_shape:total_for_a_list | 27 |
| grain_or_shape:more_rows | 21 |
| other:sql_did_not_rerun | 12 |
| missing_or_extra_columns:label_column_missing | 11 |
| grain_or_shape:rows_merged_into_total | 2 |
| grain_or_shape:fewer_rows | 1 |

Checks: re-applying the strict rule to the graded rows disagrees with the recorded verdict for 0 of 4120 answers; 12 answers have SQL with no stored result that fails on re-run (class `other`); 0 stored results had conflicting rows for the same SQL (first kept). For comparability, the regrade.mjs rounding rule (d = 1..4 only) gives 3295 lenient+rounding answers against 3296 with d = 0..4. Sensitivity (not in the headline): also accepting answers that equal the gold only after rounding the *answer* to the gold's 1–4 decimals gives 3296.

## 6. The lenient-vs-strict sentence, corrected

The earlier re-grade of set 3 (2,240 answers: 56 model×condition cells, Opus 5.5, Sonnet 5, Qwen and the GPT runs available on 29 September, before the LB/WB build filter) found **1,612 strict-correct and 1,667 lenient-correct** answers: lenient exceeded strict by 55 answers (2.5 points). Correct statement: strict k = 1,612, lenient k = 1,667 (lenient is the larger number).

With every condition now graded (all seven models, P, A, all DQL levels, LB/WB on build 627009a1 only): set 3 has **strict 2,014 and lenient 2,086** of 2,720 answers (lenient + rounding 2,139); set 4 (Sonnet 5.5) has strict 1,064, lenient 1,154, lenient + rounding 1,157 of 1,400.

Suggested wording: *On set 3, 2,014 of 2,720 answers were correct under the strict rule and 2,086 under the lenient rule (+2.6 points). The gap is not uniform: +2.1 points for DQL levels, +7.1 for one-shot SQL and +2.5 for the agent on set 3; on set 4, +2.9 for DQL levels against +13.0 (one-shot) and +13.0 (agent), mostly answers that return a different label column (e.g. a name for an id) with the right numbers.*

The draft's conclusion that "the strict scores do not depend on column naming" holds for the pooled set-3 total but not for comparisons against the baselines: see the lenient sensitivity of the set-4 paired tests in section 3.


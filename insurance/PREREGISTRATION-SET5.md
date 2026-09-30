# Pre-registration: sealed set 5

Written and committed on 30 September 2026, before set 5 exists and before any system is run on it.
The git commit that adds this file is the timestamp. Nothing below may change after set 5 is written;
any deviation is reported as a deviation.

## Why

Sets 3 and 4 were analysed after the fact: the headline condition (W2) was chosen after seeing results,
four conditions were compared with the agent without correction, the agent lacked the modeling context
DQL had, and the question writer was a Claude model while three evaluated models were Claude. Set 5
fixes all four.

## The question set

- 200 answerable questions (50 per quadrant of question complexity × schema complexity) and 50
  unanswerable questions, including near-miss questions that invite an answer from a similar column.
- Written by **GPT-6 Sol** (OpenAI, via the Codex CLI with an isolated home directory), not by a Claude
  model. The writer sees only a copy of the warehouse and the file-format specification. Its command
  log is kept and checked afterwards for any access outside its working directory; any such access is
  reported.
- Reference answers come from executing the writer's SQL. Before scoring, a person audits a random 25%
  sample (50 answerable, 13 unanswerable items); the audit result is reported, and the benchmark is
  scored both on all items and without items the audit finds wrong.
- The DQL developers do not read the questions. Only aggregate results are inspected. No DQL change is
  made because of anything set 5 shows; the first such change ends set 5's use.

## The system

- DQL is frozen before set 5 is run: the release that will accompany the paper, identified by its git
  commit and npm version, recorded here when known: `DQL build: ________`.
- Every condition runs once on that build.

## Conditions

| Id | Condition |
|---|---|
| P | One-shot SQL from the full table definitions |
| A-ddl | Agent with database tools and the table definitions |
| A-model | Agent with database tools, the table definitions and DQL's W2 knowledge (`insurance/contexts/w2-modeling.txt`) |
| L2, L3, W2, WB | DQL levels as defined in the paper |

## Models

- **Primary:** Claude Sonnet 5.5 (`claude-sonnet-5-5`), Claude Code CLI, DQL's per-step reasoning effort.
- **Secondary:** GPT-6 Sol (`gpt-6-sol`, medium) and Qwen 3.8 27B (local), same conditions.

## Primary hypothesis (one test, no correction)

**H1.** On set 5 with the primary model, DQL W2 answers a different share of questions correctly than
A-model. Test: exact two-sided McNemar on the 200 paired answers, α = 0.05. Reported with the paired
difference and its question-level bootstrap 95% interval (10,000 resamples, seed 5).

## Secondary analyses (Holm–Bonferroni within each family)

1. Accuracy of each of L2, L3, W2, WB against P and against A-model (two families of four tests).
2. Trust precision at L2 and L3 with Wilson intervals, and the number of distinct questions with a
   trusted answer; hypothesis: precision ≥ 0.95 (report the lower confidence bound).
3. Correct abstention on the 50 unanswerable questions for each DQL level against A-model (exact McNemar,
   Holm), and the number of unanswerable questions answered with a trusted label.
4. Silent-error rate σ and trusted coverage κ per condition; σ is reported as uninformative where κ = 0.

## Scoring

- Primary: strict row match (multiset, ignoring column names and order).
- Secondary: lenient (numeric columns match row by row) and lenient + rounding (differences that vanish
  when the reference value is rounded to 0–4 decimals count as correct).
- Provider usage limits are never scored; refused questions are asked again after the reset.
- No question is removed except by the audit rule above; both scorings are reported.

## Analysis code

The statistics script used for sets 3 and 4 (`stats_v2.py`: Wilson and question-level bootstrap intervals, exact McNemar, Holm), committed to the repository with the release and run unchanged except for the set name.

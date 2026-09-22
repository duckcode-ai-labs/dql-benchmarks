# Spider 2.0-Lite (SQLite subset) — first measured runs

87 of the 135 SQLite tasks, over the 23 databases the authors publish
(7 databases are missing upstream, so 48 tasks are out of scope here).
Every number below is the official evaluator (`evaluate_spider2sql`, sql mode)
on the same 87 questions, with `gpt-5.6-luna` through the Codex subscription.
A task with no SQL counts as wrong, so a refusal is never dropped from the
denominator.

## The three arms

| Arm | What it is |
| --- | --- |
| `baseline` | The model alone: every `CREATE` statement of the database in the prompt, no DQL |
| `S0` | DQL warehouse-first over the raw database, schema synced, no model |
| `S1a` | S0 plus the model DQL drafts for itself (`apply-discovery --validate`), unreviewed |

## Results

Run `sp-c` (2026-09-20), DQL at `c67dbf81`; baseline from run `sp-b`.

| Arm | Correct | 95% CI | Returned SQL | Wrong shown as trustworthy | Median |
| --- | ---: | --- | ---: | ---: | ---: |
| baseline (model alone) | 40/87 (46.0%) | 35.9–56.4% | 87 | 0 (it has no trust labels) | 20 s |
| DQL S1a | 19/87 (21.8%) | 14.5–31.6% | 46 | 0 | 64 s |
| DQL S0 | 13/87 (14.9%) | 8.9–23.9% | 42 | 0 | 66 s |

Paired, all on the same 87 questions:

- S1a vs S0: S1a only 11, S0 only 5, exact McNemar p = 0.210.
- baseline vs S1a: baseline only 26, S1a only 5, p < 0.001.

## What the first runs found

Run `sp-a` measured DQL before any of today's fixes: S0 12/87, S1a 3/87
(S0 only 11, S1a only 2, p = 0.022) — **the drafted model made Ask
significantly worse**. Every question went one of these ways:

| Outcome | sp-a (before) | sp-c (after) |
| --- | ---: | ---: |
| Returned SQL | 26 | 42 |
| Refused: "the tables do not hold it" | 27 | — |
| Blocked: the drafted SQL failed a check | 11 | — |
| Refused: read as "explain why" | 8 | 0 |
| Refused: privacy guard | 2 | 0 |
| Crash (`toEntity.keys is not iterable`) | 7 (S1a) | 0 |

Five product bugs came out of it, each fixed with a test and with the dbt
golden replays (jaffle 46/46, NBA 18/18, office 5/5) unchanged:

1. `88e91afd` a relationship check ran a many-to-many join — about 15 billion
   row pairs on `complex_oracle`, which a real warehouse would bill for.
2. `6c69f0a8` a table called `constructor` crashed modeling (JavaScript's own
   `Object.constructor` came back from the lookup), blocking all 9 f1 questions.
3. `502851cf` three false refusals: `driver`/`reason`/`investment` read as
   "explain why"; "race" read as a protected attribute; and the card budget.
4. `c67dbf81` a warehouse project showed Ask its table names with **no
   columns** — the catalog's columns were kept in a ranking-only side channel.

After them, modeling helps rather than hurts (S1a 21.8% vs S0 14.9%), and DQL
answers 42–46 of 87 instead of 26.

## What is still open

DQL remains well below the plain model (21.8% vs 46.0%, p < 0.001), and the
gap is no longer refusals — it is the answers themselves. On the questions
where DQL answered and the baseline was right:

- **The reading changes the question's shape.** "The median value of total
  sales in countries with more than 4 customers" (one number) was read as
  "the median total sales for each country" (four rows).
- **Subtle SQL modelling errors.** Asked for the median of each team's best
  season, DQL summed home and away goals as separate season rows instead of
  one total per team-season.

A plausible cause of the second, untested: the SQL writer works from compressed
cards — column names only, 40 per table, no types and no keys — while the
baseline reads the full `CREATE TABLE` text.

## Harness notes

- A runtime that dies mid-database used to be scored as refusals (5 cases in
  `sp-a`, 8 in `sp-b`). The harness now records how the server ended and runs
  that database again.
- `run.mjs` resumes database by database; its summary now includes the
  databases an earlier invocation finished, so a resumed run is scored whole.
- The baseline arm writes the same layout, so `score.py` grades all three the
  same way.

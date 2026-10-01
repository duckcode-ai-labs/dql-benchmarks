# Insurance runs re-graded: strict vs lenient

Generated 2026-09-29T21:39:01.934Z by `regrade.mjs` in this folder (`node work/insurance/analysis-2026-09-29/regrade/regrade.mjs`; re-runnable, read-only on runs/, projects/ and the source tree, no model or network calls). Scope: runs fl-opus, fl-sonnet, fl-qwen, fl-luna, fl-sol, fl-terra; levels baseline-full, L0, L1, L2, L3, LB, W0, W1, W2, WB; sets heldout-3 and all. Held-out results appear as counts only.

## Method

**Which rows are graded.** For a DQL run, the rows the answer actually showed are read from a copy of the run store (`<run>/<level>/<set>[.attempt-N]/project/.dql/local/agent-runs.sqlite` → `agent_run_artifacts` → `{ sql, result }`), matched to `results[].answer.sql` by identical SQL text. These include what DQL computes after the query (a governed ratio metric such as average loss per claim is numerator ÷ denominator in DQL, not in the SQL). When no stored result exists, the recorded SQL is re-run on a byte copy of the layer's warehouse template (`work/insurance/projects/<layer>/acme_insurance.duckdb`, opened read-only, external access off). The text-to-SQL baseline is always re-run, on the L0 warehouse as `insurance/baseline-text2sql.mjs` does. Gold rows are the ones the run was judged against (`results[].expected.goldRows`; the gold file for the baseline).

**Strict** (the published number) — the run's own `executionMatched`: the answer's rows equal the correct rows as a multiset; column names and column order are ignored; extra answer columns are allowed; numbers compare after rounding to 1e-6; a date equals a midnight timestamp of the same day. This script recomputes it from the graded rows as a check.

**Lenient ("measures")** — in the spirit of Cube's strict vs OLAP-aware verdicts: strict-right, **or** all of
1. the answer has exactly as many rows as the correct answer;
2. the correct answer has at least one *measure* column (a listing question — ids, names, dates only — keeps its strict verdict);
3. after dropping the correct answer's *label* columns, every measure column is matched by some answer column **row by row**, with the strict value rule.

So lenient accepts an answer whose numbers are right but that leaves out a label/id column, returns a different label for the same rows (a party name where the gold has the party id), or writes the same label in a different case/format. It does **not** accept a different row count (a list answered as a total or vice versa, merged, missing or extra rows), numbers that differ even by rounding, right numbers attached to the wrong rows, or a wrong listing.

*Measure* columns of the correct answer: those its top-level SELECT aggregates or computes (`sum/count/avg/min/max/datediff/…` or arithmetic), whose name reads like a number and not like an id or label (`total`, `amount`, `loss`, `premium`, `ratio`, `count`, `no_of` …; names ending `_id/_number/_code/_name/_date` or containing `identifier` are labels), or whose values are fractional. Everything else (ids, policy/claim numbers, names, dates) is a label. This widens `insurance/regrade.mjs`'s rule (which misses CTE queries and bare names like `Loss`); a wider measure set makes lenient stricter.

Two further columns, reported beside the headline and not part of it: **lenient + rounding** also accepts measure values that equal the correct values rounded to 1–4 decimals (the answer presented a rounded average or ratio); **cellCover** is `insurance/regrade.mjs`'s own "measures" rule (every gold measure value appears somewhere among the answer's cells, no row-count or row-alignment check) — looser than lenient.

**Why a strict-wrong answer was wrong** (first rule that applies):

1. **stopped** — no SQL recorded: the run stopped (`no_sql`) or asked to clarify (`asked_to_clarify`).
2. **other** — SQL recorded but no stored result and it fails on re-run (`sql_did_not_rerun`; in practice baseline SQL that never ran), or the rows match although the run said wrong (`rows_match_gold_but_recorded_wrong`; none found).
3. **grain_or_shape** — the row count differs: `list_for_a_total` (1 gold row, several answer rows), `total_for_a_list`, `rows_merged_into_total` (fewer rows carrying the gold measures summed), `empty_result`, `more_rows`, `extra_rows_gold_rows_inside` (all gold rows plus more, typically a missing filter), `fewer_rows`, `missing_rows_subset_of_gold`.
4. **missing_or_extra_columns** — same row count and every measure matches row by row, but a label column is `label_column_missing`, `label_column_substituted` (a different label, e.g. name for id), `label_case_or_format` (same label, different case/format), or `label_column_differs` (label present but paired with the rows differently); for a listing question, `listing_column_missing` (a strict subset of the correct columns; not lenient-right).
5. **wrong_numbers** — same row count but measure values differ: `values_differ`, `rounding_or_precision` (equal after rounding the gold to 1–4 decimals), `numbers_on_wrong_rows` (each measure column's values are present but paired with the wrong rows); for a listing question, `listing_values_differ` (the listed ids/dates are wrong).

**Trust.** An answer is *trusted* when `answer.trustState` is `certified` or `governed`. Wrong-trusted is reported as strict-wrong ÷ trusted and "numbers-only" = trusted answers classed `wrong_numbers` ÷ trusted (a trusted answer that is wrong only in shape or label is excluded from numbers-only). The per-cell tables also give lenient-wrong and numbers-only excluding rounding.

**Skipped reports**: fl-luna L0 all (invalid: the AI provider refused calls during the run); fl-sol W0 all (invalid: the AI provider refused calls during the run); fl-terra W2 all (invalid: the AI provider refused calls during the run).

## Held-out set `heldout-3` (40 questions, sealed — counts only)

### Accuracy, strict → lenient (%)

Cell = strict % → lenient %. Denominator 40.

| Level | opus | sonnet | qwen | luna | sol | terra |
|---|---:|---:|---:|---:|---:|---:|
| baseline-full | 75.0 → **82.5** | 62.5 → **65.0** | 45.0 → **50.0** | 62.5 → **70.0** | 65.0 → **75.0** | 65.0 → **70.0** |
| L0 | 60.0 → **60.0** | 50.0 → **50.0** | 25.0 → **25.0** | 47.5 → **47.5** | 50.0 → **50.0** | 42.5 → **42.5** |
| L1 | 85.0 → **90.0** | 82.5 → **85.0** | 70.0 → **72.5** | 80.0 → **82.5** | 75.0 → **80.0** | 75.0 → **80.0** |
| L2 | 72.5 → **75.0** | 85.0 → **85.0** | 67.5 → **72.5** | 80.0 → **85.0** | 77.5 → **82.5** | 75.0 → **80.0** |
| L3 | 82.5 → **85.0** | 72.5 → **77.5** | 65.0 → **67.5** | 80.0 → **82.5** | 82.5 → **82.5** | 77.5 → **80.0** |
| LB | 72.5 → **77.5** | 72.5 → **75.0** | 57.5 → **57.5** | — | 72.5 → **75.0** | 75.0 → **75.0** |
| W0 | 82.5 → **85.0** | 72.5 → **72.5** | 57.5 → **57.5** | 75.0 → **75.0** | 75.0 → **77.5** | 67.5 → **70.0** |
| W1 | 80.0 → **82.5** | 87.5 → **87.5** | 72.5 → **72.5** | 85.0 → **87.5** | 80.0 → **80.0** | 77.5 → **80.0** |
| W2 | 90.0 → **92.5** | 90.0 → **90.0** | 67.5 → **67.5** | 77.5 → **80.0** | 87.5 → **90.0** | 72.5 → **75.0** |
| WB | 85.0 → **87.5** | 85.0 → **87.5** | 77.5 → **77.5** | — | — | — |

### Accuracy, lenient + rounding (%)

| Level | opus | sonnet | qwen | luna | sol | terra |
|---|---:|---:|---:|---:|---:|---:|
| baseline-full | 85.0 | 72.5 | 52.5 | 70.0 | 77.5 | 70.0 |
| L0 | 65.0 | 50.0 | 27.5 | 47.5 | 50.0 | 42.5 |
| L1 | 95.0 | 85.0 | 75.0 | 82.5 | 80.0 | 80.0 |
| L2 | 80.0 | 85.0 | 75.0 | 85.0 | 82.5 | 80.0 |
| L3 | 90.0 | 77.5 | 72.5 | 82.5 | 82.5 | 80.0 |
| LB | 77.5 | 75.0 | 57.5 | — | 75.0 | 75.0 |
| W0 | 92.5 | 77.5 | 62.5 | 75.0 | 77.5 | 70.0 |
| W1 | 95.0 | 92.5 | 80.0 | 87.5 | 80.0 | 80.0 |
| W2 | 97.5 | 92.5 | 72.5 | 80.0 | 90.0 | 75.0 |
| WB | 92.5 | 87.5 | 82.5 | — | — | — |

### Trusted answers that were wrong: strict vs numbers-only

Cell = strict-wrong/trusted · wrong-numbers/trusted. Levels without certified blocks or governed metrics trust nothing.

| Level | opus | sonnet | qwen | luna | sol | terra |
|---|---:|---:|---:|---:|---:|---:|
| baseline-full | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted |
| L0 | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted |
| L1 | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted |
| L2 | 0/4 (0.0%) · 0/4 (0.0%) | 0/3 (0.0%) · 0/3 (0.0%) | 0/3 (0.0%) · 0/3 (0.0%) | 0/4 (0.0%) · 0/4 (0.0%) | 0/4 (0.0%) · 0/4 (0.0%) | 0/3 (0.0%) · 0/3 (0.0%) |
| L3 | 0/4 (0.0%) · 0/4 (0.0%) | 0/3 (0.0%) · 0/3 (0.0%) | 0/3 (0.0%) · 0/3 (0.0%) | 0/4 (0.0%) · 0/4 (0.0%) | 0/4 (0.0%) · 0/4 (0.0%) | 0/4 (0.0%) · 0/4 (0.0%) |
| LB | 4/11 (36.4%) · 2/11 (18.2%) | 4/11 (36.4%) · 2/11 (18.2%) | 3/11 (27.3%) · 1/11 (9.1%) | — | 3/10 (30.0%) · 2/10 (20.0%) | 1/7 (14.3%) · 1/7 (14.3%) |
| W0 | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted |
| W1 | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted |
| W2 | 0 trusted | 0 trusted | 1/1 (100.0%) · 1/1 (100.0%) | 1/1 (100.0%) · 1/1 (100.0%) | 0 trusted | 1/1 (100.0%) · 1/1 (100.0%) |
| WB | 1/5 (20.0%) · 1/5 (20.0%) | 0/4 (0.0%) · 0/4 (0.0%) | 2/6 (33.3%) · 1/6 (16.7%) | — | — | — |

### Strict-wrong answers by class

Cell = wrong_numbers / missing_or_extra_columns / grain_or_shape / stopped / other.

| Level | opus | sonnet | qwen | luna | sol | terra |
|---|---:|---:|---:|---:|---:|---:|
| baseline-full | 4 / 3 / 3 / 0 / 0 | 7 / 1 / 5 / 0 / 2 | 7 / 2 / 6 / 0 / 7 | 7 / 3 / 4 / 0 / 1 | 7 / 4 / 3 / 0 / 0 | 4 / 2 / 8 / 0 / 0 |
| L0 | 6 / 0 / 0 / 10 / 0 | 3 / 0 / 1 / 16 / 0 | 2 / 0 / 2 / 26 / 0 | 6 / 0 / 0 / 15 / 0 | 6 / 0 / 0 / 14 / 0 | 4 / 0 / 0 / 19 / 0 |
| L1 | 3 / 2 / 0 / 1 / 0 | 0 / 1 / 1 / 5 / 0 | 6 / 1 / 1 / 4 / 0 | 3 / 1 / 1 / 3 / 0 | 4 / 2 / 0 / 4 / 0 | 3 / 2 / 1 / 4 / 0 |
| L2 | 5 / 1 / 1 / 4 / 0 | 2 / 0 / 1 / 3 / 0 | 6 / 2 / 2 / 3 / 0 | 4 / 2 / 0 / 2 / 0 | 4 / 2 / 0 / 3 / 0 | 4 / 2 / 1 / 3 / 0 |
| L3 | 3 / 1 / 1 / 2 / 0 | 2 / 2 / 2 / 5 / 0 | 3 / 1 / 2 / 8 / 0 | 4 / 1 / 0 / 3 / 0 | 5 / 0 / 0 / 2 / 0 | 5 / 1 / 0 / 3 / 0 |
| LB | 3 / 2 / 2 / 4 / 0 | 2 / 1 / 2 / 6 / 0 | 4 / 0 / 3 / 10 / 0 | — | 6 / 1 / 1 / 3 / 0 | 4 / 0 / 2 / 4 / 0 |
| W0 | 4 / 1 / 2 / 0 / 0 | 3 / 0 / 2 / 6 / 0 | 7 / 0 / 3 / 7 / 0 | 4 / 0 / 1 / 5 / 0 | 3 / 1 / 2 / 4 / 0 | 3 / 1 / 2 / 7 / 0 |
| W1 | 6 / 1 / 1 / 0 / 0 | 3 / 0 / 1 / 1 / 0 | 5 / 0 / 2 / 4 / 0 | 4 / 1 / 1 / 0 / 0 | 7 / 0 / 1 / 0 / 0 | 4 / 1 / 1 / 3 / 0 |
| W2 | 3 / 1 / 0 / 0 / 0 | 2 / 0 / 1 / 1 / 0 | 7 / 0 / 1 / 5 / 0 | 7 / 1 / 0 / 1 / 0 | 4 / 1 / 0 / 0 / 0 | 6 / 1 / 0 / 4 / 0 |
| WB | 4 / 1 / 1 / 0 / 0 | 2 / 1 / 1 / 2 / 0 | 4 / 0 / 1 / 4 / 0 | — | — | — |

### Why strict-wrong answers were wrong — pooled

| Scope | Strict-wrong | wrong_numbers | missing_or_extra_columns | grain_or_shape | stopped | other |
|---|---:|---:|---:|---:|---:|---:|
| all models, all levels | 628 | 240 (38.2%) | 55 (8.8%) | 80 (12.7%) | 243 (38.7%) | 10 (1.6%) |
| all models, DQL levels only | 538 | 204 (37.9%) | 40 (7.4%) | 51 (9.5%) | 243 (45.2%) | 0 (0.0%) |
| all models, baseline only | 90 | 36 (40.0%) | 15 (16.7%) | 29 (32.2%) | 0 (0.0%) | 10 (11.1%) |
| opus | 86 | 41 (47.7%) | 13 (15.1%) | 11 (12.8%) | 21 (24.4%) | 0 (0.0%) |
| sonnet | 96 | 26 (27.1%) | 6 (6.3%) | 17 (17.7%) | 45 (46.9%) | 2 (2.1%) |
| qwen | 158 | 51 (32.3%) | 6 (3.8%) | 23 (14.6%) | 71 (44.9%) | 7 (4.4%) |
| luna | 85 | 39 (45.9%) | 9 (10.6%) | 7 (8.2%) | 29 (34.1%) | 1 (1.2%) |
| sol | 94 | 46 (48.9%) | 11 (11.7%) | 7 (7.4%) | 30 (31.9%) | 0 (0.0%) |
| terra | 109 | 37 (33.9%) | 10 (9.2%) | 15 (13.8%) | 47 (43.1%) | 0 (0.0%) |

| Class:sub-kind (pooled) | Count |
|---|---:|
| stopped:no_sql | 197 |
| wrong_numbers:values_differ | 172 |
| stopped:asked_to_clarify | 46 |
| wrong_numbers:rounding_or_precision | 45 |
| missing_or_extra_columns:label_column_substituted | 33 |
| grain_or_shape:empty_result | 27 |
| grain_or_shape:list_for_a_total | 25 |
| wrong_numbers:listing_values_differ | 23 |
| missing_or_extra_columns:label_case_or_format | 22 |
| grain_or_shape:more_rows | 18 |
| grain_or_shape:total_for_a_list | 10 |
| other:sql_did_not_rerun | 10 |

Trusted answers, pooled: 111 trusted; strict-wrong 21, lenient-wrong 21, wrong numbers 13 (13 excluding rounding). Why: wrong_numbers:values_differ 13, grain_or_shape:more_rows 5, grain_or_shape:list_for_a_total 3.

### Per cell detail

| Model | Level | n | Strict | Check | Rows from store / re-run | Re-run disagrees | Lenient | +rounding | cellCover | Trusted | Trusted-wrong strict / lenient / numbers / numbers ex-rounding |
|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|---|
| opus | baseline-full | 40 | 30 | ok | 0 / 40 | 0 | 33 | 34 | 33 | 0 | 0 / 0 / 0 / 0 |
| opus | L0 | 40 | 24 | ok | 30 / 0 | 0 | 24 | 26 | 24 | 0 | 0 / 0 / 0 / 0 |
| opus | L1 | 40 | 34 | ok | 39 / 0 | 0 | 36 | 38 | 36 | 0 | 0 / 0 / 0 / 0 |
| opus | L2 | 40 | 29 | ok | 36 / 0 | 0 | 30 | 32 | 30 | 4 | 0 / 0 / 0 / 0 |
| opus | L3 | 40 | 33 | ok | 38 / 0 | 0 | 34 | 36 | 34 | 4 | 0 / 0 / 0 / 0 |
| opus | LB | 40 | 29 | ok | 36 / 0 | 1 | 31 | 31 | 31 | 11 | 4 / 4 / 2 / 2 |
| opus | W0 | 40 | 33 | ok | 40 / 0 | 0 | 34 | 37 | 35 | 0 | 0 / 0 / 0 / 0 |
| opus | W1 | 40 | 32 | ok | 40 / 0 | 0 | 33 | 38 | 34 | 0 | 0 / 0 / 0 / 0 |
| opus | W2 | 40 | 36 | ok | 40 / 0 | 0 | 37 | 39 | 37 | 0 | 0 / 0 / 0 / 0 |
| opus | WB | 40 | 34 | ok | 40 / 0 | 1 | 35 | 37 | 35 | 5 | 1 / 1 / 1 / 1 |
| sonnet | baseline-full | 40 | 25 | ok | 0 / 38 (+2 unrunnable) | 0 | 26 | 29 | 26 | 0 | 0 / 0 / 0 / 0 |
| sonnet | L0 | 40 | 20 | ok | 24 / 0 | 0 | 20 | 20 | 20 | 0 | 0 / 0 / 0 / 0 |
| sonnet | L1 | 40 | 33 | ok | 35 / 0 | 0 | 34 | 34 | 34 | 0 | 0 / 0 / 0 / 0 |
| sonnet | L2 | 40 | 34 | ok | 37 / 0 | 0 | 34 | 34 | 34 | 3 | 0 / 0 / 0 / 0 |
| sonnet | L3 | 40 | 29 | ok | 35 / 0 | 0 | 31 | 31 | 31 | 3 | 0 / 0 / 0 / 0 |
| sonnet | LB | 40 | 29 | ok | 34 / 0 | 1 | 30 | 30 | 30 | 11 | 4 / 4 / 2 / 2 |
| sonnet | W0 | 40 | 29 | ok | 34 / 0 | 0 | 29 | 31 | 30 | 0 | 0 / 0 / 0 / 0 |
| sonnet | W1 | 40 | 35 | ok | 39 / 0 | 0 | 35 | 37 | 35 | 0 | 0 / 0 / 0 / 0 |
| sonnet | W2 | 40 | 36 | ok | 39 / 0 | 0 | 36 | 37 | 36 | 0 | 0 / 0 / 0 / 0 |
| sonnet | WB | 40 | 34 | ok | 38 / 0 | 1 | 35 | 35 | 35 | 4 | 0 / 0 / 0 / 0 |
| qwen | baseline-full | 40 | 18 | ok | 0 / 33 (+7 unrunnable) | 0 | 20 | 21 | 20 | 0 | 0 / 0 / 0 / 0 |
| qwen | L0 | 40 | 10 | ok | 14 / 0 | 0 | 10 | 11 | 10 | 0 | 0 / 0 / 0 / 0 |
| qwen | L1 | 40 | 28 | ok | 36 / 0 | 0 | 29 | 30 | 29 | 0 | 0 / 0 / 0 / 0 |
| qwen | L2 | 40 | 27 | ok | 37 / 0 | 0 | 29 | 30 | 29 | 3 | 0 / 0 / 0 / 0 |
| qwen | L3 | 40 | 26 | ok | 32 / 0 | 0 | 27 | 29 | 27 | 3 | 0 / 0 / 0 / 0 |
| qwen | LB | 40 | 23 | ok | 30 / 0 | 1 | 23 | 23 | 23 | 11 | 3 / 3 / 1 / 1 |
| qwen | W0 | 40 | 23 | ok | 33 / 0 | 0 | 23 | 25 | 25 | 0 | 0 / 0 / 0 / 0 |
| qwen | W1 | 40 | 29 | ok | 36 / 0 | 0 | 29 | 32 | 31 | 0 | 0 / 0 / 0 / 0 |
| qwen | W2 | 40 | 27 | ok | 35 / 0 | 0 | 27 | 29 | 28 | 1 | 1 / 1 / 1 / 1 |
| qwen | WB | 40 | 31 | ok | 36 / 0 | 1 | 31 | 33 | 31 | 6 | 2 / 2 / 1 / 1 |
| luna | baseline-full | 40 | 25 | ok | 0 / 39 (+1 unrunnable) | 0 | 28 | 28 | 29 | 0 | 0 / 0 / 0 / 0 |
| luna | L0 | 40 | 19 | ok | 25 / 0 | 0 | 19 | 19 | 19 | 0 | 0 / 0 / 0 / 0 |
| luna | L1 | 40 | 32 | ok | 37 / 0 | 0 | 33 | 33 | 33 | 0 | 0 / 0 / 0 / 0 |
| luna | L2 | 40 | 32 | ok | 38 / 0 | 0 | 34 | 34 | 34 | 4 | 0 / 0 / 0 / 0 |
| luna | L3 | 40 | 32 | ok | 37 / 0 | 0 | 33 | 33 | 33 | 4 | 0 / 0 / 0 / 0 |
| luna | W0 | 40 | 30 | ok | 35 / 0 | 0 | 30 | 30 | 31 | 0 | 0 / 0 / 0 / 0 |
| luna | W1 | 40 | 34 | ok | 40 / 0 | 0 | 35 | 35 | 36 | 0 | 0 / 0 / 0 / 0 |
| luna | W2 | 40 | 31 | ok | 39 / 0 | 0 | 32 | 32 | 32 | 1 | 1 / 1 / 1 / 1 |
| sol | baseline-full | 40 | 26 | ok | 0 / 40 | 0 | 30 | 31 | 30 | 0 | 0 / 0 / 0 / 0 |
| sol | L0 | 40 | 20 | ok | 26 / 0 | 0 | 20 | 20 | 20 | 0 | 0 / 0 / 0 / 0 |
| sol | L1 | 40 | 30 | ok | 36 / 0 | 0 | 32 | 32 | 32 | 0 | 0 / 0 / 0 / 0 |
| sol | L2 | 40 | 31 | ok | 37 / 0 | 0 | 33 | 33 | 33 | 4 | 0 / 0 / 0 / 0 |
| sol | L3 | 40 | 33 | ok | 38 / 0 | 0 | 33 | 33 | 33 | 4 | 0 / 0 / 0 / 0 |
| sol | LB | 40 | 29 | ok | 37 / 0 | 0 | 30 | 30 | 30 | 10 | 3 / 3 / 2 / 2 |
| sol | W0 | 40 | 30 | ok | 36 / 0 | 0 | 31 | 31 | 32 | 0 | 0 / 0 / 0 / 0 |
| sol | W1 | 40 | 32 | ok | 40 / 0 | 0 | 32 | 32 | 33 | 0 | 0 / 0 / 0 / 0 |
| sol | W2 | 40 | 35 | ok | 40 / 0 | 0 | 36 | 36 | 36 | 0 | 0 / 0 / 0 / 0 |
| terra | baseline-full | 40 | 26 | ok | 0 / 40 | 0 | 28 | 28 | 29 | 0 | 0 / 0 / 0 / 0 |
| terra | L0 | 40 | 17 | ok | 21 / 0 | 0 | 17 | 17 | 17 | 0 | 0 / 0 / 0 / 0 |
| terra | L1 | 40 | 30 | ok | 36 / 0 | 0 | 32 | 32 | 32 | 0 | 0 / 0 / 0 / 0 |
| terra | L2 | 40 | 30 | ok | 37 / 0 | 0 | 32 | 32 | 32 | 3 | 0 / 0 / 0 / 0 |
| terra | L3 | 40 | 31 | ok | 37 / 0 | 0 | 32 | 32 | 32 | 4 | 0 / 0 / 0 / 0 |
| terra | LB | 40 | 30 | ok | 36 / 0 | 1 | 30 | 30 | 30 | 7 | 1 / 1 / 1 / 1 |
| terra | W0 | 40 | 27 | ok | 33 / 0 | 0 | 28 | 28 | 29 | 0 | 0 / 0 / 0 / 0 |
| terra | W1 | 40 | 31 | ok | 37 / 0 | 0 | 32 | 32 | 33 | 0 | 0 / 0 / 0 / 0 |
| terra | W2 | 40 | 29 | ok | 36 / 0 | 0 | 30 | 30 | 30 | 1 | 1 / 1 / 1 / 1 |

"Check" = strict equals the report's `passed` and the strict rule re-applied to the graded rows agrees with every recorded verdict.

## Development set `all` (41 questions)

### Accuracy, strict → lenient (%)

Cell = strict % → lenient %. Denominator 41.

| Level | opus | sonnet | luna | sol | terra |
|---|---:|---:|---:|---:|---:|
| baseline-full | 75.6 → **78.0** | 51.2 → **58.5** | 61.0 → **65.9** | 53.7 → **58.5** | 41.5 → **46.3** |
| L0 | 56.1 → **61.0** | 24.4 → **24.4** | — | 22.0 → **24.4** | 26.8 → **29.3** |
| L1 | 80.5 → **80.5** | 65.9 → **68.3** | — | 43.9 → **46.3** | 61.0 → **65.9** |
| L2 | 75.6 → **80.5** | 73.2 → **73.2** | — | 63.4 → **63.4** | 65.9 → **68.3** |
| L3 | 78.0 → **78.0** | 70.7 → **73.2** | — | 65.9 → **68.3** | 73.2 → **75.6** |
| LB | 70.7 → **70.7** | 68.3 → **68.3** | — | — | — |
| W0 | 73.2 → **75.6** | 61.0 → **61.0** | — | — | 51.2 → **56.1** |
| W1 | 78.0 → **80.5** | 80.5 → **80.5** | — | — | 61.0 → **61.0** |
| W2 | 78.0 → **78.0** | 70.7 → **73.2** | — | — | — |
| WB | 73.2 → **73.2** | 75.6 → **75.6** | — | — | — |

### Accuracy, lenient + rounding (%)

| Level | opus | sonnet | luna | sol | terra |
|---|---:|---:|---:|---:|---:|
| baseline-full | 78.0 | 58.5 | 65.9 | 58.5 | 46.3 |
| L0 | 61.0 | 24.4 | — | 24.4 | 29.3 |
| L1 | 80.5 | 68.3 | — | 46.3 | 65.9 |
| L2 | 80.5 | 73.2 | — | 63.4 | 68.3 |
| L3 | 78.0 | 73.2 | — | 68.3 | 75.6 |
| LB | 70.7 | 68.3 | — | — | — |
| W0 | 75.6 | 61.0 | — | — | 56.1 |
| W1 | 80.5 | 80.5 | — | — | 61.0 |
| W2 | 78.0 | 73.2 | — | — | — |
| WB | 73.2 | 75.6 | — | — | — |

### Trusted answers that were wrong: strict vs numbers-only

Cell = strict-wrong/trusted · wrong-numbers/trusted. Levels without certified blocks or governed metrics trust nothing.

| Level | opus | sonnet | luna | sol | terra |
|---|---:|---:|---:|---:|---:|
| baseline-full | 0 trusted | 0 trusted | 0 trusted | 0 trusted | 0 trusted |
| L0 | 0 trusted | 0 trusted | — | 0 trusted | 0 trusted |
| L1 | 0 trusted | 0 trusted | — | 0 trusted | 0 trusted |
| L2 | 1/6 (16.7%) · 0/6 (0.0%) | 0/10 (0.0%) · 0/10 (0.0%) | — | 0/5 (0.0%) · 0/5 (0.0%) | 1/11 (9.1%) · 1/11 (9.1%) |
| L3 | 0/6 (0.0%) · 0/6 (0.0%) | 1/10 (10.0%) · 1/10 (10.0%) | — | 0/5 (0.0%) · 0/5 (0.0%) | 1/11 (9.1%) · 1/11 (9.1%) |
| LB | 2/15 (13.3%) · 1/15 (6.7%) | 3/19 (15.8%) · 1/19 (5.3%) | — | — | — |
| W0 | 0 trusted | 0 trusted | — | — | 0 trusted |
| W1 | 0 trusted | 0 trusted | — | — | 0 trusted |
| W2 | 0/2 (0.0%) · 0/2 (0.0%) | 0/2 (0.0%) · 0/2 (0.0%) | — | — | — |
| WB | 1/8 (12.5%) · 0/8 (0.0%) | 2/14 (14.3%) · 1/14 (7.1%) | — | — | — |

### Strict-wrong answers by class

Cell = wrong_numbers / missing_or_extra_columns / grain_or_shape / stopped / other.

| Level | opus | sonnet | luna | sol | terra |
|---|---:|---:|---:|---:|---:|
| baseline-full | 6 / 1 / 3 / 0 / 0 | 6 / 3 / 9 / 0 / 2 | 7 / 2 / 7 / 0 / 0 | 8 / 2 / 9 / 0 / 0 | 6 / 2 / 15 / 0 / 1 |
| L0 | 5 / 2 / 3 / 8 / 0 | 6 / 0 / 4 / 21 / 0 | — | 0 / 1 / 2 / 29 / 0 | 4 / 1 / 1 / 24 / 0 |
| L1 | 4 / 0 / 2 / 2 / 0 | 8 / 1 / 2 / 3 / 0 | — | 5 / 1 / 5 / 12 / 0 | 3 / 2 / 3 / 8 / 0 |
| L2 | 2 / 2 / 3 / 3 / 0 | 5 / 0 / 4 / 2 / 0 | — | 4 / 0 / 6 / 5 / 0 | 4 / 1 / 4 / 5 / 0 |
| L3 | 4 / 0 / 4 / 1 / 0 | 6 / 1 / 1 / 4 / 0 | — | 3 / 1 / 4 / 6 / 0 | 6 / 1 / 3 / 1 / 0 |
| LB | 6 / 0 / 4 / 2 / 0 | 6 / 0 / 3 / 4 / 0 | — | — | — |
| W0 | 4 / 1 / 6 / 0 / 0 | 4 / 0 / 0 / 12 / 0 | — | — | 0 / 2 / 3 / 15 / 0 |
| W1 | 4 / 1 / 3 / 1 / 0 | 5 / 0 / 1 / 2 / 0 | — | — | 3 / 0 / 3 / 10 / 0 |
| W2 | 3 / 0 / 5 / 1 / 0 | 7 / 1 / 2 / 2 / 0 | — | — | — |
| WB | 5 / 0 / 6 / 0 / 0 | 6 / 0 / 4 / 0 / 0 | — | — | — |

### Why strict-wrong answers were wrong — pooled

| Scope | Strict-wrong | wrong_numbers | missing_or_extra_columns | grain_or_shape | stopped | other |
|---|---:|---:|---:|---:|---:|---:|
| all models, all levels | 504 | 155 (30.8%) | 29 (5.8%) | 134 (26.6%) | 183 (36.3%) | 3 (0.6%) |
| all models, DQL levels only | 415 | 122 (29.4%) | 19 (4.6%) | 91 (21.9%) | 183 (44.1%) | 0 (0.0%) |
| all models, baseline only | 89 | 33 (37.1%) | 10 (11.2%) | 43 (48.3%) | 0 (0.0%) | 3 (3.4%) |
| opus | 107 | 43 (40.2%) | 7 (6.5%) | 39 (36.4%) | 18 (16.8%) | 0 (0.0%) |
| sonnet | 147 | 59 (40.1%) | 6 (4.1%) | 30 (20.4%) | 50 (34.0%) | 2 (1.4%) |
| luna | 16 | 7 (43.8%) | 2 (12.5%) | 7 (43.8%) | 0 (0.0%) | 0 (0.0%) |
| sol | 103 | 20 (19.4%) | 5 (4.9%) | 26 (25.2%) | 52 (50.5%) | 0 (0.0%) |
| terra | 131 | 26 (19.8%) | 9 (6.9%) | 32 (24.4%) | 63 (48.1%) | 1 (0.8%) |

| Class:sub-kind (pooled) | Count |
|---|---:|
| stopped:no_sql | 149 |
| wrong_numbers:values_differ | 120 |
| grain_or_shape:list_for_a_total | 59 |
| wrong_numbers:listing_values_differ | 35 |
| stopped:asked_to_clarify | 34 |
| grain_or_shape:fewer_rows | 33 |
| grain_or_shape:empty_result | 29 |
| missing_or_extra_columns:label_column_missing | 15 |
| missing_or_extra_columns:label_column_substituted | 14 |
| grain_or_shape:total_for_a_list | 7 |
| grain_or_shape:rows_merged_into_total | 3 |
| grain_or_shape:more_rows | 3 |
| other:sql_did_not_rerun | 3 |

Trusted answers, pooled: 124 trusted; strict-wrong 12, lenient-wrong 11, wrong numbers 6 (6 excluding rounding). Why: wrong_numbers:listing_values_differ 6, grain_or_shape:total_for_a_list 3, grain_or_shape:fewer_rows 2, missing_or_extra_columns:label_column_missing 1.

### Per cell detail

| Model | Level | n | Strict | Check | Rows from store / re-run | Re-run disagrees | Lenient | +rounding | cellCover | Trusted | Trusted-wrong strict / lenient / numbers / numbers ex-rounding |
|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|---|
| opus | baseline-full | 41 | 31 | ok | 0 / 41 | 0 | 32 | 32 | 33 | 0 | 0 / 0 / 0 / 0 |
| opus | L0 | 41 | 23 | ok | 33 / 0 | 0 | 25 | 25 | 26 | 0 | 0 / 0 / 0 / 0 |
| opus | L1 | 41 | 33 | ok | 39 / 0 | 0 | 33 | 33 | 33 | 0 | 0 / 0 / 0 / 0 |
| opus | L2 | 41 | 31 | ok | 38 / 0 | 0 | 33 | 33 | 33 | 6 | 1 / 0 / 0 / 0 |
| opus | L3 | 41 | 32 | ok | 40 / 0 | 0 | 32 | 32 | 33 | 6 | 0 / 0 / 0 / 0 |
| opus | LB | 41 | 29 | ok | 39 / 0 | 0 | 29 | 29 | 29 | 15 | 2 / 2 / 1 / 1 |
| opus | W0 | 41 | 30 | ok | 41 / 0 | 0 | 31 | 31 | 34 | 0 | 0 / 0 / 0 / 0 |
| opus | W1 | 41 | 32 | ok | 40 / 0 | 0 | 33 | 33 | 33 | 0 | 0 / 0 / 0 / 0 |
| opus | W2 | 41 | 32 | ok | 40 / 0 | 0 | 32 | 32 | 33 | 2 | 0 / 0 / 0 / 0 |
| opus | WB | 41 | 30 | ok | 41 / 0 | 1 | 30 | 30 | 31 | 8 | 1 / 1 / 0 / 0 |
| sonnet | baseline-full | 41 | 21 | ok | 0 / 39 (+2 unrunnable) | 0 | 24 | 24 | 24 | 0 | 0 / 0 / 0 / 0 |
| sonnet | L0 | 41 | 10 | ok | 20 / 0 | 0 | 10 | 10 | 10 | 0 | 0 / 0 / 0 / 0 |
| sonnet | L1 | 41 | 27 | ok | 38 / 0 | 0 | 28 | 28 | 28 | 0 | 0 / 0 / 0 / 0 |
| sonnet | L2 | 41 | 30 | ok | 39 / 0 | 0 | 30 | 30 | 30 | 10 | 0 / 0 / 0 / 0 |
| sonnet | L3 | 41 | 29 | ok | 37 / 0 | 0 | 30 | 30 | 30 | 10 | 1 / 1 / 1 / 1 |
| sonnet | LB | 41 | 28 | ok | 37 / 0 | 1 | 28 | 28 | 28 | 19 | 3 / 3 / 1 / 1 |
| sonnet | W0 | 41 | 25 | ok | 29 / 0 | 0 | 25 | 25 | 25 | 0 | 0 / 0 / 0 / 0 |
| sonnet | W1 | 41 | 33 | ok | 39 / 0 | 0 | 33 | 33 | 33 | 0 | 0 / 0 / 0 / 0 |
| sonnet | W2 | 41 | 29 | ok | 39 / 0 | 0 | 30 | 30 | 30 | 2 | 0 / 0 / 0 / 0 |
| sonnet | WB | 41 | 31 | ok | 41 / 0 | 2 | 31 | 31 | 31 | 14 | 2 / 2 / 1 / 1 |
| luna | baseline-full | 41 | 25 | ok | 0 / 41 | 0 | 27 | 27 | 29 | 0 | 0 / 0 / 0 / 0 |
| sol | baseline-full | 41 | 22 | ok | 0 / 41 | 0 | 24 | 24 | 25 | 0 | 0 / 0 / 0 / 0 |
| sol | L0 | 41 | 9 | ok | 12 / 0 | 0 | 10 | 10 | 10 | 0 | 0 / 0 / 0 / 0 |
| sol | L1 | 41 | 18 | ok | 29 / 0 | 0 | 19 | 19 | 22 | 0 | 0 / 0 / 0 / 0 |
| sol | L2 | 41 | 26 | ok | 36 / 0 | 0 | 26 | 26 | 30 | 5 | 0 / 0 / 0 / 0 |
| sol | L3 | 41 | 27 | ok | 35 / 0 | 0 | 28 | 28 | 30 | 5 | 0 / 0 / 0 / 0 |
| terra | baseline-full | 41 | 17 | ok | 0 / 40 (+1 unrunnable) | 0 | 19 | 19 | 21 | 0 | 0 / 0 / 0 / 0 |
| terra | L0 | 41 | 11 | ok | 17 / 0 | 0 | 12 | 12 | 12 | 0 | 0 / 0 / 0 / 0 |
| terra | L1 | 41 | 25 | ok | 33 / 0 | 0 | 27 | 27 | 27 | 0 | 0 / 0 / 0 / 0 |
| terra | L2 | 41 | 27 | ok | 36 / 0 | 0 | 28 | 28 | 29 | 11 | 1 / 1 / 1 / 1 |
| terra | L3 | 41 | 30 | ok | 40 / 0 | 0 | 31 | 31 | 31 | 11 | 1 / 1 / 1 / 1 |
| terra | W0 | 41 | 21 | ok | 26 / 0 | 0 | 23 | 23 | 23 | 0 | 0 / 0 / 0 / 0 |
| terra | W1 | 41 | 25 | ok | 31 / 0 | 0 | 25 | 25 | 26 | 0 | 0 / 0 / 0 / 0 |

"Check" = strict equals the report's `passed` and the strict rule re-applied to the graded rows agrees with every recorded verdict.

## Development questions rescued by the lenient rule

Number of model×level cells in which each `all` question is strict-wrong but lenient-right:

| Question id | Cells | Sub-kinds |
|---|---:|---|
| `what-are-all-the-premiums-that-have-been-paid-by-fe6797` | 17 | label_column_missing, label_column_substituted |
| `what-is-the-total-amount-of-premiums-that-a-poli-8f378a` | 10 | label_column_missing |
| `what-are-the-total-loss-which-is-the-sum-of-loss-56c35a` | 1 | label_column_substituted |
| `return-agents-and-the-policy-they-have-sold-that-bade1c` | 1 | label_column_substituted |

## Caveats

- Every strict verdict was reproduced: recorded `executionMatched` equals the report's `passed` in 89/89 cells, and re-applying the strict rule to the graded rows disagrees with the recording for 0 answers.
- Rows came from the run store for 2722 answers and from a re-run for 432 (all baseline). 13 answers have SQL that has no stored result and fails on re-run (baseline SQL that never ran; classed other:sql_did_not_rerun). Stored results with conflicting rows for the same SQL: 0.
- Re-running the recorded SQL alone disagrees with the recorded verdict for 11 DQL answers, all semantic-tier answers at LB/WB where DQL derives the shown column from the SQL's columns (a governed ratio such as average loss per claim: the SQL returns numerator and denominator, DQL shows the ratio). The stored rows have one column more or fewer than the re-run in every case. Grading the stored rows avoids this; a re-run-only regrade (e.g. `insurance/regrade.mjs` as written) would under-count those answers.
- The report's `metrics.execution_match_rate` is computed over `metrics.answerable_case_count`, which is partial in resumed runs (e.g. 4 or 5 of 40); use `passed`/`executionMatched`, not that rate.
- `grain_or_shape` is decided by row count alone, so a wrong filter that returns more or fewer rows lands there rather than in wrong_numbers (see the `more_rows`/`fewer_rows`/`empty_result` sub-kinds).
- The measure/label split is heuristic (names, the correct query's projection, fractional values). A label misread as a measure makes lenient stricter; a measure misread as a label would make it looser.
- fl-luna, fl-sol and fl-terra were still running; only finished, valid reports are graded, so their rows are partial.


# Spider 2.0-Lite — run g6a (gpt-6-luna), 2026-09-22

87 SQLite tasks, official evaluator, `gpt-6-luna` through the Codex
subscription for every arm, baseline included. Every DQL arm ran on a clean
committed build, recorded in its `build.json`. **Not comparable with the
gpt-5.6-luna runs sp-a..sp-i** (the model changed).

## Results

| Arm | Build | Correct | Returned SQL | Stop rate | Median | Calls/q |
|---|---|---:|---:|---:|---:|---:|
| baseline (model alone, full DDL) | — | 30/87 (34.5%) | 87 | 0% | 10 s | 1 |
| S1a (Phase 1: check fixes, auto-drafted model) | `7bad6cde` | 22/87 (25.3%) | 49 | 44% | 31 s | 2.7 |
| E0 (Phase 2: whole schema, declared keys, dialect notes) | `82fd89e3` | 24/87 (27.6%) | 59 | 32% | 25 s | 2.3 |
| E1 (E0 + value profile) | `82fd89e3` | 24/87 (27.6%) | 67 | 23% | 29 s | 2.4 |
| **E2 (Phase 3: + result review)** | `1f08af7e` | **32/87 (36.8%)** | 63 | 28% | 37 s | 3.3 |

Paired (exact McNemar):

| Comparison | Only the first right | Only the second right | p |
|---|---:|---:|---:|
| E2 vs baseline | 12 | 10 | 0.83 |
| E2 vs E1 (the review) | 16 | 8 | 0.15 |
| E1 vs E0 (the value profile) | 11 | 11 | 1.00 |
| E0 vs S1a (whole schema) | 9 | 7 | 0.80 |
| E0 vs baseline | 9 | 15 | 0.31 |

Trust: every DQL answer was `review_required`; **0 governed or certified
answers were issued**, so wrong-shown-as-trustworthy is 0 of 0. Nothing here
measures the governed tier.

Latency ran as two parallel streams, so it overstates a single user's wait.

## What it says

1. **DQL's full stack matches the plain call for the first time**: 32 vs 30,
   p = 0.83. Parity on the point estimate, not a win, and one run of 87 moves
   by several points.
2. **The result review is the step that moved accuracy**: +8 over E1 (16
   gained, 8 lost), and wrong answers fell from 43 to 31. Seeing the result's
   shape catches wrong grain and wrong row counts.
3. **The whole schema and the value profile raised coverage, not accuracy**:
   the stop rate fell 44% → 32% → 23%, but the recovered questions came back
   wrong as often as right. More answers is not better answers without the
   review.
4. **gpt-6-luna is faster and weaker than gpt-5.6-luna on the plain prompt**
   (30 vs 40; 10 s vs 20 s median). DQL on gpt-6 (32) is below plain gpt-5.6
   (40).

## Where E2 still stops (24 of 87)

| Why | n | Baseline-right among them |
|---|---:|---:|
| **The reading step asked a clarifying question** | 10 | 4 (local062, local132, local230, local329) |
| The query ran twice and found no rows | 5 | 1 (local275) |
| The drafter said a needed field is missing | 5 | 0 |
| Time budget | 2 | 0 |
| Double-counting check | 1 | 0 |
| Catalog validator (a misspelled column) | 1 | 0 |

The clarifications are the largest remaining loss, and several put DQL's
internals in front of the user: "Can the host calculate date-part
differences…?", "The available intent vocabulary has no way to express…".
On a warehouse-first project those questions are for the drafter, not the
user; genuine ambiguities ("IDs or names?", "which sales figure?") are cases
for answering the most plausible reading and saying the assumption.

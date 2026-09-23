# Spider 2.0-Lite and insurance on Claude Sonnet 5 — runs cl-1 / cl-i1, 2026-09-23

`claude-sonnet-5` through the claude-code subscription (no API). DQL drafts SQL at effort `high` and reads questions at `medium`; **both plain baselines write their SQL at `high`**, so the arms differ in DQL alone. DQL build `claude/dql-review-everywhere @ 59683be5` (clean, unreleased). **One run each.** Every run on a fresh project copy; DQL's memory and hint stores stayed empty; every Claude call ran with no session, no tools, no MCP and an isolated working directory.

## Spider 2.0-Lite, SQLite subset (87 tasks)

| Arm | Correct | 95% CI | Returned SQL | Stop rate | Median |
|---|---:|---|---:|---:|---:|
| plain model (full DDL, effort high) | 45/87 (51.7%) | 41.4–61.9% | 84 | 3% | 13 s |
| DQL E6 | 45/87 (51.7%) | 41.4–61.9% | 80 | 8% | 19 s |

Paired: 15 against 15, p = 1.0. **Parity.** Of the 15 DQL lost: 1 double-counting false alarm on a `COUNT(DISTINCT)` self-join (fixed, `20fef262`); 2 forecast questions that name their method (declined; open policy question); 2 coherent readings that found no rows; 10 differing interpretations (the plain model also lost 15 that DQL answered).

## Insurance main set (41 questions)

| Condition | Correct | 95% CI | Wrong, shown as trustworthy | Stopped | p50 |
|---|---:|---|---:|---:|---:|
| plain text-to-SQL (effort high) | 20/41 (48.8%) | 34.3–63.5% | 21 | 0 | 7 s |
| **DQL L3** (dbt + modeling + MetricFlow + skills) | **31/41 (75.6%)** | 60.7–86.2% | **0** | 3 | 38 s |
| **DQL W2** (no dbt: modeling + dbt Labs' metrics on DQL's native engine) | **32/41 (78.0%)** | 63.3–88.0% | **0** | 3 | 40 s |

- **L3 vs text-to-SQL: +26.8 points (95% CI 11.7–42.0); 12 against 1; p = 0.0034.**
- **W2 vs text-to-SQL: +29.3 points (13.8–44.7); 13 against 1; p = 0.0018.**
- L3 on the unanswerable set: 14 of 15 stopped correctly.
- Every DQL miss was `review_required` or blocked. Misses: a column the answer key requires is missing (L3 5, W2 4); refusals on loss-ratio questions (L3 3, W2 2), one of them a certified-join check refusing a join on every certified key plus two more (fixed, `8fcbf6ac`), one the drafter never shown the agent tables; wrong row counts; one clarification on W2.
- Latency on the subscription route is 38–40 s median against 7 s for one plain call.

Single runs on an unreleased build: not publishable.

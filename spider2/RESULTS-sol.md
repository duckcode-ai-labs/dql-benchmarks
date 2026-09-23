# Spider 2.0-Lite on gpt-5.6-sol — run sol-f1, 2026-09-23

87 SQLite tasks, official evaluator, `gpt-5.6-sol` through the Codex subscription, reasoning effort medium for both arms. DQL build `claude/dql-draft-first @ 47e27d0d` (clean): Phase 1 check fixes, whole schema with declared keys, value profile, result review, assume-and-state, draft-first, SQLite worker. **One run.** The ChatGPT usage limit refused 24 baseline calls in the first pass; they were asked again after the reset (run `sol-f1-fill`) and merged, so both arms answered all 87.

| Arm | Correct | 95% CI | Returned SQL | Stop rate | Median | Calls/q |
|---|---:|---|---:|---:|---:|---:|
| baseline (model alone, full DDL) | 48/87 (55.2%) | 44.7–65.2% | 87 | 0% | 20 s | 1 |
| **DQL E5** | **53/87 (60.9%)** | 50.4–70.5% | 82 | 6% | 38 s | 2.2 |

- Paired: DQL right alone on 12, the baseline alone on 7; exact McNemar p = 0.36. **DQL is ahead by 5 and not significantly: parity, one run.**
- Every DQL answer was `review_required`; no governed or certified answer was issued (no semantic layer on these databases).
- Run-to-run variance is large at this size: the baseline scored 18/22 and 13/22 on two passes of the same 22-task quick set. Repeats are needed before any claim; runs `sol-f2` and `sol-f3` were refused by the usage limit and are set aside.

Development evidence: these 87 tasks drove the fixes, so they are not a held-out result.

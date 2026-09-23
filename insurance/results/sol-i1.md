# Insurance on gpt-5.6-sol — run sol-i1, 2026-09-23

Main set (41 questions), `gpt-5.6-sol` through the Codex subscription, reasoning effort medium for every condition. DQL build `claude/dql-draft-first @ 47e27d0d` (clean, not a release). One run each. W1, W0 and the L3 unanswerable run were refused by the ChatGPT usage limit part way (marked INVALID) and are not reported.

| Condition | Correct | 95% CI | Wrong, shown as trustworthy | Stopped | p50 | AI calls (mean) |
|---|---:|---|---:|---:|---:|---:|
| Plain text-to-SQL (dbt Labs' prompt, small DDL) | 18/41 (43.9%) | 29.9–59.0% | 23 | 0 | 15.6 s | 1.0 |
| **DQL L3** (dbt + modeling + MetricFlow + skills) | **30/41 (73.2%)** | 58.1–84.3% | **0** | 5 | 64.7 s | 2.3 |
| DQL W2 (no dbt: modeling + dbt Labs' metrics on DQL's native engine) | 25/41 (61.0%) | 45.7–74.3% | 2 | 8 | 56.9 s | 2.8 |

- **L3 vs text-to-SQL: +29.3 points (95% CI +15.3 to +43.2); L3 right alone on 12, text-to-SQL on 0; exact McNemar p = 0.0005.**
- W2 vs text-to-SQL: +17.1 points (−1.9 to +36.1); 12 against 5; p = 0.14.
- W2's two governed-but-wrong answers are the two open answer-key questions: "average policy size" (dbt Labs' `premium` metric sums `fire_claim.Premium`; the key uses `policy_amount`) and "total premiums a policy holder has paid" (the right total without the per-holder column the key expects).
- Latency on this model is well above the plain call (p50 57–65 s against 16 s).

Single runs on an unreleased build: not publishable.

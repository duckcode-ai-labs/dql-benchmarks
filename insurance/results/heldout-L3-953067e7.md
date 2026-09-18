## L3 · heldout · run fx-h

DQL 1.17.3 (env @ 953067e7) · claude-code / claude-sonnet-5 · harness d1befcf · 2026-09-18T06:44:30.715Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 15/44 | 34.1% | 21.9–48.9% |
| Accepted answer key | 0/0 | — | — |
| dbt Labs' 11 | 0/0 | — | — |
| LQLS (low question complexity, low schema complexity) | 8/12 | 66.7% | 39.1–86.2% |
| LQHS (low question complexity, high schema complexity) | 0/10 | 0.0% | 0.0–27.8% |
| HQLS (high question complexity, low schema complexity) | 7/11 | 63.6% | 35.4–84.8% |
| HQHS (high question complexity, high schema complexity) | 0/11 | 0.0% | 0.0–25.9% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 15 |
| wrong | 11 |
| declined | 15 |
| asked to clarify | 3 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 14 | 9 |
| not_applicable | 0 | 4 |
| blocked | 0 | 15 |
| governed | 1 | 1 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 22.1 s · 95th percentile 98.1 s · slowest 182.0 s · AI calls per question: mean 1.5, max 4 · cost: not measured on this provider route

### Data sent to the AI model

67 AI calls recorded; result rows sent to the model: **0** (target 0).

> Held-out set: questions are sealed; this scorecard shows totals only. Answer key not yet reviewed by the owner.


## L0 · heldout · run fx-h

DQL 1.17.3 (env @ 953067e7) · claude-code / claude-sonnet-5 · harness d1befcf · 2026-09-18T07:07:59.786Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 14/44 | 31.8% | 20.0–46.6% |
| Accepted answer key | 0/0 | — | — |
| dbt Labs' 11 | 0/0 | — | — |
| LQLS (low question complexity, low schema complexity) | 7/12 | 58.3% | 32.0–80.7% |
| LQHS (low question complexity, high schema complexity) | 0/10 | 0.0% | 0.0–27.8% |
| HQLS (high question complexity, low schema complexity) | 6/11 | 54.5% | 28.0–78.7% |
| HQHS (high question complexity, high schema complexity) | 1/11 | 9.1% | 1.6–37.7% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 14 |
| wrong | 7 |
| declined | 21 |
| asked to clarify | 2 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 14 | 7 |
| blocked | 0 | 21 |
| not_applicable | 0 | 2 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 24.0 s · 95th percentile 113.9 s · slowest 215.9 s · AI calls per question: mean 2.0, max 6 · cost: not measured on this provider route

### Data sent to the AI model

86 AI calls recorded; result rows sent to the model: **0** (target 0).

> Held-out set: questions are sealed; this scorecard shows totals only. Answer key not yet reviewed by the owner.


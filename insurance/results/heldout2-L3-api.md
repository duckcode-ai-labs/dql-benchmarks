## L3 · heldout-2 · run api-h2

DQL 1.17.3 (env @ b83d2c68) · anthropic / claude-sonnet-5 · harness 9745653 · 2026-09-18T15:55:39.548Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 23/43 | 53.5% | 38.9–67.5% |
| Accepted answer key | 0/0 | — | — |
| dbt Labs' 11 | 0/0 | — | — |
| LQLS (low question complexity, low schema complexity) | 8/11 | 72.7% | 43.4–90.3% |
| LQHS (low question complexity, high schema complexity) | 5/10 | 50.0% | 23.7–76.3% |
| HQLS (high question complexity, low schema complexity) | 9/12 | 75.0% | 46.8–91.1% |
| HQHS (high question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 23 |
| wrong | 12 |
| declined | 6 |
| asked to clarify | 2 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 22 | 10 |
| governed | 1 | 1 |
| not_applicable | 0 | 3 |
| blocked | 0 | 6 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 19.5 s · 95th percentile 69.1 s · slowest 90.3 s · AI calls per question: mean 2.1, max 4 · 20,853 tokens per question; cost $2.55 in all, $0.0592 per question at list prices of 2026-09-18

### Data sent to the AI model

89 AI calls recorded; result rows sent to the model: **0** (target 0).

> Held-out set: questions are sealed; this scorecard shows totals only. Answer key not yet reviewed by the owner.


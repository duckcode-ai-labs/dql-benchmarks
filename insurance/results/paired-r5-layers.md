> **Not publishable.** L0: DQL came from the DQL_CLI override, not a release — L1: DQL came from the DQL_CLI override, not a release — L2: DQL came from the DQL_CLI override, not a release — L3: DQL came from the DQL_CLI override, not a release

### All questions (n = 41)

| Condition | Correct | Accuracy | 95% CI | Wrong, shown as trustworthy | Stopped | p50 latency | p95 latency | AI calls (mean / max) | $ / question | Wrong but certified |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| L0 | 10/41 | 24.4% | 13.8%–39.3% | 0 | 25 | 45.8 s | 177.5 s | 2.5 / 5 | — | 0 |
| L1 | 20/41 | 48.8% | 34.3%–63.5% | 0 | 14 | 42.1 s | 187.0 s | 2.5 / 5 | — | 0 |
| L2 | 21/41 | 51.2% | 36.5%–65.7% | 1 | 6 | 39.3 s | 104.4 s | 2.3 / 3 | — | 0 |
| L3 | 23/41 | 56.1% | 41.0%–70.1% | 1 | 6 | 36.2 s | 117.0 s | 2.4 / 5 | — | 0 |

- **L1 vs L0:** +24.4 points (95% CI 11.2 to 37.5); only L1 right on 10, only L0 right on 0; exact McNemar p = 0.0020.
- **L2 vs L0:** +26.8 points (95% CI 13.3 to 40.4); only L2 right on 11, only L0 right on 0; exact McNemar p = 0.0010.
- **L3 vs L0:** +31.7 points (95% CI 17.5 to 46.0); only L3 right on 13, only L0 right on 0; exact McNemar p = 0.0002.


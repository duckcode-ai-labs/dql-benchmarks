> **Not publishable.** L0: DQL came from the DQL_CLI override, not a release — L1: DQL came from the DQL_CLI override, not a release — L2: DQL came from the DQL_CLI override, not a release — L3: DQL came from the DQL_CLI override, not a release

### All questions (n = 41)

| Condition | Correct | Accuracy | 95% CI | Wrong, shown as trustworthy | Stopped | p50 latency | p95 latency | AI calls (mean / max) | $ / question | Wrong but certified |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| L0 | 14/41 | 34.1% | 21.6%–49.5% | 0 | 18 | 47.3 s | 156.2 s | 2.7 / 6 | — | 0 |
| L1 | 17/41 | 41.5% | 27.8%–56.6% | 0 | 11 | 37.5 s | 186.6 s | 2.8 / 6 | — | 0 |
| L2 | 22/41 | 53.7% | 38.7%–67.9% | 0 | 4 | 35.9 s | 115.5 s | 2.3 / 4 | — | 0 |
| L3 | 26/41 | 63.4% | 48.1%–76.4% | 0 | 3 | 33.1 s | 126.7 s | 2.3 / 3 | — | 0 |

- **L1 vs L0:** +7.3 points (95% CI -6.8 to 21.5); only L1 right on 6, only L0 right on 3; exact McNemar p = 0.5078.
- **L2 vs L0:** +19.5 points (95% CI 5.6 to 33.4); only L2 right on 9, only L0 right on 1; exact McNemar p = 0.0215.
- **L3 vs L0:** +29.3 points (95% CI 15.3 to 43.2); only L3 right on 12, only L0 right on 0; exact McNemar p = 0.0005.


> **Not publishable.** L0: DQL came from the DQL_CLI override, not a release — L1: DQL came from the DQL_CLI override, not a release — L2: DQL came from the DQL_CLI override, not a release — L3: DQL came from the DQL_CLI override, not a release

### All questions (n = 41)

| Condition | Correct | Accuracy | 95% CI | Wrong, shown as trustworthy | Stopped | p50 latency | p95 latency | AI calls (mean / max) | $ / question | Wrong but certified |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| text-to-SQL | 19/41 | 46.3% | 32.1%–61.3% | 22 | 0 | 6.2 s | 23.9 s | 1.0 / 1 | — | 0 |
| L0 | 14/41 | 34.1% | 21.6%–49.5% | 0 | 18 | 47.3 s | 156.2 s | 2.7 / 6 | — | 0 |
| L1 | 17/41 | 41.5% | 27.8%–56.6% | 0 | 11 | 37.5 s | 186.6 s | 2.8 / 6 | — | 0 |
| L2 | 22/41 | 53.7% | 38.7%–67.9% | 0 | 4 | 35.9 s | 115.5 s | 2.3 / 4 | — | 0 |
| L3 | 26/41 | 63.4% | 48.1%–76.4% | 0 | 3 | 33.1 s | 126.7 s | 2.3 / 3 | — | 0 |

- **L0 vs text-to-SQL:** -12.2 points (95% CI -27.6 to 3.2); only L0 right on 3, only text-to-SQL right on 8; exact McNemar p = 0.2266.
- **L1 vs text-to-SQL:** -4.9 points (95% CI -19.9 to 10.2); only L1 right on 4, only text-to-SQL right on 6; exact McNemar p = 0.7539.
- **L2 vs text-to-SQL:** +7.3 points (95% CI -6.8 to 21.5); only L2 right on 6, only text-to-SQL right on 3; exact McNemar p = 0.5078.
- **L3 vs text-to-SQL:** +17.1 points (95% CI 3.7 to 30.4); only L3 right on 8, only text-to-SQL right on 1; exact McNemar p = 0.0391.


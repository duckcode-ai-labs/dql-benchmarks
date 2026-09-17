> **Not publishable.** L0: DQL came from the DQL_CLI override, not a release — L1: DQL came from the DQL_CLI override, not a release — L2: DQL came from the DQL_CLI override, not a release — L3: DQL came from the DQL_CLI override, not a release

### All questions (n = 41)

| Condition | Correct | Accuracy | 95% CI | Wrong, shown as trustworthy | Stopped | p50 latency | p95 latency | AI calls (mean / max) | $ / question | Wrong but certified |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| text-to-SQL | 19/41 | 46.3% | 32.1%–61.3% | 22 | 0 | 6.2 s | 23.9 s | 1.0 / 1 | — | 0 |
| L0 | 10/41 | 24.4% | 13.8%–39.3% | 0 | 25 | 45.8 s | 177.5 s | 2.5 / 5 | — | 0 |
| L1 | 20/41 | 48.8% | 34.3%–63.5% | 0 | 14 | 42.1 s | 187.0 s | 2.5 / 5 | — | 0 |
| L2 | 21/41 | 51.2% | 36.5%–65.7% | 1 | 6 | 39.3 s | 104.4 s | 2.3 / 3 | — | 0 |
| L3 | 23/41 | 56.1% | 41.0%–70.1% | 1 | 6 | 36.2 s | 117.0 s | 2.4 / 5 | — | 0 |

- **L0 vs text-to-SQL:** -22.0 points (95% CI -36.3 to -7.6); only L0 right on 1, only text-to-SQL right on 10; exact McNemar p = 0.0117.
- **L1 vs text-to-SQL:** +2.4 points (95% CI -10.2 to 15.1); only L1 right on 4, only text-to-SQL right on 3; exact McNemar p = 1.0000.
- **L2 vs text-to-SQL:** +4.9 points (95% CI -10.2 to 19.9); only L2 right on 6, only text-to-SQL right on 4; exact McNemar p = 0.7539.
- **L3 vs text-to-SQL:** +9.8 points (95% CI -5.1 to 24.6); only L3 right on 7, only text-to-SQL right on 3; exact McNemar p = 0.3438.


# Test-suite check on database variants (secondary, not pre-registered)

An answer that is strict-correct on the original warehouse is re-executed, together with the reference query, on three altered copies: **V1** an independent cloned book: new ids, amounts x3+7, dates +400 days (close dates +410), distinct names and street addresses; catastrophes, cities and codes shared; **V2** the same clone in the same period: open dates unchanged, close dates +10 days. It **survives** when it matches the reference on every variant (one consistent column mapping, extra columns allowed). Answers whose recorded SQL does not reproduce their correct rows on the original warehouse (for example a governed ratio computed by DQL after the query) are **not checkable**.

| Set | Condition | Answers | Strict-correct | Survive | Fragile | Not checkable | Fragile on V1 / V2 | Survival rate (lower–upper) |
|---|---|---:|---:|---:|---:|---:|---|---|
| heldout-3 | P | 280 | 177 | 169 | 0 | 8 | 0 / 0 | 60.4–63.2% |
| heldout-3 | A | 80 | 65 | 63 | 0 | 2 | 0 / 0 | 78.8–81.2% |
| heldout-3 | L0 | 280 | 134 | 132 | 0 | 2 | 0 / 0 | 47.1–47.9% |
| heldout-3 | L1 | 280 | 219 | 212 | 0 | 7 | 0 / 0 | 75.7–78.2% |
| heldout-3 | L2 | 280 | 218 | 211 | 0 | 7 | 0 / 0 | 75.4–77.9% |
| heldout-3 | L3 | 280 | 217 | 209 | 0 | 8 | 0 / 0 | 74.6–77.5% |
| heldout-3 | LB | 280 | 202 | 186 | 0 | 16 | 0 / 0 | 66.4–72.1% |
| heldout-3 | W0 | 280 | 209 | 198 | 0 | 11 | 0 / 0 | 70.7–74.6% |
| heldout-3 | W1 | 280 | 231 | 221 | 0 | 10 | 0 / 0 | 78.9–82.5% |
| heldout-3 | W2 | 280 | 233 | 221 | 0 | 12 | 0 / 0 | 78.9–83.2% |
| heldout-3 | WB | 280 | 238 | 219 | 0 | 19 | 0 / 0 | 78.2–85.0% |
| heldout-3 | DQL levels | 2520 | 1901 | 1809 | 0 | 92 | 0 / 0 | 71.8–75.4% |
| heldout-4 | P | 200 | 126 | 115 | 3 | 8 | 1 / 3 | 57.5–61.5% |
| heldout-4 | A | 200 | 156 | 140 | 3 | 13 | 0 / 3 | 70.0–76.5% |
| heldout-4 | Am | 200 | 168 | 155 | 0 | 13 | 0 / 0 | 77.5–84.0% |
| heldout-4 | L2 | 200 | 142 | 126 | 4 | 12 | 1 / 4 | 63.0–69.0% |
| heldout-4 | L3 | 200 | 147 | 131 | 4 | 12 | 1 / 4 | 65.5–71.5% |
| heldout-4 | W2 | 200 | 171 | 152 | 6 | 13 | 2 / 6 | 76.0–82.5% |
| heldout-4 | WB | 200 | 154 | 137 | 6 | 11 | 2 / 6 | 68.5–74.0% |
| heldout-4 | DQL levels | 800 | 614 | 546 | 20 | 48 | 6 / 20 | 68.2–74.2% |

## Set 4 (Claude Sonnet 5.5): paired comparison on surviving answers

| Comparison | Reading | Left | Right | Gained / lost | McNemar p (raw) |
|---|---|---:|---:|---|---:|
| W2 vs Am | lower | 152/200 | 155/200 | 16 / 19 | 0.7359 |
| W2 vs Am | upper | 165/200 | 168/200 | 17 / 20 | 0.7428 |
| W2 vs A | lower | 152/200 | 140/200 | 27 / 15 | 0.0884 |
| W2 vs A | upper | 165/200 | 153/200 | 28 / 16 | 0.0961 |
| W2 vs P | lower | 152/200 | 115/200 | 47 / 10 | 0.0000 |
| W2 vs P | upper | 165/200 | 123/200 | 52 / 10 | 0.0000 |
| Am vs A | lower | 155/200 | 140/200 | 16 / 1 | 0.0003 |
| Am vs A | upper | 168/200 | 153/200 | 17 / 2 | 0.0007 |

Run time 77.1 s. Generated 2026-10-02T17:41:09-0500 by variants.py (DuckDB, read-only copies; no model calls).

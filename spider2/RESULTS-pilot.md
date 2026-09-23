# Spider modeled-layer pilot — IPL and f1, Claude Sonnet 5, 2026-09-23

The 20 tasks on IPL and f1, one run each, `claude-sonnet-5` through the claude-code subscription. L2 and L3 layers were written blind from each warehouse by separate agents (`spider2/layers/AUTHORING.md`; logs audited, no forbidden file read). Labelled AI-authored, independently reviewed, not human-certified.

| Arm | Build | Correct | Returned SQL | Median |
|---|---|---:|---:|---:|
| plain model (run cl-1, effort high) | — | 10/20 | 20 | — |
| L1: DQL on the raw warehouse | `8fcbf6ac` | 8/20 | 20 | 27 s |
| L2: + modeling (entities, relationships certified on data) | `8fcbf6ac` | 6/20 | 19 | 20 s |
| L3: + skills and 5 native metrics | `8fcbf6ac` | **2/20** | 17 | 68 s |
| L3 after the routing fix | `0255ccd9` | 7/20 | 19 | 42 s |

- **Modeling made DQL worse, through routing.** Any metric in a warehouse-first project switched draft-first off, so every question went through the reading step. The five mechanical metrics (runs_off_bat, race_points, ...) answered none of the questions but pulled readings toward them: a "governed" bowling average built from runs_off_bat that ended in a clarification, a restated question with a different shape. Fixed in `0255ccd9`: the governed tiers go first only when the question names a governed block, metric or measure.
- **After the fix, modeling neither helps nor hurts here:** L3 7 against L1 8 (1 against 2, p = 1.0). No governed answer was issued in any arm: Spider's questions define their own computations and none maps to a recurring metric, which is what a semantic layer governs.
- The blind authors found five defects in DQL's own modeling tools (queued separately).

Single runs on 20 tasks: a screening result, not a claim.

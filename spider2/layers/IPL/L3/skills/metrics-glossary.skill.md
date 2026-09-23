---
id: metrics-glossary
description: "Business terms mapped to the native IPL semantic-layer metrics."
---
# Metrics glossary

Native metrics in `semantic-layer/metrics/` (single table, no filters). Prefer them when a question
matches exactly; everything else is defined in `ipl-runs-wickets-definitions` and
`ipl-matches-teams-results`.

| Metric | Table | Meaning |
| --- | --- | --- |
| `runs_off_bat` | `batsman_scored` | SUM(runs_scored): runs hit off the bat; no extras. |
| `extras_conceded` | `extra_runs` | SUM(extra_runs): all extras; slice by `extra_type`. |
| `deliveries_bowled` | `ball_by_ball` | COUNT(*): every delivery including wides and no-balls (not legal balls, not balls faced). |
| `dismissal_records` | `wicket_taken` | COUNT(*): every dismissal row of any `kind_out`, including retired hurt and run outs (not bowler wickets). |
| `matches_played` | `match` | COUNT(*): matches with a `match` row (567). |

Terms that are **not** single metrics because they combine tables or encode a convention:
team or innings total (`runs_off_bat` + `extras_conceded` for the same innings), balls faced, legal balls,
overs, runs conceded by a bowler, bowler wickets, averages, strike rates and economy.

Dimensions: `extra_type` (extra_runs), `kind_out` (wicket_taken), `season_id`, `venue`, `match_date` (match).

---
id: ipl-runs-wickets-definitions
kind: metric_policy
status: active
owner: 43963011+KKranthi6881@users.noreply.github.com
description: "How runs off the bat, extras, team and innings totals, balls faced, legal balls, overs, wickets credited to a bowler, and standard batting and bowling rates are computed from the IPL delivery tables."
triggers:
  - runs
  - total runs
  - score
  - innings total
  - team total
  - runs scored
  - batting
  - batter
  - batsman
  - striker
  - boundary
  - four
  - fours
  - six
  - sixes
  - dot ball
  - century
  - fifty
  - half century
  - extras
  - wide
  - wides
  - no ball
  - no-ball
  - bye
  - leg bye
  - penalty
  - wicket
  - wickets
  - dismissal
  - out
  - run out
  - bowler
  - bowling
  - economy
  - strike rate
  - batting average
  - bowling average
  - balls faced
  - overs bowled
  - runs conceded
  - partnership
  - powerplay
  - death overs
source_refs:
  - IPL.sqlite (queries run by the author, see spider2/layers/IPL/AUTHORING-LOG.md)
  - semantic-layer/metrics/runs_off_bat.yaml, extras_conceded.yaml, deliveries_bowled.yaml, dismissal_records.yaml
clarify_when:
  - The user asks for a batter's or bowler's "runs" without saying whether extras count (for a batter they never do; for a bowler, say that wides and no-balls are charged and byes and leg-byes are not).
  - The user asks for "wickets" of a bowler; run outs, retired hurt and obstructing the field are not credited to the bowler.
  - The user asks for a rate (average, strike rate, economy) with no minimum qualification; say which minimum (balls, innings, overs) you applied, if any.
---
# Runs, extras, balls and wickets

Every delivery-level fact is joined on the full delivery key
`match_id, innings_no, over_id, ball_id` (see `ipl-data-model`).

## Runs

| Term | Definition in this data |
| --- | --- |
| **Runs off the bat** (a batter's runs) | `batsman_scored.runs_scored` (0-6). Credit them to `ball_by_ball.striker` of the same delivery. Native metric `runs_off_bat`. |
| **Extras** | `extra_runs.extra_runs`, the total extras on a delivery (1-5). `extra_type` is `wides`, `legbyes`, `noballs`, `byes` or `penalty`. Native metric `extras_conceded`. Extras are never a batter's runs. |
| **Innings total / team score** | runs off the bat + extras of that `match_id, innings_no`. Sum `batsman_scored` and `extra_runs` **separately** (or `UNION ALL` them) and add; do not reach `extra_runs` through `ball_by_ball` (one extra row has no delivery row) and never join the two on fewer than the four key columns. |
| **Runs a bowler conceded** | runs off the bat on his deliveries + `extra_runs` where `extra_type` in (`wides`, `noballs`). Byes, leg-byes and penalty runs are not charged to the bowler (cricket scoring convention). |

Checked: innings totals built this way reproduce the recorded result (the `win_margin` of a "runs" win, or
the chasing side ahead in a "wickets" win) in 545 of 567 matches. The other 22 are rain-shortened matches with
revised targets or have small gaps in the ball data, so do not re-derive the winner from totals; use
`match.match_winner`.

- **Boundary**: `runs_scored = 4` (a four) or `runs_scored = 6` (a six). `runs_scored` of 3 and 5 are run
  (or overthrow) outcomes, not boundaries.
- **Fifty / century** (batter milestones): runs off the bat by one striker in one `match_id` (one innings)
  of at least 50 / 100. A score counts as a fifty only if it is 50-99 when fifties and hundreds are listed
  separately.

## Balls and overs

| Term | Definition |
| --- | --- |
| **Delivery** | one `ball_by_ball` row, including wides and no-balls. Native metric `deliveries_bowled`. |
| **Legal ball** (counts toward the over) | a delivery with no `extra_runs` row of type `wides` or `noballs`. |
| **Balls faced** by a batter | deliveries where he is `striker`, excluding wides (no-balls count as balls faced, by convention). LEFT JOIN `extra_runs` and keep `extra_type IS NULL OR extra_type <> 'wides'`. |
| **Balls bowled** by a bowler | his legal balls. **Overs bowled** = legal balls / 6, written as complete overs + balls (e.g. 22 balls = 3.4 overs). Do not count distinct `over_id` when the question needs balls. |
| **Dot ball** (batting) | a ball faced with `runs_scored = 0`. |
| **Over number** | `over_id` 1-20. Phase conventions used by analysts (not stored in the data): powerplay = overs 1-6, middle = 7-15, death = 16-20. |

Note that `batsman_scored` has no row for most wides, so counting `batsman_scored` rows is
neither deliveries nor balls faced.

## Wickets and dismissals

- A **dismissal** is one `wicket_taken` row; `player_out` is the batter out (usually the striker; when it is the
  non-striker the dismissal is a run out). Native metric `dismissal_records` counts all rows.
- `kind_out` values: `caught`, `bowled`, `run out`, `lbw`, `stumped`, `caught and bowled`, `retired hurt`,
  `hit wicket`, `obstructing the field` (lower case, as written).
- **Wicket credited to the bowler** = `kind_out` in (`bowled`, `caught`, `lbw`, `stumped`,
  `caught and bowled`, `hit wicket`); the bowler is `ball_by_ball.bowler` of the same delivery. Run out,
  retired hurt and obstructing the field are not bowler wickets.
- **Wickets fallen in an innings** (team view): dismissals in that `match_id, innings_no` excluding
  `retired hurt`. Checked: for every "wickets" win in which a wicket fell, win_margin = 10 - wickets fallen in
  the chase.
- A batter is **not out** in an innings when he batted (appears as `striker` or `non_striker`) and has no
  `wicket_taken` row as `player_out` in that `match_id, innings_no`. Retired hurt counts as not out by
  convention.
- Fielders (catcher, run-out fielder) are not recorded.

## Standard rates (cricket conventions)

| Rate | Formula |
| --- | --- |
| Batting average | runs off the bat / times dismissed (dismissals as `player_out`, excluding retired hurt) |
| Batting strike rate | 100 * runs off the bat / balls faced |
| Bowling average | runs conceded / bowler wickets |
| Economy rate | runs conceded / (legal balls / 6) |
| Bowling strike rate | legal balls / bowler wickets |
| Run rate (team) | innings total / (legal balls / 6) |

Use real division (`* 1.0`) in SQLite; integer division truncates. Averages with zero dismissals are
undefined, not zero.

## Partnerships

The two batters at the crease on a delivery are `striker` and `non_striker`. A partnership is the run of
consecutive deliveries in one innings with the same unordered pair (`min(striker, non_striker)`,
`max(striker, non_striker)`); its runs are the runs off the bat plus extras on those deliveries. It ends
at a dismissal (or retirement). Order deliveries by `over_id, ball_id` within `match_id, innings_no`.

---
id: ipl-data-model
kind: domain_reference
status: active
owner: 43963011+KKranthi6881@users.noreply.github.com
description: "What each IPL table records, its grain and keys, how deliveries, innings, overs and balls relate, how dates and seasons are stored, and the known gaps (missing team 1, player 35, match 419136)."
triggers:
  - ipl
  - cricket
  - match
  - season
  - innings
  - over
  - ball
  - delivery
  - team
  - player
  - playing xi
  - squad
  - venue
  - date of birth
  - age
  - country
  - batting hand
  - bowling skill
  - captain
  - keeper
source_refs:
  - IPL.sqlite (queries run by the author, see spider2/layers/IPL/AUTHORING-LOG.md)
  - domains/ipl/modeling/areas/matches.dql.yaml
  - domains/ipl/modeling/areas/deliveries.dql.yaml
clarify_when:
  - The user names a team that has no row in `team` (team_id 1 has no name in the data).
  - The user asks for a "season" by name or year and the answer depends on season_id versus calendar year (they are the same here, but say which one you used).
---
# IPL data model

Indian Premier League, seasons 2008-2016, 567 matches with a result. Eight tables in schema `main`.

## Tables, grain and keys (checked on the data)

| Table | One row is | Key (unique, no nulls) | Rows |
| --- | --- | --- | --- |
| `match` | one match | `match_id` | 567 |
| `team` | one franchise | `team_id` | 12 |
| `player` | one player | `player_id` | 468 |
| `player_match` | one player in one match's playing XI | `match_id, player_id` | 12,495 |
| `ball_by_ball` | one delivery bowled | `match_id, innings_no, over_id, ball_id` | 134,703 |
| `batsman_scored` | runs off the bat on one delivery | same four columns | 131,259 |
| `extra_runs` | extras on one delivery | same four columns | 7,349 |
| `wicket_taken` | one batter out on one delivery | same four columns | 6,618 |

A delivery is identified by **all four** columns `match_id, innings_no, over_id, ball_id`. Joining the
delivery tables on fewer columns multiplies rows (over_id and ball_id repeat in every innings of every match).

## Innings, overs and balls

- `innings_no` is 1 (team batting first) or 2 (team chasing). There are no super overs in the data.
- `over_id` runs 1-20; the first over is 1 (not 0).
- `ball_id` is the delivery's sequence number within the over, 1-9. Wides and no-balls are re-bowled, so an
  over with extras has more than six deliveries. Almost every over has exactly six deliveries that are not wides
  or no-balls; nearly all shorter overs are the last over of an innings.
- An innings can stop before over 20 (all out, target reached, rain-shortened match).
- The bowler is normally the same for the whole over (16 overs list two bowlers); no bowler bowls two overs in a row.
- `striker_batting_position` is the striker's place in the batting order for that innings (1-11; unique per
  batter per innings; 1 and 2 are the openers). A batter who never faced a ball appears only as `non_striker`.

## Which table records what

- **Who batted and bowled**: `ball_by_ball` (`striker`, `non_striker`, `bowler`, `team_batting`, `team_bowling`).
  It holds no runs.
- **Runs off the bat**: `batsman_scored.runs_scored`, credited to `ball_by_ball.striker` of the same delivery.
- **Extras**: `extra_runs` (`extra_type`, `extra_runs`).
- **Dismissals**: `wicket_taken` (`player_out`, `kind_out`). No bowler or fielder column: the bowler is
  `ball_by_ball.bowler` of the same delivery; fielders are not recorded.
- **Which team a player played for in a match, and captain/keeper**: `player_match` (`team_id`, `role`).
  `role` is `Player`, `Captain`, `Keeper` or `CaptainKeeper` (captain who kept wicket). Each team in a match
  has exactly one keeper and, in all but 3 team-match cases, exactly one captain. A player can play for different teams across seasons, so always take
  the team from `player_match` for that match, not from another match.
- **Match facts**: `match` (date, season, venue, toss, result, man of the match). No city column.

## Dates, seasons and codes

- `match.match_date` and `player.dob` are TEXT in `YYYY-MM-DD` form (all rows). Use `substr(match_date,1,4)`
  or `strftime('%Y', match_date)` for the year; `julianday()` differences for ages or gaps.
- `match.season_id` is 1-9; **season year = season_id + 2007** (1 = 2008 ... 9 = 2016), checked on every
  match against the year of `match_date`. There is no season table.
- `player.batting_hand`: `Right-hand bat` or `Left-hand bat`.
- `player.bowling_skill`: 14 style labels: Right-arm medium, Right-arm offbreak, Right-arm fast-medium,
  Slow left-arm orthodox, Right-arm medium-fast, Legbreak, Legbreak googly, Right-arm fast, Left-arm fast-medium,
  Left-arm medium, Left-arm medium-fast, Slow left-arm chinaman, Left-arm fast, Right-arm bowler. Spin styles are
  offbreak, legbreak, legbreak googly, slow left-arm orthodox and slow left-arm chinaman; the rest are pace. Every player has one, including specialist batters, so it is not proof that a
  player bowled; use `ball_by_ball.bowler` for that.
- `player.country_name`: 11 values: India, Australia, South Africa, New Zealand, Sri Lanka, West Indies,
  England, Pakistan, Bangladesh, `Zimbabwea` (spelled so; means Zimbabwe), Netherlands.
- `player.player_name` is unique, in scorecard short form (`V Kohli`, `SC Ganguly`).
- `match.venue` is free text (35 names). The Mohali ground appears as both
  `Punjab Cricket Association Stadium Mohali` and `Punjab Cricket Association IS Bindra Stadium Mohali`.

## Known gaps: join with LEFT JOIN

| Gap | Where it shows | Effect of an inner join |
| --- | --- | --- |
| `team_id` 1 has no row in `team` | 129 matches as team_1/team_2 (51 at Eden Gardens), toss and match winner ids, 1,429 `player_match` rows, ~11% of deliveries | that team's rows vanish; show the id when the name is null |
| `player_id` 35 has no row in `player` | 124 `player_match` rows, ~1% of deliveries as striker/non-striker/bowler, 67 dismissals, 7 man-of-the-match awards | that player vanishes from rankings |
| match 419136 (its id falls between two 2010 matches) has no row in `match` | 250 deliveries, 22 `player_match` rows | the match drops out of season totals that join `match` |
| first delivery of match 335987 is not in `ball_by_ball` | its leg-bye (1 run) is in `extra_runs` | 1 extra run lost if extras are reached through `ball_by_ball` |
| player 40 is not in match 501274's XI | 9 deliveries he faced, 1 dismissal | his team in that match is unknown from `player_match` |

Team names are the franchise name at the time; renamed or replaced franchises have separate ids
(Deccan Chargers 8, Sunrisers Hyderabad 11; Pune Warriors 10, Rising Pune Supergiants 12; Kochi Tuskers
Kerala 9 played only 2011, Rising Pune Supergiants 12 and Gujarat Lions 13 only 2016).

## Mislabelled batting team in three matches

In matches 392202, 392207 and 419119, 169 second-innings rows of `ball_by_ball` have `team_batting` and
`team_bowling` swapped (the striker's `player_match.team_id` disagrees). Innings 1 is always labelled
correctly. For team-level batting figures, prefer: the batting team of innings 1 = `team_batting` of innings 1,
the batting team of innings 2 = the other team of the match; or the striker's team from `player_match`
(`match_id`, `striker` = `player_id`).

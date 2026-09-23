---
id: ipl-matches-teams-results
kind: glossary
status: active
owner: 43963011+KKranthi6881@users.noreply.github.com
description: "How IPL matches, toss, results, margins, man of the match, a team's matches and a player's team and appearances are read from the match, team, player and player_match tables."
triggers:
  - match
  - matches
  - fixture
  - game
  - toss
  - toss winner
  - elected to bat
  - elected to field
  - result
  - win
  - won
  - winner
  - loss
  - lost
  - margin
  - won by runs
  - won by wickets
  - man of the match
  - player of the match
  - home
  - venue
  - stadium
  - ground
  - season
  - team
  - franchise
  - appearances
  - matches played
  - captain
  - wicketkeeper
source_refs:
  - IPL.sqlite (queries run by the author, see spider2/layers/IPL/AUTHORING-LOG.md)
  - semantic-layer/metrics/matches_played.yaml
clarify_when:
  - The user asks about a team's "home" matches; the data has no home/away flag and team_1/team_2 order is only a listing order.
  - The user names a team whose id has no row in `team` (team_id 1).
  - The user asks about ties, no-results or super overs; none are recorded in this data.
---
# Matches, teams and results

## A match

- One row of `match` per match (`match_id`). The two sides are `team_1` and `team_2` (team ids). Their order
  is only a listing order: there is **no home/away flag** and no city column, only `venue`.
- **A team's matches** = matches where the team is `team_1` **or** `team_2`. Count or list with
  `team_1 = :t OR team_2 = :t`, or unpivot both columns with `UNION ALL`. Filtering on one column misses
  about half of a team's matches.
- `match_date` is TEXT `YYYY-MM-DD`; season year = `season_id + 2007`.
- Matches in `match`: 567. Match 419136 has deliveries and a playing XI but no `match` row, so it has no date,
  venue or result.

## Toss

- `toss_winner` is the team id that won the toss; `toss_decision` is that team's choice: `bat` or `field`.
- The toss winner **bats first** when the decision is `bat` and **fields first** when it is `field`
  (checked on every match against innings 1 `team_batting`). So the team batting first is
  `CASE WHEN toss_decision = 'bat' THEN toss_winner ELSE (the other team) END`, where the other team is
  `CASE WHEN toss_winner = team_1 THEN team_2 ELSE team_1 END`.

## Result

- `outcome_type` is `Result` for every match; there are no ties, no-results or super overs recorded.
- `match_winner` is the winning team id, always one of `team_1`/`team_2`. The loser is the other one.
- `win_type` + `win_margin`:
  - `runs`: the side **batting first** won; `win_margin` is the run difference.
  - `wickets`: the side **batting second** (chasing) won; `win_margin` is wickets in hand
    (10 minus wickets fallen in the chase).
- Do not re-derive winners or margins from ball totals; rain-shortened matches have revised targets
  (see `ipl-runs-wickets-definitions`).
- `man_of_the_match` is a player id (join `player`, with LEFT JOIN: player 35 has 7 awards and no `player`
  row). The award can go to a player on the losing side.

## Teams

- `team` has 12 franchises (`team_id` 2-13) with `name`. `team_id` 1 appears in matches, the playing XI and
  deliveries but has **no row in `team`**; always LEFT JOIN `team` and fall back to the id.
- Franchise renames or replacements have separate ids and are not linked in the data: Deccan Chargers (8)
  and Sunrisers Hyderabad (11); Pune Warriors (10) and Rising Pune Supergiants (12). Treat them as
  separate teams unless the user asks to combine them.

## A player's team and appearances

- **Matches played** by a player = rows of `player_match` for that `player_id` (one per match in the playing
  XI). A player listed in the XI counts as playing even if he did not bat or bowl.
- **His team in a match** = `player_match.team_id` for that `match_id`. Players move between franchises
  across seasons, so a player's team is per match, not per player; there is no team column on `player`.
- **Captain / keeper** = `player_match.role` in (`Captain`, `CaptainKeeper`) / (`Keeper`, `CaptainKeeper`).
- **Innings batted** by a player = distinct (`match_id`, `innings_no`) where he is `striker` or
  `non_striker` in `ball_by_ball`. **Innings bowled** = distinct (`match_id`, `innings_no`) where he is
  `bowler`.
- **Age** at a match = difference between `match_date` and `player.dob` (both `YYYY-MM-DD` text), e.g.
  `(julianday(match_date) - julianday(dob)) / 365.25`.

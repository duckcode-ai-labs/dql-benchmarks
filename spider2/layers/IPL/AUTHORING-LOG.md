# IPL L2/L3 authoring log

- **Author**: Claude (Opus 5.5), a fresh agent that has not seen the Spider 2.0-Lite questions, answers or
  per-question documents.
- **Start**: Wed Sep 23 10:45:53 CDT 2026
- **End**: Wed Sep 23 10:58 CDT 2026 (about 13 minutes of wall-clock time)
- **Status of the result**: AI-authored, independently reviewed, not human-certified.

## Files read outside the working folder

| File | Why |
| --- | --- |
| `spider2/layers/AUTHORING.md` | the rules |
| `insurance/layers/L1/domains/insurance/domain.dql` | domain file format |
| `insurance/layers/L1/domains/insurance/modeling/areas/claims.dql.yaml` (first ~200 lines) | entity/relationship/certifiedAgainst/validation format |
| `insurance/layers/L1/domains/insurance/modeling/concepts.dql.yaml` (first 50 lines) | concepts format (not used in the end) |
| `insurance/layers/L3/skills/insurance-claims-reserves-payments.skill.md` (first 80 lines), `insurance-data-coverage.skill.md` (first 30 lines), `grep kind:` over the five insurance skills | skill front-matter format and `kind` values |
| `work/insurance/projects/W2/semantic-layer/` (directory listing only) | looked for native metric examples; they were MetricFlow imports, so not used |
| DQL source under `scratchpad/phase3/`: `packages/dql-core/src/manifest/dbt-first-modeling.ts` (RawEntity/RawRelationship fields, relationship compile and certification rules, lifecycle/analytical-role/optionality/join_types parsers), `dbt-first-authoring.ts` (grep), `types.ts` (grep), `packages/dql-agent/src/relationship-validation.ts` (validator and evidence rules), `packages/dql-agent/src/governed-relational-compiler.ts` (lines 200-235: `join_types: [left]` becomes a LEFT JOIN), `packages/dql-agent/src/metadata/analytical-policy.ts` (lines 420-460), `apps/cli/src/commands/model.ts`, `apps/cli/src/local-runtime.ts` (relationship validate/profile routes), `packages/dql-core/src/semantic/semantic-layer.ts` (MetricDefinition, parser, composeQuery), `packages/dql-core/src/semantic/yaml-loader.ts`, `packages/dql-agent/src/skills/loader.ts` (grep) | file formats and how validation evidence is produced |
| DQL docs: `docs/reference/semantic-layer.md`, `docs/tutorials/04-agentic-analytics.md` (lines 106-149) | native metric YAML shape |

Nothing under `data/`, `work/spider2/runs/`, `work/spider2/projects/`, `work/spider2/*.log`, any
`*spider2-lite*.jsonl`, any `*gold*` file, or any other `spider2/` path was opened. One `ls -la` of the
`dql-benchmarks` root was run by accident (directory names only; no files opened).

## Queries run (read-only, `sqlite3 -readonly IPL.sqlite`), summarised

1. `.schema`; row counts of all 8 tables.
2. Samples of `team`, `player`, `match`; match_id/date/season ranges; matches per season with min/max date;
   `typeof` of `match_date` and `dob`; format check (`glob '[0-9][0-9][0-9][0-9]-...'`) on both; season year
   check `substr(match_date,1,4) = season_id + 2007` (0 exceptions).
3. Code profiles: `toss_decision`; `win_type` x `outcome_type` with margin ranges and nulls; team ids used as
   team_1/team_2; toss winner and match winner always one of the two teams; venues (35).
4. Orphans and coverage: player ids 1-469 (468 rows); man_of_the_match not in `player`; `player_match` ids not
   in `player`/`team`/`match`; the same for every delivery table against `match`; missing ids found:
   team 1, player 35, match 419136 (and its adjacent match ids/dates); union of every player-id column not in
   `player` = only 35.
5. Delivery structure: innings_no values; over_id and ball_id ranges and ball_id distribution; runs_scored
   distribution; extra_type and extra_runs distribution; kind_out distribution.
6. Delivery-key joins: every `batsman_scored` and `wicket_taken` row matches `ball_by_ball`; 1 `extra_runs`
   row does not (match 335987 innings 1 over 1 ball 1 - inspected the over); deliveries without a
   `batsman_scored` row are all wides; wides/no-balls/byes/leg-byes with and without bat rows; legal balls
   per over (6 in 21,489 of 21,832 overs) and whether short overs are the last over (328 of 340).
7. `ball_by_ball` column nulls; batting/bowling team always one of the match teams; striker/non-striker/
   bowler not in `player`; player_out is striker or non-striker; toss winner bats first iff `bat`; innings with
   two batting teams (3 matches, inspected: labels swapped on 169 rows); overs with two bowlers (16);
   same bowler in consecutive overs (0).
8. `player_match`: roles; players per team per match (one team with 10: match 501274); two teams per match;
   team_id always a match team; keepers and captains per team-match; ball_by_ball striker/non-striker/bowler
   and wicket player_out against `player_match` (match_id, player_id) and team agreement.
9. Result check: innings totals (runs off the bat + extras, summed separately) against `win_type`/`win_margin`
   (545 of 567 consistent; listed the 22 others and inspected overs per innings for 4 of them: rain-shortened);
   wickets fallen (excluding retired hurt) vs wicket-win margins (no mismatches); innings per number of overs.
10. Player attributes: batting_hand, bowling_skill, country_name distributions; player_name uniqueness.
11. Grain proof for all 8 entities: row count = distinct key count, 0 null keys.
12. Definition sanity checks: runs by striker join total; balls faced count; runs conceded formula; bowler
    wickets; no-ball and wide extra_runs values; wicket kinds on extra deliveries; striker_batting_position
    unique per batter per innings and per position; man of the match on the losing side (13 matches);
    team seasons for franchises 8-13.
13. All 23 relationships run through DQL's own validator (below).

## How relationship evidence was produced

`dql model discover/apply-discovery --validate` only proposes joins on same-named columns, and the CLI has no
command to validate a hand-authored relationship (the Modeling page does it through the notebook server's
`/api/modeling/dbt-first/relationships/validate`). So a scratch script
(`scratchpad/ipl/validate-lib.mjs`, `generate.mjs`) called the same functions that route calls,
`catalogKeyTypes` + `validateRelationshipOnWarehouse` from `@duckcodeailabs/dql-agent` (dist of the given
build), against `IPL.sqlite` with better-sqlite3 and dialect `sqlite`. It first reproduced the exact
`query_fingerprint` and `proof_fingerprint` that `apply-discovery` had written for `ball_by_ball_to_match`,
then wrote `validation:` blocks for all relationships. `dql model validate .` reports no stale-proof warnings,
and `dql model explain` shows certified relationships as automatic join proof.

## Decisions

### Entities (8, all `status: certified`)

Grain and keys proven on the data (row count = distinct key count, no null keys) for every table:
`match(match_id)`, `team(team_id)`, `player(player_id)`, `player_match(match_id, player_id)`, and
`ball_by_ball`, `batsman_scored`, `extra_run` (table `extra_runs`), `wicket_taken` on
`(match_id, innings_no, over_id, ball_id)`. Entity ids from DQL's draft were kept. The draft's grain order
was changed to `match_id, innings_no, over_id, ball_id`. Each entity has a business description from the
data (what a row is, codes, date storage, known gaps) and an `analytical_role` (event, dimension, bridge for
`player_match`). Value counts that would amount to answers were left out of the descriptions.

The draft `modeling/model.dql.yaml` was replaced by two areas: `matches` (match, team, player, player_match)
and `deliveries` (ball_by_ball, batsman_scored, extra_run, wicket_taken).

### Certification rule for relationships

Certified when DQL's validator passes (declared cardinality holds with safe fanout), rows join, there are no
null keys, and the unmatched from-rows are at most 2% of the table and all trace to one identified record
missing from the parent. Those relationships carry `join_types: [left]` (the relational compiler then emits a
LEFT JOIN), so the missing parent never drops rows. Otherwise draft, with the reason in the description.

### Certified (16)

| Relationship | Keys | Card. | Evidence (from rows / joined / unmatched) |
| --- | --- | --- | --- |
| batsman_scored_to_ball_by_ball | 4 delivery keys | 1:1 | 131,259 / 131,259 / 0 |
| wicket_taken_to_ball_by_ball | 4 delivery keys | 1:1 | 6,618 / 6,618 / 0 |
| extra_run_to_ball_by_ball | 4 delivery keys | 1:1 | 7,349 / 7,348 / 1 (first delivery of 335987) - left |
| ball_by_ball_to_match | match_id | m:1 | 134,703 / 134,453 / 250 (match 419136) - left |
| batsman_scored_to_match | match_id | m:1 | 131,259 / 131,017 / 242 (419136) - left |
| extra_run_to_match | match_id | m:1 | 7,349 / 7,334 / 15 (419136) - left |
| wicket_taken_to_match | match_id | m:1 | 6,618 / 6,605 / 13 (419136) - left |
| player_match_to_match | match_id | m:1 | 12,495 / 12,473 / 22 (419136) - left |
| player_match_to_player | player_id | m:1 | 12,495 / 12,371 / 124 (player 35) - left |
| ball_by_ball_striker_to_player | striker = player_id | m:1 | 134,703 / 133,391 / 1,312 (0.97%, player 35) - left |
| ball_by_ball_non_striker_to_player | non_striker = player_id | m:1 | 134,703 / 133,317 / 1,386 (1.03%, player 35) - left |
| ball_by_ball_bowler_to_player | bowler = player_id | m:1 | 134,703 / 132,976 / 1,727 (1.28%, player 35) - left |
| wicket_taken_player_out_to_player | player_out = player_id | m:1 | 6,618 / 6,551 / 67 (1.01%, player 35) - left |
| match_man_of_the_match_to_player | man_of_the_match = player_id | m:1 | 567 / 560 / 7 (1.23%, player 35) - left |
| ball_by_ball_striker_to_player_match | match_id, striker = match_id, player_id | m:1 | 134,703 / 134,694 / 9 (player 40 in match 501274) - left |
| ball_by_ball_bowler_to_player_match | match_id, bowler = match_id, player_id | m:1 | 134,703 / 134,703 / 0 |

Max `to` rows per key is 1 for every relationship (1 on both sides for the 1:1 ones). Relationships with the
same pair of entities carry `roles` (striker / non_striker / bowler / player_out / man_of_the_match).

### Draft (7) and why

All seven go to `team`: `match_team_1_to_team`, `match_team_2_to_team`, `match_toss_winner_to_team`,
`match_winner_to_team`, `player_match_to_team`, `ball_by_ball_team_batting_to_team`,
`ball_by_ball_team_bowling_to_team`. The validator passes (m:1, safe) but `team_id` 1 has no row in `team`,
so 10.6-12.2% of rows would lose their team name (above the 2% rule). The two `ball_by_ball` team
relationships also carry 169 rows with swapped batting/bowling team labels in matches 392202, 392207 and
419119. Each is declared with `join_types: [left]` and the reason in its description.

### L3

- Skills written: `ipl-data-model` (domain_reference: tables, grain, delivery key, innings/overs/balls,
  code values, date and season storage, known gaps, mislabelled team rows), `ipl-runs-wickets-definitions`
  (metric_policy: runs off the bat vs extras, innings totals, bowler runs conceded, balls faced, legal balls,
  overs, bowler wickets, wickets fallen, not out, standard rates, partnerships), `ipl-matches-teams-results`
  (glossary: a team's matches via team_1 OR team_2, toss and who bats first, win_type/win_margin, man of the
  match, team gaps and franchise ids, a player's team per match, appearances, captain/keeper, age).
  `metrics-glossary.skill.md` (DQL starter) was rewritten to list the native metrics. The DQL starter skills
  `block-authoring`, `domain-rules`, `sql-conventions` were left unchanged and are copied as-is.
- Cricket scoring conventions not stored in the data (bowler not charged byes/leg-byes; run out not a bowler
  wicket; no-balls count as balls faced; powerplay overs 1-6) are labelled as conventions in the skills.
- Profile counts that could double as answers (players per country, dismissals per kind, boundaries,
  extras totals, toss-winner-wins) were removed from the skills; value lists were kept.
- Native metrics (5, single table, no filters, `status: certified`): `runs_off_bat` = SUM(batsman_scored.runs_scored),
  `extras_conceded` = SUM(extra_runs.extra_runs), `deliveries_bowled` = COUNT(*) ball_by_ball,
  `dismissal_records` = COUNT(*) wicket_taken, `matches_played` = COUNT(*) match. Dimensions: `extra_type`,
  `kind_out`, `season_id`, `venue`, `match_date`. Not made metrics because they combine tables or encode a
  convention: innings total, balls faced, legal balls, runs conceded, bowler wickets, rates.
- No blocks were written.

## Validation

- `dql model validate .`: valid, 8 entities, 23 relationships, no diagnostics.
- `dql semantic validate .`: valid; `dql semantic query extras_conceded extra_type` composes
  `SELECT extra_type, SUM(extra_runs) ... FROM extra_runs GROUP BY extra_type`.
- `dql validate .`: all files valid. `dql doctor .`: 14/16 (version-drift notice and retrieval-health
  warning, both environment-level).
- All 7 skills load through `@duckcodeailabs/dql-agent` `loadSkills` with no diagnostics.

## DQL defects / format limitations hit

1. No CLI command validates a hand-authored relationship (different column names, composite keys or role
   joins); `apply-discovery --validate` only covers same-named columns. Evidence had to be produced by calling
   the validator functions directly (same code the Modeling page's HTTP route uses).
2. `optionality` semantics (`from`/`to` = required/optional) are not documented; it was not used, and
   optional parents are expressed with `join_types: [left]` plus the description.

---
id: f1-points-and-standings
kind: metric_policy
status: active
owner: benchmark-owner
domain: f1
description: "How points are recorded per race, per sprint and per constructor, and how the drivers' and constructors' championship standings work (cumulative after each race; the final table is the last race of the season)."
triggers:
  - points
  - total points
  - championship
  - standings
  - champion
  - world champion
  - title
  - constructors championship
  - drivers championship
  - leader
  - position in the championship
  - season points
  - wins in a season
  - max points
preferred_metrics: [race_points, sprint_points]
source_refs:
  - "warehouse: main.results, main.sprint_results, main.constructor_results, main.driver_standings, main.driver_standings_ext, main.constructor_standings, main.races_ext"
clarify_when:
  - The user asks for a driver's "points in a season" before 1991, where championship points (after dropped scores) and the sum of race points differ.
  - The user asks for 2024 totals; the data stops after round 12.
---
# Points and championship standings

## Points by race

- `results.points` = a driver's points from one Grand Prix (REAL). It includes the fastest-lap
  bonus point where the season awarded one and excludes sprint points. Half points were awarded
  for shortened races (e.g. 4.5, 12.5); the 2014 Abu Dhabi GP paid double (50 to the winner).
- `sprint_results.points` = points from a sprint race (2021 onward).
- `constructor_results.points` = a constructor's points from one race (1958 onward, when the
  constructors' championship began). From 1980 it equals the sum of its cars' `results.points`
  plus their sprint points (checked on every 1980-2024 row); before 1980 usually only the
  best-placed car scored for the constructor. `status = 'D'` marks McLaren's 2007 exclusion.
- Winner's points by era (from the data): 8 (1950-1960; 9 when the winner also set the fastest
  lap in 1950-1959),
  9 (1961-1990), 10 (1991-2009), 25 (2010 onward; +1 fastest lap 2019-2024; sprint winner 3 in
  2021, 8 from 2022). `races_ext.max_points` holds the most one driver could score at each race
  weekend (8, 9, 10, 25, 26, 29 or 34).

## Standings are cumulative snapshots

- `driver_standings` and `constructor_standings` have one row per driver (constructor) **after
  each race**: `points` and `wins` are the season totals **so far**, `position` the championship
  position at that moment. Never sum standings rows across races.
- **Final championship table of a season** = the standings rows of the season's last race that
  has standings: `race_id` of `MAX(round)` among that year's races with standings rows.
  **Champion** = `position = 1` in that table (e.g. 2023 Max Verstappen 575 points, 19 wins;
  1988 Ayrton Senna 90; constructors 2023 Red Bull 860). The 2024 table is after round 12 only.
- Standings `points` include sprint points (2023 final: Verstappen 530 race + 45 sprint = 575).
- Standings `wins` = count of `results.position = 1` so far that season (matches on every final
  table).
- Up to 1990 the championship counted only a driver's best N results ("dropped scores"), so final
  standings points are lower than the sum of race points for some drivers (1-6 drivers in 26
  seasons between 1950 and 1990). For "championship points" use standings; for "points scored"
  use the sum of `results.points` (+ sprint points) and say which you used.
- `position_text` codes: drivers' 'D' once (a driver disqualified from the 1997 championship,
  position 26); constructors' 'E' = excluded (McLaren 2007, position 11).

## Completed driver standings (driver_standings_ext)

- `driver_standings` omits some drivers who raced (e.g. 5 of 20 at the first 2009 race).
  `driver_standings_ext` adds 417 rows for drivers with a result at that race but no standings
  row: `driver_standings_id = 0`, 0 points, 0 wins, `position_text` NULL, placed after the
  recorded drivers. Use it when every participant must appear in a standings table; use
  `driver_standings` for the official table. Its unique key is `race_id + driver_id`.

## Common calculations

- Driver's season points (race + sprint): `SUM(results.points)` + `SUM(sprint_results.points)`
  for the driver's rows in races of that `year`, or the final standings row (after dropped scores
  before 1991).
- Points gap to the leader after a race: leader's standings `points` minus the driver's, same
  `race_id`.
- Constructor's season points: final `constructor_standings.points`, or
  `SUM(constructor_results.points)` over the season's races. From 1980 the two agree for 567 of
  569 constructor-seasons; they differ for constructor_id 10 in 2018 (standings 52 vs summed 111) and
  constructor_id 211 in 2020 (195 vs 210), where the championship total was adjusted. The
  standings value is the championship total.

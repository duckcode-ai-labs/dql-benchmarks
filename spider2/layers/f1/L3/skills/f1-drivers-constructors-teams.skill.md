---
id: f1-drivers-constructors-teams
kind: domain_reference
status: active
owner: 43963011+KKranthi6881@users.noreply.github.com
domain: f1
description: "Drivers and constructors: names, codes, nationality, date of birth, which team a driver raced for, stints within a season, teammates and team driver rank, short team names and livery colours."
triggers:
  - driver
  - drivers
  - constructor
  - constructors
  - team
  - teams
  - teammate
  - nationality
  - date of birth
  - age
  - driver code
  - car number
  - drove for
  - changed team
  - stint
  - lead driver
  - livery
  - colour
source_refs:
  - "warehouse: main.drivers, main.drivers_ext, main.constructors, main.constructors_ext, main.short_constructor_names, main.drives, main.team_driver_ranks, main.tdr_overrides, main.liveries"
clarify_when:
  - The user names a team by its modern short name (e.g. "Lotus") that maps to several constructor rows.
---
# Drivers, constructors and teams

## Drivers

- `drivers`: one row per driver (`driver_id`). Name = `forename`, `surname`; `full_name` is a
  generated column (`forename || ' ' || surname`); full names are unique in this data.
  `driver_ref` is a unique lowercase key (e.g. `hamilton`).
- `dob` is text `YYYY-MM-DD` (1896 to 2005). `nationality` is a demonym (British 166, American
  158, Italian 99, ...), not a country name.
- `number` (permanent number) is filled for only 57 drivers and `code` (e.g. HAM) for 102; both
  are NULL for most historical drivers. `drivers_ext.code` fills every code (mostly the first three
  letters of the surname, upper case), so there codes repeat (SCH x15): never use code as a key.
- A driver's car number in a given race is `results.number`, not `drivers.number`.

## Constructors (teams)

- `constructors`: one row per constructor entry (`constructor_id`); `constructor_ref` unique
  (e.g. `red_bull`, `ferrari`, `mercedes`); `nationality` a demonym (Red Bull: Austrian).
- In the 1950s-70s an entrant name often includes the engine ("Cooper-Climax", "Lotus-Ford"), so
  one team appears as several constructors. `constructors_ext.short_name` (from
  `short_constructor_names`) groups them ("Cooper-Climax" -> "Cooper", "Team Lotus" -> "Lotus");
  otherwise it equals `name`. Group by `short_name` when the question means the team brand, and by
  `constructor_id` when it means the entry.
- **Which team a driver raced for** in a race = `results.constructor_id` (also on
  `qualifying` and `sprint_results`). There is no team column on `drivers`.

## Stints within a season (drives)

- `drives`: one row per continuous stint of a driver with a constructor in a season:
  `first_round` to `last_round`, `drive_id` = 1, 2, ... in order. Rows with `drive_id = -1` and
  `constructor_id = -1` are gaps (rounds between stints with no result) and must be excluded when
  listing teams. `is_first_drive_of_season` / `is_final_drive_of_season` flag the first and last
  stint.
- **Drivers who drove for more than one constructor in a season**: `COUNT(DISTINCT
  constructor_id) > 1` over `drive_id > 0` rows (310 driver-seasons).

## Teammates and team driver rank

- **Teammates** in a race = drivers with the same `race_id` and `constructor_id` in `results`.
- `team_driver_ranks`: one row per driver per constructor per season, `team_driver_rank`
  1 = the team's lead driver, 2 = second, ... (up to 29 for 1950s teams with many entrants).
  The rank is supplied with the data (it is not reproducible from points or races alone) and
  already includes the 48 manual corrections in `tdr_overrides` (2004-2022).

## Livery colours

- `liveries`: a constructor's primary colour (`primary_hex_code`, e.g. `#900000`) for
  `start_year` to `end_year` (NULL = current). Join on `constructor_ref`; three rows use
  "benneton", which matches no constructor (the constructor is `benetton`).

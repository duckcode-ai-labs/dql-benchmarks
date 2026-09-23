---
id: f1-calendar-and-coverage
kind: domain_reference
status: active
owner: 43963011+KKranthi6881@users.noreply.github.com
domain: f1
description: "Seasons, races, rounds, circuits, race dates and times, sprint weekends, the derived _ext tables, and how far each table's data goes."
triggers:
  - season
  - year
  - race
  - grand prix
  - round
  - circuit
  - track
  - venue
  - race date
  - race time
  - sprint weekend
  - first race
  - last race
  - calendar
source_refs:
  - "warehouse: main.seasons, main.races, main.races_ext, main.circuits, main.circuits_ext, main.short_grand_prix_names"
clarify_when:
  - The user asks about "races in 2024" without saying whether scheduled races count; only the first 12 of 24 have results.
---
# Calendar, circuits and data coverage

## Seasons and races

- A **season** is a `year` (`seasons`, 1950 to 2024). Races belong to a season through
  `races.year`; there is no season id.
- A **race** (Grand Prix) is one row of `races` (`race_id`). `year + round` is unique: `round` is
  the race's order in its season (1 = first race of the season). The **first race of a season** is
  `round = 1`; the **last race** is `MAX(round)` for that year.
- `races.name` is the Grand Prix name ("British Grand Prix", "Indianapolis 500" for 1950-1960,
  which counted for the championship). The same name recurs every year, so a specific race is
  `name + year`.
- `races.circuit_id` -> `circuits`. `circuits.name` is the circuit ("Silverstone Circuit"),
  `location` the town, `country` the country as written in the data (e.g. "UK", "USA", "Italy");
  `circuit_ref` is a short unique key (e.g. `monza`).

## Dates and times

- `races.date` is text `YYYY-MM-DD`; compare and sort it as text or use SQLite date functions
  (`strftime('%m', date)`, `julianday(date)`).
- `races.time` is the start time as text `HH:MM:SS` in UTC (the 2023 Australian GP shows
  `05:00:00`); it is NULL for 731 older races.
- Practice (`fp1_*`, `fp2_*`, `fp3_*`), qualifying (`quali_*`) and sprint (`sprint_*`) date and
  time columns are text, filled only from 2021.
- `drivers.dob` is text `YYYY-MM-DD`. A driver's **age at a race** =
  `(julianday(races.date) - julianday(drivers.dob)) / 365.25`, or compare year/month/day parts.

## Data coverage (checked on the data)

| Table | Races covered | Years |
| --- | --- | --- |
| races | 1,125 (includes 12 not yet run) | 1950 to 2024-12-08 |
| results, driver_standings, lap_positions | 1,113 | 1950 to 2024-07-07 |
| constructor_results / constructor_standings | 1,048 / 1,049 | 1958 to 2024-07-07 |
| qualifying | 482 | 1994 to 2024 (only some races 1996-2002) |
| lap_times, lap_time_stats | 531 | 1996 to 2024-06-30 (no laps for the 2024 British GP) |
| pit_stops | 273 | 2011 to 2024-07-07 |
| overtakes | 272 | 2011 to 2024-06-30 |
| sprint_results | 15 | 2021 to 2024-06-30 |

- The data ends after round 12 of 2024 (British GP, 2024-07-07). Races 13-24 of 2024 exist in
  `races` only, so "the 2024 season" is partial: standings for 2024 are after round 12.
- A race **has happened** when it has `results` rows. Count races with
  `COUNT(DISTINCT results.race_id)` when the question means races held.

## Sprint weekends

- A sprint belongs to the Grand Prix weekend's `race_id`. The 15 weekends with sprint results are
  flagged `races_ext.has_sprint = 1` (2021: 3, 2022: 3, 2023: 6, 2024: 3). `races.sprint_date` is
  also set for three late-2024 sprints that have no results yet.

## The _ext tables (derived copies with extra columns)

- `races_ext` = `races` + `is_pit_data_available` (1 when the race has pit stop rows),
  `short_name` (short GP name, e.g. "Britain", falls back to the full name), `has_sprint`,
  `max_points` (most points one driver could score that weekend: 8, 9, 10, 25, 26, 29 or 34
  depending on the season's system; see the points skill).
- `circuits_ext` = `circuits` + `last_race_year` and `number_of_races` (counts every scheduled
  race at the circuit, including 2024 races not yet run).
- `short_grand_prix_names` covers only 40 GP names; prefer `races_ext.short_name`.
- Join an _ext table to its base table on the id (one-to-one); never add both to a count.

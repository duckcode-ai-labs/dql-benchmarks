---
id: f1-results-and-status
kind: metric_policy
status: active
owner: benchmark-owner
domain: f1
description: "How race results, finishing positions, status codes, retirements, wins, podiums, pole positions, fastest laps and qualifying are recorded, with the codes checked on the data."
triggers:
  - result
  - results
  - finish
  - finished
  - finishing position
  - winner
  - win
  - wins
  - victory
  - podium
  - pole
  - pole position
  - grid
  - starting position
  - qualifying
  - q1
  - q2
  - q3
  - fastest lap
  - dnf
  - retired
  - retirement
  - disqualified
  - status
  - classified
  - lapped
  - sprint
source_refs:
  - "warehouse: main.results, main.sprint_results, main.status, main.qualifying, main.retirements, main.lap_positions"
clarify_when:
  - The user asks for "finishes" without saying whether lapped cars ("+1 Lap") count as finishers.
  - The user asks for "pole positions" for seasons before 1994, where only results.grid is available.
---
# Race results, status codes and qualifying

## One row of results

`results` has one row per **car** per race (`result_id`). `race_id`, `driver_id`,
`constructor_id` say which race, driver and team. In 1950-1978 a driver can have 2-3 rows in one
race (shared cars, car changes), so do not assume `race_id + driver_id` is unique; count
`DISTINCT race_id` for "races entered".

| Column | Meaning (checked on the data) |
| --- | --- |
| `grid` | starting grid position; `0` = no grid slot (did not qualify / prequalify, withdrew, pit-lane start) |
| `position` | classified finishing position; NULL when not classified |
| `position_text` | the position as text, or a code: `R` retired, `D` disqualified, `E` excluded, `W` withdrew, `F` failed to qualify, `N` not classified |
| `position_order` | the full running order of every car in the race (always filled, 1..n); use it to rank all cars |
| `points` | points from this race (REAL; half points exist, e.g. 4.5; fastest-lap point included where awarded; sprint points not included) |
| `laps` | laps completed |
| `time` | winner: total race time `h:mm:ss.sss`; others: gap text like `+11.987`; only for cars classified on a timed lap |
| `milliseconds` | total race time in ms (same rows as `time`) |
| `fastest_lap`, `fastest_lap_time`, `fastest_lap_speed`, `rank` | from 2004 only: lap number of the car's fastest lap, its time (`m:ss.sss` text), speed (km/h, text), and `rank` of that lap in the race (1 = fastest lap of the race, 0 = no timed lap) |
| `status_id` | -> `status.status` |

## Status codes (`status` table)

- `1 Finished` = finished on the lead lap.
- `+1 Lap`, `+2 Laps`, ... (`status LIKE '+%Lap%'`) = classified finisher that many laps down.
- `2 Disqualified`, `96 Excluded`, `54 Withdrew`, `62 Not classified`, `81 Did not qualify`,
  `97 Did not prequalify`.
- Everything else is a retirement cause: Engine (5), Accident (3), Collision (4), Gearbox (6),
  Spun off (20), Suspension, Transmission, Electrical, Brakes, ...
- **Finished (incl. lapped)** = `status = 'Finished' OR status LIKE '+%Lap%'` (14,951 rows).
  **Did not finish** = every other status. Say which definition you use.
- `position` is filled for 15,591 rows: 14,925 finishers plus 666 cars classified despite a late
  retirement (status e.g. Engine, but `position` set); 26 finisher-status rows (codes N/R) have no
  position. Use `position IS NOT NULL` for "classified", and status for "finished".

## Retirements

- `retirements` has one row per non-finishing result (11,568 = every results row whose status is
  not Finished and not +N Laps), joined to results on `race_id + driver_id + position_order`.
  `lap` = the lap the car stopped on (`results.laps + 1`).
- `retirement_type`: "Retirement (Driver Error)" = Accident, Collision, Spun off;
  "Retirement (Disqualification)" = Disqualified; "Retirement (Mechanical Problem)" = **every other
  status**, including Did not qualify, Withdrew and Not classified. For mechanical failures in the
  strict sense, filter on the status text instead.

## Wins, podiums, poles, fastest laps

- **Win** = `results.position = 1`. 1,116 winning rows over 1,113 races: three 1950s races credit
  two drivers who shared the winning car. Count wins as rows with `position = 1` per driver, or
  `DISTINCT race_id` per constructor.
- **Podium** = `position <= 3` (`position` is NULL for unclassified cars, so they drop out).
- **Points finish** = `points > 0`.
- **Pole position** = `qualifying.position = 1` (1994 onward; 482 races, one pole each). For all
  years use `results.grid = 1` (starting from first; differs from the qualifying pole when the
  pole-sitter is penalised: 470 of 482 poles also started first). Say which one you use.
- **Fastest lap of a race** = `results.rank = 1` (2004 onward), or the minimum
  `lap_times.milliseconds` in the race (1996 onward).
- **Grid versus qualifying**: `results.grid` is where the car started; `qualifying.position` is
  where it qualified. `lap_positions` rows with `lap = 0` label each start as "Starting Position -
  Qualifying" (grid = qualifying position), "- Grid Drop" (started further back), "- Grid Increase"
  (started further forward), "- Pit Lane Start", or "- No Qualification" (no qualifying row).
- **Positions gained** in a race = `grid - position` for classified cars with `grid > 0`.

## Qualifying

- `qualifying` has one row per driver per race (`race_id + driver_id` unique), 1994 onward, and
  only for some races in 1996-2002. `position` = qualifying position.
- `q1`, `q2`, `q3` are the best lap in each session as text `m:ss.sss`. `q2` exists from 2005
  and `q3` from 2006, only for drivers who reached that session; otherwise NULL or empty string
  (treat `''` as missing). Convert to ms with
  `CAST(substr(q1, 1, instr(q1, ':') - 1) AS INTEGER) * 60000 + CAST(substr(q1, instr(q1, ':') + 1) AS REAL) * 1000`.

## Sprint results

- `sprint_results` has the same columns and codes as `results` (no `rank`), for the 15 sprint
  weekends of 2021-2024. `points` are sprint points (3-2-1 in 2021, 8 for the winner from 2022).
- Its `result_id` is its own sequence (1-300): never join it to `results.result_id`. The race
  result of the same driver that weekend is `results` on `race_id + driver_id`.
- A driver's weekend points = race points + sprint points.

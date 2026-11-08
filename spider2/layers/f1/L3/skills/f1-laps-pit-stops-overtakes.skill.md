---
id: f1-laps-pit-stops-overtakes
kind: metric_policy
status: active
owner: benchmark-owner
domain: f1
description: "Lap times and their units, running race time, per-driver lap statistics, positions per lap, pit stops (durations, red-flag stops) and overtakes (position changes and their types)."
triggers:
  - lap
  - laps
  - lap time
  - fastest lap
  - average lap time
  - lap position
  - running order
  - leader after lap
  - pit stop
  - pit stops
  - pit lane
  - stop duration
  - overtake
  - overtakes
  - overtaking
  - passes
  - position change
preferred_metrics: [pit_stop_count, timed_laps]
source_refs:
  - "warehouse: main.lap_times, main.lap_times_ext, main.lap_time_stats, main.lap_positions, main.pit_stops, main.overtakes"
clarify_when:
  - The user asks for "overtakes" without saying whether passes caused by pit stops or retirements count.
  - The user asks for average pit stop time; red-flag stoppages recorded as pit stops distort it.
---
# Laps, pit stops and overtakes

## Lap times (1996 onward)

- `lap_times`: one row per driver per lap per race (`race_id + driver_id + lap`, lap from 1).
  `position` = running position at the end of the lap.
- Use `milliseconds` (INT, always filled) for arithmetic; `seconds` = `milliseconds / 1000`.
  `time` is display text `m:ss.sss`, or `h:mm:ss.sss` for 43 laps over an hour (red-flag laps),
  so do not parse `time` when `milliseconds` is there.
- Lap times range from 55.4 s to 2 h 5 min: slow laps include safety-car, pit and red-flag laps.
  Averages over all laps include them.
- **Fastest lap of a race** = `MIN(milliseconds)` over the race's lap_times rows (or
  `results.rank = 1`, 2004 onward).
- `lap_times_ext` = the same rows plus `running_milliseconds`, the driver's cumulative race time
  at the end of each lap (running sum of `milliseconds`, verified on every row). Use it for gaps
  between drivers at a given lap.
- `lap_time_stats`: one row per driver per race: `avg_milliseconds` = mean lap time (all laps),
  `stdev_milliseconds` = population standard deviation (divides by n; e.g. 15,927.05 ms for
  race 1 driver 1 over 58 laps, where the sample stdev would be 16,066.16). `_seconds` columns
  are the same values / 1000.
- The 2024 British GP (2024-07-07) has results and pit stops but no lap times.

## Positions per lap (lap_positions)

- `lap_type = 'Race'` rows (lap >= 1, 1996 onward) are the lap_times positions.
- `lap = 0` rows give the start: `position` = `results.grid`, typed "Starting Position -
  Qualifying / Grid Drop / Grid Increase / Pit Lane Start / No Qualification" (see the results
  skill). Pre-1996 races have only lap 0 and retirement rows.
- "Retirement (Driver Error | Mechanical Problem | Disqualification)" rows sit on the lap the car
  retired, with `position` = its final `position_order`.
- Filter on `lap_type` before using positions: e.g. **leader after lap N** =
  `lap_type = 'Race' AND lap = N AND position = 1`.

## Pit stops (2011 onward)

- `pit_stops`: one row per stop (`race_id + driver_id + stop`). `stop` = the driver's stop
  number in the race, `lap` = lap of the stop, `time` = local time of day (text `HH:MM:SS`; e.g.
  18:23:40 in the 2023 Bahrain GP, which started 15:00 UTC).
- `duration` is text (`24.682` seconds, or `m:ss.sss` for 500 stops of a minute or more);
  use `milliseconds` or `seconds` for arithmetic.
- Stops of a minute or more are mostly red-flag stoppages the source records as pit stops (49 in
  the 2023 Australian GP; the longest is 51 minutes). Exclude them (e.g. `milliseconds < 60000`) when the
  question is about normal pit stop times, and say so.
- In the 2024 Monaco GP stop numbers are not consecutive (a stop numbered 70), so count stops
  with `COUNT(*)`, not `MAX(stop)`.
- **Number of pit stops** of a driver in a race = `COUNT(*)` of their rows.
- `races_ext.is_pit_data_available = 1` marks races that have pit stop rows.

## Overtakes (2011 onward)

- `overtakes`: one row per pair of drivers who swapped order from the previous lap to this lap.
  `overtaking_driver_id` got ahead of `overtaken_driver_id` on `lap`; `current_position` and
  `previous_position` are the overtaking driver's positions after and before.
- `overtake_type` / `overtake_desc` (checked against pit_stops and retirements):
  - `S` "Start": position gained on lap 1 compared with the grid (2,452);
  - `T` "Track": an on-track pass (14,388);
  - `P` "Pit Stop (Pit Entry)": the overtaken driver pitted on that lap (13,099); "Pit Stop (Pit
    Exit)": the overtaken driver pitted on the previous lap (23,668);
  - `R` "Retirement (Driver Error | Mechanical Problem | Disqualification)": the overtaken driver
    retired (5,699).
- **On-track overtakes** = `overtake_type = 'T'`; include `'S'` when start gains count. Do not
  count `P` and `R` rows as overtakes unless the question asks for all position changes.
- A pair of drivers can appear twice on one lap with different types (grain: race, both drivers,
  lap, `overtake_desc`).

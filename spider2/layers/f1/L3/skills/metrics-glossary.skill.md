---
id: metrics-glossary
description: "Business terms mapped to the native semantic-layer metrics of the F1 project."
---
# Metrics glossary

Native metrics in `semantic-layer/metrics/f1.yaml` (AI-authored, not human-certified). They are
plain counts and sums; business measures that need a filter choice (wins, podiums, poles, DNFs,
championship points) are defined in the F1 skills instead.

| Business term | Metric | Definition |
| --- | --- | --- |
| Race entries, starts, cars entered | `race_entries` | `COUNT(*)` of `results` (one row per car per race) |
| Race points, Grand Prix points | `race_points` | `SUM(results.points)`; excludes sprint points; not championship points before 1991 |
| Sprint points | `sprint_points` | `SUM(sprint_results.points)` (2021 onward) |
| Pit stops | `pit_stop_count` | `COUNT(*)` of `pit_stops` (2011 onward; includes red-flag stoppages) |
| Timed laps | `timed_laps` | `COUNT(*)` of `lap_times` (1996 onward) |

For championship totals use the final `driver_standings` / `constructor_standings` row of the
season (see the `f1-points-and-standings` skill).

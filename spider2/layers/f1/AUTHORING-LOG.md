# f1 — L2/L3 authoring log

Author: a fresh Claude agent (Claude Opus 5.5) that has not seen the benchmark questions, answers or
documents. Layers are **AI-authored, not human-certified**.

- Start: Wed Sep 23 10:46:07 CDT 2026
- End: Wed Sep 23 11:05:58 CDT 2026 (about 20 minutes)
- DQL CLI used: `…/scratchpad/phase3/apps/cli/dist/index.js` (the build named in the task)

## Files read outside the working folder

- `spider2/layers/AUTHORING.md` (the rules).
- Insurance format examples: `insurance/layers/L1/domains/insurance/domain.dql`,
  `insurance/layers/L1/domains/insurance/modeling/areas/claims.dql.yaml` (first 150 lines),
  `insurance/layers/L1/domains/insurance/modeling/concepts.dql.yaml` (first 40 lines),
  `insurance/layers/L3/skills/insurance-claims-reserves-payments.skill.md` (first 80 lines);
  file listing of `insurance/layers/L1` and `insurance/layers/L3`.
- Insurance native-metric examples: listing of `work/insurance/projects/W2/semantic-layer/`,
  `metrics/policy_amount/total_policy_amount.yaml`, `cubes/uncategorized/claim.yaml` (first 60 lines).
- DQL source/docs (to learn formats and the validation proof), all under
  `…/scratchpad/phase3/`: `packages/dql-core/src/manifest/dbt-first-modeling.ts` (entity and
  relationship parsing, certification and proof rules), `apps/cli/src/commands/model.ts`,
  `apps/cli/src/warehouse-model-discovery.ts` (excerpt), `apps/cli/src/local-runtime.ts`
  (excerpts: the `/api/modeling/dbt-first/relationships/validate` route and
  `validateModelingRelationship`), `packages/dql-agent/src/relationship-validation.ts`,
  `packages/dql-connectors/src/optional-dependency.ts`,
  `packages/dql-core/src/semantic/{semantic-layer.ts (excerpts), yaml-loader.node.ts,
  providers/dql-provider.ts}`, `apps/cli/src/commands/semantic.ts` (excerpt),
  `packages/dql-agent/src/skills/loader.ts` (grep), `packages/dql-agent/src/skills/defaults.ts`
  (grep), `docs/reference/semantic-layer.md`, `docs/tutorials/04-agentic-analytics.md` (grep).

No file under `data/`, no other `spider2/` file, nothing under `work/spider2/runs/` or
`work/spider2/projects/`, no `*spider2-lite*.jsonl`, no `*gold*` file and no `*.sql` outside the
working folder was opened.

## Queries run (read-only, `sqlite3 -readonly` on `f1.sqlite`)

About 345 queries (310 through a logging wrapper in the session scratchpad, plus about 35 initial schema and row-count queries). Summary:

1. Schema: `sqlite_master` (30 tables, no views; PKs from the DDL), row counts of every table.
2. Samples and fill rates of every table; `typeof` of loosely typed `_ext`/derived columns.
3. Key uniqueness: single and composite candidates for every table (e.g. races year+round;
   results race+driver is NOT unique, race+driver+position_order is; lap_positions needs
   race+driver+lap+lap_type+position; drives needs year+driver+constructor+first_round;
   overtakes needs race+both drivers+lap+overtake_desc; liveries constructor_ref+start_year).
4. `_ext` tables vs base tables column by column (drivers_ext only fills `code`;
   driver_standings_ext adds 417 rows with id 0; lap_times_ext running_milliseconds = running
   sum on all rows; circuits_ext number_of_races counts scheduled races; races_ext flags checked
   against pit_stops/sprint_results; short_name = COALESCE(lookup, name) on all rows).
5. Codes: `position_text` codes vs status, status list and usage, retirement_type vs status,
   lap_type vs grid/qualifying, overtake types vs pit_stops/retirements, constructor_results
   status, standings position_text codes.
6. Semantics: standings are cumulative (points incl. sprint = race + sprint sums in 2023; wins =
   count of position 1 on every final table; dropped-score differences 1950-1990),
   constructor_results vs results (+ sprint) by era, winner points by era, max_points, sprint
   points, half/double points, lap_time_stats mean and population stdev, time-text to ms
   conversion, pit stop durations and red-flag stops, data coverage per table.
7. Hypothesis tests for team_driver_rank (points, races, first round, car number): none
   reproduces it (best 2,062 of 3,530), so it is described as supplied data.
8. Relationship checks: key coverage and cardinality for every relationship, then DQL's own
   validation statement (below).

## How relationship evidence was produced

`dql model apply-discovery --validate` had already written evidence for its drafts. For the
relationships I wrote (new keys, composite keys), I ran DQL's own validator — the same
`validateRelationshipOnWarehouse` + `catalogKeyTypes` call the Modeling page's Validate action
uses (`validateModelingRelationship`) — from a small script
(`scratchpad/validate-rels.mjs`) against the project's sqlite connection, for all 60
relationships, and wrote the returned evidence unchanged into the YAML
(`scratchpad/apply-evidence.py`). `dql model validate .` then reports valid with 0 diagnostics
(no stale or mismatched proofs) and `dql model explain` shows "automatic join allowed" for the
certified relationships.

## Decisions

### Draft model reviewed and replaced

The draft had one file (`domains/f1/modeling/model.dql.yaml`, 30 entities, 79 relationships).
I replaced it with five area files (calendar_and_participants, race_results,
championship_standings, laps_and_pit_stops, drives_and_teammates) and rewrote `domain.dql`.
Changes to the draft:

- Grains corrected/added: drivers_ext (driver_id, not driver_ref), driver_standings_ext
  (race_id+driver_id; driver_standings_id repeats as 0), retirements (race_id+driver_id+
  position_order), lap_positions (race_id+driver_id+lap+lap_type+position), drives
  (year+driver_id+constructor_id+first_round), overtakes (race_id+overtaking+overtaken+lap+
  overtake_desc), lap_time_stats (race_id+driver_id), lap_times_ext, team_driver_ranks
  (year+constructor_id+driver_id), liveries (constructor_ref+start_year; the declared PK includes
  a nullable end_year). Entity `statu` renamed `status`.
- Removed wrong draft relationships: `sprint_result_to_result` on result_id (sprint result_id is
  its own 1-300 sequence; the values only coincidentally exist in results),
  `driver_standings_ext_to_driver_standing` on driver_standings_id (0 for the 417 added rows).
- Removed redundant draft paths: every fact → constructors_ext / circuits_ext join, the by_name,
  by_url and by_ref duplicates of the one-to-one _ext links, race_to_circuits_ext,
  team_driver_rank/tdr_override joins by ref to constructors/drivers, races_ext → season/circuit.
  Facts join the base dimension; each _ext table joins its base table once.
- Added: overtake → driver twice (overtaking and overtaken roles), result → qualifying,
  retirement → result, lap_time → lap_time_stat, lap_times_ext → lap_time, lap_position →
  lap_time, pit_stop → lap_time, driver_standings_ext → driver_standing (race+driver),
  constructor_result → constructor_standing, tdr_override → team_driver_rank, sprint_result →
  result (race+driver).

### Certified (56): keys match, declared cardinality holds on the whole table, rows join

All many_to_one links from facts to race, driver, constructor, status and season; the four
one-to-one _ext → base links (circuits, constructors, drivers, races); short_constructor_name → constructor; retirement → result (3 keys, 11,568
of 11,568); lap_times_ext → lap_time (3 keys, 575,029 of 575,029); lap_time → lap_time_stat;
tdr_override → team_driver_rank (48 of 48, values equal); overtake → driver (both roles).
Certified with unmatched rows explained by design (recorded in each description):
drive → constructor (163 gap rows with constructor_id -1), driver_standings_ext →
driver_standing (417 added rows), result → qualifying (optional: no qualifying before 1994;
all 10,254 qualifying rows join), constructor_result → constructor_standing (optional both
sides, 1:1 where matched), pit_stop → lap_time (45 stops of the 2024 British GP have no lap times).
Each description carries the counts; each has `certifiedAgainst` and DQL's passed validation.

### Draft (4), with reasons

- `sprint_result_to_result` (race_id+driver_id): all 300 sprint rows match exactly one result,
  but results can hold up to 3 rows per race+driver (1950s shared drives), so DQL's whole-table
  many_to_one check fails (evidence status failed, recorded).
- `lap_position_to_lap_time`: only the `lap_type = 'Race'` rows correspond; 38,071 rows have no
  lap time and 12 retirement rows fall on a timed lap.
- `livery_to_constructor`: 3 of 64 rows use "benneton", which is not a constructor_ref.
- `races_ext_to_short_grand_prix_name`: lookup covers 1,033 of 1,125 races; races_ext.short_name
  already applies it with a fallback.

Entities are left without a status (draft by default): grains and keys were checked on the data
but no person has certified them.

### L3

- Skills (5 new): `f1-calendar-and-coverage`, `f1-results-and-status`,
  `f1-points-and-standings`, `f1-laps-pit-stops-overtakes`, `f1-drivers-constructors-teams`.
  Every rule in them was checked with a query (codes, eras, counts, formats, exceptions).
  `metrics-glossary` (starter) rewritten to list the metrics. The other starter skills
  (`block-authoring`, `domain-rules`, `sql-conventions`) are unchanged DQL starters.
- Native metrics (5, `semantic-layer/metrics/f1.yaml`): `race_entries` (COUNT results),
  `race_points` (SUM results.points), `sprint_points` (SUM sprint_results.points),
  `pit_stop_count` (COUNT pit_stops), `timed_laps` (COUNT lap_times). Wins, podiums, poles, DNFs,
  championship points and average pit time were not made metrics: each needs a filter or rule
  choice the data does not settle (lapped finishers, qualifying vs grid pole, red-flag stops,
  dropped scores). `dql semantic validate` passes; `dql semantic query race_points` composes.
- No blocks written.

## DQL defects / limitations hit

1. Warehouse discovery proposes joins on same-named columns that are not foreign keys and its
   validation marks them passed: `sprint_results.result_id → results.result_id` (separate
   sequences whose values happen to exist on both sides) and
   `driver_standings_ext.driver_standings_id → driver_standings` (417 rows with sentinel 0, shown
   as passed with 417 unmatched). `dql model discover` still re-proposes both after review.
2. Validation passes `many_to_one` regardless of how many from rows are unmatched; coverage is
   only visible in the numbers, so the author must read `unmatched_from`.
3. Cardinality is only provable over the whole table: a join that is unique within a subset
   (sprint era) cannot be certified.
4. There is no CLI command to validate an authored relationship; evidence for new relationships
   needed the Modeling page (notebook server) or a script calling DQL's validator directly. The
   script also had to pass `moduleSearchPaths` for the sqlite driver package.
5. Entity `status: reviewed` is silently read as draft (only evaluated/certified/deprecated are
   recognised); I left entity status unset.

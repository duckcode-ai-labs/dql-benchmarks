# Layer B authoring log

- Author: layer-B author agent (Claude), following `insurance/layers/AUTHORING-B.md`.
- Start: **2026-09-23 18:23 CDT**. Business brief finished: **18:36 CDT** (before any metric,
  skill or block was written).
- **Interruption:** work stopped on a usage limit at about 19:00 CDT, right after the first
  both-arm block runs; resumed 19:58 CDT at "rebuild LB and WB and test". No files were changed
  in between.
- End: **2026-09-23 20:05 CDT**. Active time about 1 h 40 min (elapsed 1 h 42 min including the
  pause).
- Nothing is certified by the author: every block is `status = "draft"`; relationship
  certifications are the prior L1 author's, re-proven by DQL (see Decisions).

## Files read outside the working folder

- `insurance/layers/AUTHORING-B.md` (rules), `insurance/build.mjs` (how B is assembled; it
  imports `insurance/questions.mjs`, which was **not** opened).
- DQL worktree (`.claude/worktrees/dql-agentic-query-construction-d182f3`), docs and source only:
  `docs/guides/authoring-blocks.md`, `docs/reference/file-formats.md`, `docs/reference/cli.md`,
  `docs/reference/semantic-layer.md`, `docs/reference/project-layout.md`;
  `packages/dql-core/src/blocks/semantic.ts`, `packages/dql-core/src/semantic/semantic-layer.ts`
  (composeQuery, resolveComposableMetric, qualifyBareSqlIdentifiers, keyword list),
  `packages/dql-core/src/semantic/providers/dbt-provider.ts` (entity->join, metric and ratio
  conversion), `packages/dql-core/src/manifest/dbt-first-modeling.ts` (modeling schema,
  certification checks), `packages/dql-notebook/src/execute.ts`, `apps/cli/src/commands/new.ts`,
  `commands/certify.ts`, `commands/semantic.ts`, `commands/notebook.ts` (flags only),
  `apps/cli/src/semantic-import.ts` (function list), `semantic-runtime.ts` (header),
  `metricflow.ts` (CLI resolution/args), `local-runtime.ts` (route list, Block Studio run route,
  `runBlockStudioPreviewSource`, `extractBlockStudioSql`). No test, fixture, golden or cassette
  file was opened.
- MetricFlow's installed package (`~/.local/share/uv/tools/dbt-metricflow/...`): versions and
  the `MAX_JOIN_HOPS` constant only (grep).
- Build outputs `work/insurance/projects/LB` and `WB` (config, semantic-layer YAML of the import,
  block/skill listings).
- **Accidental read to record:** two of my own command outputs were too large and the tool saved
  them under `~/.claude/projects/.../tool-results/` (a dump of `prior-layers/` and of
  `build.mjs`); I read the first one back from there before noticing the location. Its content
  is only working-folder text (prior L1/L3). After that I read files at their source paths.
  Nothing else under `~/.claude/`, no `data/`, `spider2/`, `private/`, other `work/` folders,
  other projects (L0-W4), question/gold/benchmark/report files or `duckcode-private` was read.

## Queries run against the warehouse (read-only, `work/insurance/authoring-b/project/acme_insurance.duckdb`)

1. Table list with row counts for all 29 views in `main` (and the seed schema).
2. Full dump of every small table with all-NULL columns identified (policy, agreement, roles,
   coverage details, policy amounts, premium, claims, claim amounts and the four subtype
   tables, catastrophe, occurrences, locations, assessments, organizations).
3. Person names, party/person/organization key coverage (party 100 is the organization, 1-29
   persons, only 1-3 named); fire_claim profile (820 rows; policy/claim/premium/location
   columns empty; loss ratio by fireplace).
4. Tests of the FROM-first membership subquery (`x in (from "main"."loss_payment")`) against
   plain joins: identical sums (3,500 / 3,100 / 3,700 / 3,300; premium 98,000).
5. Subtype overlap (no claim amount in two subtype tables); claim -> claim_coverage ->
   coverage detail -> policy vs the claim's insured object (found the claim 12312702 conflict);
   uniqueness of Policy_Coverage_Detail_Identifier (6/6); coverage periods within policy terms;
   policy_amount.Policy_Identifier agrees with its coverage detail's policy (0 mismatches);
   premium membership vs Amount_Type_Code (6 'Year' premiums, 6 NULL non-premiums).
6. Hand-written check SQL for every metric (table below).

## Checks run

| Check | Result |
| --- | --- |
| `node insurance/build.mjs --layer LB` | pass (seeds 29/29, models 29/29, `dql model validate` valid: 29 entities, 36 relationships) |
| `dbt parse` in LB | pass; `target/semantic_manifest.json` holds 12 semantic models, 37 metrics |
| `dql semantic list . --format json` in LB | provider dbt, 39 entries (37 metrics + 2 filtered-metric base measures), 34 dimensions |
| `node insurance/build.mjs --layer WB` | pass; all 31 validated relationships re-validated `passed` on warehouse tables; `dql semantic import` ok; 39 metrics, 34 dimensions; `dql model validate` valid |
| Each block run in both arms (Block Studio run route `POST /api/block-studio/run` on `dql notebook` servers at ports 3641 LB / 3642 WB) | 9/9 blocks run in LB and 9/9 in WB with identical rows; `dql parse` ok for all 9 |
| Every metric vs hand-written SQL, both arms | 30/30 simple metrics equal in LB, WB and hand SQL; 7 ratio metrics fail to run in both arms (see defects) and were checked by hand SQL only |

### Metric values (hand SQL = LB = WB unless noted)

| Metric | Value | Metric | Value |
| --- | --- | --- | --- |
| written_premium | 98,000 | losses_paid | 3,500 |
| monthly_premium | 8,166.67 | loss_reserves | 3,100 |
| premium_records | 6 | expenses_paid | 3,700 |
| other_policy_amount | 5,600,000 | expense_reserves | 3,300 |
| policies | 2 | incurred_losses | 6,600 |
| coverage_periods | 6 | incurred_expenses | 7,000 |
| policies_with_premium | 2 | total_paid | 7,200 |
| coverage_periods_with_premium | 6 | total_reserves | 6,400 |
| policies_sold / policies_held | 2 / 2 | incurred_loss_and_expense | 13,600 |
| agents / policy_holders | 1 / 1 | claims / claims_with_amounts | 2 / 2 |
| underwriting_assessments | 2 | closed_claims / open_claims | 2 / 0 |
| avg_assessment_days | 35 | avg_days_to_close | 20.5 |
| fire_risk_records | 820 | fire_sample_avg_loss_ratio | 0.642927 |
| claim_severity (hand only) | 3,300 | loss_ratio (hand only) | 0.0673469 |
| avg_premium_per_policy (hand only) | 49,000 | loss_and_lae_ratio (hand only) | 0.138776 |
| avg_premium_per_coverage_period (hand only) | 16,333.33 | paid_loss_ratio (hand only) | 0.0357143 |
| claim_frequency (hand only) | 0.333333 | | |

Sliced spot checks (both arms equal and correct): policies_sold/held by person name (Bob Agent
2/0, Mary Holder 0/2); incurred_losses by claim amount kind (3,500 + 3,100); claims and days to
close by status; losses_paid by date of loss (1,200 on 2019-01-14, 2,300 on 2019-06-01);
written_premium vs other amount by policy amount kind; underwriting assessments by begin date.

## Decisions

- **Semantic models sit directly on `models/omg_models`** (no new dbt models): the WB warehouse
  is built from dbt Labs' project alone, so a B-only dbt model would not exist there.
- **Amount kinds by subtype membership**, written as `case when <id> in (from "main"."<subtype>")
  then amount end`. Joins to the subtype tables cannot be used: DQL's native engine refuses a
  metric filter on a joined table, and MetricFlow cannot filter a measure by another model's
  rows. The FROM-first form has no SELECT/WHERE keyword and quoted names, so the native
  compiler's identifier qualifier leaves the subquery intact (verified in multi-table SQL).
- **Simple metrics carry the measure's name**, so DQL's ratio import can find them; same-model
  ratios (severity, average premium) use same-model measures. Cross-fact ratios (loss ratios,
  frequency) are defined as MetricFlow ratio metrics and also delivered as SQL blocks.
- **Coverage-detail entity key** is Policy_Coverage_Detail_Identifier alone (unique in the data,
  6/6) because DQL's native join builder prefixes the key expression with the table alias and
  breaks on a composite expression. Modeling relationships keep the full two-column key.
- Claims are attributed to policies through `claim_coverage` (ontology "against"/`hasClaim`);
  the claim 12312702 insured-object conflict is stated in the brief, skills, modeling and the
  Claims Register / loss-ratio blocks. Not repaired, because the data does not say which record
  is wrong.
- **Modeling:** started from L1. All 31 certified relationships kept (their proofs pass in LB
  and DQL re-proved all 31 on the warehouse in WB). Kept draft: `policy_to_agreement` (proven in
  the data but the agreement key column is mislabeled `Agreement_Type_Code` in the dbt model),
  and four DDL foreign keys whose columns are empty in every row (policy / policy_amount ->
  geographic_location, policy_amount -> insurable_object, occurrence -> geographic_location).
  Added descriptions: claim has no policy column; claim_coverage cardinality and the conflict;
  governed metrics per entity; domain description. No relationship was newly certified.
- **Skills:** L3's five skills kept and extended (governed metric names and values, the conflict,
  earned = written premium, report lag, severity/frequency, supported/unsupported KPI list);
  new `metrics-glossary.skill.md` replaces DQL's starter glossary with the KPI -> metric ->
  dimension -> block map and the rule to compute ratios from their parts when a ratio metric
  cannot run.
- **Blocks (9, all draft, tagged `ai-authored`, `review-required`):** 4 semantic (premium by
  policy and year, claim financials by claim, claims and losses by catastrophe, fire sample by
  fireplace) and 5 SQL (loss ratio summary, loss ratio by policy and coverage year, book by agent
  and holder, claims register, underwriting activity). SQL blocks use `main.<table>`, valid in
  both arms, aggregate each fact before joining.
- **KPIs not supported by the data:** earned premium at a past date (no earning dates; all
  periods expired so earned = written today), coverage limit / total insured value (non-premium
  amount unlabeled; exposed only as `other_policy_amount`), expense and combined ratio (no
  underwriting expenses or commissions), retention/renewal/cancellation, IBNR, recoveries,
  quote/hit ratios, product/line of business, demographics.

## DQL defects and format limitations found

1. **Ratio metrics never run on DQL's native engine**, even when numerator and denominator are
   on one model: the import writes the ratio SQL but no `table`, and `resolveComposableMetric`
   refuses non-simple metrics without a table. `governedRatioExpression` also looks the
   numerator/denominator up as *measure* names, though MetricFlow ratios name *metrics*.
2. **MetricFlow in this environment cannot compile**: the `mf` on PATH (dbt-metricflow 0.14 /
   metricflow 0.212) has no `dbt-duckdb` adapter, so every non-native metric fails in LB with
   "missing adapter package". All 7 ratio metrics are therefore unrunnable in both arms.
3. In WB (no dbt) the failure message for a ratio metric says "dbt semantic execution requires
   target/semantic_manifest.json" - misleading in a project that has no dbt.
4. **`// dql-format: 1` header breaks semantic blocks** in Block Studio run:
   `extractBlockStudioSql` guards blocks with `/^\s*block\s+"/`, which fails when the file starts
   with the version header, so the keyword scan reads prose; a description containing "with"
   (or select/show/update/...) is sent to DuckDB as SQL ("syntax error at or near book").
   Worked around: semantic blocks have no header and no SQL keywords in their prose.
5. A semantic model's `primary_entity:` (model-level) is ignored by the import; dimensions are
   qualified with the model name instead. Worked around by naming those models after their
   primary entity.
6. Native entity joins are `${left}.<expr> = ${right}.<expr>`: any entity `expr` that is not a
   bare column (composite key, cast) produces invalid SQL.
7. Metric filters on a dimension of a joined model are refused by the native composer
   (documented in source); subtype membership cannot be expressed as a filter.
8. Semantic block `order_by` is not applied in the Block Studio run output (rows come back
   unordered).
9. MetricFlow's two-hop join limit keeps claim money from reaching policy, agent or holder
   through the claim_coverage bridge; those cuts are SQL blocks.

## Fixes after verification (2026-09-23, 20:08-20:25 CDT)

The verifier's report (`VERIFICATION.md`, not edited) failed sign-off on D1. All ten defects
were fixed; files read for this round: `VERIFICATION.md` only (plus my own files and the
rebuilt LB/WB projects).

| # | Fix |
| --- | --- |
| D1 (blocking) | Removed every literal result from DQL-visible files: the "Book value" column and ratio values of `metrics-glossary`; book totals and per-claim amounts (claims skill); per-year premiums and the book total (premium skill); addresses and zips (locations skill); agent, holder, underwriter names and party ids, the insurer's name (policies skill); fire-sample counts and averages (data-coverage skill); claim/policy/coverage ids in the conflict notes of the claims skill, the claims modeling area and the Claims Register / Loss Ratio by Policy blocks (now "one claim's claim_coverage row names a different policy than the policy insuring the claim's damaged object"); catastrophe names, the result code, city/state, row counts, value ranges, person ids and the insurer's name in modeling and dbt descriptions; example policy/claim numbers and the unlabeled amounts' values in dbt descriptions; the date range in the time-spine description and comment. Definitions, grains, join paths, empty/coded-column facts and the conflict rule stay. The check values now live only in this log. |
| D2 | `claim_amounts.amount_event_date` = `cast(Event_Date as date)`, `policy_party_role.role_effective_date` = `cast(Effective_Date as date)`. MetricFlow `incurred_losses, loss_ratio` and `policies_sold, agents` by `metric_time__year` now run (claim money and role metrics fall in the empty-date bucket, as documented). |
| D3 | Catastrophe block uses `claims_with_amounts` (same model as the money metrics) and `claim__catastrophe__catastrophe_name`; runs in MetricFlow (LB) and native (WB): Fire 2 / 6,600 / 13,600. Glossary lists both spellings for catastrophe and date of loss. |
| D4 | Policies skill: the insurer's short name is in `Alternate_Name`; `Acronym_Name` is empty (no name written). |
| D5 | `monthly_premium` metric/measure descriptions, premium skill and glossary: a monthly equivalent per coverage period; a sum over periods is not a monthly amount. |
| D6 | `claims` metric input has `fill_nulls_with: 0`; MF `claim_frequency` by `metric_time__year` = 0 for years with exposure and no claims, 1.0 for 2019. |
| D7 | Correction to "DQL defects" item 2 above: the ratio failures in LB came from the `mf` on PATH (no DuckDB adapter). With `DQL_METRICFLOW_BIN=.venv-mf/bin/mf` all 7 ratio metrics run in LB and equal hand SQL (claim_severity 3,300; avg_premium_per_policy 49,000; avg_premium_per_coverage_period 16,333.3; claim_frequency 0.333333; loss_ratio 0.0673469; loss_and_lae_ratio 0.138776; paid_loss_ratio 0.0357143). Whether they run in LB depends on which `mf` the runtime resolves. In WB they still cannot run (native engine limitation, defect 1). |
| D8 | Claim dimension renamed `damaged_object_id`, label "Damaged object (claim record)"; coverage dimension labeled "Insured object (coverage)"; both descriptions and the glossary say losses by object and premium by object are different scopes and there is no governed loss ratio by object. |
| D9 | The unfiltered role measures were removed. `policies_sold`, `policies_held`, `agents`, `policy_holders` are now simple metrics on role-specific measures (`count distinct case when Party_Role_Code = 'AG'/'PH' ...`), no metric filters; `dql semantic list` shows 37 metrics in LB and WB (was 39). |
| D10 | Book of Business block: never sum or average `loss_ratio`; recompute from summed incurred losses / summed premium. Same warning in the Loss Ratio by Policy block and the glossary. |
| extra | Semantic blocks use `chart = "table"`: MetricFlow (LB) returns dunder column names (`policy__policy_number`) while the native engine returns short names (`policy_number`), so a fixed x/y binding cannot be right in both arms (new DQL finding 10). |

Checks re-run after the fixes:
- `node insurance/build.mjs --layer LB` and `--layer WB`: pass; `dql model validate` valid in both (29 entities, 36 relationships); WB re-validated all 31 certified relationships `passed`.
- `dbt parse` in LB: pass; `semantic_manifest.json` 12 semantic models, 37 metrics. `dql semantic list`: 37 metrics, 35 dimensions in LB and WB.
- MetricFlow (`.venv-mf/bin/mf query`, on a copy of LB): all 37 metrics in one query equal the hand-SQL table above.
- Block Studio run route, LB server started with `DQL_METRICFLOW_BIN=.venv-mf/bin/mf`, WB native: 9/9 blocks run in each arm with the same values; `dql parse` clean for all 9 in both projects.
- Metric vs hand SQL through the DQL runtime: LB 37/37 equal; WB 30/30 simple metrics equal, 7 ratios refused by the native engine.
- D1 grep over every file in `B/dbt` and `B/dql` for digits, names, addresses, zips, ids and catastrophe/result values: no literal results remain. Remaining digits are formula constants (`/ 12`), SQL literals (`COALESCE(x, 0)`, `then 1 else 0`, the time-spine date range in code), column names (`Line_1_Address`), "1 January", and the DQL-generated `validation:` evidence on certified relationships (row counts and fingerprints that DQL writes and requires for certification; WB rewrites them on every build).
- The last change (time-spine SQL comment) was copied into the built LB project and `dbt parse` re-run; it does not affect the semantic manifest or WB.

New DQL finding 10: semantic block result columns are named differently by the two engines
(MetricFlow keeps `entity__dimension`, native uses the bare dimension name, and the time
dimension is `x__year` vs `x_year`), so charts and downstream references bound to a column
name break when a block moves between LB and WB.

End of fix round: 2026-09-23 20:25 CDT.

## v2 (2026-09-23, 22:08-22:16 CDT)

Requested after the v1 pilot: (1) claim money must reach policy, agent and policy holder within
MetricFlow's two-hop limit; (2) role metrics must count only parties with the role. No other
changes. Files read: only my own files, DQL source in the phase4 CLI tree
(`packages/dql-core/src/semantic/semantic-layer.ts`, `yaml-loader.ts`: filter handling) and the
rebuilt LB/WB projects.

Changes:
- New dbt model `dbt/models/business_semantics/claim_policy.sql` (+ `claim_policy.yml`): one row
  per claim with the policy it is made against (claim_coverage -> policy_coverage_detail on both
  keys -> policy), the policy number, and the policy's agent and holder (roles pivoted to one
  per policy before joining; dbt tests unique/not_null on Claim_Identifier). New semantic model
  `claim_policies` (primary entity `claim_policy`, foreign `policy`; dimensions policy_number,
  policy_id, agent_name, agent_party_id, policy_holder_name, policy_holder_party_id,
  coverage_start_date). `claim_amounts` and `insurance_claims` got a foreign entity
  `claim_policy` (Claim_Identifier), so policy, agent and holder are one join away
  (`claim_policy__policy__*` for other policy attributes is two). No measure moved; every
  existing metric is unchanged.
- Role metrics `policies_sold`, `policies_held`, `agents`, `policy_holders` have their role
  filter again (`policy_party_role__party_role_code = 'AG'/'PH'`), so rows of other roles are
  removed before grouping. Their measures are renamed `*_measure` (still role-specific CASE
  expressions): with the measure named like the metric, DQL's native loader let the measure
  entry (measures/ folder) replace the metric and the metric's filter was lost, so WB returned
  zero rows for non-holders. The 4 measures are now listed by `dql semantic list` (41 entries;
  37 metrics) and described as building blocks of their metric.
- Skills: glossary section "Claims and claim money by policy, agent and policy holder" lists the
  new dimensions and the role-metric population rule; policies skill points to them. No values.

Checks (hand SQL for the new cuts: claim money joined through claim_coverage ->
policy_coverage_detail -> policy and the pivoted roles):

| Check | Hand SQL | MetricFlow (`.venv-mf/bin/mf`, LB) | DQL runtime LB | DQL runtime WB |
| --- | --- | --- | --- | --- |
| losses_paid, incurred_loss_and_expense by policy (`claim_policy__policy`, `claim_policy__policy_number`) | policy ...336: 3,500 / 13,600 | same | same (+ claims 2) | fails: table `main.claim_policy` does not exist |
| incurred_losses, claims by agent (`claim_policy__agent_name`) | Bob Agent 6,600 / 2 | same | same | fails (same reason) |
| loss_reserves, expenses_paid by holder (`claim_policy__policy_holder_name`) | Mary Holder 3,100 / 3,700 | same | same | fails (same reason) |
| policies_held by person | Mary Holder 2 only | same | same | same (WHERE applied) |
| policies_sold by person | Bob Agent 2 only | same | same | same |
| agents / policy_holders by person | Bob Agent 1 / Mary Holder 1 only | same | same | same |
| all 37 metrics at book level | table in section "Metric values" | 37/37 equal | 37/37 equal | 30/30 simple equal; 7 ratios refused (native limitation, unchanged) |
| 9 blocks | - | - | 9/9 run | 9/9 run |

Builds: LB and WB build; `dbt parse` passes (13 semantic models, 37 metrics); `dql model
validate` valid in both (29 entities, 36 relationships). D1 grep over `B/dbt` and `B/dql`: no
names, addresses, ids or results (only hex validation fingerprints match the patterns).

Open issue for the harness (not fixable inside B): the WB warehouse is built from dbt Labs'
project only (`copyProject('L0', warehouse-source)`), so B's dbt model `claim_policy` does not
exist there. In WB the imported `claim_policies` semantic model points at a missing table:
book-level and all other cuts are unaffected, but any cut by `claim_policy__*` fails at query
time. Building the WB warehouse with B's dbt models (as a team without dbt at query time would
still have the tables its transformation job built) makes WB match LB.

Two more DQL findings: (11) a measure with the same name as a filtered metric replaces the
metric in the native loader and silently drops the metric's filter; (12) when two role metrics
with different filters are queried together, the native engine returns 0 for the other role
(per-metric CASE) while MetricFlow returns empty; values for role holders agree.

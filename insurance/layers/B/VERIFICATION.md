# Layer B verification

- Verifier: independent verifier agent (Claude), not the author. Date: 2026-09-23.
- Scope: `BUSINESS-BRIEF.md`, `AUTHORING-LOG.md`, `dbt/models/business_semantics/*` (12 semantic
  models, 37 metrics), `dql/` (domain, 29 entities, 35 area relationships + 10 concept
  equivalences, 6 skills, 9 blocks), checked against the warehouse and the built arms LB and WB.
- Method: every value below comes from **my own hand SQL** on a read-only copy of
  `work/insurance/projects/LB/acme_insurance.duckdb` (and a copy of WB's), compared with
  (a) MetricFlow in LB (`.venv-mf/bin/mf query`) and (b) DQL's native composer
  (`dql semantic query`) in LB and WB, whose composed SQL I executed on the copies. SQL blocks
  were executed from their `query` text; semantic blocks were reproduced with the same metrics
  and dimensions through both engines. I did not start a notebook server (so the Block Studio run
  route itself was not re-run by me).

## Reads outside the work under review (for the record)

- Read: `insurance/layers/AUTHORING-B.md`, everything in `insurance/layers/B/`, the working
  folder (`docs/`, `prior-layers/L1`, `prior-layers/L3`), the LB/WB projects (config, starter
  skills, semantic manifest, modeling), `insurance/build.mjs` (grep only), DQL CLI source
  `apps/cli/src/commands/semantic.ts` and `apps/cli/src/semantic-runtime.ts` (adapter selection).
- Two incidents, no question/answer content seen:
  1. One of my command outputs (a `cat` of B's dbt YAML) was large and the tool saved it under
     `~/.claude/projects/.../tool-results/`. I did **not** open that file; I re-read the YAML at
     its source path.
  2. I ran `git -C work/insurance/projects/LB status --short` (read-only) while checking whether
     LB was a repo. It printed three path names of the dql-benchmarks repo
     (`insurance/baseline-text2sql.mjs`, `insurance/build.mjs`, `insurance/layers/AUTHORING-B.md`);
     no file content was read and nothing was changed.
- Nothing under `data/`, `spider2/`, `private/`, other `work/` folders, question/gold/benchmark/
  heldout/unanswerable/report files, or `duckcode-private` was opened.

## 1. Business brief

| Check | Result |
| --- | --- |
| KPI set is a sensible P&C carrier set (written/earned premium, exposure, paid/reserved/incurred loss and LAE, claim counts, severity, frequency, loss / loss+LAE / paid loss ratios, cycle time, report lag, book by agent/holder, underwriting activity) | PASS |
| Row counts and filled/empty columns in section 1 (every table profiled by me: 29 views, all-null columns listed per view) | PASS - every count and every "empty" claim matches |
| Earned premium: all coverage periods ended by 2020-05-31, so earned = written over the full periods; earned at a past date needs pro-rating | PASS |
| Coverage limit not supported: the non-premium amounts are `hasPolicyAmount` (not `Premium`) in the r2rml mapping, no type code | PASS |
| Expense/combined ratio, IBNR, retention, quote/hit, recoveries not supported | PASS - no such data |
| Claim -> policy via `claim_coverage`: grounded in the r2rml mapping (`claim_coverage` maps both `Claim against PolicyCoverageDetail` and `PolicyCoverageDetail hasClaim Claim`) | PASS |
| Data conflict (claim 12312702: claim_coverage -> coverage 5 / object 1 / policy 31003000336; `claim.Insurable_Object_Identifier` = 2, insured by policy 31003000337 coverage 6, which covers the 2019-06-01 loss date) | PASS - reproduced exactly |

## 2. Metrics (37) - book value: hand SQL vs MetricFlow (LB) vs native (WB)

All 37 ran in MetricFlow with the DuckDB adapter (`.venv-mf`), including the 7 ratio metrics.
Simple metrics were also composed natively in WB (ratio metrics cannot run natively - a DQL
limitation, see "Environment notes").

| Metric | Definition check (grain / kind) | Hand SQL | MF (LB) | Result |
| --- | --- | --- | --- | --- |
| written_premium | policy_amount rows in `premium` only | 98,000 | 98,000 | PASS |
| monthly_premium | premium with period `Year` / 12 | 8,166.67 | 8,166.67 | PASS (see D5) |
| premium_records | count of premium rows | 6 | 6 | PASS |
| other_policy_amount | policy_amount rows NOT in premium | 5,600,000 | 5,600,000 | PASS |
| policies | distinct policy | 2 | 2 | PASS |
| coverage_periods | distinct coverage detail | 6 | 6 | PASS |
| avg_premium_per_policy | premium / policies with premium | 49,000 | 49,000 | PASS |
| avg_premium_per_coverage_period | premium / coverage periods with premium | 16,333.33 | 16,333.3 | PASS |
| policies_sold | distinct policies with role AG | 2 | 2 | PASS |
| policies_held | distinct policies with role PH | 2 | 2 | PASS |
| agents | distinct AG parties | 1 | 1 | PASS |
| policy_holders | distinct PH parties | 1 | 1 | PASS |
| policies_with_premium | distinct policies with a premium row | 2 | 2 | PASS |
| coverage_periods_with_premium | distinct coverage details with a premium row | 6 | 6 | PASS |
| losses_paid | claim_amount in loss_payment | 3,500 | 3,500 | PASS |
| loss_reserves | in loss_reserve | 3,100 | 3,100 | PASS |
| expenses_paid | in expense_payment | 3,700 | 3,700 | PASS |
| expense_reserves | in expense_reserve | 3,300 | 3,300 | PASS |
| incurred_losses | LP + LR | 6,600 | 6,600 | PASS |
| incurred_expenses | EP + ER | 7,000 | 7,000 | PASS |
| total_paid | LP + EP | 7,200 | 7,200 | PASS |
| total_reserves | LR + ER | 6,400 | 6,400 | PASS |
| incurred_loss_and_expense | all four kinds (0 unclassified amounts; no amount in two subtype tables) | 13,600 | 13,600 | PASS |
| claims | distinct claim | 2 | 2 | PASS |
| closed_claims | close date filled | 2 | 2 | PASS |
| open_claims | close date empty | 0 | 0 | PASS |
| avg_days_to_close | mean(close - open) = (16 + 25) / 2 | 20.5 | 20.5 | PASS |
| claims_with_amounts | distinct claims on claim_amount | 2 | 2 | PASS |
| claim_severity | incurred losses / claims with amounts | 3,300 | 3,300 | PASS |
| claim_frequency | claims / coverage periods | 0.3333 | 0.333333 | PASS (see D6) |
| loss_ratio | 6,600 / 98,000 | 0.067347 | 0.0673469 | PASS |
| loss_and_lae_ratio | 13,600 / 98,000 | 0.138776 | 0.138776 | PASS |
| paid_loss_ratio | 3,500 / 98,000 | 0.035714 | 0.0357143 | PASS |
| underwriting_assessments | results listed in underwriting_assessment | 2 | 2 | PASS |
| avg_assessment_days | mean(end - begin) = (44 + 26) / 2 | 35 | 35 | PASS |
| fire_risk_records | rows of fire_claim | 820 | 820 | PASS |
| fire_sample_avg_loss_ratio | unweighted mean of Loss_Ratio | 0.642927 | 0.642927 | PASS |

Fan-out / grain: premium is on `policy_amount` (coverage-period grain, membership test on
`premium`); claim money on `claim_amount` (amount grain, subtype membership); claim counts on
`claim`; role metrics on `agreement_party_role` with a role filter. No measure sums across the
role bridge or the claim bridge. Native composer refuses the fan-out cuts
(`written_premium` by `person__full_name`, `incurred_losses` by `policy__policy_number`,
`claims + written_premium` by policy) instead of double counting; MetricFlow refuses them too.
When native combines two facts at book level (`incurred_losses, written_premium`) it aggregates
each separately (6,600 / 98,000).

### Group-by spot checks (all equal to my hand SQL)

| Metric(s) | Cut | Engine | Values | Result |
| --- | --- | --- | --- | --- |
| written_premium, monthly_premium, coverage_periods_with_premium | policy x coverage year | MF, native (WB) | 336: 15k/16k/17k/18k/20k (2015-19); 337: 12k (2019) | PASS |
| written_premium, other_policy_amount | policy | MF | 336: 86,000 / 5,000,000; 337: 12,000 / 600,000 | PASS |
| written_premium / other_policy_amount | policy amount kind | MF, native | Premium 98,000; Other 5,600,000 | PASS |
| written_premium | insured object (coverage) | MF, native | obj 1: 86,000; obj 2: 12,000 | PASS |
| coverage_periods | policy | MF, native | 5 / 1 | PASS |
| avg_premium_per_policy, per_coverage_period | policy | MF | 86,000 / 17,200; 12,000 / 12,000 | PASS |
| policies_sold, policies_held | person name | MF, native | Bob Agent 2/0; Mary Holder 0/2 | PASS |
| agents, policy_holders | party role | MF | Agent 1; Policy holder 1 | PASS |
| 7 claim-money metrics | claim number | MF, native (LB, WB) | 12312701: 1200/1000/1300/1100/2200/2400/4600; 12312702: 2300/2100/2400/2200/4400/4600/9000 | PASS |
| claims, incurred_losses, incurred_loss_and_expense, claim_severity | catastrophe | MF (see D3), native | Fire: 2 / 6,600 / 13,600 / 3,300 | PASS (numbers) |
| losses_paid, total_reserves | date of loss | MF, native | 2019-01-14: 1,200 / 2,100; 2019-06-01: 2,300 / 4,300 | PASS |
| loss_reserves, total_paid | claim's insured object | MF, native | obj 1: 1,000 / 2,500; obj 2: 2,100 / 4,700 | PASS (see D8) |
| incurred_losses | claim amount kind | MF, native | LP 3,500; LR 3,100; EP/ER empty | PASS |
| claims, closed_claims, avg_days_to_close | status | MF, native | Closed 2 / 2 / 20.5 | PASS |
| claims, avg_days_to_close | claim number / close month | MF, native | 16 and 25 days | PASS |
| claim_frequency | metric_time year | MF | 2019: 1.0 (2 claims / 2 periods); other years NULL | PASS (see D6) |
| underwriting_assessments, avg_assessment_days | assessment year | MF | 2014: 1 / 44; 2019: 1 / 26 | PASS |
| fire_risk_records, fire_sample_avg_loss_ratio | fireplace | MF, native | yes 692 / 0.6581; no 128 / 0.5609 | PASS |
| any claim-money metric, loss ratios, role metrics | metric_time | MF | runtime error | DEFECT D2 |

## 3. Relationships

Independent check per relationship on the warehouse: null FK count, unmatched FK rows, max rows
per key on the "to" side (must be 1), max per key on the "from" side (must be 1 for
one_to_one), joined rows = from rows. `dql model validate` on LB and WB: valid, 29 entities,
36 relationships, no diagnostics.

| Relationship | Status | Keys match / cardinality holds | Result |
| --- | --- | --- | --- |
| claim_coverage_to_claim | certified | 2/2 joined, to unique | PASS |
| claim_coverage_to_policy_coverage_detail (Effective_Date + id) | certified | 2/2 joined, to unique | PASS |
| claim_to_catastrophe | certified | 2/2, to unique | PASS |
| claim_to_occurrence | certified | 2/2, to unique | PASS |
| claim_to_insurable_object | certified | 2/2, to unique | PASS |
| claim_amount_to_claim | certified | 8/8, many-to-one (max 4) | PASS |
| loss_payment / loss_reserve / expense_payment / expense_reserve _is_claim_amount (4) | certified | 2/2 each, 1:1, no amount in two subtypes | PASS (4) |
| insurable_object_to_geographic_location | certified | 2/2 | PASS |
| geographic_location_to_location_address | certified | 8/8 | PASS |
| geographic_location_to_physical_location | certified | 8/8 | PASS |
| physical_location_to_location_address | certified | 8/8; the two address paths agree on all 8 rows (0 mismatches) | PASS |
| agreement_party_role_to_policy | certified | 4/4, many-to-one (2 roles per policy) | PASS |
| agreement_party_role_to_party | certified | 4/4 | PASS |
| agreement_party_role_to_party_role | certified | 4/4 | PASS |
| person_is_party | certified | 29/29, 1:1 | PASS |
| organization_is_party | certified | 1/1, 1:1 | PASS |
| policy_coverage_detail_to_policy | certified | 6/6 | PASS |
| policy_coverage_detail_to_insurable_object | certified | 6/6 | PASS |
| policy_amount_to_policy_coverage_detail (2-column key) | certified | 12/12 | PASS |
| policy_amount_to_policy | certified | 12/12 | PASS |
| premium_is_policy_amount | certified | 6/6, 1:1 | PASS |
| agreement_assessment_to_policy | certified | 2/2 | PASS |
| agreement_assessment_to_assessment | certified | 2/2 | PASS |
| assessment_result_to_assessment | certified | 2/2 | PASS |
| underwriting_assessment_is_assessment_result | certified | 2/2, 1:1 | PASS |
| assessment_party_role_to_assessment / _to_party / _to_party_role (3) | certified | 2/2 each | PASS (3) |
| policy_to_agreement | draft | holds in data (2/2, 1:1); reason given (agreement key column mislabeled `Agreement_Type_Code`) | PASS (draft with reason) |
| policy_to_geographic_location, policy_amount_to_geographic_location, policy_amount_to_insurable_object, occurrence_to_geographic_location | draft | FK empty in every row; reason given | PASS (4) |
| Concept equivalences (10: person/organization -> party, 5 subtypes, underwriting_assessment, premium certified; policy -> agreement draft) | as listed | all hold 1:1 | PASS |

Relationship statuses are unchanged from prior L1 (ids and statuses identical); B added
descriptions only. No relationship was newly certified by the author.

## 4. Skills (6)

Every factual statement was checked against my table profile. The "always empty" list in
`insurance-data-coverage` matches the all-null columns of every view exactly.

| Skill | Rules true in the data | Consistent with metrics / modeling | Answer-like content | Result |
| --- | --- | --- | --- | --- |
| insurance-claims-reserves-payments | yes (status by dates, subtype rule, empty columns, one claim_coverage row per claim, report lag, conflict) | yes | per-claim amounts for 12312701 / 12312702 and book totals | DEFECT D1 |
| insurance-coverage-and-premium | yes (premium subtype, `Year` period, earning dates empty, coverage codes empty) | yes | per-coverage-year premium of both policies, book total | DEFECT D1 |
| insurance-data-coverage | yes (all empty-column claims verified) | yes | fire sample 820 / 0.643 / 0.658 / 0.561 | DEFECT D1 |
| insurance-locations | yes (join path, Austin TX only, unattached locations, empty parent) | yes | each claim's street address and zip | DEFECT D1 |
| insurance-policies-and-parties | yes, except "acronym MUSIC" (D4) | yes | agent/holder/underwriter names and ids, "both policies have the same holder and agent" | DEFECT D1, D4 |
| metrics-glossary | definitions and metric names correct; `catastrophe__catastrophe_name` listed as a claim-money dimension (D3) | yes | book value of every metric and every ratio | DEFECT D1, D3 |

No skill contradicts a metric definition or the modeling. The definitions, rules and
join paths themselves are grounded and correct.

## 5. Blocks (9)

All nine: named in brief section 3, `status = "draft"`, tags `ai-authored`, `review-required`,
`dql parse` clean, no narrow filters or hard-coded ids in SQL.

| Block | Type | Check | Result |
| --- | --- | --- | --- |
| Written Premium by Policy and Coverage Year | semantic | same metrics/dims in MF and native: 6 rows as in section 2 | PASS |
| Claim Financials by Claim | semantic | MF, native LB, native WB: 2 rows as in section 2 | PASS |
| Claims and Losses by Catastrophe | semantic | native LB/WB: Fire 2 / 6,600 / 13,600 = hand SQL. In MetricFlow the same request fails (dimension name not common to `claims` and claim-amount metrics) | PASS (numbers), DEFECT D3 |
| Loss Ratio Summary | SQL | one row = my book values (98,000; 2; 6; 2; 3,500; 3,100; 3,700; 3,300; 6,600; 13,600; 0.06735; 0.13878; 0.03571; 0.3333) | PASS |
| Loss Ratio by Policy and Coverage Year | SQL | 6 rows; 336-2019: 20,000 premium, 2 claims, 6,600, 13,600, 0.33; other rows 0 claims; equals my SQL via claim_coverage | PASS |
| Book of Business by Agent and Policy Holder | SQL | 336: Bob Agent / Mary Holder, 5 periods, 86,000, 2 claims, 6,600, 13,600, 0.0767; 337: 1 period, 12,000, 0 claims. My independent agent roll-up: Bob Agent 98,000 / 2 / 6,600 / 0.0673 | PASS (see D10) |
| Claims Register | SQL | days to close 16 / 25, report lag 1 / 1, claim object 1 / 2 vs coverage object 1 / 1, addresses and all amounts equal my SQL | PASS |
| Underwriting Activity | SQL | 2 rows: policy 336 44 days, 337 26 days, Alice Writer (party 3), OK | PASS |
| Fire Risk Sample Loss Ratio by Fireplace | semantic | yes 692 / 0.6581, no 128 / 0.5609 in MF and native | PASS |

## 6. Leakage review

- **Metrics, blocks, modeling: no tailoring found.** The metric set is a textbook P&C set;
  `other_policy_amount` and `monthly_premium` are grounded in the ontology mapping (PolicyAmount,
  monthly premium amount). Blocks are generic reports with no filters on ids, names or dates.
  Relationship certifications are L1's, unchanged, and re-proved.
- **Claim 12312702 conflict: a data fact, not overfitting.** I reproduced it independently; the
  chosen rule (attribute via `claim_coverage`) follows the r2rml `against` / `hasClaim` mapping,
  the Claims Register shows both objects, and no number was adjusted to "fix" it. Naming the
  claim and policies is how a data team documents a known record-level data-quality issue.
- **Skills and descriptions carry literal results (D1).** B added (these are not in prior L3)
  the value of every KPI and ratio, per-claim amounts, per-coverage-year premiums, each claim's
  street address and zip, the names of agent, holder and underwriter, and the fire sample's
  averages by fireplace. The author did not see the questions, so this is not question fitting,
  but in effect it is an answer sheet inside the test arm: an agent can repeat these numbers
  without running a governed metric or block. It gives LB/WB an advantage no other arm has, and
  it creates a second, unversioned source of truth that goes stale when the data changes.

## 7. Defects

| # | Severity | Blocking | Defect | Evidence | Recommended fix |
| --- | --- | --- | --- | --- | --- |
| D1 | misleading (benchmark validity) | **yes** | Literal result values in the skills (and one entity description) act as precomputed answers | `metrics-glossary` "Book value" column and the ratio values; `insurance-claims-reserves-payments` "Book values ... claim 12312701 amounts 1,000 ..."; `insurance-coverage-and-premium` "98,000 ... 15,000 / 16,000 ..."; `insurance-locations` "Claim 12312701 is at 5315 Martin Ave (78751) ..."; `insurance-policies-and-parties` "`agents` (1: Bob Agent, party 2) ... Alice Writer (party 3)"; `insurance-data-coverage` "(0.643; 0.658 with a fireplace, 0.561 without)" | Remove the values; keep definitions, formulas, grain, join paths, empty-column facts and the conflict description (ids of the conflicting records may stay, results may not). Keep the hand-check values in `AUTHORING-LOG.md` / this file, which are not copied into the arms |
| D2 | misleading (query fails) | no | `claim_amounts.amount_event_date` (`Event_Date`) and `policy_party_role.role_effective_date` (`Effective_Date`) are INTEGER all-null columns declared as `time`: any MF query on metric_time with a claim-money metric (9), the 3 loss ratios, or the 4 role metrics raises a DuckDB binder error | `mf query --metrics incurred_losses --group-by metric_time__year` -> `date_trunc(STRING_LITERAL, INTEGER)`; same for `policies_sold` | Use `cast(Event_Date as date)` / `cast(Effective_Date as date)` (as done for the underwriting and fire models) and keep the "slice by claim dates, not metric_time" note |
| D3 | cosmetic (portability) | no | The catastrophe block and the glossary use `catastrophe__catastrophe_name` for claim-money metrics; MetricFlow only accepts `claim__catastrophe__catastrophe_name` for those, and none common with `claims`, so the block's request fails if it is ever routed to MF | MF error "does not match to a common item"; `claims_with_amounts, incurred_losses, incurred_loss_and_expense, claim_severity` by `claim__catastrophe__catastrophe_name` runs in MF and native with the same values (2 / 6,600 / 13,600 / 3,300) | Use `claims_with_amounts` and `claim__catastrophe__catastrophe_name` in the block; list both spellings in the glossary |
| D4 | cosmetic | no | "acronym MUSIC": `Acronym_Name` is empty; MUSIC is `Alternate_Name` | organizations row | Say "alternate name MUSIC" |
| D5 | cosmetic | no | Book-level `monthly_premium` (8,166.67) sums monthly equivalents across six policy-years 2015-2020; the glossary presents it as a book value | definition | State it is meaningful per coverage period (or per policy-year cut) only |
| D6 | cosmetic | no | `claim_frequency` by year shows NULL, not 0, for years with exposure and no claims | MF by metric_time__year: 2015-2018 empty | Add `fill_nulls_with: 0` to the `claims` measure/metric input, or document |
| D7 | cosmetic (log) | no | Log DQL defect 2 says all 7 ratio metrics are unrunnable in both arms; with the DuckDB-capable MF (`.venv-mf`) all 7 run in LB and match | section 2 | Say it depends on which `mf` the LB runtime resolves |
| D8 | cosmetic | no | Two dimensions labeled "Insured object ID" mean different things (claim's damaged object vs coverage's object) and disagree for 12312702, so loss by object and premium by object do not share a scope | section 2 cuts | Label them "Damaged object (claim record)" and "Insured object (coverage)"; note that loss ratio by object is not governed |
| D9 | cosmetic | no | The unfiltered base measures `policies_with_role_count` and `parties_with_role_count` are exposed as metrics (39 listed) and mix agents with holders | `dql semantic list` in LB/WB | Hide them or describe them as role-agnostic |
| D10 | cosmetic | no | Book of Business description says "sum the rows for agent or holder totals"; the `loss_ratio` column must not be summed | block description | Add "recompute the loss ratio from the summed losses and premium" |

Defects were not returned to the author inside this session; resolution is pending.

## Environment notes (not defects of B)

- DQL's native engine cannot run ratio metrics (the import writes no table for them), so in WB,
  and in LB whenever the runtime has no DuckDB-capable MetricFlow, the 7 ratios fail. B's skills
  handle this correctly: compute from the simple parts, or use the Loss Ratio blocks.
- `dql semantic query` and the blocks run B's simple metrics identically in LB and WB.

Sign-off: FAIL (1 blocking defect)

---

## Re-verification (2026-09-23, after the author's fix round 20:08-20:25 CDT)

Same verifier, rules and tools as above. Inputs: the author's "Fixes after verification" section
in `AUTHORING-LOG.md`, every file under `B/dbt` and `B/dql`, and the rebuilt LB and WB projects
(fresh read-only copies of both warehouses). I did not edit any B file; this section is
appended below the original report, which is unchanged.

### R1. D1 - literal results: independent scan

Method:
1. A numeric-token scan of every `.yml/.yaml/.sql/.dql/.md/.json` file in `B/dbt`, `B/dql`
   and the copies DQL reads (`LB/skills`, `LB/domains`, `LB/models/business_semantics`,
   `WB/skills`, `WB/domains`, `WB/semantic-layer`). DQL's `validation:` evidence blocks were
   scanned separately (below).
2. A search for every data value I saw in the warehouse: person, organization and insurer
   names (and MUSIC), street addresses, city, state, zip codes, catastrophe names, the result
   code, policy and claim numbers, amounts in both 98000 and 98,000 form, and ratio values.
   The search covered all of LB and WB, including `.dql/cache`, `.dql/local` and `target/`,
   but not the `.duckdb` files.
3. A read of all prose that uses quantity words (one, both, every, all, only, same) next to a
   business noun.

Results:

| Check | Result |
| --- | --- |
| Numbers left in B outside `validation:` | Only formula and SQL constants (`/ 12`, `12.0`, `then 1 else 0`, `COALESCE(x, 0)`, `expr: "1"`, `row_count == 1`), `version: 2`, `dql-format: 1`, column names (`Line_1_Address`, "address line 1 and 2"), "1 January", and the time-spine range in SQL code (`2010-01-01`..`2031-01-01`). No KPI, ratio, amount, count or id | PASS |
| Names, addresses, zips, catastrophe names, result code, policy/claim numbers, stored values | None in B or in the arms' skills, domains, blocks, dbt descriptions or WB semantic-layer YAML. The only hits in LB are dbt Labs' own seed CSVs under `LB/ACME_Insurance/data/`, which is the warehouse source and is expected | PASS |
| Arm copies | LB and WB skills and blocks are identical to B. LB `models/business_semantics` is identical to B. WB modeling is B's, converted to warehouse form by the build, and scans clean | PASS |
| Runtime state in the arms | `LB/.dql/local` and `WB/.dql/local` agent-run and Ask-trace databases hold 0 rows. No old values in the caches | PASS |
| Coded values still named | `PH`/`AG`/`UW`, `'Year'` (premium period), `'yes'/'no'` (fireplace coding). These are code lists an agent needs to write a correct filter, not results | Acceptable |
| Structural data facts still stated | "every coverage period has expired" (the premise of the earned = written rule), "every claim has amounts", "every assessment is an underwriting assessment", "for one claim the coverage names a different policy", "some locations are not attached to an insured object", "both rows match" (the `policy_to_agreement` rationale, inherited verbatim from L1). These are the premises of governed rules or documented data-quality issues. None names a record or a value. At most one indirectly hints at an answer (no coverage period is in force today) | Acceptable, low residual risk |

**Judgement on DQL's `validation:` evidence (row counts on certified relationships).** It is
**acceptable**, for four reasons:
- DQL writes it itself, and requires it, as the proof behind a certified relationship.
  Removing it would decertify the model. WB rewrites it on every build.
- It records table row counts and key statistics at proof time, not KPI values, amounts,
  names or ids.
- It is identical in prior L1, and in every arm that carries the L1 modeling, so it gives LB and
  WB no advantage over the other arms.
- A real DQL deployment ships with exactly this evidence.

The residual risk, stated explicitly: some counts equal the answer to a bare row-count
question. For example, `to_rows` on `agreement_party_role_to_policy` is the number of
policies, and on `claim_coverage_to_claim` it is the number of claims. That risk is shared by
every arm with certified modeling and is not something layer B introduced.

**D1: RESOLVED.**

### R2. D2-D10 re-checked

| # | Re-check | Result |
| --- | --- | --- |
| D2 | `amount_event_date` = `cast(Event_Date as date)`, `role_effective_date` = `cast(Effective_Date as date)`. MF `incurred_losses, loss_ratio` by `metric_time__year` now runs: premium years 2015-2019 have an empty loss ratio, and claim money sits in the empty-date bucket (6,600). `policies_sold, agents` by `metric_time__year` runs (2 / 1 in the empty bucket). The glossary says `metric_time` is always empty for claim money | RESOLVED |
| D3 | Catastrophe block = `claims_with_amounts, incurred_losses, incurred_loss_and_expense` by `claim__catastrophe__catastrophe_name`. MF (LB) and native (LB, WB) give Fire 2 / 6,600 / 13,600, which equals my hand SQL. The glossary lists both spellings and says to use `claims_with_amounts` next to claim money | RESOLVED |
| D4 | Policies skill: short name in `Alternate_Name`, `Acronym_Name` empty, no name written. Matches the data | RESOLVED |
| D5 | `monthly_premium` metric, measure, premium skill and glossary: monthly equivalent per coverage period; a sum over periods is not a monthly amount | RESOLVED |
| D6 | `claims` metric input has `fill_nulls_with: 0`. MF `claim_frequency` by `metric_time__year`: 2015-2018 = 0, 2019 = 1 (2 claims opened / 2 periods starting) | RESOLVED |
| D7 | The log now says the ratio failures came from the `mf` on PATH. I re-confirmed that all 7 ratios run with `.venv-mf` and equal hand SQL | RESOLVED |
| D8 | Claim dimension renamed `damaged_object_id` ("Damaged object (claim record)"). The coverage dimension is labelled "Insured object (coverage)". Both descriptions and the glossary say losses by object and premium by object are different scopes, with no governed loss ratio by object. MF and native: `claim__damaged_object_id` gives 1: 1,000 reserves / 2,500 paid; 2: 2,100 / 4,700 (unchanged, correct) | RESOLVED |
| D9 | Unfiltered role measures removed. Role metrics are now simple metrics on role-specific `count distinct case when Party_Role_Code = ...` measures. `dql semantic list`: 37 metrics, 35 dimensions in LB and WB, and no `*_role_count`. By person (MF and native): Bob Agent 2 sold / 0 held / 1 agent; Mary Holder 0 / 2 / 1 holder. By role (MF): Agent 1 agent / 2 sold; Policy holder 1 holder / 0 sold. Book level 2 / 2 / 1 / 1. All correct | RESOLVED |
| D10 | Book of Business and Loss Ratio by Policy block descriptions and the glossary say never to sum or average `loss_ratio`, and to recompute it from summed parts | RESOLVED |

### R3. Regression sample (no regressions)

- **Metrics:** all 37 re-run in MetricFlow (LB, `.venv-mf`), in five queries. Every value equals
  section 2 above. My hand SQL on the fresh copy again gives:
  - written premium 98,000;
  - losses paid 3,500, loss reserves 3,100, expense reserves 3,300;
  - claims 2;
  - loss ratio 0.0673469.
- **Cuts:**
  - premium by policy and coverage year (MF, native LB, native WB);
  - losses paid and reserves by claim number (MF);
  - losses paid and total reserves by date of loss, using the full path (native LB/WB);
  - claims, closed, open and days to close at book level (native LB/WB);
  - premium by coverage insured object (MF).

  All equal the earlier hand-SQL values.
- **Relationships:** my independent check re-run on B. The 30 certified relationships and 9
  certified equivalences all hold. The 5 drafts are unchanged, with reasons. Ids, keys,
  cardinalities and statuses are identical to L1. `dql model validate`: valid in LB and WB
  (29 entities, 36 relationships, no diagnostics).
- **Blocks:**
  - All 5 SQL blocks re-executed: Loss Ratio Summary, Loss Ratio by Policy and Coverage Year,
    Book of Business, Claims Register and Underwriting Activity. Row for row they equal the
    first round and my SQL: book loss ratio 0.0673; policy 336 in 2019 at 0.33; Book of
    Business 86,000 / 2 claims / 6,600 and 12,000 / 0; register days to close 16 / 25.
  - 3 semantic blocks reproduced with their exact metrics and dimensions in both engines: the
    premium block, the catastrophe block and Claim Financials by Claim. They give the values
    above.
  - All 9 blocks: `status = "draft"`, and `dql parse` is clean.

### R4. New changes reviewed

| Change | Assessment |
| --- | --- |
| Three semantic blocks changed from charts to `chart = "table"` (premium, catastrophe, fire sample) | Acceptable. It is display only, with no change to metrics, dimensions or values. The author's reason is valid: MF returns `entity__dim` column names and native returns bare names, so a fixed x/y binding cannot work in both arms. This is a DQL finding, not a defect of B |
| Two unfiltered role measures removed; role metrics rebuilt without metric filters | Correct (see D9). One behaviour change: grouping a role metric by person or role now also returns rows with 0, for example Mary Holder with 0 policies sold, where MF with a filter omitted them. The values are correct |
| `claims` input `fill_nulls_with: 0` | Only affects ratio/time buckets as intended (`claim_frequency` 0 in years without claims). Book value unchanged (0.333333) |
| Dimension rename `insured_object_id` -> `damaged_object_id` on claims | Blocks do not use it. Glossary and skills updated. 35 dimensions listed in both arms |

New defects: none.

Environment note (unchanged, not a B defect): whether the 7 ratio metrics run in LB depends on
DQL resolving a DuckDB-capable `mf` (`DQL_METRICFLOW_BIN=.venv-mf/bin/mf`). WB cannot run them
(native engine limitation). The skills tell agents to compute from the parts or use the loss-ratio
blocks.

Sign-off: PASS

---

## v2 verification (2026-09-23, after the author's v2 changes 22:08-22:16 CDT and the harness rebuild)

Same verifier, rules and tools. Inputs:
- the "v2" section of `AUTHORING-LOG.md`;
- the changed files: `dbt/models/business_semantics/claim_policy.sql` and `claim_policy.yml`
  (new), `claims.yml`, `policies.yml`, `skills/metrics-glossary.skill.md` and
  `skills/insurance-policies-and-parties.skill.md`;
- the rebuilt LB and WB projects: fresh read-only warehouse copies of both, MetricFlow
  `.venv-mf/bin/mf` in LB, and the native engine through the phase4 CLI
  (`dql semantic query`, composed SQL executed on the copies) in LB and WB.

The hand SQL below is my own. No B file was edited.

### V2-a. `claim_policy`: grain, attribution rule, no double counting

| Check | Evidence | Result |
| --- | --- | --- |
| Present in both warehouses | `main.claim_policy` (view) exists in LB and in WB. The WB project still has no dbt project, models or profiles; the table comes from the harness building B's dbt models into the WB warehouse | PASS |
| Grain = one row per claim | 2 rows, 2 distinct `Claim_Identifier`, 2 claims in `claim`. The model starts from `claim` with left joins, so no claim can be dropped. The dbt `unique` + `not_null` tests on `Claim_Identifier` guard the one-coverage-row-per-claim assumption | PASS |
| Attribution rule | coverage = `claim_coverage` joined to `policy_coverage_detail` on **both** `Effective_Date` and `Policy_Coverage_Detail_Identifier`, then `policy`. `claim.Insurable_Object_Identifier` is not used. My independent join gives the same policy for both claims, including the conflicting claim, which follows `claim_coverage` as the governed rule says | PASS |
| Agent and holder cannot double count | Roles are reduced with `min(case when role = ...)` grouped by policy, so one row per policy is joined to a claim-grain row. Joining `claim_amount` (many) to `claim_policy` (one per claim) is many-to-one. The claim-money sum by agent (6,600 incurred) and by holder equals the book total. No role row can multiply a claim | PASS |
| Limitation (documented in the SQL comment) | If a policy ever had two agents or two holders, only the lower party id would be kept. That under-attributes rather than double counts. The data has one of each per policy | Acceptable (note) |
| Other fan-out paths through the new entity | Native: `incurred_losses` by `person__full_name` and `incurred_losses, claims` by `policy_party_role__party_role` are refused (not composed), and the MF join graph has no path either. `incurred_losses` by `policy__policy_number` composes as `claim_amount -> claim_policy -> policy`, many-to-one only: 6,600 on policy 31003000336. `incurred_losses, written_premium` by `policy__policy_number` aggregates each fact separately and joins on the key: 6,600 / 86,000 and NULL / 12,000, which is correct under the claim_coverage rule | PASS |

### V2-b. Claim money and claims by policy, agent and holder (hand SQL vs MF vs native)

Hand SQL (claim_coverage -> coverage detail on both keys -> policy, roles filtered per role):
policy 31003000336, agent Bob Agent, holder Mary Holder:

| Measure | Value |
| --- | --- |
| claims | 2 |
| losses paid | 3,500 |
| loss reserves | 3,100 |
| expenses paid | 3,700 |
| expense reserves | 3,300 |
| incurred losses | 6,600 |
| incurred loss and expense | 13,600 |

The other policy has no claims.

| Cut | MetricFlow (LB) | Native LB | Native WB | Result |
| --- | --- | --- | --- | --- |
| 6 claim-money metrics by `claim_policy__policy_number` | 3,500 / 3,100 / 3,700 / 3,300 / 6,600 / 13,600 | same | same | PASS |
| same by `claim_policy__agent_name` | Bob Agent, same values | same | same | PASS |
| same by `claim_policy__policy_holder_name` | Mary Holder, same values | same | same | PASS |
| `claims, closed_claims` by policy number + agent + holder | 2 / 2 | same | same | PASS |
| `claims, incurred_losses` by agent (native); `claims_with_amounts, incurred_losses` by agent party id (MF) | 2 / 6,600 | 2 / 6,600 | 2 / 6,600 | PASS |
| `incurred_losses` by `claim_policy__policy__policy_number` (MF, two hops) | 6,600 | - | - | PASS |

The author's log table shows WB "fails: table does not exist" for these cuts. That is
superseded: after the harness change they run in WB and match.

### V2-c. Role metrics by person list only role holders

| Query (by `person__full_name`) | MF (LB) | Native LB | Native WB | Result |
| --- | --- | --- | --- | --- |
| `policies_sold` | Bob Agent 2 only | Bob Agent 2 only | Bob Agent 2 only | PASS |
| `policies_held` | Mary Holder 2 only | Mary Holder 2 only | Mary Holder 2 only | PASS |
| `agents` | Bob Agent 1 only | same | same | PASS |
| `policy_holders` | Mary Holder 1 only | same | same | PASS |
| all four together | role holders only, empty cells for the other role | both persons, 0 for the other role | same as LB | Values correct. The 0-vs-empty difference is the engines' behaviour (author's DQL finding 12), not a B defect |

The metrics carry the role filter again (`policy_party_role__party_role_code = 'AG'/'PH'`) on
role-specific `*_measure` measures.

### V2-d. No regressions

- **Metrics at book level:** all 37 in one MetricFlow query equal the round-1 hand-SQL table
  exactly:
  - 98,000; 8,166.67; 6; 5,600,000; 2; 6; 49,000; 16,333.3;
  - 2 / 2 / 1 / 1; 2; 6;
  - 3,500; 3,100; 3,700; 3,300; 6,600; 7,000; 7,200; 6,400; 13,600;
  - 2; 2; 2; 0; 20.5; 3,300; 0.333333; 0.0673469; 0.138776; 0.0357143;
  - 2; 35; 820; 0.642927.
- **Native WB:** premium, the four claim-money kinds, incurred loss and expense, claims,
  policies, coverage periods, policies sold and agents all equal. Ratios are still refused
  natively (known DQL limitation).
- **Cuts:** premium by policy x coverage year (native WB) and the catastrophe block's request
  (native WB) are unchanged.
- **Blocks:** unchanged in v2 and identical in both arms. Loss Ratio Summary and Book of
  Business re-executed: identical to before (98,000 / 6,600 / 0.0673; 86,000 / 2 / 6,600 and
  12,000 / 0 / 0).
- **Semantic list:** `dql semantic list` shows 41 entries (37 metrics + 4 `*_measure` building
  blocks) and 40 dimensions in both LB and WB.
- **Model validation:** `dql model validate` is valid in both (29 entities, 36 relationships).
- **Arm copies:** B's blocks, skills and `business_semantics` are identical in the arms.

### V2-e. D1 leak scan of the changed files

- **Numbers:** the scan over `B/dbt` and `B/dql` finds only the same formula, SQL and version
  constants as before. `claim_policy.yml` adds only `version: 2`.
- **Values:** a search for policy and claim numbers, person and insurer names, addresses, zips,
  city, catastrophe names and KPI values (98,000, 6,600, 13,600, 0.0673, 5,600,000) over
  `B/dbt`, `B/dql` and all of LB and WB (including `.dql` caches and `target/`, excluding
  `.duckdb` files and dbt Labs' seed CSVs) returns no hits.
- **New prose:** the new glossary section and the policies-skill pointer name dimensions and
  rules only. The claim_policy SQL comments state the rule and the pivot limitation, with no
  values.
- **Stale guidance:** "the metric joins cannot reach claims from a party" and the two-hop
  comment were updated, and no file still says claims cannot reach policy, agent or holder.
- **`claim_policy` itself** is a derived warehouse table (claim -> policy -> agent/holder
  names). It holds data an agent must still query, not results written into instructions.

**D1: PASS.**

### New observations (non-blocking)

| # | Severity | Observation | Recommendation |
| --- | --- | --- | --- |
| V2-1 | cosmetic | The 4 `*_measure` entries appear in `dql semantic list` next to the metrics, with the **same labels** ("Policies sold (by agent)", "Agents", ...) and no role filter. Picked by mistake and cut by person, they return the other role's person with 0 (for example Mary Holder 0 agents) instead of only role holders. Values are never wrong | Give them distinct labels (for example "Policies sold - building block"), or hide the measures from the list if DQL supports it |
| V2-2 | process | `FROZEN.json` (`frozenAt` 2026-09-23T20:28:11-05:00) predates the v2 edits to `dbt/` and `dql/` (22:08-22:16). It describes v1, and its rule says no edits after freezing | Re-issue `FROZEN.json` for v2 after this sign-off. Label any run made before that with the v1 freeze |
| V2-3 | harness (not B) | WB's warehouse now contains the tables B's dbt models build (`claim_policy`, `metricflow_time_spine`), while the WB project has no dbt. This is a reasonable definition (a no-dbt team still has its transformation job's output) and applies equally to LB | Record this in the WB arm description and in the build identity of v2 runs |
| V2-4 | note | `claim_policy` is not modeled as a DQL entity (the modeling still has 29 entities); it lives only in the semantic layer | Optional: add it to the claims area with its certified many-to-one keys |

Blocking defects: none.

Sign-off: PASS

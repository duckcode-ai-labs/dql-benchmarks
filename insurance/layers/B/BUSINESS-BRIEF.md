# ACME Insurance — business brief (layer B)

Author: layer-B author agent. Written before any metric, skill or block.
Started 2026-09-23 18:23 CDT; brief finished **2026-09-23 18:36 CDT**.

## 1. The business and the data

ACME is a property-and-casualty (P&C) carrier: it writes property policies through agents,
splits each policy into yearly **coverage periods** (policy coverage details) on one insured
property, charges an annual **premium** per coverage period, and pays **claims** made
against a coverage period. Each claim carries four kinds of money: **loss payments**,
**loss reserves** (case reserves), **expense payments** and **expense reserves** (loss
adjustment expense, LAE). Claims can be tagged with a **catastrophe** (peril) and a loss
**occurrence** (date of loss). Underwriters assess a policy before it is written.

The warehouse is dbt Labs' ACME build of the OMG P&C data model (DuckDB, schema `main`, 29
views over seeds). It is a **very small sample**; every KPI below is computed from exactly
these rows (read in full on 2026-09-23):

| Object | Rows | What is filled |
| --- | --- | --- |
| policy | 2 | number, term dates (policy 1: 2015-01-01..2019-12-31; policy 2: 2019-06-01..2020-05-31). Status, rating location empty |
| policy_coverage_detail | 6 | yearly coverage periods (5 for policy 1, 1 for policy 2), insured object. Coverage type/part/description empty |
| policy_amount / premium | 12 / 6 | premium rows (Amount_Type_Code `Year`, 12,000–20,000) and 6 unlabeled rows (600,000–1,000,000; almost certainly the coverage limit, but not labeled) |
| agreement_party_role | 4 | each policy has one PH (policy holder) and one AG (agent) role; both policies: holder party 1 (Mary Holder), agent party 2 (Bob Agent) |
| claim | 2 | claim number, open and close dates, catastrophe (both `Fire`), occurrence, insured object. Status, reported date, description empty |
| claim_amount + 4 subtype tables | 8 | 2 of each kind; each amount is in exactly one subtype table; no amount dates |
| claim_coverage | 2 | both claims point to coverage detail 5 (policy 1, 2019) |
| catastrophe | 4 | Hurricane, Tornado, Flood, Fire (peril names, not named events) |
| occurrences | 2 | begin/end dates only |
| assessment (+ result, underwriting marker, links) | 2 | one underwriting assessment per policy, result `OK`, underwriter party 3 (Alice Writer) |
| insurable_object / geographic_location / address / coordinates | 2 / 8 / 8 / 8 | all Austin, TX; 2 insured objects |
| fire_claim | 820 | a separate fire-risk sample; its policy, claim, premium and location columns are empty in every row |

Known data conflict: claim 2 (`12312702`) is recorded in `claim_coverage` against coverage
detail 5 (policy 31003000336, insured object 1), but `claim.Insurable_Object_Identifier` says
the damaged object is 2, which is insured by policy 31003000337 (coverage 6, 2019-06-01..
2020-05-31, which also covers the loss date 2019-06-01). The governed rule follows
`claim_coverage` (the OMG "claim is made against a coverage" record and the ontology's
`hasClaim` mapping); every report that attributes claims to policies states this.

## 2. KPIs

Grain = the row one value of the KPI is computed from. "Cut by" = the dimensions the
business slices it by. Supported = the data holds what the definition needs.

### Premium and exposure

| # | KPI | Business definition | Grain | Cut by | Supported? |
| --- | --- | --- | --- | --- | --- |
| P1 | **Written premium** | Sum of the premium charged for coverage periods: `policy_amount.Policy_Amount` for amounts listed in `premium` | premium amount (one per coverage period) | policy, coverage year (coverage effective date), policy holder, agent, insured location | **Yes** |
| P2 | Monthly premium | Annual premium / 12 (ontology Premium Amount Monthly; only for `Year` premiums) | premium amount | as P1 | **Yes** |
| P3 | Earned premium | Premium earned over the elapsed part of each coverage period | premium × days | as P1 | **Partly**: earning dates are empty. Every coverage period ended by 2020-05-31, so earned = written for all periods today; no earned premium at a past date (would need pro-rating, an assumption) |
| P4 | Policy count (policies in force / written) | Distinct policies; in force on a date when policy effective ≤ date ≤ expiration | policy | effective year, agent, holder, in force on a date | **Yes** (status code empty, so in force comes from dates only) |
| P5 | Coverage periods (policy-years, exposure) | Distinct policy coverage details; the exposure base (one per insured object per year) | coverage detail | policy, coverage year | **Yes** |
| P6 | Average premium | Written premium / policies (per policy) and / coverage periods (per policy-year) | derived | policy, year | **Yes** |
| P7 | Total insured value / coverage limit | Sum of limits on the book | coverage detail | policy, year | **No (not labeled)**: the non-premium policy amounts (1,000,000 and 600,000) look like limits but carry no type code; exposed only as "other (non-premium) policy amount" with that caveat |
| P8 | Policy retention / renewal, cancellations, new business | | | | **No**: no status, renewal or cancellation data |

### Claims and losses

| # | KPI | Business definition | Grain | Cut by | Supported? |
| --- | --- | --- | --- | --- | --- |
| C1 | **Losses paid** (paid loss) | Sum of claim amounts that are loss payments | claim amount | claim, catastrophe, date of loss, claim open year, policy (via claim_coverage), holder, agent | **Yes** |
| C2 | **Loss reserves** (case reserves, outstanding loss) | Sum of claim amounts that are loss reserves | claim amount | as C1 | **Yes** (current snapshot only; no reserve history) |
| C3 | **Expenses paid** (paid LAE) | Sum of claim amounts that are expense payments | claim amount | as C1 | **Yes** |
| C4 | **Expense reserves** (LAE reserves) | Sum of claim amounts that are expense reserves | claim amount | as C1 | **Yes** |
| C5 | **Incurred losses** | Losses paid + loss reserves | derived | as C1 | **Yes** |
| C6 | Incurred loss and LAE | All four kinds | derived | as C1 | **Yes** |
| C7 | Total paid (loss + LAE) / total reserves (loss + LAE) | payments / reserves across loss and expense | derived | as C1 | **Yes** |
| C8 | **Claim count** | Distinct claims (reported claims) | claim | claim open date, catastrophe, date of loss, policy, holder, agent | **Yes** |
| C9 | Open / closed claims | Closed when a close date is filled (and on/before the as-of date) | claim | as C8 | **Yes** (dates only; status code empty; both claims closed) |
| C10 | Claim cycle time (days to close) | Close date − open date, averaged over closed claims | claim | as C8 | **Yes** |
| C11 | Report lag (days from loss to claim open) | Claim open date − occurrence begin date | claim | as C8 | **Yes** (reported date empty, so open date is the proxy) |
| C12 | **Claim severity** | Incurred losses / claim count | derived | catastrophe, year | **Yes** |
| C13 | **Claim frequency** | Claims / coverage periods (claims per policy-year) | derived | year, policy | **Yes** (very small numbers) |
| C14 | **Claims by catastrophe** | C1–C8 cut by catastrophe (peril) | claim | catastrophe name | **Yes** (both claims are `Fire`; catastrophe names are perils, not named events) |
| C15 | Claims by property / location | C1–C8 cut by insured object and its address | claim | insured object, address, zip | **Yes** (all Austin TX; claim → insured object; occurrence location empty) |
| C16 | Subrogation / salvage recoveries, IBNR, claim denials, litigation, fraud | | | | **No**: not in the data |

### Profitability

| # | KPI | Business definition | Grain | Cut by | Supported? |
| --- | --- | --- | --- | --- | --- |
| R1 | **Loss ratio** | Incurred losses / premium for the same scope | derived | total, policy, coverage year | **Yes** with caveats: premium is written = earned (P3); claim attribution to policy follows claim_coverage |
| R2 | Loss and LAE ratio | (Incurred losses + incurred LAE) / premium | derived | as R1 | **Yes** |
| R3 | Paid loss ratio | Losses paid / premium | derived | as R1 | **Yes** |
| R4 | Expense ratio, combined ratio, underwriting profit | Underwriting expenses (commission, acquisition, overhead) / premium | | | **No**: no underwriting or acquisition expenses, no commissions (only claim-handling expense exists) |
| R5 | fire_claim average loss ratio | Unweighted average of the sample's precomputed `Loss_Ratio` | fire-risk record | fireplace, year built, distance to fire station, firefighters | **Yes, separate sample only**; never combined with the claims above |

### Distribution, customers and underwriting

| # | KPI | Business definition | Grain | Cut by | Supported? |
| --- | --- | --- | --- | --- | --- |
| D1 | **Book by agent** (policies sold, premium, claims, incurred) | Policies where the party plays role AG, with their premium and claims | policy × agent | agent | **Yes** (one agent in the data) |
| D2 | **Book by policy holder** | Same with role PH | policy × holder | policy holder | **Yes** (one holder) |
| D3 | Agent commission, agency hierarchy, channel | | | | **No** |
| U1 | **Underwriting activity** | Underwriting assessments: count, result, days from begin to end, underwriter, policy | underwriting assessment | underwriter, result, policy, year | **Yes** |
| U2 | Quote-to-bind / hit ratio, declined submissions | | | | **No**: only accepted (`OK`) assessments on written policies |
| X1 | Customer demographics, lifetime value, product / line of business, reinsurance, budgets | | | | **No** |

## 3. Standard reports (the blocks)

A carrier's recurring reports that this data can feed. Each becomes one draft block.

1. **Written premium by policy and coverage year** (P1, P2) — semantic block on the premium metric.
2. **Claim financials by claim** (C1–C7) — paid, reserved and incurred loss and LAE per claim; semantic block.
3. **Claims and losses by catastrophe** (C8, C5, C12, C14) — semantic block.
4. **Loss ratio summary** (R1–R3, book level) — semantic block on the ratio metrics.
5. **Loss ratio by policy and coverage year** (R1 at policy × year) — SQL block (claims reach the policy through claim_coverage, deeper than the metric join limit).
6. **Book of business by agent and policy holder** (D1, D2, P4, P1, C8, C5) — SQL block.
7. **Claims register** (C8–C11, C15) — one row per claim with policy, dates, cycle time, report lag, catastrophe, insured address and amounts; SQL block.
8. **Underwriting activity** (U1) — SQL block.
9. **Fire risk sample: loss ratio by fireplace** (R5) — semantic block on the separate sample.

## 4. Rules every KPI follows

- Amount kinds are decided **only** by the subtype tables (`loss_payment`, `loss_reserve`,
  `expense_payment`, `expense_reserve`; `premium`), never by `Amount_Type_Code`, and the
  unfiltered sum of `claim_amount` or `policy_amount` is never a KPI.
- Premium is at coverage-period grain; claims at claim grain; claim amounts at amount grain.
  Premium and claims are aggregated separately and only then combined (ratios), because
  joining policies to claims or to the two role rows per policy fans out.
- Always filter `agreement_party_role` to one role before joining it.
- Claims reach a policy only through `claim_coverage` → `policy_coverage_detail` → `policy`.

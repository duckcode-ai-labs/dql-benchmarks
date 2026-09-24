---
id: insurance-coverage-and-premium
kind: metric_policy
status: active
owner: insurance-analytics@acme-insurance.test
description: "Definitions of coverage periods, premium, monthly premium and other policy amounts, and how they map to policy_coverage_detail, policy_amount and premium."
triggers:
  - premium
  - premiums
  - monthly premium
  - annual premium
  - premium period
  - coverage
  - coverage period
  - policy coverage detail
  - policy amount
  - insured object
  - insurable object
source_refs:
  - docs/insurance.ttl (PolicyCoverageDetail, Premium, premiumAmount, premiumAmountMonthly, premiumPeriod)
  - docs/data.world_P&C_Insurance_Ontology_V1.r2rml (Premium and PolicyAmount mappings)
  - docs/ACME_small.ddl (Policy_Coverage_Detail, Policy_Amount, Premium)
clarify_when:
  - The user asks for a coverage limit, deductible or sum insured (the data has no labeled limit or deductible).
  - The user asks for earned premium or written premium for a period that does not match the coverage periods.
---
# Coverage and premium

## Policy coverage detail

- A **policy coverage detail** is one coverage period of a policy on one insurable object:
  a row of `policy_coverage_detail`, identified by **both** `Effective_Date` and
  `Policy_Coverage_Detail_Identifier`. Join to it on both columns.
- **Coverage period**: `policy_coverage_detail.Effective_Date` to `Expiration_Date`. Coverage
  periods are yearly and sit inside the policy term. When a question is about a year of coverage or the premium for a year,
  use the coverage period, not the policy term.
- `policy_coverage_detail.Policy_Identifier` is the policy; `Insurable_Object_Identifier` is the
  insured object.
- Coverage type, coverage part, description and inclusion/exclusion codes are empty: the data
  does not say what peril or line of business a coverage is.

## Policy amount and premium

- `policy_amount` holds every money amount on a coverage detail (`Policy_Amount`), with the
  policy (`Policy_Identifier`) and the coverage `Effective_Date`.
- `premium` is a **specialization** of `policy_amount`: it lists the `Policy_Amount_Identifier`s
  that are premiums and has no other columns. A policy amount **is a premium** only if its
  identifier is in `premium`:
  `premium JOIN policy_amount USING (Policy_Amount_Identifier)`.
- **Premium amount** = `policy_amount.Policy_Amount` for premium rows.
- **Premium period** = `policy_amount.Amount_Type_Code` for premium rows. The only value is
  `'Year'`: the amount is an annual premium for that coverage period.
- **Monthly premium** = premium amount / 12, defined only when the premium period is `'Year'`
  (the ontology's Premium Amount Monthly).
- The premium of a policy for a coverage period is the premium row whose coverage detail
  (`Effective_Date`, `Policy_Coverage_Detail_Identifier`) is that period. A policy's total
  premium over several periods is the sum over its coverage details; say which periods are
  included.
- **Other policy amounts**: rows of `policy_amount` that are not in `premium` have an empty
  `Amount_Type_Code`. The data does not say what they are. Call them "policy amount
  (non-premium)". Never add them to premium. If a user asks for a coverage limit, deductible
  or sum insured, say that the data has no labeled limit or deductible and that the
  non-premium policy amount is unlabeled.
- `Earning_Begin_Date` and `Earning_End_Date` are empty, so **earned premium** cannot be
  computed from earning dates. If a user asks for earned premium, say so; do not pro-rate
  unless the user asks for an assumption and it is stated in the answer.
- `policy_amount.Geographic_Location_Identifier`, `Insurable_Object_Identifier` and
  `Insurance_Type_Code` are empty; reach the insured object and its location through
  `policy_coverage_detail`.

## Governed metrics

- `written_premium`, `monthly_premium`, `premium_records`, `coverage_periods`, `policies`,
  `other_policy_amount` (unlabeled, never premium). Slice premium by coverage year with
  `policy_amount__premium_period_start_date` at granularity `year`, and by policy with
  `policy__policy_number`.
- **Earned premium**: every coverage period in the data has already expired, so earned premium = written
  premium for every period today. Earned premium at an earlier date needs pro-rating by days,
  which is an assumption: do it only when asked and state it.
- A **coverage year** is the year a coverage period starts; a period that does not start on
  1 January runs into the next calendar year.
- `monthly_premium` is the monthly equivalent of each annual premium. Summed over several
  coverage periods it is not a monthly amount; report it per coverage period (policy and
  coverage year) or say what it adds up.

## Aggregation rules

- Premium is additive across coverage details and policies. Monthly premium is additive only
  across rows that are all annual.
- Do not join premium to claims or to `agreement_party_role` without first reducing the other
  side to one row per policy or coverage detail; both fan out.

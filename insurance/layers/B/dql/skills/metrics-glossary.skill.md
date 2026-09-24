---
id: metrics-glossary
kind: metric_policy
status: active
owner: insurance-analytics@acme-insurance.test
description: "ACME P&C KPIs mapped to the governed semantic-layer metrics, their dimensions, and the standard report blocks."
triggers:
  - metric
  - kpi
  - premium
  - written premium
  - losses paid
  - paid loss
  - loss reserve
  - case reserve
  - expense
  - lae
  - incurred
  - loss ratio
  - severity
  - frequency
  - claim count
  - policy count
  - agent
  - policy holder
  - underwriting
source_refs:
  - dbt models/business_semantics (semantic models and metrics of layer B)
  - BUSINESS-BRIEF.md (layer B KPI definitions)
---
# Metrics glossary

Use a governed metric whenever a question matches one. Each metric was checked against
hand-written SQL on the warehouse before release. Values are never recorded here: run the
metric or the block.

## Premium and exposure (semantic models `policy_amounts`, `insurance_policies`, `policy_coverage_periods`)

| Business term | Metric |
| --- | --- |
| Written premium (premium, annual premium; equals earned premium because every period has expired) | `written_premium` |
| Monthly premium (annual premium / 12; report per coverage period, a sum over several periods is not a monthly amount) | `monthly_premium` |
| Premium records (one per coverage period) | `premium_records` |
| Other, unlabeled policy amount (NOT premium, NOT a labeled limit) | `other_policy_amount` |
| Policies | `policies` |
| Coverage periods / policy-years / exposure | `coverage_periods` |
| Policies / coverage periods that carry premium | `policies_with_premium`, `coverage_periods_with_premium` |
| Policies sold by an agent / held by a policy holder | `policies_sold`, `policies_held` |
| Number of agents / policy holders | `agents`, `policy_holders` |

Dimensions: `policy__policy_number`, `policy__policy_effective_date`,
`policy__policy_expiration_date`, `policy_amount__premium_period_start_date` (coverage year of
the premium: use it with granularity `year`), `policy_amount__policy_amount_kind`,
`policy_coverage_detail__coverage_start_date`, `policy_coverage_detail__insured_object_id`
(the object the coverage insures), `person__full_name` (with the role metrics: agent name for
`policies_sold`, holder name for `policies_held`), `policy_party_role__party_role`.

## Claims and losses (semantic models `claim_amounts`, `insurance_claims`)

| Business term | Metric |
| --- | --- |
| Losses paid (paid loss, indemnity paid) | `losses_paid` |
| Loss reserves (case reserves, outstanding loss) | `loss_reserves` |
| Expenses paid (LAE paid, adjusting expense paid) | `expenses_paid` |
| Expense reserves (LAE reserves) | `expense_reserves` |
| Incurred losses (paid + reserved loss) | `incurred_losses` |
| Incurred expenses (incurred LAE) | `incurred_expenses` |
| Total paid (loss + expense) | `total_paid` |
| Total reserves (loss + expense) | `total_reserves` |
| Incurred loss and expense (all four kinds) | `incurred_loss_and_expense` |
| Claims (claim count) | `claims` |
| Closed / open claims (today) | `closed_claims`, `open_claims` |
| Average days to close | `avg_days_to_close` |
| Claims with claim amounts (claim count on the claim-amount model) | `claims_with_amounts` |

Dimensions for the claim-money metrics (they reach the claim through one join):
`claim__claim_number`, `claim__claim_status`, `claim__claim_open_date`,
`claim__claim_close_date`, `claim__damaged_object_id`, `claim_amount__claim_amount_kind`,
and, two joins away, the catastrophe and the date of loss. Spelling of those two: DQL's native
engine accepts `catastrophe__catastrophe_name` / `occurrence__loss_date`; MetricFlow needs the
full path `claim__catastrophe__catastrophe_name` / `claim__occurrence__loss_date`. The full
path works in both. To count claims next to claim money in one query, use
`claims_with_amounts` (same model) rather than `claims`.
Dimensions for `claims`, `closed_claims`, `open_claims`, `avg_days_to_close`:
`claim__claim_number`, `claim__claim_status`, `claim__claim_open_date`,
`claim__claim_close_date`, `claim__damaged_object_id`, `catastrophe__catastrophe_name`,
`occurrence__loss_date`.
Claim amounts have no date of their own: slice them in time by `claim__claim_open_date` or the
date of loss; `metric_time` for claim-money metrics is always empty.

`claim__damaged_object_id` (the object named on the claim) and
`policy_coverage_detail__insured_object_id` (the object a coverage insures) are different
fields and disagree for one claim, so losses by object and premium by object are not the same
scope; there is no governed loss ratio by object.

## Ratios

`loss_ratio` (incurred losses / written premium), `loss_and_lae_ratio` ((incurred losses +
incurred expenses) / written premium), `paid_loss_ratio` (losses paid / written premium),
`claim_frequency` (claims / coverage periods), `claim_severity` (incurred losses / claims with
amounts), `avg_premium_per_policy` (written premium / policies with premium),
`avg_premium_per_coverage_period` (written premium / coverage periods with premium) are ratio
metrics. They compile through MetricFlow; DQL's native engine does not run ratio metrics.
When a ratio metric cannot run, compute it from its simple parts over the same scope and state
the formula, or use the **Loss Ratio Summary** / **Loss Ratio by Policy and Coverage Year**
blocks. Never add up ratios across rows: recompute them from summed numerators and
denominators.

## Claims and claim money by policy, agent and policy holder

Claims reach a policy only through claim_coverage -> policy_coverage_detail -> policy. The
claim-grain model `claim_policy` (semantic model `claim_policies`) stores that path once per
claim, with the policy's agent and policy holder, so every claim-money metric and the claim
count metrics (`claims`, `closed_claims`, `open_claims`, `avg_days_to_close`,
`claims_with_amounts`) can be cut by:
`claim_policy__policy_number`, `claim_policy__policy_id`, `claim_policy__agent_name`,
`claim_policy__agent_party_id`, `claim_policy__policy_holder_name`,
`claim_policy__policy_holder_party_id`, `claim_policy__coverage_start_date` (coverage period
the claim is made against). Other policy attributes: `claim_policy__policy__<dimension>`.
These cuts follow the claim_coverage rule (see the claims skill for the one claim whose
damaged object is insured by a different policy). Premium by agent or policy holder: the
**Book of Business** block (premium per policy with its agent and holder); per-policy loss
ratios: the **Loss Ratio by Policy and Coverage Year** block.

Role metrics (`policies_sold`, `policies_held`, `agents`, `policy_holders`) count only rows
with their role, so cut by `person__full_name` they list only the parties that hold that role.

## Standard report blocks (domain insurance, draft, not human-certified)

Written Premium by Policy and Coverage Year; Claim Financials by Claim; Claims and Losses by
Catastrophe; Loss Ratio Summary; Loss Ratio by Policy and Coverage Year; Book of Business by
Agent and Policy Holder; Claims Register; Underwriting Activity; Fire Risk Sample Loss Ratio
by Fireplace.

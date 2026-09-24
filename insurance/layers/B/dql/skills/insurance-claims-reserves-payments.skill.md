---
id: insurance-claims-reserves-payments
kind: metric_policy
status: active
owner: insurance-analytics@acme-insurance.test
description: "Definitions of claims, claim dates, loss and expense reserves and payments, and how claim amounts specialize into those four kinds."
triggers:
  - claim
  - claims
  - claim number
  - open claim
  - closed claim
  - loss payment
  - paid loss
  - loss reserve
  - expense payment
  - expense reserve
  - reserve
  - reserves
  - payment
  - incurred
  - claim amount
  - catastrophe
  - occurrence
  - date of loss
source_refs:
  - docs/insurance.ttl (Claim, LossPayment, LossReserve, ExpensePayment, ExpenseReserve, Catastrophe, against, hasCatastrophe)
  - docs/data.world_P&C_Insurance_Ontology_V1.r2rml (claim amount subtype mappings)
  - docs/ACME_small.ddl (Claim, Claim_Amount, Loss_Payment, Loss_Reserve, Expense_Payment, Expense_Reserve, Claim_Coverage)
clarify_when:
  - The user asks for "claim cost" or "claim amount" without saying whether they mean payments, reserves, loss only or loss plus expense.
  - The user asks for amounts "as of" a date; claim amounts have no date.
---
# Claims, reserves and payments

## Claim

- A **claim** is one row of `claim` (`Claim_Identifier`). The **claim number** people use is
  `claim.Company_Claim_Number`.
- **Claim open date** = `Claim_Open_Date`; **claim close date** = `Claim_Close_Date`.
- A claim is **closed** when `Claim_Close_Date` is filled and on or before the date in
  question, and **open** otherwise. `Claim_Status_Code` is empty, so status comes from the dates.
- **Claim duration (days to close)** = `Claim_Close_Date - Claim_Open_Date` in days.
- **Date of loss** = the claim's loss occurrence date: `occurrences.Occurrence_Begin_Date`
  (join `claim.Occurrence_Identifier`). Reported date, claims-made date and reopen date are
  empty.
- **Catastrophe**: `claim.Catastrophe_Identifier` -> `catastrophe.Catastrophe_Name`. The names are
  peril types, not named events, so "claims by catastrophe" means claims by
  that peril. Several claims can share one catastrophe.
- **Insured object of a claim**: `claim.Insurable_Object_Identifier` -> `insurable_object`.

## Claim -> policy

A claim is made **against** a policy coverage detail (ontology `against`):
`claim` -> `claim_coverage` (`Claim_Identifier`) -> `policy_coverage_detail` on **both**
`Effective_Date` and `Policy_Coverage_Detail_Identifier` -> `policy` (`Policy_Identifier`).
There is no policy column on `claim` itself. From the policy, continue to the policy holder or
agent through `agreement_party_role` (see the policies skill).

**Data conflict:** for one claim, the policy reached through `claim_coverage` is not the
policy that insures the object named on `claim.Insurable_Object_Identifier` (the coverage
detail's `Insurable_Object_Identifier` differs from the claim's). The governed rule attributes a
claim to a policy through `claim_coverage` (the record of what the claim is made against); say
so whenever an answer attributes claims or losses to policies, holders or agents. To see the
disagreement, compare `claim.Insurable_Object_Identifier` with the coverage detail's
`Insurable_Object_Identifier` (the Claims Register block shows both).
Each claim has exactly one `claim_coverage` row today; if a claim ever had several, amounts
would repeat per coverage row, so aggregate amounts per claim before joining coverage.

## Claim amounts and their four kinds

- `claim_amount` holds every money amount on a claim: `Claim_Amount` with `Claim_Identifier`.
  A claim has several amounts.
- The kind of an amount is known **only** from which specialization table lists its
  `Claim_Amount_Identifier` (each is one-to-one with `claim_amount`):

| Business term | Table | Meaning |
| --- | --- | --- |
| **Loss payment** (paid loss) | `loss_payment` | money paid to settle the loss |
| **Loss reserve** (case reserve) | `loss_reserve` | money set aside for the expected loss |
| **Expense payment** | `expense_payment` | money paid for handling the claim (adjusting, legal) |
| **Expense reserve** | `expense_reserve` | money set aside for expected handling expense |

- To get, for example, loss payments: `loss_payment JOIN claim_amount USING (Claim_Amount_Identifier)`
  and use `claim_amount.Claim_Amount`; join `claim_amount.Claim_Identifier` to `claim`.
- `claim_amount.Amount_Type_Code`, `Event_Date` and `Insurance_Type_Code` are empty. Never use
  them to classify amounts, and never sum `claim_amount` without choosing a kind: the unfiltered
  sum mixes reserves with payments.

## Governed metrics

Use the metrics: `losses_paid`, `loss_reserves`, `expenses_paid`, `expense_reserves`,
`incurred_losses`, `incurred_expenses`, `total_paid`, `total_reserves`,
`incurred_loss_and_expense`, `claims`, `closed_claims`, `open_claims`, `avg_days_to_close`
(see the metrics glossary). They slice by claim number, claim status, claim dates,
catastrophe, date of loss and amount kind.

## Derived measures (industry conventions)

State the formula when you use one of these:

- **Total paid** = loss payments + expense payments.
- **Total reserves** (outstanding) = loss reserves + expense reserves.
- **Incurred loss** = loss payments + loss reserves.
- **Incurred loss and expense** = all four kinds.
- **Claim severity** = incurred losses / number of claims. **Claim frequency** = claims /
  coverage periods (policy-years).
- **Report lag** = claim open date - date of loss (the reported date is empty).
- **Loss ratio** = incurred loss / premium for the same policies and period. The data has no
  earned premium (see the coverage and premium skill); if you compute a loss ratio from annual
  premium, say so. The `fire_claim` table has its own precomputed `Loss_Ratio` per record; it
  is not linked to these claims and must not be combined with them.

Amounts have no transaction date, so there is no reserve or payment history over time; a
question about amounts at a past date cannot be answered from these tables.

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
  peril types (Hurricane, Tornado, Flood, Fire), so "claims by catastrophe" means claims by
  that peril. Several claims can share one catastrophe.
- **Insured object of a claim**: `claim.Insurable_Object_Identifier` -> `insurable_object`.

## Claim -> policy

A claim is made **against** a policy coverage detail (ontology `against`):
`claim` -> `claim_coverage` (`Claim_Identifier`) -> `policy_coverage_detail` on **both**
`Effective_Date` and `Policy_Coverage_Detail_Identifier` -> `policy` (`Policy_Identifier`).
There is no policy column on `claim` itself. From the policy, continue to the policy holder or
agent through `agreement_party_role` (see the policies skill).

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

## Derived measures (industry conventions)

State the formula when you use one of these:

- **Total paid** = loss payments + expense payments.
- **Total reserves** (outstanding) = loss reserves + expense reserves.
- **Incurred loss** = loss payments + loss reserves.
- **Incurred loss and expense** = all four kinds.
- **Loss ratio** = incurred loss / premium for the same policies and period. The data has no
  earned premium (see the coverage and premium skill); if you compute a loss ratio from annual
  premium, say so. The `fire_claim` table has its own precomputed `Loss_Ratio` per record; it
  is not linked to these claims and must not be combined with them.

Amounts have no transaction date, so there is no reserve or payment history over time; a
question about amounts at a past date cannot be answered from these tables.

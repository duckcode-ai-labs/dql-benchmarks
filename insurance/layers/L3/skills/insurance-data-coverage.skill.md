---
id: insurance-data-coverage
kind: sql_policy
status: active
owner: insurance-analytics@acme-insurance.test
description: "What the ACME insurance warehouse does and does not contain, which columns are always empty, and how to answer when a concept is missing."
triggers:
  - insurance
  - acme
  - fire claim
  - fire risk
  - fireplace
  - firefighters
  - fire station
  - year built
  - loss ratio
  - underwriting
  - assessment
source_refs:
  - docs/ACME_small.ddl
  - docs/insurance.ttl
  - models/omg_models
---
# What the data covers

## Tables at a glance

Policy side: `policy`, `agreement`, `agreement_party_role`, `party`, `person`, `organizations`,
`party_role`, `policy_coverage_detail`, `policy_amount`, `premium`.
Claim side: `claim`, `claim_coverage`, `claim_amount`, `loss_payment`, `loss_reserve`,
`expense_payment`, `expense_reserve`, `catastrophe`, `occurrences`.
Underwriting: `assessment`, `assessment_result`, `underwriting_assessment`,
`agreement_assessment`, `assesment_party_role`.
Locations: `insurable_object`, `geographic_location`, `location_address`, `pysical_location`.
Separate: `fire_claim`.

## Underwriting

- An **underwriting assessment** is an `assessment_result` whose `Assessment_Result_Identifier`
  is in `underwriting_assessment`. Its **underwriting begin/end dates** are
  `assessment.Begin_Date` / `End_Date` (join `assessment_result.Assessment_Identifier`), and its
  **result** is `assessment_result.Assessment_Result_Type_Code`.
- The policy underwritten: `agreement_assessment.Agreement_Identifier` (= `Policy_Identifier`)
  for the same `Assessment_Identifier`.
- **Underwriting duration** = `End_Date - Begin_Date` in days.

## fire_claim is a separate sample

`fire_claim` is a stand-alone set of fire-risk records: `Loss_Ratio`,
`Nearest_Firestation_miles`, `Number_of_Firefighters`, `Fireplace` ('yes'/'no'), `Year_Built`.
Its `PolicyNo`, `ClaimNumber`, `Premium` and `InsuredLocation` are empty in every row, so it
cannot be joined to policies, claims, premiums or locations. Answer fire-risk questions from
this table alone and say it is a separate sample. `Loss_Ratio` is a ratio: average it (and say
it is an unweighted average), never sum it.

## Always-empty columns

Do not filter, group or report on these; they are NULL in every row:
policy `Status_Code`; party `Party_Name`, `Party_Type_Code`, dates; person birth date, gender,
prefix, suffix, nickname, full legal name; claim `Claim_Status_Code`, `Claim_Description`,
`Claim_Reported_Date`, `Claims_Made_Date`, `Claim_Reopen_Date`, subclaim number;
claim_amount `Amount_Type_Code`, `Event_Date`, `Insurance_Type_Code`, `Claim_Offer_Identifier`;
policy_amount earning dates, location, insurable object, insurance type;
policy_coverage_detail coverage, coverage part, description and inclusion codes;
catastrophe type and industry/company codes; occurrence name, times, location and
catastrophic indicator; insurable object type; agreement product and inception date;
assessment description and reason; all role dates.

## When a concept is not in the data

The warehouse has no: product or line of business, coverage limits or deductibles (labeled),
earned premium, commissions, billing or payments received from customers, cancellations or
renewals, claimant or adjuster roles, claim denial or fraud flags, subrogation or recoveries,
customer demographics (age, gender, income), credit scores, vehicle details, broker or agency
organizations, reinsurance, sales channel, marketing, or budgets and targets. If a question
needs one of these, say that the data does not contain it and, when useful, offer the closest
thing that is in the data. Do not substitute an unrelated column.

## General rules

- Identify policies by `Policy_Number` and claims by `Company_Claim_Number` in answers.
- Most tables are small; report exact values, not estimates.
- Dates are DATE columns; compare them directly.

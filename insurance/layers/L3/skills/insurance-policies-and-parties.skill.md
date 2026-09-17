---
id: insurance-policies-and-parties
kind: domain_reference
status: active
owner: insurance-analytics@acme-insurance.test
description: "What a policy, policy holder, agent and underwriter are in the ACME insurance warehouse, and how to find them."
triggers:
  - policy
  - policies
  - policy number
  - policy holder
  - policyholder
  - insured
  - customer
  - agent
  - sold by
  - underwriter
  - underwriting
  - party
  - person
  - role
source_refs:
  - docs/insurance.ttl (Policy, PolicyHolder, Agent, hasPolicyHolder, soldByAgent)
  - docs/data.world_P&C_Insurance_Ontology_V1.r2rml (Agent, PolicyHolder, Underwriter, UnderwritingAssessment mappings)
  - docs/ACME_small.ddl (Policy, Agreement_Party_Role)
clarify_when:
  - The user says "customer" and it is unclear whether they mean the policy holder or any party.
  - The user asks for an agent's or underwriter's policies and it is unclear whether they mean policies sold (agent) or policies underwritten (underwriter).
---
# Policies and the parties on them

The warehouse follows the OMG Property & Casualty data model. All tables are dbt views in
schema `main`. Column names are mixed case (`Policy_Identifier`).

## Policy

- A **policy** is one row of `policy`, identified by `Policy_Identifier`.
- The **policy number** customers and staff use is `policy.Policy_Number` (for example
  31003000336). Use it, not `Policy_Identifier`, when showing or filtering a policy by number.
- **Policy term**: `policy.Effective_Date` to `policy.Expiration_Date` (inclusive). A policy is
  **in force** on a date when `Effective_Date <= date <= Expiration_Date`. A policy term can
  span several years.
- `policy.Status_Code` is empty for every policy, so there is no recorded status (active,
  cancelled, lapsed). Decide "in force" from the dates only, and say so.
- A policy is an **agreement**. `Policy_Identifier` is the agreement identifier used in
  `agreement_party_role.Agreement_Identifier` and `agreement_assessment.Agreement_Identifier`.
  In the `agreement` view the identifier column is mislabeled `Agreement_Type_Code`; it is not a
  type code. `agreement` adds only `Agreement_Name` ("Policy <number>").

## Parties and roles

- A **party** is anyone the company deals with (`party.Party_Identifier`). A party is either a
  **person** (`person.Person_Identifier = Party_Identifier`) or an **organization**
  (`organizations.Organization_Identifier = Party_Identifier`). `party` itself has no name;
  take names from `person` (`First_Name`, `Middle_Name`, `Last_Name`) or
  `organizations.Organization_Name`.
- A **person's name** is First_Name + ' ' + Last_Name (add Middle_Name only when asked for the
  full name). Most person rows have empty names; only people who play a role have names.
- Role codes (`party_role`): `PH` = PolicyHolder, `AG` = Agent, `UW` = Underwriter.

| Business role | Where it is recorded | Rule |
| --- | --- | --- |
| **Policy holder** (insured, policyholder) | `agreement_party_role` | `Party_Role_Code = 'PH'` and `Agreement_Identifier = policy.Policy_Identifier` |
| **Agent** (the party who sold the policy) | `agreement_party_role` | `Party_Role_Code = 'AG'` and `Agreement_Identifier = policy.Policy_Identifier` |
| **Underwriter** | `assesment_party_role` (note the spelling) | `Party_Role_Code = 'UW'`; reaches a policy only through `agreement_assessment` |

- The **Policy Holder ID**, **Agent ID** and **Underwriter ID** are the party's `Party_Identifier`.
- The same party can hold or sell several policies. `agreement_party_role` has one row per
  policy, party and role, so **always filter `Party_Role_Code` before joining it to policy
  data**, otherwise every policy row is repeated once per role and amounts are double counted.
- Role dates (`Effective_Date`/`Expiration_Date` on `agreement_party_role`, `Begin_Date`/`End_Date`
  on `assesment_party_role`) are empty. There is no history of role changes.
- The only organization is the insurer, Mesa Underwriters Specialty Insurance Company (acronym
  MUSIC). It has no role row on any policy.

## Join paths

- Policy -> holder name: `policy` -> `agreement_party_role` (PH) on
  `Agreement_Identifier = Policy_Identifier` -> `person` on `Person_Identifier = Party_Identifier`.
- Policy -> agent name: same path with `Party_Role_Code = 'AG'`.
- Policy -> underwriter: `policy` -> `agreement_assessment` (`Agreement_Identifier = Policy_Identifier`)
  -> `assessment` -> `assesment_party_role` (`Assessment_Identifier`, `Party_Role_Code = 'UW'`)
  -> `person`.
- Party -> claims: a party is connected to claims only through its policies (policy ->
  policy_coverage_detail -> claim_coverage -> claim). There is no claimant role in the data.

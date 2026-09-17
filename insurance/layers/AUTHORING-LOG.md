# Authoring log: insurance L1 (modeling) and L3 (skills)

Author: a fresh Claude agent (Claude Opus 5, Claude Code) that had not seen the benchmark
questions or answers. No Ask / `dql agent ask` / `dql agent eval` / AI question answering was
used, and no test questions were invented or tuned against.

- Start: 2026-09-17 01:53:31 UTC
- End: 2026-09-17 02:04:00 UTC
- Total: about 11 minutes (01:53:31 to 02:04:00 UTC)

## Files written

| Layer | File (paths as they sit in a DQL project) |
| --- | --- |
| L1 | `insurance/layers/L1/domains/insurance/domain.dql` |
| L1 | `insurance/layers/L1/domains/insurance/modeling/areas/policies.dql.yaml` |
| L1 | `insurance/layers/L1/domains/insurance/modeling/areas/claims.dql.yaml` |
| L1 | `insurance/layers/L1/domains/insurance/modeling/areas/underwriting.dql.yaml` |
| L1 | `insurance/layers/L1/domains/insurance/modeling/areas/locations.dql.yaml` |
| L1 | `insurance/layers/L1/domains/insurance/modeling/areas/fire_claims.dql.yaml` |
| L1 | `insurance/layers/L1/domains/insurance/modeling/concepts.dql.yaml` |
| L3 | `insurance/layers/L3/skills/insurance-policies-and-parties.skill.md` |
| L3 | `insurance/layers/L3/skills/insurance-coverage-and-premium.skill.md` |
| L3 | `insurance/layers/L3/skills/insurance-claims-reserves-payments.skill.md` |
| L3 | `insurance/layers/L3/skills/insurance-locations.skill.md` |
| L3 | `insurance/layers/L3/skills/insurance-data-coverage.skill.md` |
| - | `insurance/unanswerable.json` (15 questions) |
| - | `insurance/layers/AUTHORING-LOG.md` (this file) |

The starter skills `dql init` wrote (`skills/block-authoring`, `domain-rules`,
`metrics-glossary`, `sql-conventions`) were left unchanged and are not part of L3.

## Files read

Benchmark side (only what AUTHORING.md allows):
- `dql-benchmarks/insurance/layers/AUTHORING.md`
- `work/insurance/authoring/docs/ACME_small.ddl`
- `work/insurance/authoring/docs/insurance.ttl`
- `work/insurance/authoring/docs/data.world_P&C_Insurance_Ontology_V1.r2rml` (whole file; the
  SQL queries, class and predicate lists extracted with grep)
- `work/insurance/authoring/project/`: `dql.config.json`, `dbt_project.yml`, `profiles.yml`,
  all 29 `models/omg_models/*.sql`, the four starter `skills/*.skill.md`, the header lines of
  `ACME_Insurance/data/Agreement.csv`, `FireClaim.csv`, `Policy_Amount.csv`,
  `target/manifest.json` and `target/catalog.json` (model unique ids, relation names, column
  types only), plus a file listing of the project.
- No file under `data/`, `work/insurance/gold`, `runs`, `projects`, `insurance/*.json(l)`,
  `insurance/*.mjs`, `REPORT.md`, `results/`, other `*.ttl`, or any `investigation` /
  `hex_notebook` folder was opened or searched. No web search. No benchmark question or answer
  was seen in any tool output.

DQL side (worktree `dql-agentic-query-construction-d182f3`, read only):
- `docs/reference/project-layout.md`, `docs/reference/file-formats.md`,
  `docs/rfcs/0002-dbt-first-domain-modeling.md`,
  `docs/specs/dql-2-domain-context/04-domain-modeling-and-governance.md`,
  `docs/reference/cli.md` (model commands)
- `packages/dql-core/src/manifest/dbt-first-modeling.ts` (entity/relationship/concept/area
  parsing, certification and validation-proof rules)
- `packages/dql-core/src/manifest/knowledge-skills.ts` (skill frontmatter)
- `packages/dql-core/src/manifest/domain-package-registry.ts`, `domain-writer.ts` (domain.dql fields)
- `packages/dql-agent/src/relationship-validation.ts` (the Domain Studio "Validate" proof)
- `packages/dql-agent/src/skills/loader.ts` (skill kinds)
- `apps/cli/src/commands/model.ts`, parts of `apps/cli/src/local-runtime.ts` (validate route, identifier quoting)
- Fixtures: `apps/cli/test/fixtures/dbt-first-commerce/domains/commerce/{domain.dql,modeling/model.dql.yaml,skills/revenue-reporting.skill.md}`,
  `nba-golden/domains/nba/{domain.dql,modeling/areas/core.dql.yaml}`,
  `jaffle-golden/domains/commerce/{domain.dql,skills/customer-profile.skill.md}`,
  `ask-observability-office/domains/revenue_operations/skills/fiscal-revenue.skill.md`

## SQL run to understand the data (read-only DuckDB, summarised)

1. `information_schema.tables/columns` for every relation, with `count(*)` per relation
   (29 views in `main`, seeds in `main__seed`; all tables have 1 to 30 rows except
   `fire_claim` with 820).
2. `SELECT *` of every small view (all except `fire_claim`) to see keys, code values and
   which columns are empty.
3. `SUMMARIZE fire_claim`; distinct counts of `PolicyNo`/`ClaimNumber` (all NULL); joins of
   `fire_claim` to `policy.Policy_Number` and `claim.Company_Claim_Number` (0 rows);
   `Fireplace` value counts; `Loss_Ratio` range.
4. For each entity, row count vs distinct count of the declared key and null-key count
   (all keys unique and non-null).
5. `policy` joined to `agreement` on `Agreement_Type_Code = Policy_Identifier` and
   `Agreement_Name = 'Policy ' || Policy_Number` (2 of 2 rows match).
6. party / person / agreement_party_role for parties 1-3 and 100 (names match roles:
   Mary Policy Holder = PH, Bob Insurance Agent = AG, Alice Under Writer = UW; 100 = insurer).
7. `policy_amount` vs `policy_coverage_detail` effective dates (always equal);
   `Amount_Type_Code` null vs 'Year' counts (6 / 6).
8. Date ranges: claim open dates 2019-01-15 to 2019-06-02; coverage periods 2015-01-01 to
   2020-05-31; distinct role codes PH, AG, UW.
9. Column-name search over `information_schema.columns` for concepts used in unanswerable.json
   (commission, subrogation, reinsurance, billing, credit, vehicle, roof, fraud, adjuster,
   broker, product, campaign, email, phone): none present except the empty
   `agreement.Product_Identifier`.
10. DQL's own relationship validation statement (from `relationship-validation.ts`) for all
    36 relationships, executed read-only through DuckDB (see below).

## Decisions

- **One domain `insurance`**, split into five Model Areas (policies, claims, underwriting,
  locations, fire_claims) so each is reviewable; concepts in a separate
  `modeling/concepts.dql.yaml`. Areas carry no `intent_examples`, to avoid writing anything
  that looks like a test question.
- **Entities**: all 29 dbt models are bound (ids are business names: `occurrence` for
  `occurrences`, `organization` for `organizations`, `physical_location` for
  `pysical_location`, `assessment_party_role` for `assesment_party_role`). Grain and keys follow
  the DDL primary keys where the DDL has them; otherwise the OMG convention (`<Table>_Identifier`)
  confirmed unique in the data.
- **agreement_party_role key**: the DDL key includes `Effective_Date`, which is NULL in every
  row, so the declared key is (Agreement_Identifier, Party_Identifier, Party_Role_Code), which
  is unique in the data.
- **agreement's key**: the `agreement` dbt model has no `Agreement_Identifier`; the seed CSV
  header names its first column `Agreement_Type_Code` (and repeats that name), but the column
  holds the agreement id. The entity uses `Agreement_Type_Code` as key with a warning in its
  business context, and `policy_to_agreement` stays **draft** (data-proven, but it would
  certify a mislabeled column; fixing the dbt model is the right step and was out of scope).
- **Parties to policies through roles**: `agreement_party_role` is a bridge;
  certified many-to-one edges to `policy` (Agreement_Identifier = Policy_Identifier, as in the
  r2rml Agent/PolicyHolder mappings), `party` and `party_role`. Underwriters reach policies via
  `assesment_party_role` -> `assessment` <- `agreement_assessment` -> `policy` (r2rml
  hasUnderwriter / underwritesPolicy). `person` and `organizations` are certified one-to-one
  subtypes of `party`.
- **Amount specializations**: `premium` -> `policy_amount` and `loss_payment`,
  `loss_reserve`, `expense_payment`, `expense_reserve` -> `claim_amount`, plus
  `underwriting_assessment` -> `assessment_result`, are certified `one_to_one`, fanout safe,
  `join_types: [inner]`, and also expressed as business concepts with one-to-one
  equivalences (which compile into conformance declarations).
- **Composite joins**: `claim_coverage` and `policy_amount` join `policy_coverage_detail` on
  both `Effective_Date` and `Policy_Coverage_Detail_Identifier`, as the DDL foreign keys say.
- **Certified joins (31)**: only where the key is declared by the DDL/ontology mapping or is
  the OMG subtype convention, and the warehouse proof passed with zero null keys, zero
  unmatched rows and max one row per key on the "one" side.
- **Draft joins (5)**: `policy_to_agreement` (above) and the DDL foreign keys whose key
  columns are NULL in every row: `policy_to_geographic_location`,
  `policy_amount_to_geographic_location`, `policy_amount_to_insurable_object`,
  `occurrence_to_geographic_location`. (DQL's validation reports "passed" for these because
  a NULL key never multiplies rows, but joined_rows is 0, so nothing is proven.) Not modeled:
  the `geographic_location` parent self-reference (all NULL).
- **fire_claim**: bound as an entity with no grain or keys and no relationships, because its
  only identifying columns (PolicyNo, ClaimNumber, InsuredLocation) are NULL in every row.
- **Validation evidence**: generated with DQL's own `validateRelationshipOnWarehouse` +
  `catalogKeyTypes` (the same code Domain Studio's Validate button runs), via a scratchpad
  Node script that imports the built `dql-core`/`dql-agent` dist files and executes the SQL
  through the benchmark venv's DuckDB (read-only), with DuckDB double-quote identifier
  quoting. The script wrote each `validation:` block into the YAML. Evidence `checked_at` is
  2026-09-17 ~01:59 UTC; no `evidence_expires_at` is set.
- **Owner**: `insurance-analytics@acme-insurance.test` (a team placeholder).
- **L3 location**: the skills are in the project-level `skills/` folder (the configured
  `layout.skillsPath`) without a `domain` field, so they load as global skills whether or not
  the L1 domain package is present. Putting them under `domains/insurance/skills/` would make
  them load only together with L1. Kinds: `domain_reference`, `metric_policy` (2),
  `glossary`, `sql_policy`. No `examples`, `preferred_blocks`, `preferred_metrics` or
  `vocabulary` (there are no certified blocks or semantic metrics to point to).
- **Skill content**: definitions come from the ontology (Policy Holder, Agent, Underwriter,
  Premium Amount / Monthly = yearly / 12 / Period, the four claim amount kinds, Location
  attributes) and the r2rml SQL (role codes PH/AG/UW, subtype joins). Industry-convention
  measures (total paid, total reserves, incurred loss, loss ratio) are labeled as conventions
  and must be stated when used. Data facts (empty columns, date-only status, unlabeled
  non-premium policy amounts, fire_claim being unlinked) are written down so answers do not
  invent them.
- **unanswerable.json**: 4 missing measures (commission, subrogation, ceded reinsurance,
  unpaid premium balance), 4 missing attributes (credit score, vehicle make/model, building
  size/roof, fraud/denial), 3 missing time periods/grains (claims opened in 2023, premium for
  2012, quarterly reserve history), 4 missing entities (adjuster, agency/sales office,
  product line, marketing campaign). Each was checked against the DDL, ontology and warehouse
  columns. Questions about columns that exist but are empty (for example birth date, gender)
  were avoided, since the concept is in the schema.

## `dql model discover`

Run on the untouched project (`model discover` and `--format json`). It proposed one domain,
`omg_models` ("Omg Models"), containing all 29 models, confidence low (0.55), from the model
path only; no relationship candidates ("Relationships declared in dbt tests: none found"),
no unassigned models, and one review-only skill draft `omg_models_analyst`. Used only as a
check that all 29 models belong together; the domain was named `insurance` instead and
nothing was applied (`apply-discovery` was not run).

## Validation output

`model validate` and `model list` were run from `work/insurance/authoring/project/` with the
L1 files copied in (and the L3 skills copied into `skills/`). First run (before evidence):
valid, 29 entities, 36 relationships, 0 errors, and for each of the 31 certified relationships
two warnings ("has no passed warehouse validation evidence", "validation proof no longer
matches"). After the evidence was written:

```
DQL dbt-first modeling: valid
  29 entities, 36 relationships
```

`--format json`: `valid: true`, 0 diagnostics. `model explain` on
`insurance::relationship::agreement_party_role_to_policy` and `premium_is_policy_amount`:
"automatic join allowed"; on `policy_to_agreement`: "not automatic join proof" (draft).
The compiled manifest has 5 model areas, 12 concepts and 8 derived conformance declarations.
All five L3 skills load through `loadManifestKnowledgeSkills` and the agent's `loadSkills`
with no diagnostics (`global::skill::insurance-*`). The only compile warnings are
pre-existing / expected: a "Customer" domain used by an example block/term outside these
layers, and "domain Insurance has no terms, blocks, or business views yet".

Warehouse proof per certified relationship (from_rows / to_rows / joined / unmatched /
max rows per key on the to side): every one has 0 null keys, 0 unmatched rows and
max_to_per_key = 1 (one-to-one edges also max_from_per_key = 1). Examples:
agreement_party_role_to_policy 4/2/4/0/1; claim_amount_to_claim 8/2/8/0/1;
premium_is_policy_amount 6/12/6/0/1; policy_amount_to_policy_coverage_detail 12/6/12/0/1;
person_is_party 29/30/29/0/1.

After checking, the copied files were removed from `work/insurance/authoring/project/`
(`domains/insurance/` and `skills/insurance-*.skill.md`), leaving the L0 project as it was.
No dbt model, seed or warehouse was changed. Nothing was committed.

## What DQL's format could not express

- **Role-filtered relationships**: "policy holder" and "agent" are `agreement_party_role`
  rows filtered on `Party_Role_Code`. A relationship cannot carry a filter, so the filter lives
  in the relationship description, the concepts and the skills; there is no separate
  certified "policy -> policy holder" edge.
- **Subtype / specialization**: there is no "is-a" relationship kind. Specializations are
  one-to-one certified relationships with `join_types: [inner]` plus concept equivalences.
- **Mislabeled key column**: an entity cannot rename a dbt column, so the agreement key has
  to be `Agreement_Type_Code`; the right fix is in the dbt model.
- **Entity without a key** (`fire_claim`): allowed, but it cannot take part in any proven join.
- **Proof of an all-NULL foreign key**: DQL's validation passes such a join (no fanout), so
  these were kept draft by judgment rather than by the validator.
- **Metric definitions** (premium, monthly premium, incurred loss): there is no semantic layer
  in this project, so they are written as skill text, not as governed metrics.

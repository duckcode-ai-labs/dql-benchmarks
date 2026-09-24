# Human certification of layer B blocks

The nine standard-report blocks were written by the author agent and checked by the independent verifier agent (VERIFICATION.md). The project owner reviewed and certified all nine in the DQL Workbench (Block Studio certification: validation, query, tests, chart and lineage gates), on a separate review copy of the LB project, never in a benchmark project.

Certification changed only each block's `status` (draft → certified) and added the Workbench tag `app-source`; the file was renamed to the Workbench's slug. No SQL, definition or description changed.

| Block | Before (v2) | Certified file (v3) | Certified at |
|---|---|---|---|
| Book of Business by Agent and Policy Holder | `book_of_business_by_agent_and_holder.dql` | `book-of-business-by-agent-and-policy-holder.dql` | 2026-09-23T22:29:18-05:00 |
| Claim Financials by Claim | `claim_financials_by_claim.dql` | `claim-financials-by-claim.dql` | 2026-09-23T22:29:24-05:00 |
| Claims and Losses by Catastrophe | `claims_and_losses_by_catastrophe.dql` | `claims-and-losses-by-catastrophe.dql` | 2026-09-23T22:29:29-05:00 |
| Claims Register | `claims_register.dql` | `claims-register.dql` | 2026-09-23T22:29:32-05:00 |
| Fire Risk Sample Loss Ratio by Fireplace | `fire_risk_loss_ratio_by_fireplace.dql` | `fire-risk-sample-loss-ratio-by-fireplace.dql` | 2026-09-23T22:29:38-05:00 |
| Loss Ratio by Policy and Coverage Year | `loss_ratio_by_policy_and_coverage_year.dql` | `loss-ratio-by-policy-and-coverage-year.dql` | 2026-09-23T22:29:40-05:00 |
| Loss Ratio Summary | `loss_ratio_summary.dql` | `loss-ratio-summary.dql` | 2026-09-23T22:29:44-05:00 |
| Underwriting Activity | `underwriting_activity.dql` | `underwriting-activity.dql` | 2026-09-23T22:29:12-05:00 |
| Written Premium by Policy and Coverage Year | `written_premium_by_policy_and_year.dql` | `written-premium-by-policy-and-coverage-year.dql` | 2026-09-23T22:29:48-05:00 |

Certified by: the project owner (DQL identity owner of the project). Results that use v3 are labelled **"blocks human-certified; metrics, modeling and skills AI-authored and independently AI-verified"**.

## v3.1 — the review-required tag removed (Sept 24 2026)

Certifying in Block Studio changed each block's status but kept the author's `review-required` tag; Ask reads certified beside review-required as a contradiction and served none of the nine blocks (runs fc1–fc2 therefore measured the layer without certified blocks). DQL now clears the tag when a block is certified (`claude/dql-benchmark-gaps` 61b868ac). v3.1 applies the same change to the nine blocks the owner certified; nothing else changed.

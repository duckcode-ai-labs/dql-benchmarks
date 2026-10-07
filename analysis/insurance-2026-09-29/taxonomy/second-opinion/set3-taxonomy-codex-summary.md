# Set 3 taxonomy review

Reviewed all 26 rows in order against the isolated local warehouse on 2026-10-06. This is Codex's second opinion, not the human reviewer's verdicts.

## Counts

| Review group | Agree | Disagree | Unsure |
|---|---:|---:|---:|
| Root cause (items 1–7) | 7 | 0 | 0 |
| Lenient-only (items 8–26) | 19 | 0 | 0 |
| Total | 26 | 0 | 0 |

Twenty-three agreements have high confidence; items 1, 6, and 7 have medium confidence. All 26 were checked with local SQL.

Counts using each exact sheet part:

| Part | Agree | Disagree | Unsure |
|---|---:|---:|---:|
| 6.8 root cause | 7 | 0 | 0 |
| 6.8 lenient-only (Claude Opus 5.5, L1) | 1 | 0 | 0 |
| 6.8 lenient-only (Claude Opus 5.5, LB) | 1 | 0 | 0 |
| 6.8 lenient-only (Claude Sonnet 5.5, P) | 1 | 0 | 0 |
| 6.8 lenient-only (Claude Sonnet 5, L1) | 1 | 0 | 0 |
| 6.8 lenient-only (Claude Sonnet 5, L3) | 1 | 0 | 0 |
| 6.8 lenient-only (Claude Sonnet 5, LB) | 1 | 0 | 0 |
| 6.8 lenient-only (Qwen 3.8 27B (local), P) | 1 | 0 | 0 |
| 6.8 lenient-only (Qwen 3.8 27B (local), L1) | 1 | 0 | 0 |
| 6.8 lenient-only (Qwen 3.8 27B (local), L2) | 1 | 0 | 0 |
| 6.8 lenient-only (Claude Sonnet 5.5, L3) | 1 | 0 | 0 |
| 6.8 lenient-only (Claude Sonnet 5.5, L1) | 1 | 0 | 0 |
| 6.8 lenient-only (GPT-6 Sol (medium), L2) | 1 | 0 | 0 |
| 6.8 lenient-only (GPT-6 Sol (medium), W2) | 1 | 0 | 0 |
| 6.8 lenient-only (GPT-6 Sol (medium), P) | 2 | 0 | 0 |
| 6.8 lenient-only (Claude Sonnet 5.5, W1) | 1 | 0 | 0 |
| 6.8 lenient-only (GPT-5.6 Terra (high), L2) | 2 | 0 | 0 |
| 6.8 lenient-only (Claude Opus 5.5, L2) | 1 | 0 | 0 |

## Every row other than agree with high confidence

| Item | Verdict | Your classification | Reason |
|---|---|---|---|
| 1 | agree, medium | — | NULL-versus-98000 source mismatch is reproduced; definition attribution depends on the supplied metric description and import evidence. |
| 6 | agree, medium | — | The displayed percentage is 100 times too small; supplied answer SQL omits the derived column, limiting independent pipeline-stage attribution. |
| 7 | agree, medium | — | The paid-share percentage is a fraction; the derived step is described in evidence but absent from supplied answer SQL. |

No disagreement or unsure verdict was recorded. An empty your_classification field means agreement, not absence of a category.

## Worked example 1: root cause — item 3

**Question:** Look for the requested calculation and shape: one compound annual growth rate for a specific policy, over the years between first and last term starts. It is not asking for a premium history.

**Reference:** One value, 0.07456993182354199. The endpoints are 15000 on 2015-01-01 and 20000 on 2019-01-01, four years apart. The calculation is (20000 / 15000)^(1 / 4) − 1.

**Answer:** Five annual rows: 15000, 16000, 17000, 18000, 20000. Those inputs are correct, but the requested rate is absent.

**Verdict:** Agree with **route**. A trusted path returned a useful sub-answer without completing the question. Correct inputs do not make a missing requested calculation acceptable. The supplied reader evidence also says CAGR could not be expressed. The local replay establishes the incomplete result; it does not independently verify other runs' counts or archived traces.

## Worked example 2: harmless equivalent label — item 17

**Question:** Four mileage bands, with count and mean loss ratio in each.

**Reference:** The fourth group is labeled “more than 15 miles,” containing 170 records with mean 0.8582352941176468.

**Answer:** The same group is labeled “More than 15 miles,” with exactly those values. All other groups match: counts 335, 164, and 151, with matching means.

**Verdict:** Agree with **harmless (equivalent label)**. Capitalizing the first letter does not change the range or hide which group the values describe. The preview showed only three groups; replaying the SQL was essential to check the changed fourth label.

## Worked example 3: identity lost — item 12

**Question:** The policyholder's **first and last name**, together with premium total, term count, and mean premium per term.

**Reference:** Mary | Holder | 98000 | 6 | 16333.333333333334.

**Answer:** party_identifier 1 | party_name NULL | 98000 | 6 | 16333.333333333334.

**Verdict:** Agree with **identity lost**. The numeric statistics match, but the person expressly requested cannot be named from the delivered result. A reviewer can recover Mary Holder by querying the database; that does not mean the business user received the requested name.

## How to apply the categories consistently

- First identify the requested entity, grain, calculation, and units; compare what the result delivers before consulting the AI label.
- An accurately labeled internal key can preserve identity when the question merely asks “for each claim/policy” (items 18, 21, 26). When the question expressly asks for a business number or person name, omitting it loses requested identity (9, 10, 12, 13, 16).
- Keys deceptively named policy_number or claim_number also change a column's meaning (8, 11, 14). These overlap with identity lost; the AI's different-meaning primary category is defensible because the label asserts the wrong business identifier. Do not double-count them.
- UW is a role; OK is an assessment outcome (15). Correct days do not make those interchangeable.
- Combining Alice and Writer in one name column preserves both requested name components (23).
- Percentage scaling is substantive: item 6 needs 109.090909... and 104.545454..., not 1.090909... and 1.045454.... Item 7 needs 53.030303..., not 0.530303....
- Raw distances instead of bands, annual years instead of decades, or input series instead of one requested rate are incomplete trusted answers, not harmless labeling changes.

## Evidence limits

All supplied SQL was replayed read-only. Full results, including omitted fourth bands, were checked. Items 6 and 7 have a mismatch between the shown final result schema and the supplied answer SQL: the SQL returns the base metrics but does not return the derived ratio column. The supplied evidence attributes that calculation to a later derived step. Compilation is a supported classification conditional on that account; distinguishing it conclusively from reading-to-intent scale loss requires the actual intent/derived-step trace.

For item 1, the bad selected source is directly reproduced, but the metric definition/import provenance is supplied text rather than an independently accessible artifact. The same limit applies to historical run counts and quoted diagnostics throughout. No repository or other notes were opened to resolve those claims.

Only the requested CSV and this summary were written. The human reviewer should use these public worked examples to learn the method and then form independent verdicts.

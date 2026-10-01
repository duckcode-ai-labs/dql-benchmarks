# Auditing the reference answers of sealed set 4

The sealed questions and their reference SQL were written by an AI agent. Before the paper is posted, a
person (not the AI that ran the benchmark) checks a random sample of them. This file explains how.

## What you received

`set4-audit-sample.csv`: 120 rows, open it in Google Sheets or Excel.

- **100 answerable items**, 25 from each complexity quadrant, picked at random (seed 20260930).
  Each row has the question, the reference SQL and the first rows of its result.
- **20 unanswerable items**: questions the data should not be able to answer, each with the reason.

Please do not share the file: the questions stay sealed until the paper is published.

## What to decide for each row

Fill the column **VERDICT** with one of:

- **correct**: the reference SQL answers the question as a reasonable insurance analyst would read it.
- **wrong**: the SQL answers a different question, uses the wrong table or join, the wrong filter, the
  wrong grain (for example one total where the question asks for a list), or computes the number wrongly.
- **ambiguous**: the question has more than one fair reading and the reference picks one of them.

For an unanswerable row, **correct** means the data really cannot answer it; **wrong** means it can
(say how in the next column).

Use the next column to say what is wrong or ambiguous. If you can, add corrected SQL. Add your name
and the date.

## How to check a query yourself (optional)

Run any SQL against a copy of the warehouse with DuckDB (read-only, so nothing can change):

```bash
cp work/insurance/projects/L0/acme_insurance.duckdb /tmp/acme_insurance.duckdb   # from the repository root, after building the projects (insurance/README.md)
duckdb -readonly /tmp/acme_insurance.duckdb
```

Then paste the reference SQL at the `D` prompt. `.tables` lists the tables and `DESCRIBE main.claim;`
shows a table's columns.

## Useful facts about the data

- 2 policies, 2 claims (both linked to the Fire catastrophe), one named policy holder and one named agent.
- Money on a claim is in `claim_amount`; which kind it is (loss payment, loss reserve, expense payment,
  expense reserve) comes only from which of those four tables holds its `Claim_Amount_Identifier`.
- People reach policies through `agreement_party_role` (role code `PH` = policy holder, `AG` = agent).
- `fire_claim` has 820 rows but cannot be joined to policies or claims.

## When you are done

Save the sheet and return it. The paper reports the share of correct, wrong and ambiguous items with a
95% interval, and re-scores the benchmark without any item found wrong.

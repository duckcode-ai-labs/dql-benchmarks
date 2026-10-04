# Auditing the reference answers of sealed sets 4 and 5

The sealed questions and their reference SQL were written by an AI agent. Before the paper is posted, a
person (not the AI that ran the benchmark) checks a random sample of them. This file explains how.

## What you received

Two sheets, the same layout; open them in Google Sheets or Excel:

- `set4-audit-sample.csv`: 120 rows: **100 answerable items**, 25 from each complexity quadrant, picked
  at random (seed 20260930), and **20 unanswerable items**.
- `set5-audit-sample.csv`: 63 rows, the pre-registered 25% sample of set 5: **50 answerable items**
  (13, 13, 12, 12 per quadrant; seed 20261001) and **13 unanswerable items**.

Each answerable row has the question, the reference SQL and the first rows of its result; each
unanswerable row has the question and why the data should not answer it.

Please do not share the files: the questions stay sealed until their release. DQL was frozen for set 5
before this sheet was made (`insurance/FREEZE-SET5.md`); nothing in DQL may change because of what you
read in either sheet.

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

## A second, separate review: the set-5 questions where W2 and A-model disagree

`work/insurance/audit/set5-discordant-review.csv` (made by `insurance/audit/make_discordant_sheet.py`,
after set 5 was scored) lists every answerable set-5 question where exactly one of DQL W2 and A-model
returned the reference rows: 34 questions. It judges the answers, not the reference. It is reported
separately from the reference audit above, as a post-hoc analysis of the primary result.

The two answers appear as **Answer 1** and **Answer 2** in a random order, so you do not know which is
DQL's. Judge each from its result rows against the question and the reference result:

- **acceptable**: a business reader who asked this question would accept this result as the answer: the
  numbers are right and each is attached to an identifiable entity, period or group as asked. A different
  but equivalent label (a name where the reference shows an id) is acceptable.
- **not acceptable**: wrong numbers, a different grain or shape (a total where a list was asked), the
  entity a number belongs to cannot be identified, or it answers a different question.
- **unsure**: you cannot decide from what is shown; say why.

Then say which answer is better (1, 2 or same) and why. The SQL columns at the right are optional: their
style may reveal which system wrote them, so read them only when the rows alone do not settle it.
`set5-discordant-key.json` says which answer is which; open it only after every verdict is written.

# Review: why trusted answers were wrong, and what a lenient grade forgives (public set 3)

You are an independent reviewer for a research paper. Accuracy matters more than speed. A person will
do the same review after you and compare; your output is a second opinion, not the final word.

## Background

The paper evaluates DQL, a system that answers business questions about an insurance data warehouse
with SQL. DQL labels each answer: **governed** (computed from approved metric definitions) or
**certified** means "you can trust this without checking"; **review required** means "drafted SQL,
check it". Answers are graded against a reference result (the rows of a reference SQL query):

- **strict grade:** the answer's rows must equal the reference rows (column names and order ignored;
  extra columns allowed);
- **lenient grade:** also accepts an answer with the right numbers when a label column is missing,
  substituted or formatted differently (for example an internal id instead of the policy number).

An AI assistant classified two kinds of answers on question set 3 (public). You check its work.

## What is in this folder

- `taxonomy-review-sheet.csv`, 26 rows. Columns: `item`, `part`, `question (set 3, public)`,
  `AI classification`, `AI evidence`, `reference SQL`, `answer SQL`, `reference rows (first 5)`,
  `answer rows (first 5)`, then blank reviewer columns (ignore them).
  - Rows whose `part` is "6.8 root cause" (7 rows): one wrong **trusted** answer per root-cause group.
  - Rows whose `part` is "6.8 lenient-only (model, condition)" (19 rows): answers the strict grade
    marks wrong and the lenient grade marks right. (The paper's section is now numbered 6.9.)
- `wh/acme_insurance.duckdb`: the warehouse, to check anything you need. Open it read-only:
  `duckdb -readonly wh/acme_insurance.duckdb` (`.tables`, `DESCRIBE main.claim;`, `.quit`), or in Python
  `duckdb.connect('wh/acme_insurance.duckdb', read_only=True)`. Keep the file name.
- Both files are write-protected on purpose.

## Rules

1. Work only in this folder; do not open or search anything outside it, and use no other project,
   notes or memory.
2. Change nothing; write only the two output files below.
3. Do not search the web. Run SQL only against the local file.
4. Review every row, in order, and save each to the output file as you finish it.

## The categories the AI used

**Root cause of a wrong trusted answer** (rows 1-7):

- *definition*: the governed metric itself computes the wrong thing;
- *reading*: DQL read the question wrong while the definition was fine;
- *route*: a trusted route answered although it did not cover the whole question (for example it
  returned the inputs of a growth rate but not the rate);
- *compilation*: definition and reading right, the generated result wrong (for example "as a
  percentage" returned as a fraction);
- *execution*: right SQL, wrong rows at run time;
- *reference*: the reference itself is wrong, or the question is ambiguous.

**Kind of a lenient-only answer** (rows 8-26):

- *harmless (equivalent label)*: the numbers are right and every number is still attached to an
  identifiable entity; the label differs (a key instead of a number, different letter case, a name
  format), but a business reader loses nothing the question asked for;
- *identity lost*: the question names an identifier or a person (for example "the policy number",
  "the policy holder's name") and the answer gives an internal key or NULL instead, so the reader
  cannot tell which policy or person a number belongs to;
- *different meaning despite matching numbers*: a column means something other than its name or the
  question asks for, or the numbers match only by coincidence on this data.

## How to review each row

1. Read the question as a business user would.
2. Compare the reference rows and the answer rows (and run the SQL on the warehouse if the first five
   rows are not enough).
3. Read the AI's classification and evidence. Is the classification right? Is the evidence true?
4. Give a verdict:
   - **agree**: the classification is right and the evidence supports it;
   - **disagree**: another category fits better; name it and say why;
   - **unsure**: you cannot decide; say what would settle it.

## What to write

1. `set3-taxonomy-codex-review.csv`, one row per sheet row (all 26), with the columns
   `item, part, verdict, your_classification, reason, confidence, checked_with_sql, notes`:
   `verdict` agree / disagree / unsure; `your_classification` only when you disagree, using the category
   names above; `reason` one or two plain sentences a non-expert can follow; `confidence` high / medium /
   low; `checked_with_sql` yes / no. Use proper CSV quoting.
2. `set3-taxonomy-codex-summary.md`: counts of agree / disagree / unsure for each part; a table of every
   row that is not "agree, high confidence" (item, verdict, your classification, one-line reason); and,
   for three rows of your choice (one root-cause row, one harmless row, one identity-lost row), a short
   worked explanation written for a person doing this review for the first time: what to look at in the
   question, in the reference rows and in the answer rows, and how that leads to the verdict.

When you are done, reply with the counts and the list of rows you did not agree with.

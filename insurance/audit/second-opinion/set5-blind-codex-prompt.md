# Blind review: which answers would a business user accept? (34 questions)

You are an independent reviewer for a research paper. Accuracy matters more than speed. A person will
do the same review separately; your output is a second opinion, not the final word.

## Background

Two systems answered the same 200 business questions about an insurance data warehouse with SQL. Each
answer is graded against a reference result (the rows of a reference SQL query) by a **strict** rule:
the answer's rows must equal the reference rows (column names and order ignored; extra columns allowed).
Under a **lenient** rule that also accepts the right numbers with a missing or different label column
(for example an internal id instead of the policy number), the two systems scored the same; under the
strict rule one scored 14 questions more. The question is whether those strict differences matter to a
person who asked the question.

This folder holds the 34 questions on which exactly one of the two answers passed the strict rule. You
do not know which system gave which answer, and you must not try to find out: judge each answer on what
it returns.

## What is in this folder

- `set5-discordant-review.csv`, 34 rows. Columns: `item`, `question`, `reference result`,
  `Answer 1 result`, `Answer 2 result` (each result: the column names, then up to 10 rows, then the row
  count), blank reviewer columns (ignore them), and at the right `Answer 1 SQL`, `Answer 2 SQL`,
  `reference SQL`.
- `wh-L0/acme_insurance.duckdb`: the warehouse the reference SQL ran on.
- `wh-W2/acme_insurance.duckdb`: the warehouse both answers ran on (same data).
  Open either read-only: `duckdb -readonly wh-W2/acme_insurance.duckdb`, or in Python
  `duckdb.connect('wh-W2/acme_insurance.duckdb', read_only=True)`. Keep the file names.
- Everything is write-protected on purpose.

## Rules

1. The questions are sealed (an unreleased test set). Work only in this folder; do not open, list or
   search anything outside it; do not search the web; do not paste question text or SQL anywhere.
2. Do not try to work out which system wrote which answer (from SQL style or otherwise); it must not
   affect your verdict. Judge from the result rows first; read the SQL only when the rows alone do not
   settle it.
3. Change nothing; write only the two output files below.
4. Review every row, in order, and save each to the output file as you finish it.

## How to judge each answer

Imagine the person who asked the question receives this result. Mark each answer:

- **acceptable**: they would accept it as the answer. The numbers are right, and each number is attached
  to the entity, period or group the question asks about. A different but equivalent label is fine (a
  name where the reference shows an id, a business number beside an internal key, different letter
  case or date format), and so are extra helpful columns and sensible rounding.
- **not acceptable**: wrong numbers; a different grain or shape (one total where a list was asked, or
  the reverse; rows per day where per year was asked); the question names an identifier or a person
  (for example "the policy number", "the agent's name") and the answer does not give it, so a number
  cannot be tied to what was asked; a column that means something other than the question asks; or it
  answers a different question.
- **unsure**: the result shown is not enough to decide; say what is missing.

Then say which answer is **better** for that person: `1`, `2` or `same`.

The reference result is the intended answer, but it is not perfect: if both answers are acceptable and
the reference is merely one of several fair forms, say so in `notes`. If you think the reference itself
is wrong, say so too; do not let that change how you judge the two answers against the question.

Check numbers that matter with SQL on the warehouse when the first rows do not settle it.

## What to write

1. `set5-blind-codex-review.csv`, one row per sheet row (all 34), with the columns
   `item, answer_1_verdict, answer_2_verdict, better, reason, confidence, checked_with_sql, notes`:
   verdicts acceptable / not acceptable / unsure; `better` 1 / 2 / same; `reason` one or two plain
   sentences naming what decided it (for example "Answer 1 lists internal ids where the question asks for
   the policy number"); `confidence` high / medium / low; `checked_with_sql` yes / no. Use proper CSV
   quoting.
2. `set5-blind-codex-summary.md`: how many answers you judged acceptable, not acceptable and unsure
   (Answer 1 and Answer 2 separately, and together); how many rows had both answers acceptable, exactly
   one acceptable, or neither; the patterns that recur (for example "id instead of the named
   identifier", "fraction instead of percentage", "different grain"); and every row you marked unsure or
   low confidence, with one line on why.

When you are done, reply with those counts and patterns only.

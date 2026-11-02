# WideWorldImporters benchmark: design

Written and committed on 2026-11-02, before any scored question was asked.

## Question

How does ZLens's Ask score on NVIDIA's own 41-question WideWorldImporters set,
against NVIDIA's schema-only control, under NVIDIA's own grader?

This is not a comparison with Auto Ontology. Auto Ontology is not run here.

## Data

- Questions, gold SQL, custom analyses and seed: NVIDIA/ontology-sql-eval at
  a7f95e358a4dba79cc168f933c9081f971f2968b, `datasets/wideworldimporters`.
  `evaluation.json` sha256 starts ec01b149754146bb.
- 39 of 41 gold queries run. q4 and q27 are broken gold, so by NVIDIA's rule they
  leave the denominator and are not asked of ZLens. 4 gold results are empty, so
  every score is also given on the 35 non-empty questions.
- Postgres 16, local, seeded in NVIDIA's order. All answers run as a read-only role.

## Arms

All use `claude-sonnet-5-5` through the `claude` command's login, with no effort
set, so all get the same default.

| Arm | What it gets |
|---|---|
| C | NVIDIA's control: its system prompt, the question and the 61 KB DDL dump. One shot, no tools |
| W0 | ZLens on a new project: connect, sync the schema. No modelling |
| W1a | W0 + ZLens's own model draft, unreviewed, on the default path |
| WM | One-domain draft; the 95 joins with a declared foreign key that passed on the warehouse, certified; NVIDIA's 19 custom analyses imported, 18 certified; value profile on |

Nothing in any arm is written by hand. WM stands in for a modelled project. It has
no glossary, metrics or descriptions written by a person, so it isn't a test of a
real human model.

ZLens arms get NVIDIA's projection line after each question, "Return exactly the
requested output fields and NO others.", because both NVIDIA arms get it.

ZLens build: main at the commit recorded in each report, unreleased.

## Scoring

- **Strict, the headline.** A port of `exec_match.py`: `set(gold) == set(pred)` on
  raw psycopg rows. The control's SQL comes through the same `extract_sql`, quirks
  included.
- **Form, a diagnostic.** Column order and extra columns ignored, numbers equal to
  1e-6. Never the headline.
- A ZLens answer counts only if ZLens ran it. A refusal or a clarifying question
  has no SQL, so it scores zero under this rule, and is reported on its own line.
  A drafted query that ZLens refused to run counts as a refusal.

## Passes and health

- Three passes per arm. Pass 1 is the headline, as pass@1, and passes 2 and 3
  measure stability. Each ZLens pass starts from a fresh copy of the project.
- NVIDIA's gate: no headline while more than 5% of an arm's answers are broken
  runs. Questions lost to a provider failure are re-asked. Wrong SQL and refusals
  are never re-asked.
- ZLens code isn't changed between arms or passes, and no fix goes in during the
  run. Bugs found are reported, not patched.

## Reading the result

- With 39 questions, a confidence interval is about ±15 points. Differences of a
  few questions are noise. McNemar's exact test is given against the control.
- If WM is well above W0 and W1a, modelling matters here and the first-draft work
  is worth designing. If W1a is about level with WM, the mechanical model adds
  little on this set.

## Limits known in advance

- Before this file was written I saw the first four question stems and one gold
  query, while checking formats. I wrote nothing from them.
- I ran two questions of my own for a smoke test. They aren't in the set.
- One dataset, one model, one person's harness. It says nothing about Auto
  Ontology's own score, which needs its stack and a separate run.

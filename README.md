# DQL Benchmarks

Benchmarks, evidence and analysis for [DQL](https://github.com/duckcode-ai-labs/dql), DuckCode's open-source governed analytics layer. This repository holds everything behind the paper *Accuracy, Trust Labels and Abstention in a Governed Text-to-SQL Layer* (draft, [analysis/insurance-2026-09-29/](analysis/insurance-2026-09-29/)): the harness that ran it, the question sets that may be published, every run report, the statistics script and the paper generator.

**What is measured:** DQL's Ask answering business questions in plain English, scored on three things at once:
- **accuracy**, the share of answers that return the reference rows;
- **trust precision**, how often an answer DQL labels *certified* or *governed* is actually right;
- **abstention**, how often DQL declines a question the data cannot answer.

The comparisons are against one-shot SQL from the table definitions and against an agent with database tools, with and without DQL's modeling knowledge.

## Headline results (insurance warehouse, set 4, Claude Sonnet 5.5, 200 questions)

| Condition | Correct | Question-level 95% CI |
|---|---:|---|
| One-shot SQL (P) | 126 | 56.0–69.5% |
| Agent with database tools (A) | 156 | 72.0–83.5% |
| Agent + DQL's modeling knowledge as text (A-model) | 168 | 78.5–89.0% |
| DQL L2 / L3 (dbt metrics, + skills) | 142 / 147 | 64.5–77.0% / 67.5–79.5% |
| DQL W2 (warehouse + native metrics) | 171 | 80.5–90.0% |
| DQL WB (+ authored business layer) | 154 | 71.0–82.5% |

- **Against one-shot SQL:** DQL W2 is significantly more accurate (Holm-adjusted p < 0.001).
- **Against an agent with the same knowledge:** W2 and A-model differ by +1.5 points (p = 0.73). The results are consistent with the modeling knowledge explaining much of the gain; an additional advantage from DQL's answering pipeline was not established. This is not a claim of equivalence: no equivalence margin was set.
- **Trust labels:**
  - 3 of 28 governed dbt-metric answers were wrong.
  - 13 of 26 business-layer answers were wrong.
- **Abstention:** DQL declined 40–43 of 50 unanswerable questions; both agents declined 47.

The paper reports every caveat: the post-hoc choice of W2, different builds, the AI-written reference answers and their audit, and pooling across repeated questions. A confirmatory test on a new set is pre-registered in [insurance/PREREGISTRATION-SET5.md](insurance/PREREGISTRATION-SET5.md).

> Set 4 and its reports are sealed until the paper is posted, so they are not in this repository yet; the numbers above come from them. Set 5 stays sealed until its pre-registered run is reported. See [docs/RELEASE-CHECKLIST.md](docs/RELEASE-CHECKLIST.md).

## Layout

```
insurance/                 the insurance benchmark harness
  build.mjs, run.mjs       build a context level's project and warehouse; ask a question set through DQL
  baseline-text2sql.mjs    one-shot SQL baseline (P)
  baseline-agent.mjs       agent baseline with database tools (A; --context modeling for A-model)
  contexts/                the W2 modeling knowledge given to A-model as text
  layers/                  files written for the levels (modeling, skills, business layer B)
  heldout.mjs, heldout/    question-set import and reference answers; dev set and sets 2–3 (set 4 at release)
  gold-audit.jsonl         reference-answer disputes on the development set
  audit/                   human audit of set 4: sampler (seed 20260930) and instructions
  set5-writer/             what the set-5 question writer (GPT-6 Sol) was given: prompt, format, validator
  PREREGISTRATION-SET5.md  confirmatory test, committed before set 5 existed
results/insurance/         every run behind the paper: report.json (+ evals.yml, agent transcripts)
analysis/insurance-2026-09-29/
  paper/stats_v2/          statistics: question-level bootstrap, exact McNemar, Holm, lenient re-grade
  paper/paper_docx.py      builds the paper (.docx) from stats_v2.json; figures fig1/fig2
  paper/references_verified.md   every reference checked against a primary source
  regrade/, analyze.py     earlier re-grade and per-level analysis
lib/, paired/, scripts/    DQL resolver, identity stamp, row matching, paired scorer, installers, run scripts
spider2/                   Spider 2.0-Lite pilot: harness, layers written blind, reports
docs/                      methodology, reproduction, data and licences, release checklist, history rewrite
```

## Reproducing

[docs/REPRODUCE.md](docs/REPRODUCE.md) covers recomputing every number from the committed reports, and re-running a model's round from scratch with the same DQL builds. Run stores and project copies (about 450 MB) go to a release archive, not to git.

## Principles

1. **Paired comparisons** on the same questions and grader, with question-level bootstrap intervals and Holm correction within pre-declared families.
2. **Provenance:** every report names the repository commit, DQL build, model identifier, CLI version and run settings.
3. **Reference answers are audited** and the audits are published; strict and lenient grades are both reported.
4. **Trust labels are scored:** a wrong answer labelled certified or governed is counted separately, by distinct question.
5. **No tuning on held-out sets.** Every system change made during a study is disclosed with the evidence that prompted it.
6. **Provider usage limits are never scored;** refused questions are asked again after the reset.

## License

Code is Apache-2.0. The insurance data comes from [data.world's cwd-benchmark-data](https://github.com/datadotworld/cwd-benchmark-data) (Apache-2.0) as packaged by [dbt Labs](https://github.com/dbt-labs/dbt-llm-sl-bench) and is downloaded, not redistributed; see [docs/DATA.md](docs/DATA.md).

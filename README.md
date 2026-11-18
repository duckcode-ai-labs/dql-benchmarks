# DQL Benchmarks

[![DOI](https://zenodo.org/badge/1398903034.svg)](https://doi.org/10.5281/zenodo.24329319)

Everything behind the paper **[Context, Trust Labels and Abstention in a Governed Text-to-SQL Layer: A Pre-registered Evaluation on an Insurance Warehouse](analysis/insurance-2026-09-29/paper/paper.pdf)** (Kondapaka, 2026, preprint v1, 24 pages): the harness that ran it, all five question sets, every run report, the human audits, the statistics script and the paper generator.

[DQL](https://github.com/duckcode-ai-labs/dql) is the open-source engine of **[ZLens](https://zlens.app)**, an analytics layer that labels every answer by how it was made: *certified* by a person, *governed* (built from approved metrics), *review required* (drafted SQL) or *blocked*.

**[Read the paper (PDF)](analysis/insurance-2026-09-29/paper/paper.pdf)** · [Pre-registration](insurance/PREREGISTRATION-SET5.md) · [Sealing hashes](docs/SEALING.md) · [Reproduce the numbers](docs/REPRODUCE.md) · DOI [10.5281/zenodo.24329320](https://doi.org/10.5281/zenodo.24329320)

## The short version

One AI model (Claude Sonnet 5.5) answered the same 200 business questions on the ACME insurance warehouse in four setups. The questions were written by a GPT model after the test plan was [published](insurance/PREREGISTRATION-SET5.md), and nothing was changed in DQL because of them.

| Setup (set 5, pre-registered) | Exactly right | Question-level 95% CI | Lenient grade | Declined the 50 unanswerable |
|---|---:|---|---:|---:|
| One-shot SQL from the table definitions (P) | 119 (59.5%) | 52.5–66.5% | 151 | – |
| Agent with database tools (A) | 141 (70.5%) | 64.0–77.0% | 176 | 45 |
| Same agent + DQL's modeling knowledge as text (A-model) | 161 (80.5%) | 75.0–86.0% | 184 | 46 |
| DQL, dbt project + modeling + dbt metrics (L2) | 159 (79.5%) | 73.5–85.0% | 177 | 45 |
| DQL, + written business rules (L3) | 165 (82.5%) | 77.0–87.5% | 181 | 43 |
| **DQL, warehouse catalog + modeling + metrics (W2)** | **175 (87.5%)** | **83.0–92.0%** | 184 | 41 |
| DQL, + hand-built business layer (WB) | 166 (83.0%) | 77.5–88.0% | 177 | 39 |

What the study found:

- **A model of the warehouse is what moves accuracy.** Against one-shot SQL every DQL level was significantly better (Holm p < 0.001). The agent alone gained 10 points from reading DQL's modeling knowledge as text. On set 3, adding modeling raised every one of seven AI models by 8 to 18 of 40 questions.
- **The pre-registered hypothesis held under the strict grade.** W2 against A-model: +7.0 points (95% CI +1.5 to +12.5, exact McNemar p = 0.02), and W2 led in two repeat runs (174 vs 160, 173 vs 157). Under the lenient grade, which forgives a missing or different label column, the two tie at 184.
- **A hand-built business layer did not help.** WB scored below W2 on set 5 (83.0% vs 87.5%) and on set 4 (77% vs 85.5%), where 13 of its 26 *governed* answers were wrong.
- **No dbt project needed.** The best level, W2, read the warehouse catalog directly.

Where DQL fell short, reported as measured:

- **Trust labels.** 36 of 54 answers labelled *governed* at the dbt-metric levels were right under the strict grade (53 under lenient + rounding). The pre-registered target of 95% precision was not met.
- **Abstention.** DQL declined 39 to 45 of the 50 unanswerable questions; the agent with the same knowledge declined 46.
- **Smaller model.** With the pre-registered secondary model, Qwen 3.8 27B run locally, W2 and A-model did not differ (145 vs 141, p = 0.71).
- **Scale.** The warehouse has 2 policies and 2 claims. It tests an awkward schema, not scale. The figures cannot be compared with BIRD or Spider 2.0 scores.

The earlier, exploratory sets (3 and 4), the database-variant check and a root-cause taxonomy of wrong trusted answers are in the paper's Section 6 and appendices, with every deviation from our own protocol listed in Section 8.

## What is in this repository

All five question sets are public. Sets 4 and 5 were sealed until the paper was posted; their SHA-256 hashes were published in [docs/SEALING.md](docs/SEALING.md) before any system was run on them, so you can check that the released files are the ones that were run. The run archive (run stores, cassettes and project copies, needed to re-grade from raw rows) will be deposited with a persistent identifier and linked here.

## How to cite

Kondapaka, K. (2026). *Context, Trust Labels and Abstention in a Governed Text-to-SQL Layer: A Pre-registered Evaluation on an Insurance Warehouse* (preprint v1). DuckCode AI Labs. https://doi.org/10.5281/zenodo.24329320

That DOI is the archived v1 of this repository on Zenodo, with the paper inside. https://doi.org/10.5281/zenodo.24329319 always resolves to the latest version. GitHub's "Cite this repository" button reads [CITATION.cff](CITATION.cff).

## Layout

```
insurance/                 the insurance benchmark harness
  build.mjs, run.mjs       build a context level's project and warehouse; ask a question set through DQL
  baseline-text2sql.mjs    one-shot SQL baseline (P)
  baseline-agent.mjs       agent baseline with database tools (A; --context modeling for A-model)
  contexts/                the W2 modeling knowledge given to A-model as text
  layers/                  files written for the levels (modeling, skills, business layer B)
  heldout.mjs, heldout/    question-set import and reference answers: dev set and sets 2–5
  gold-audit.jsonl         reference-answer disputes on the development set
  audit/                   human audits of sets 4 and 5: samplers, instructions, completed sheets, blind review
  set5-writer/             what the set-5 question writer (GPT-6 Sol) was given: prompt, format, validator
  PREREGISTRATION-SET5.md  confirmatory test, committed before set 5 existed
results/insurance/         every run behind the paper: report.json (+ evals.yml, agent transcripts)
analysis/insurance-2026-09-29/
  paper/stats_v2/          statistics: question-level bootstrap, exact McNemar, Holm, lenient re-grade
  paper/paper.pdf          the paper, preprint v1
  paper/paper_docx.py      builds the paper (.docx) from the stats_v2 outputs; figures fig1, fig2, fig5
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

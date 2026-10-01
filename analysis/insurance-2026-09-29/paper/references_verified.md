# Verified bibliography

Every field below was checked on 2026-09-30 against a page fetched that day: arXiv abstract/HTML pages, NeurIPS/ICLR proceedings BibTeX, Crossref, JAMA, JMLR, ACL Anthology, GitHub pages/API, and the named blogs and sites. Anything not confirmed is marked **unconfirmed**. Machine-readable version: `references_verified.json`.

Status legend: **VERIFIED** = matches what the paper had. **CORRECTED** = something had to change. **UNVERIFIABLE** = could not be confirmed from a primary source.

## Summary table

| # | Key | Status | What changed |
|---|-----|--------|--------------|
| 1 | sequeda2023benchmark | VERIFIED | Claims hold (16.7% vs 54.2%; both high-schema quadrants 0% for SQL). The abstract rounds these to 16% and 54%. |
| 2 | dataworld_cwd_benchmark | VERIFIED | Contents listed below |
| 3a | ganz2026dbtbenchmark | CORRECTED | Authors and date added; "8 to 16 points" is our own arithmetic, not a claim in the post; no significance tests |
| 3b | dbt_llm_sl_bench | VERIFIED | Repo now also holds Aug 2026 results |
| 4a | cube_slbenchmark_repo | VERIFIED | Size of the markdown document is inconsistent in the source (4 KB vs ~9 KB) |
| 4b | rumiantsau2026semantic | CORRECTED | Full title; 99 scored questions, not 100; the "semantic layer" is a markdown prompt document, not an engine |
| 5a | jin2026pervasive (arXiv) | CORRECTED | Exact title and authors; numbers differ from the CIDR version |
| 5b | jin2026cidr (CIDR 2026) | CORRECTED | Exact title; 66.1% (not 62.8%) for Spider 2.0-Snow; up to 3 positions (not 9) |
| 6 | li2023bird | CORRECTED | NeurIPS 2023 **Datasets and Benchmarks Track**, vol. 36, pp. 42330–42357, DOI added; the two sources give different author counts |
| 7 | lei2025spider2 | VERIFIED | Pages 28691–28735 added |
| 8 | livesqlbench | VERIFIED | BIRD Team (HKU) with Google Cloud; no paper yet |
| 9 | mcnemar1947 | VERIFIED | Full title added |
| 10 | wilson1927 | VERIFIED | Full title added |
| 11 | hanley1983 | VERIFIED | Full title added. The page I fetched does not use the words "rule of three". |
| 12 | dbt_metricflow_docs | VERIFIED | No date on the page, so cite with an access date |
| 13 | dql_repo | VERIFIED | Public. GitHub's API reports the licence as NOASSERTION; check the LICENSE file |
| 14 | elyaniv2010foundations | VERIFIED | JMLR 11(53) |
| 15 | geifman2017selective | VERIFIED | NIPS 2017, vol. 30; the proceedings give no page range |
| 16 | richardson2026predicts | VERIFIED (new) | Full title "…? A Selective-Prediction Study"; single author |
| 17 | chen2025rts | VERIFIED (new) | Published in PACMMOD 3(1) 2025, DOI 10.1145/3709719; author order differs from arXiv |
| 18 | wang2023know | VERIFIED (new) | Full title "…: Handling Ambiguous and Unknown Questions for Text-to-SQL" |

## References (formatted)

1. Juan Sequeda, Dean Allemang, Bryon Jacob. *A Benchmark to Understand the Role of Knowledge Graphs on Large Language Model's Accuracy for Question Answering on Enterprise SQL Databases.* arXiv:2311.07509, 2023. https://arxiv.org/abs/2311.07509
2. data.world. *cwd-benchmark-data* (Data for the Chat With Your Data benchmark). GitHub, 2023. Apache-2.0. https://github.com/datadotworld/cwd-benchmark-data
3. Jason Ganz, Benoit Perigaud. *Semantic Layer vs. Text-to-SQL: 2026 Benchmark Update.* dbt Developer Blog, 7 April 2026. https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026
4. dbt Labs. *dbt-llm-sl-bench.* GitHub. https://github.com/dbt-labs/dbt-llm-sl-bench
5. Cube. *semantic-layer-benchmark.* GitHub, 2026. https://github.com/cubedevinc/semantic-layer-benchmark
6. Michael Rumiantsau, Ivan Fokeev. *Semantic Layers for Reliable LLM-Powered Data Analytics: A Paired Benchmark of Accuracy and Hallucination Across Three Frontier Models.* arXiv:2604.25149, 2026.
7. Tengjun Jin, Yoojin Choi, Yuxuan Zhu, Daniel Kang. *Pervasive Annotation Errors Break Text-to-SQL Benchmarks and Leaderboards.* arXiv:2601.08778 (v3), 2026. **(recommended)**
8. Tengjun Jin, Yoojin Choi, Yuxuan Zhu, Daniel Kang. *Text-to-SQL Benchmarks are Broken: An In-Depth Analysis of Annotation Errors.* CIDR 2026 (16th Conference on Innovative Data Systems Research), Chaminade, USA. https://www.vldb.org/cidrdb/papers/2026/p5-jin.pdf
9. Jinyang Li, Binyuan Hui, Ge Qu, Jiaxi Yang, Binhua Li, Bowen Li, et al. *Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs.* Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track, pp. 42330–42357. doi:10.52202/075280-1835. arXiv:2305.03111.
10. Fangyu Lei, Jixuan Chen, Yuxiao Ye, Ruisheng Cao, et al. *Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows.* ICLR 2025 (Oral), pp. 28691–28735. arXiv:2411.07763.
11. BIRD Team (HKU) and Google Cloud. *LiveSQLBench: A Dynamic and Contamination-Free Benchmark for Evaluating LLMs on Real-World Text-to-SQL Tasks.* https://livesqlbench.ai (accessed 2026-09-30).
12. Quinn McNemar. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. *Psychometrika* 12(2):153–157, 1947. doi:10.1007/BF02295996
13. Edwin B. Wilson. Probable Inference, the Law of Succession, and Statistical Inference. *Journal of the American Statistical Association* 22(158):209–212, 1927. doi:10.1080/01621459.1927.10502953
14. James A. Hanley, Abby Lippman-Hand. If Nothing Goes Wrong, Is Everything All Right? Interpreting Zero Numerators. *JAMA* 249(13):1743–1745, 1983. doi:10.1001/jama.1983.03330370053031
15. dbt Labs. *About MetricFlow.* dbt Developer Hub. https://docs.getdbt.com/docs/build/about-metricflow (accessed 2026-09-30).
16. DuckCode AI. *DQL.* GitHub. https://github.com/duckcode-ai/dql
17. Ran El-Yaniv, Yair Wiener. On the Foundations of Noise-free Selective Classification. *Journal of Machine Learning Research* 11(53):1605–1641, 2010.
18. Yonatan Geifman, Ran El-Yaniv. Selective Classification for Deep Neural Networks. *Advances in Neural Information Processing Systems 30* (NIPS 2017). arXiv:1705.08500.
19. Robert Richardson. *What Predicts Correctness in Text-to-SQL? A Selective-Prediction Study.* arXiv:2607.06799, 2026.
20. Kaiwen Chen, Yueting Chen, Nick Koudas, Xiaohui Yu. Reliable Text-to-SQL with Adaptive Abstention. *Proceedings of the ACM on Management of Data* 3(1):1–30, 2025. doi:10.1145/3709719. arXiv:2501.10858.
21. Bing Wang, Yan Gao, Zhoujun Li, Jian-Guang Lou. Know What I don't Know: Handling Ambiguous and Unknown Questions for Text-to-SQL. *Findings of ACL 2023*, pp. 5701–5714. doi:10.18653/v1/2023.findings-acl.352

## Corrected factual claims the paper must use

### Item 1 — Sequeda, Allemang, Jacob (2023)
- The benchmark has 43 questions on the ACME insurance schema. GPT-4 was prompted zero-shot at temperature 0.3. The metric is Average Overall Execution Accuracy (AOEA).
- Overall: **16.7% on the SQL schema vs 54.2% with the knowledge graph (SPARQL)**. The abstract rounds these to 16% and 54%.
- Per quadrant (SQL vs KG): low question/low schema 25.5% vs 71.1%; high question/low schema 37.4% vs 66.9%; **low question/high schema 0% vs 35.7%; high question/high schema 0% vs 38.5%**. The claim that both high-schema-complexity quadrants scored 0% for SQL is correct.
- Cite it as an arXiv preprint. The arXiv record has no journal-ref.

### Item 2 — data.world cwd-benchmark-data
- The repo contains `ACME_Insurance/`:
  - `DDL/ACME_small.ddl`
  - 29 CSV tables
  - an R2RML mapping (`data.world_P&C_Insurance_Ontology_V1.r2rml`)
  - `ontology/insurance.ttl`
  - `investigation/acme-benchmark.ttl` (the questions)
- Licence: Apache-2.0. Created 2023-10-12.

### Item 3 — dbt Labs 2026 blog and repo
- Authors are Jason Ganz and Benoit Perigaud. Published 7 April 2026.
- Dataset: the ACME Insurance benchmark of Sequeda et al. Design: **11 questions, each run 20 times**.
- Main results were computed after adding **3 dbt models** so that the Semantic Layer covers every question:
  - Claude Sonnet 4.6: text-to-SQL 90.0% vs Semantic Layer 98.2%
  - GPT-5.3-Codex: text-to-SQL 84.1% vs Semantic Layer 100.0%
- The gain is **+8.2 and +15.9 points**. "8 to 16 points" is our own summary of these two rows; the post does not state that range.
- The post reports **no confidence intervals, error bars, p-values or significance tests**.
- Before the extra modeling, results were split by "Too Many Hops":
  - Semantic Layer accuracy on the "True" questions: **0.0%** for both models.
  - Text-to-SQL on the same questions: 70.0% (Sonnet 4.6) and 100.0% (GPT-5.3 Codex).
  - All questions together: text-to-SQL 64.5% vs Semantic Layer 72.7% for both models.
  - The post says Semantic Layer failure "looks like an error message", whereas text-to-SQL gives "a plausible but incorrect answer". The claim that the semantic layer returned errors rather than wrong numbers on out-of-scope questions is supported.
- The post does not say how many of the 11 questions fall in the "Too Many Hops" group.
- The GitHub repo has since added August 2026 runs (Claude Sonnet 5 / Opus 5 / GPT-5.6).

### Item 4 — Cube benchmark and paper (Rumiantsau & Fokeev, Cube)
- Data: the Cleaned Contoso Retail Dataset in **ClickHouse**. The benchmark has **100 questions** in 5 tiers, of which **99 are scored**; q33 was excluded because its reference query exceeds ClickHouse's memory quota.
- The "semantic layer" condition is a **hand-authored markdown document prepended to the prompt**. The model still writes raw SQL; there is no query engine. The paper calls it "approximately 4 KB (8,969 characters, ~2,200 tokens)"; the README says "~9 KB". Better to say "a ~2.2K-token markdown document".
- Protocol: single-shot, no tools or retries, medium reasoning effort.
- Gains:
  - Opus 4.7: 50.5% → 67.7% (+17.2)
  - Sonnet 4.6: 46.5% → 68.7% (+22.2)
  - GPT-5.4: 45.5% → 68.7% (+23.2)
- Statistics: **Wilson 95% CIs** and **paired two-sided exact McNemar**, p ≤ 0.0015 in the paper (the README says "p < 0.002"). Correct wording: "+17 to +23 points".

### Item 5 — Jin, Choi, Zhu, Kang (two versions)

| | arXiv 2601.08778 v3 (19 Jan 2026) | CIDR 2026 |
|---|---|---|
| Title | Pervasive Annotation Errors Break Text-to-SQL Benchmarks and Leaderboards | Text-to-SQL Benchmarks are Broken: An In-Depth Analysis of Annotation Errors |
| BIRD Mini-Dev error rate | 52.8% | 52.8% |
| Spider 2.0-Snow error rate | **62.8%** | **66.1%** (121 problems with open gold SQL) |
| Agents re-evaluated | all 16 open-source BIRD-leaderboard agents | 5 leading open-source agents |
| Performance change (relative) | **−7% to +31%** | **−3% to +31%** (−2% to +19% absolute) |
| Rank change | **−9 to +9 positions** | **up to 3 positions** (−2 to +3) |
| Extra | Spearman r_s = 0.85 (uncorrected subset vs full Dev) vs 0.32 (corrected subset) | CHESS 62% → 81%, 4th → 1st |

**Recommendation:** cite the **arXiv v3** version. It is the later and broader study, and it is the only version that supports "up to nine places". Use its numbers: 52.8% / 62.8%, −7% to +31%, ±9. If the paper wants the peer-reviewed CIDR citation, use only the CIDR numbers with it: 52.8% / 66.1%, −3% to +31%, up to three positions. Never mix 66.1% with ±9, or 62.8% with "three positions".

## New references: what they do and how they relate to trust labels and abstention
- **Richardson (2026), arXiv:2607.06799.**
  - What it does: measures, as AUROC, how well different signals predict whether generated SQL is correct, on BIRD and Spider. Black-box signals reach about 0.61–0.68 and LLM judges 0.72–0.78. A two-provider judge ensemble reaches 0.82 with ECE 0.03 and supports abstention frontiers, for example answering 27% of questions at 24% selective risk.
  - How it relates: it scores text-to-SQL correctness prediction as risk vs coverage, which is the same accounting as trust labels and stops.
- **Chen, Chen, Koudas, Yu (2025), PACMMOD 3(1), doi:10.1145/3709719.**
  - What it does: RTS applies conformal prediction to LLM hidden states at schema linking to detect likely errors. It then abstains or asks the user, with probabilistic guarantees on schema-linking accuracy on BIRD.
  - How it relates: it is a system-level "stop rather than guess" policy.
- **Wang, Gao, Li, Lou (2023), Findings of ACL.**
  - What it does: sorts ambiguous and unanswerable text-to-SQL questions into 6 categories, generates counterfactual examples of them, and proposes the DTE model to detect, localise and explain them.
  - How it relates: it treats "no SQL answer should be given" as a correct outcome, which is what a correct-refusal label measures.

## arXiv policy findings
- **Official arXiv policy** (info.arxiv.org/help/moderation, section "Policy for authors' use of generative AI language tools"):
  - Authors must disclose significant use of text-to-text generative AI.
  - Each author takes full responsibility for all contents "irrespective of how the contents were generated". That includes AI-produced errors, plagiarism and **incorrect references**.
  - AI tools must not be listed as authors.
  - **This page does not state a penalty.** Neither do the Code of Conduct or its enforcement page. The enforcement page only mentions suspension of submission privileges "for a designated period".
- **The one-year ban** comes from Thomas Dietterich, chair of arXiv's CS section, in a Bluesky thread posted 2026-05-13 (text read through the public Bluesky API) and on X.
  - Penalty: incontrovertible evidence of unchecked LLM output means a **1-year arXiv ban, followed by a requirement that later submissions first be accepted at a reputable peer-reviewed venue**.
  - Examples of evidence he gives: hallucinated references (not minor errors) and LLM meta-comments left in the text.
  - He adds that co-authors should also be penalised, with appeal, and that such papers are withdrawn.
  - TechCrunch (Anthony Ha, 16 May 2026) reports the same rule as "one-strike" with appeal, citing his social posts rather than an arXiv policy page.
- **Accepted formats** (info.arxiv.org/help/submit):
  - Accepted, in order of preference: (La)TeX / AMS(La)TeX / PDFLaTeX, then PDF, then HTML with JPEG/PNG/GIF images.
  - Not accepted: dvi, PS, **PDF created from TeX/LaTeX source**, and scanned documents.
  - **.docx is not accepted.** A Word-authored paper must be submitted as a single PDF, following the PDF guidelines (embedded outline fonts, machine-readable text, no "Print to PDF" rasterising).

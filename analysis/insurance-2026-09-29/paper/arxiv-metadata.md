# arXiv submission fields

Generated from paper.docx by arxiv_metadata.py; re-run after any change to the paper.

- **Title:** Context, Trust Labels and Abstention in a Governed Text-to-SQL Layer: An Exploratory Case Study on an Insurance Warehouse
- **Authors:** [Author names]  <- fill in before submitting
- **Primary category:** cs.DB (Databases); **cross-lists:** cs.CL, cs.AI
- **Comments:** <pages> pages, 2 figures, 14 tables. Code, data, pre-registration and run archive: https://github.com/duckcode-ai-labs/dql-benchmarks
- **License:** the author's choice (CC BY 4.0 lets others reuse the text with attribution; the arXiv default licence does not)
- **Abstract length:** 1372 characters (arXiv limit 1,920)

## Abstract (as in the paper)

Text-to-SQL systems are usually judged by execution accuracy alone. For business use, two further properties matter: whether a label marking an answer as computed from approved definitions can be trusted, and whether the system declines questions the data cannot answer. We evaluate DQL, an open-source analytics layer that labels each answer by how it was produced, on a small insurance warehouse with held-out question sets written by AI agents. In a pre-registered test on 200 answerable questions written by a GPT model, DQL with modeled context (level W2) answered 87.5% correctly with Claude Sonnet 5.5, against 59.5% for one-shot SQL and 80.5% for an agent given the same modeling knowledge as text (+7.0 points, 95% CI +1.5 to +12.5, exact McNemar p = 0.02; similar in 2 repeat runs); the difference from that agent vanishes under a grade that forgives label columns. Answers labelled governed at DQL's dbt-metric levels were right in 36 of 54 cases (53 when label columns are forgiven), short of the pre-registered 95%, and DQL declined 39 to 45 of 50 unanswerable questions against 46 for the agent. Exploratory results on a second set of 250 questions written by a Claude model agree on the gain over one-shot SQL and did not establish an advantage over the same-context agent; there, 13 of 26 answers labelled governed by an authored business layer were wrong.

## Abstract (ASCII, for the form)

Text-to-SQL systems are usually judged by execution accuracy alone. For business use, two further properties matter: whether a label marking an answer as computed from approved definitions can be trusted, and whether the system declines questions the data cannot answer. We evaluate DQL, an open-source analytics layer that labels each answer by how it was produced, on a small insurance warehouse with held-out question sets written by AI agents. In a pre-registered test on 200 answerable questions written by a GPT model, DQL with modeled context (level W2) answered 87.5% correctly with Claude Sonnet 5.5, against 59.5% for one-shot SQL and 80.5% for an agent given the same modeling knowledge as text (+7.0 points, 95% CI +1.5 to +12.5, exact McNemar p = 0.02; similar in 2 repeat runs); the difference from that agent vanishes under a grade that forgives label columns. Answers labelled governed at DQL's dbt-metric levels were right in 36 of 54 cases (53 when label columns are forgiven), short of the pre-registered 95%, and DQL declined 39 to 45 of 50 unanswerable questions against 46 for the agent. Exploratory results on a second set of 250 questions written by a Claude model agree on the gain over one-shot SQL and did not establish an advantage over the same-context agent; there, 13 of 26 answers labelled governed by an authored business layer were wrong.

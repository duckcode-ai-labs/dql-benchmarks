# How the L1 and L3 layers are written

The L1 (modeling) and L3 (skills) layers are written the way a data team would write them for a new DQL project: from the project and its documentation. They are **never** written from the benchmark's questions or answers.

## Who writes them

A separate AI agent (Claude, started fresh for this job) that has not seen the benchmark. The person or agent that built the harness has read every question and correct answer while auditing the answer key, so it does not write these layers.

## What the author may read

- The L0 project: `work/insurance/authoring/project/` (the dbt project dbt Labs published, with its seed data and the DuckDB warehouse built from it).
- The benchmark's published schema documents, copied to `work/insurance/authoring/docs/`:
  - `ACME_small.ddl`: the table definitions;
  - `insurance.ttl`: data.world's insurance ontology (the business concepts and how they relate);
  - `data.world_P&C_Insurance_Ontology_V1.r2rml`: data.world's mapping from those concepts to the tables.
- DQL's own documentation and source code, to learn the file formats.

## What the author must not read

Anything that contains the questions or their answers:
- `data/`, `insurance/` (except this file), `work/insurance/gold/`, `work/insurance/runs/`, `work/insurance/projects/`;
- any file named `*benchmark*.ttl`, any `investigation/` or `hex_notebook/` folder;
- the dbt Labs benchmark runner and its results database.

The author's working folder is `work/insurance/authoring/`; it contains none of these.

## What the author produces

1. **L1: DQL modeling** for the insurance domain: a domain, its entities, the relationships between them (keys, cardinality), and the joins that are safe to certify. Files go under `insurance/layers/L1/`, laid out as they sit in a DQL project.
2. **L3: DQL skills**: the business definitions and rules an insurance analyst would write down (for example, what a policy holder or an agent is in this data). Files go under `insurance/layers/L3/`.
3. **Questions the data cannot answer**: 15 plain-English questions a business user might plausibly ask of an insurance warehouse, which this data cannot answer (the concept is not in the data at all). Written to `insurance/unanswerable.json` with, for each one, the reason the data cannot answer it.
4. **An authoring log**: start and end time, the files read, and the decisions made. Written to `insurance/layers/AUTHORING-LOG.md`.

No certified block that answers a specific business question is written; a certified block would be an answer.

## Why the source of each layer matters

A buyer will ask how much work each layer took and whether it was fitted to the test. The log answers the first; this file and the separation of authors answer the second.

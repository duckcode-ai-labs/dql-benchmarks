# How the Spider 2.0-Lite L2 and L3 layers are written

The modeled layers are written the way a data team would write them for a warehouse it has just connected to DQL: from the warehouse itself. They are **never** written from the benchmark's questions, answers or per-question documents.

| Layer | What the project has | Where the files go |
|---|---|---|
| L1 | the warehouse only (DQL on the raw schema) | nothing written |
| **L2** | + modeling: one domain, its entities (grain, keys), relationships, business context | `spider2/layers/<db>/L2/` |
| **L3** | + skills (business definitions and rules) and, where a measure is unambiguous from the data, native metrics | `spider2/layers/<db>/L3/` |

## Who writes them

A separate AI agent (Claude, started fresh for each database) that has not seen the benchmark. The session that built this harness has read the questions and answers, so it does not write layers.

## What the author may read

- Its working folder, `work/spider2/authoring/<db>/`:
  - `project/`: a DQL warehouse-first project on a copy of the database, with its schema synced and DQL's own unreviewed draft model applied (`dql model apply-discovery --apply --validate`);
  - `<db>.sqlite`: the database copy (read-only queries: schema, sample rows, counts, distinct values).
- DQL's documentation and source code, to learn the file formats.
- The insurance layers as format examples: `insurance/layers/L1/`, `insurance/layers/L3/` (a different domain; no Spider content).

## What the author must not read

Anything that contains Spider questions, answers or question-specific documents:
- `data/` (the Spider repository, its questions, gold SQL, gold results and `external_knowledge` documents);
- `spider2/` except this file and `spider2/layers/<db>/` of its own database;
- `work/spider2/runs/`, `work/spider2/projects/`, `work/spider2/*.log`;
- any file named `*spider2-lite*.jsonl`, `*gold*`, `*.sql` outside its working folder.

## What the author produces

1. **L2 modeling** for the database's one domain:
   - an entity for every table and view that holds business data, bound with `relation: main.<table>`, with its grain and keys and a business description written from the data (what one row is; which columns are filled, empty or coded);
   - the relationships between entities with keys and cardinality. A relationship is **certified only when the data proves it** (the keys match, the declared cardinality holds, and it joins rows); otherwise it stays a draft, with the reason;
   - `dql model validate` must pass.
2. **L3 skills and metrics**:
   - skills (`skills/*.skill.md`): definitions an analyst would write down from the data (what a status code means, how dates are stored, which table is the record of an event, units), each grounded in rows the author looked at;
   - native metrics only where the measure is unambiguous from the data (a count of rows of a fact, a sum of an amount column). No metric that encodes a business choice the data does not settle.
3. **No certified block.** A block that answers a specific question would be an answer.
4. **An authoring log**, `spider2/layers/<db>/AUTHORING-LOG.md`: start and end time, every file read outside the working folder, every query run, and the decisions made (what was certified, what stayed a draft, and why).

## Why the source of each layer matters

A reader will ask how much work each layer took and whether it was fitted to the test. The log answers the first; this file, the separation of authors and the log's list of files read answer the second. Results for L2 and L3 are labelled **"AI-authored, independently reviewed, not human-certified"** until a person certifies them.

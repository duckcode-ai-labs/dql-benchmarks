# Sealed question sets: commitments

A sealed set's files are kept out of this repository until its release (see RELEASE-CHECKLIST.md).
To make the sealing auditable, this file publishes SHA-256 hashes of every file that contains a sealed
set's questions or reference SQL: the set itself, its reference answers, and the transcripts of the
agent that wrote it. On release day the files are published and anyone can check them against these
hashes. A hash reveals nothing about the content.

## Set 4 (hashed 1 October 2026)

Written by a Claude Opus 5.5 agent (task "Write sealed held-out set 4"). The files are archived
together, unread, outside the repository (`private/sealed/set4-writer-artifacts.tar`).

| File | Bytes | SHA-256 |
|---|---:|---|
| `questions-4.json` (questions, reference SQL, unanswerable items) | 121517 | `507790a9e81c4f17d961c6c60a86337cac581610b69c3810575ad81a80d747fe` |
| `heldout-4.json` (reference rows from executing the reference SQL) | 175426 | `5bf5de63184ee0c7f560112ac0ace80756bc8fbb6e04c77ed0998407c7d07553` |
| `agent-a65326ab7580e9155.jsonl` (writer transcript) | 718110 | `0ffadfc4e3049e1eb08b12202068ad4fcbeccd98b29060683c6bba59f2cf6fa8` |
| `agent-a65326ab7580e9155.meta.json` (writer task metadata) | 192 | `482c62918b5923cae523e0bfd090c17d106c9a81e19db452ae7c236a63881326` |
| `bl4lg4szv.txt` (a tool output shown during writing; contains question prefixes) | 30242 | `09fba1abeb222c03db0a2d639ff89076b10f4846cb38c45302f01cec945cfaae` |
| `set4-writer-artifacts.tar` (all of the above plus two identical task-output copies) | | `e1b17444146030d3670a740cc243c29c0464e37edad9e13029aa75e8fe00f7bd` |

Known exposure, also stated in the paper: two set-4 question identifiers (hashes, not text) appeared in
a run log the operator's assistant displayed, and two set-4 reference queries are textually identical
to set-3 reference queries (whose question wording differs). The set-3 writer's transcript contains
one question prefix that also opens a set-4 question.

## Set 5

Not yet written at the time this file was committed. The writer's command log, final message and the
question file will be hashed here as soon as they exist, before any system is run on set 5.

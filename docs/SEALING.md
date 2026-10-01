# Sealed question sets: commitments

A sealed set's files are kept out of this repository until its release (see RELEASE-CHECKLIST.md).
To make the sealing auditable, this file publishes SHA-256 hashes of every file that contains a sealed
set's questions or reference SQL: the set itself, its reference answers, and the transcripts of the
agent that wrote it. On release day the files are published and anyone can check them against these
hashes. A hash reveals nothing about the content.

## Set 4 (hashed 30 September 2026, 21:54 CDT)

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

## Set 5 (hashed 30 September 2026, 21:54 CDT, before any system was run on it)

Written by GPT-6 Sol (`gpt-6-sol`, high reasoning) through the Codex CLI from an isolated home, in a
folder holding only a copy of the warehouse, `FORMAT.md`, `PROMPT.txt` and `validate.py`
(published in `insurance/set5-writer/`). Started 20:50 and finished 20:59 (CDT) on 30 September 2026;
the validator reported 200 answerable questions (50 per quadrant) and 50 unanswerable, with every
reference query returning rows. The access audit of the writer's command log found no path outside its
folder. The pre-registration (`insurance/PREREGISTRATION-SET5.md`, commit `6f60a71`) was committed at
18:19 CDT and pushed to this public repository at 20:50:22 CDT; the writer, started automatically when
the provider limit lifted, began at 20:50:33 CDT. Both times are from the same machine's clock
(git reflog and the writer's log); GitHub's push record shows the first. No system had been run on
set 5 when this file was committed. The frozen DQL build is recorded in `insurance/FREEZE-SET5.md`.

| File | Bytes | SHA-256 |
|---|---:|---|
| `questions-5.json` (as imported into `insurance/heldout/`) | 100563 | `26c125c858a4238c26948756986388d7f59521d048da87e69e1751d358268bee` |
| `questions-5.writer.json` (the writer's own file) | 100583 | `4407b8ef7041c230e764e8b6bf7e125c901d3f5f7aeafc1bc2dc7019ce398d54` |
| `heldout-5.json` (reference rows) | 261602 | `389f25ffd0c2cc29421a15ae154321dd5b48060d5678206d198c45efe02ffdf3` |
| `codex-log.jsonl` (writer command log) | 65578 | `d2be2f77affc08bb5ca05b23197a98c4132d8c89a340ed96d367167614a9666c` |
| `final-message.txt` (writer's final reply: validator counts only) | 114 | `710f5105411301f8244c7bfbfda7022756b97ea730258b4978d3f7f1084a7718` |
| `set5-writer-artifacts.tar` (all of the above plus the writer's inputs) | | `de7be79fb6c5b9336558229e9c86997fd88e2b2575ca6314580c39022b425774` |

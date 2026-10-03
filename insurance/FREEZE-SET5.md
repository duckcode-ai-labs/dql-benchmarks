# Set 5: frozen build and run plan

Recorded 2026-09-30 22:05 CDT, before any system was run on set 5. This file fills the blank left in
PREREGISTRATION-SET5.md ("DQL build: ________"); the pre-registration itself is unchanged.

## DQL build

- **Commit `627009a13ae86330fa3fcaa5085d1786328ec47f`** (DQL 1.17.3 development build; tagged locally
  `bench-set5-frozen`). It is 49c0e1cb plus the short-table-name fix, the build that produced the
  set-4 WB results. Clean working tree. It does not contain the later "lists answered with a count" fix.
- The npm version of the release that will accompany the paper is recorded when it is published; set 5
  is run on this commit regardless, and no DQL change is made because of anything set 5 shows.
- Business layer B: v3.1 (`insurance/layers/B/FROZEN.json`).

## Runs (each condition once)

| Model | Conditions | Run ids |
|---|---|---|
| Claude Sonnet 5.5 (`claude-sonnet-5-5`, Claude Code CLI 2.1.285; DQL per-step effort, P and agents high) — primary | P, A-ddl, A-model, L2, L3, W2, WB | `fl5-sonnet55`, `ag5-sonnet55`, `ag5m-sonnet55` |
| Qwen 3.8 27B (`qwen3.8:27b`, Ollama 0.34.4, local) — secondary | same | `fl5-qwen`, `ag5-qwen`, `ag5m-qwen` |
| GPT-6 Sol (`gpt-6-sol`, medium, Codex CLI, isolated home) — secondary | same | added when the provider limit allows |

Sets: `heldout-5` (200 answerable) and `heldout-5-unanswerable` (50); P runs on the answerable set only.
Node v22.18.0. Provider usage limits are waited out and never scored.

## Audit

The 25% audit sample (50 answerable, 13 unanswerable; seed 20261001) is drawn after this freeze and
audited by an author; DQL is not changed after the auditor has read the sample.

## Addendum, 3 October 2026 (before any answer was re-asked): runtime connection failures

During the set-5 runs, some answers ended within 5–20 seconds with "the runtime did not answer: read
ECONNRESET" or "socket hang up": DQL's local runtime dropped the connection and no answer was produced.
None occurred in the 8,364 answers of sets 3 and 4. By the time of this addendum there were 24 on set 5
(Qwen L2 6, L3 13, W2 3; Sonnet 5.5 L3 2), on 23 different questions, scattered through each run, so
they are not tied to particular questions. This rule was decided after those counts and the per-level
totals were known; it is reported as a deviation.

- **Definition.** An answer whose recorded failure is "the runtime did not answer" (connection reset
  or socket hang up) is an infrastructure failure, like a provider usage limit: the system under test
  gave no answer.
- **Handling.** Each such answer is asked again once, on a fresh agent, after its condition's run
  finishes (`insurance/run.mjs --retry-runtime-failures`). The original report is kept unchanged beside
  the result as `<set>.as-recorded`. If the retry also fails, the answer counts as wrong.
- **Reporting.** The main analysis uses the retried answers, as for refused calls; the as-recorded
  reading, where every such failure counts as wrong, is reported beside it for every condition.
- **Scope.** All models and conditions on set 5. The pre-registered primary test (Sonnet 5.5, W2 vs
  A-model) is unaffected: neither condition had such a failure.
- **Environment.** Jobs run under launchd, whose default limit of 256 open files per process is a
  possible cause; the Qwen job is restarted with a limit of 10,240. No DQL code changes.

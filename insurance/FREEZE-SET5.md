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

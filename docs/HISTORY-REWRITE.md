# History rewrite of 30 September 2026

Before the first push to GitHub the history was rewritten twice, on the same day:

1. Three internal planning documents (`spider2/BUILD-PLAN.md`, `spider2/DEEP-REVIEW.md`, `spider2/REVIEW-REQUEST.md`) were removed from every commit; the one commit that only moved them out became empty and was dropped.
2. The author's personal e-mail address was replaced by their GitHub noreply address, in commit metadata and in the `owner` fields of the Spider 2.0 layer files.

Nothing else changed: file contents, commit messages and dates are as recorded. Because commit hashes changed, run reports made before the rewrite record the old `repoCommit`; this table maps each old commit to the published one.

| Old commit | Published commit | Subject |
|---|---|---|
| `0c9de3c485b9` | `1ae85fbd9058` | Start the DQL benchmarks repository |
| `4ab64f6126f0` | `6766f849c46e` | Spider 2.0-DBT: inventory, scoring pipe and task import |
| `f09c28929f07` | `9b66f910cde9` | Spider 2.0-DBT: agent runner, development tasks and answer isolation |
| `d044053d8520` | `6ac8299e274d` | Spider 2.0-DBT: pin dbt 1.9 and attempt every task |
| `08ad6ff145b0` | `9c28c4af4416` | Focus on Ask text-to-SQL over dbt; remove Spider 2.0-DBT |
| `0bf1071fee2a` | `08adf5dc7b0a` | Insurance: build dbt Labs' project, compute correct answers, run Ask |
| `185056eca84a` | `e73d3a07f55d` | Insurance: fresh project per run, pinned settings, timeout diagnosis |
| `9e59ccf5aed9` | `fca399de499f` | Scorecard: every angle a buyer checks, and a scorer for insurance runs |
| `8997afc3cf2f` | `c7655c5df96c` | Insurance: first L0 result and the L1/L3 authoring rules |
| `ac30cf20d8a1` | `b8b85a74ac4e` | Insurance: L1 and L3 layers, unanswerable set, init-first layer builds |
| `47303c2ecb59` | `6093a10285ee` | Insurance: plain text-to-SQL baseline with dbt Labs' own prompt |
| `709a1533b97f` | `142979502b41` | Insurance: sub-r3 results; pin MetricFlow with the DuckDB adapter |
| `18e65aa7289f` | `a8049191370f` | Insurance: plain text-to-SQL baseline result; MetricFlow at DQL's range |
| `d36412440e17` | `0429e1416f5d` | Insurance: list the DQL defects the benchmark found |
| `f7f4f1bc5702` | `c7ef214b606a` | Insurance: sub-r5 results on the fixed DQL build |
| `f0ae91649d53` | `3dc6ea1ddffb` | REPORT: how the effort fix passed DQL's golden suites |
| `739dc9a93333` | `1115f102b853` | REPORT: defects 13-15 from the sub-r5 misses |
| `5e2bf7899bdf` | `27ffc0ab7f0f` | Methodology: when results are published |
| `35dd5bf2cdce` | `ab74bcc0baad` | Insurance: sub-r6 results (DQL f064f023) |
| `b1e0751ed3d0` | `9d2188d02fc7` | REPORT: sub-r6 results and defect 16 |
| `7d13272c238f` | `eba2588dcbe3` | REPORT: order the defects table |
| `5780f3e279c4` | `eef1560c4030` | Insurance: read repeat runs together (average, pooled CI, stability) |
| `1b32a26b80c0` | `c1e2e8c77262` | Insurance: grade the same answers several ways |
| `027ce7cdedd3` | `6272ec9b151a` | Docs: notes moved out of this repository |
| `a562a10333ca` | `3297b3824b0a` | Docs: keep notes outside this repository |
| `c09d64f70c2b` | `492b2cf30269` | Insurance: three repeats per layer on DQL 1.17.3 |
| `04d2695955fc` | `1e197f0732ed` | REPORT: order the defects table |
| `9f9166885b30` | `8e56f427d646` | insurance: sealed held-out set, baseline repeats, defects 17-18 diagnosis |
| `ce57d56f946f` | `7a51af50c762` | insurance: refuse to record over an interrupted attempt; speed breakdown |
| `baa4f2908eb0` | `97006c8965ac` | insurance: mark a run invalid when the AI provider refuses calls |
| `d1befcf51187` | `7bcb572df91d` | REPORT: invalid runs from the usage limit |
| `7912910dc84c` | `2adfb0c93e25` | insurance: fixed-build L3 repeats (67.5%), first held-out results, defect 19 |
| `58e3d9f5ece9` | `b403537b621a` | harness: Anthropic API runs with measured cost |
| `5ba2385b0c72` | `e1d00b6bf490` | REPORT: defects 19-27 fixed, ready for the API run |
| `ad67e1fda661` | `39b0bee2ba4b` | insurance: numbered held-out sets (a spent set is never overwritten) |
| `97456531a49c` | `fc87daa67b50` | insurance: held-out set 2 (sealed; written from the warehouse only) |
| `c51d134a5605` | `2d0e47b76cbd` | REPORT: Anthropic API runs, L3 72.4% vs text-to-SQL 40.7% |
| `eecd66d50cd8` | `328859da9541` | REPORT: held-out set 2 on the API (DQL 53.5% vs text-to-SQL 44.2%, p=0.34) |
| `2dd2a7c1c754` | `9ed1710a03a6` | run.mjs: --reading-effort (DQL_ASK_READING_EFFORT), recorded in the report |
| `dfa9ea44391e` | `950d82e9bebb` | REPORT: answer-key questions for the owner; latest fixes |
| `45fe02f47405` | `04c1a3261654` | REPORT: low-effort reading speed test |
| `118d5aecd737` | `8563a1ad5e7a` | REPORT: low-effort reading, 3 runs |
| `8047a58f8ef0` | `b5429e88a40b` | harness: Codex (ChatGPT subscription) for DQL runs and the text-to-SQL baseline |
| `003e8331f442` | `7d68343cf69a` | REPORT: Claude subscription runs on 1b3d2f39 (69.9%, stability 82.9%) |
| `d2591cda8ae1` | `929cb560b4de` | harness: local Ollama models (accuracy runs with DQL's largest deadline); baseline --only |
| `fb3a65c23c7a` | `aa0341ae3161` | REPORT: first local-model test (qwen3.8:27b, 6 questions) |
| `f439f6ec34d3` | `600c6bdd179d` | REPORT: local model full set (qwen3.8:27b: DQL 61.0% vs alone 39.0%) |
| `b97c2b62f4e4` | `ebb7fa532617` | harness: record how a runtime ended; insurance local-model arm and report |
| `a7548edeac8c` | `498c615b4abf` | spider2: Spider 2.0-Lite SQLite harness, baseline arm, reports and reviews |
| `d56f450246d5` | `53183280322e` | harness: every run records the build behind it; score prints trust with denominators and why questions stopped |
| `0692966c0f19` | `7f73877611f6` | harness: projects record the build that drafted them; a run refuses projects from other code |
| `5044ad011e08` | `3c86bdca7972` | harness: E0 and E1 arms for the drafter evidence work |
| `4c9e8fe1959d` | `67c6570b1c40` | harness: E2 arm for the result-review build |
| `02b6300ec212` | `cfc0ff8f5d1d` | harness: default model gpt-6-luna (Codex) |
| `e2069c2fa472` | `1ed3c9292816` | RESULTS: g6a on gpt-6-luna — DQL full stack 32/87 vs model alone 30/87 |
| `25b6304fc485` | `9c8025ac906d` | harness: a quick check in minutes before a full run in hours |
| `b467734e106c` | `16cad7d6039b` | harness: default model gpt-5.6-sol; E3 arm for the assume-and-state build |
| `64692e81d072` | `15035cc39970` | harness: E4 arm for the draft-first build; --case-timeout-ms |
| `f322b6f41966` | (removed: became empty after the planning documents were removed) | spider2: keep measurement reports here; planning documents moved out |
| `7227b67f5283` | `64ebc350d6cb` | harness: E5 arm for the SQLite-worker build |
| `13d429257a7f` | `174747679cc9` | harness: a baseline call the provider refuses stops the run as invalid |
| `f9f2885e3266` | `ff16f3af9460` | RESULTS: gpt-5.6-sol — Spider run sol-f1 (DQL 53/87 vs 48/87) and insurance sol-i1 (L3 73% vs text-to-SQL 44%) |
| `40ca690d3274` | `d4f50b77986d` | harness: Claude Sonnet 5 through the claude-code subscription by default; the baseline writes SQL at DQL's drafting effort |
| `f52f9f6ec9df` | `477399270659` | harness: E6 arm for the review-everywhere build |
| `3efe5450f1a9` | `f6fd911b7352` | harness: the baseline's refusal check reads a failed call's error output, never the model's SQL |
| `77c77035e98c` | `d43657420705` | RESULTS: Claude Sonnet 5 — Spider parity 45/45; insurance L3 75.6% and W2 78.0% vs text-to-SQL 48.8% |
| `386e3666935d` | `1f09df0dc335` | spider2: L2 and L3 arms from layers a blind author writes from the warehouse |
| `b7362ace0180` | `b5d349b57704` | spider2 layers: IPL and f1 L2/L3 written blind from the warehouse (pilot) |
| `d4dd19602fb8` | `3cf6fe343ecd` | spider2: pilot set (the 20 IPL and f1 tasks) |
| `c0d2d347c5d5` | `55b9a616e0e0` | RESULTS: Spider modeled-layer pilot — layers hurt through routing (2/20), neutral after the fix (7/20 vs L1 8/20) |
| `b28fa22810a4` | `58959c6cf93a` | insurance: business layer B (author, verifier, owner certification), LB/WB arms, sealed held-out set 3 |
| `e2c5f486ecad` | `74354221df10` | insurance/run: per-level authored-layer identity; capture matches questions with stray spaces |
| `1ae4c5d48189` | `856bb4180f55` | insurance/run: --resume keeps the answers of an attempt the provider cut off and re-asks only the refused questions |
| `dbce0707211d` | `8dbba99e0f59` | insurance/run: record every DQL_ASK_* experiment switch in the run identity |
| `70260d6a262b` | `f20224afe830` | insurance: --codex-effort pins every Codex call's reasoning level and the report records it |
| `eaf15c331916` | `48f4ec9f8f40` | insurance: find the codex command in the ChatGPT app's new codex-cli/bin folder, and say so when it is missing |
| `3fab9135ed14` | `bbd3295625f3` | insurance: --codex-home runs Codex from an isolated, signed-in home with no personal instructions, plugins or memories |
| `b24809bde7f5` | `1f1dc1d82578` | insurance: a model at capacity or a 429 is a provider refusal, resumed after a wait, never a DQL stop |
| `a84be31d1a2a` | `b069dc09157e` | insurance: deep Codex reasoning runs get the local-model deadline and DQL's longest call limit |
| `2a2c09f0cde2` | `b1a2edd981a6` | insurance: every Codex run at a pinned reasoning level gets the accuracy-first deadlines |
| `5cd9153baff6` | `13784b1803ef` | insurance: an agentic text-to-SQL baseline that explores the warehouse before it answers |
| `220bbafdd500` | `30e4bf8c3731` | insurance: gold audit — three answer-key disputes agreed with the owner (loss-ratio definition, unrequested column, total vs list) |
| `f7e42c424007` | `335426c66ad0` | insurance: agent baseline with DQL's W2 knowledge (--context modeling): the fair comparison for the W2 level |
| `f2e835af2715` | `6f60a71bf0cd` | insurance: pre-register sealed set 5 (non-Claude question writer, fair agent baseline, one primary test) |

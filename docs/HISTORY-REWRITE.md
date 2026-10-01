# History rewrite of 30 September 2026

Before the first push to GitHub, three internal planning documents (`spider2/BUILD-PLAN.md`, `spider2/DEEP-REVIEW.md`, `spider2/REVIEW-REQUEST.md`) were removed from every commit. Nothing else changed: file contents, authors and dates are as recorded. Because commit hashes changed, run reports made before the rewrite record the old `repoCommit`; this table maps each old commit to its new one. Commit messages and dates are unchanged.

| Old commit | New commit | Subject |
|---|---|---|
| `0c9de3c485b9` | `0c9de3c485b9` | Start the DQL benchmarks repository |
| `4ab64f6126f0` | `4ab64f6126f0` | Spider 2.0-DBT: inventory, scoring pipe and task import |
| `f09c28929f07` | `f09c28929f07` | Spider 2.0-DBT: agent runner, development tasks and answer isolation |
| `d044053d8520` | `d044053d8520` | Spider 2.0-DBT: pin dbt 1.9 and attempt every task |
| `08ad6ff145b0` | `08ad6ff145b0` | Focus on Ask text-to-SQL over dbt; remove Spider 2.0-DBT |
| `0bf1071fee2a` | `0bf1071fee2a` | Insurance: build dbt Labs' project, compute correct answers, run Ask |
| `185056eca84a` | `185056eca84a` | Insurance: fresh project per run, pinned settings, timeout diagnosis |
| `9e59ccf5aed9` | `9e59ccf5aed9` | Scorecard: every angle a buyer checks, and a scorer for insurance runs |
| `8997afc3cf2f` | `8997afc3cf2f` | Insurance: first L0 result and the L1/L3 authoring rules |
| `ac30cf20d8a1` | `ac30cf20d8a1` | Insurance: L1 and L3 layers, unanswerable set, init-first layer builds |
| `47303c2ecb59` | `47303c2ecb59` | Insurance: plain text-to-SQL baseline with dbt Labs' own prompt |
| `709a1533b97f` | `709a1533b97f` | Insurance: sub-r3 results; pin MetricFlow with the DuckDB adapter |
| `18e65aa7289f` | `18e65aa7289f` | Insurance: plain text-to-SQL baseline result; MetricFlow at DQL's range |
| `d36412440e17` | `d36412440e17` | Insurance: list the DQL defects the benchmark found |
| `f7f4f1bc5702` | `f7f4f1bc5702` | Insurance: sub-r5 results on the fixed DQL build |
| `f0ae91649d53` | `f0ae91649d53` | REPORT: how the effort fix passed DQL's golden suites |
| `739dc9a93333` | `739dc9a93333` | REPORT: defects 13-15 from the sub-r5 misses |
| `5e2bf7899bdf` | `5e2bf7899bdf` | Methodology: when results are published |
| `35dd5bf2cdce` | `35dd5bf2cdce` | Insurance: sub-r6 results (DQL f064f023) |
| `b1e0751ed3d0` | `b1e0751ed3d0` | REPORT: sub-r6 results and defect 16 |
| `7d13272c238f` | `7d13272c238f` | REPORT: order the defects table |
| `5780f3e279c4` | `5780f3e279c4` | Insurance: read repeat runs together (average, pooled CI, stability) |
| `1b32a26b80c0` | `1b32a26b80c0` | Insurance: grade the same answers several ways |
| `027ce7cdedd3` | `027ce7cdedd3` | Docs: notes moved out of this repository |
| `a562a10333ca` | `a562a10333ca` | Docs: keep notes outside this repository |
| `c09d64f70c2b` | `c09d64f70c2b` | Insurance: three repeats per layer on DQL 1.17.3 |
| `04d2695955fc` | `04d2695955fc` | REPORT: order the defects table |
| `9f9166885b30` | `9f9166885b30` | insurance: sealed held-out set, baseline repeats, defects 17-18 diagnosis |
| `ce57d56f946f` | `ce57d56f946f` | insurance: refuse to record over an interrupted attempt; speed breakdown |
| `baa4f2908eb0` | `baa4f2908eb0` | insurance: mark a run invalid when the AI provider refuses calls |
| `d1befcf51187` | `d1befcf51187` | REPORT: invalid runs from the usage limit |
| `7912910dc84c` | `7912910dc84c` | insurance: fixed-build L3 repeats (67.5%), first held-out results, defect 19 |
| `58e3d9f5ece9` | `58e3d9f5ece9` | harness: Anthropic API runs with measured cost |
| `5ba2385b0c72` | `5ba2385b0c72` | REPORT: defects 19-27 fixed, ready for the API run |
| `ad67e1fda661` | `ad67e1fda661` | insurance: numbered held-out sets (a spent set is never overwritten) |
| `97456531a49c` | `97456531a49c` | insurance: held-out set 2 (sealed; written from the warehouse only) |
| `c51d134a5605` | `c51d134a5605` | REPORT: Anthropic API runs, L3 72.4% vs text-to-SQL 40.7% |
| `eecd66d50cd8` | `eecd66d50cd8` | REPORT: held-out set 2 on the API (DQL 53.5% vs text-to-SQL 44.2%, p=0.34) |
| `2dd2a7c1c754` | `2dd2a7c1c754` | run.mjs: --reading-effort (DQL_ASK_READING_EFFORT), recorded in the report |
| `dfa9ea44391e` | `dfa9ea44391e` | REPORT: answer-key questions for the owner; latest fixes |
| `45fe02f47405` | `45fe02f47405` | REPORT: low-effort reading speed test |
| `118d5aecd737` | `118d5aecd737` | REPORT: low-effort reading, 3 runs |
| `8047a58f8ef0` | `8047a58f8ef0` | harness: Codex (ChatGPT subscription) for DQL runs and the text-to-SQL baseline |
| `003e8331f442` | `003e8331f442` | REPORT: Claude subscription runs on 1b3d2f39 (69.9%, stability 82.9%) |
| `d2591cda8ae1` | `d2591cda8ae1` | harness: local Ollama models (accuracy runs with DQL's largest deadline); baseline --only |
| `fb3a65c23c7a` | `fb3a65c23c7a` | REPORT: first local-model test (qwen3.8:27b, 6 questions) |
| `f439f6ec34d3` | `f439f6ec34d3` | REPORT: local model full set (qwen3.8:27b: DQL 61.0% vs alone 39.0%) |
| `b97c2b62f4e4` | `b97c2b62f4e4` | harness: record how a runtime ended; insurance local-model arm and report |
| `a7548edeac8c` | `a38c8fdf5b96` | spider2: Spider 2.0-Lite SQLite harness, baseline arm, reports and reviews |
| `d56f450246d5` | `4f94f61ac321` | harness: every run records the build behind it; score prints trust with denominators and why questions stopped |
| `0692966c0f19` | `4f89b28a5d3e` | harness: projects record the build that drafted them; a run refuses projects from other code |
| `5044ad011e08` | `df1f8631c1ec` | harness: E0 and E1 arms for the drafter evidence work |
| `4c9e8fe1959d` | `69b27c68f80d` | harness: E2 arm for the result-review build |
| `02b6300ec212` | `619947911671` | harness: default model gpt-6-luna (Codex) |
| `e2069c2fa472` | `7477c13ca9ba` | RESULTS: g6a on gpt-6-luna — DQL full stack 32/87 vs model alone 30/87 |
| `25b6304fc485` | `306b4a1567a5` | harness: a quick check in minutes before a full run in hours |
| `b467734e106c` | `691e8ce47da3` | harness: default model gpt-5.6-sol; E3 arm for the assume-and-state build |
| `64692e81d072` | `8a5b7d998b40` | harness: E4 arm for the draft-first build; --case-timeout-ms |
| `f322b6f41966` | `(removed: became empty after the planning documents were removed)` | spider2: keep measurement reports here; planning documents moved out |
| `7227b67f5283` | `9125e4048ab3` | harness: E5 arm for the SQLite-worker build |
| `13d429257a7f` | `2c4d8068d6ab` | harness: a baseline call the provider refuses stops the run as invalid |
| `f9f2885e3266` | `a94f9ce3de15` | RESULTS: gpt-5.6-sol — Spider run sol-f1 (DQL 53/87 vs 48/87) and insurance sol-i1 (L3 73% vs text-to-SQL 44%) |
| `40ca690d3274` | `6184b85642af` | harness: Claude Sonnet 5 through the claude-code subscription by default; the baseline writes SQL at DQL's drafting effort |
| `f52f9f6ec9df` | `ebf86a93fe35` | harness: E6 arm for the review-everywhere build |
| `3efe5450f1a9` | `a1ea77558b0e` | harness: the baseline's refusal check reads a failed call's error output, never the model's SQL |
| `77c77035e98c` | `97379ddb4573` | RESULTS: Claude Sonnet 5 — Spider parity 45/45; insurance L3 75.6% and W2 78.0% vs text-to-SQL 48.8% |
| `386e3666935d` | `d84b9d5c3ce8` | spider2: L2 and L3 arms from layers a blind author writes from the warehouse |
| `b7362ace0180` | `e3d3c2cc22c3` | spider2 layers: IPL and f1 L2/L3 written blind from the warehouse (pilot) |
| `d4dd19602fb8` | `62e0b74ee8c2` | spider2: pilot set (the 20 IPL and f1 tasks) |
| `c0d2d347c5d5` | `88995901ea23` | RESULTS: Spider modeled-layer pilot — layers hurt through routing (2/20), neutral after the fix (7/20 vs L1 8/20) |
| `b28fa22810a4` | `aface38f58b5` | insurance: business layer B (author, verifier, owner certification), LB/WB arms, sealed held-out set 3 |
| `e2c5f486ecad` | `9e9b6f272063` | insurance/run: per-level authored-layer identity; capture matches questions with stray spaces |
| `1ae4c5d48189` | `3e2da83e165e` | insurance/run: --resume keeps the answers of an attempt the provider cut off and re-asks only the refused questions |
| `dbce0707211d` | `c84616d1de10` | insurance/run: record every DQL_ASK_* experiment switch in the run identity |
| `70260d6a262b` | `27c8a11fe99b` | insurance: --codex-effort pins every Codex call's reasoning level and the report records it |
| `eaf15c331916` | `5f0f174eb56d` | insurance: find the codex command in the ChatGPT app's new codex-cli/bin folder, and say so when it is missing |
| `3fab9135ed14` | `c7486910d5a1` | insurance: --codex-home runs Codex from an isolated, signed-in home with no personal instructions, plugins or memories |
| `b24809bde7f5` | `f019277fe623` | insurance: a model at capacity or a 429 is a provider refusal, resumed after a wait, never a DQL stop |
| `a84be31d1a2a` | `1c96380c26ec` | insurance: deep Codex reasoning runs get the local-model deadline and DQL's longest call limit |
| `2a2c09f0cde2` | `306c71cdcdfb` | insurance: every Codex run at a pinned reasoning level gets the accuracy-first deadlines |
| `5cd9153baff6` | `2c9c691e71c7` | insurance: an agentic text-to-SQL baseline that explores the warehouse before it answers |
| `220bbafdd500` | `69954750d5ff` | insurance: gold audit — three answer-key disputes agreed with the owner (loss-ratio definition, unrequested column, total vs list) |
| `f7e42c424007` | `8467006ed46a` | insurance: agent baseline with DQL's W2 knowledge (--context modeling): the fair comparison for the W2 level |
| `f2e835af2715` | `1ab17d8c8c9d` | insurance: pre-register sealed set 5 (non-Claude question writer, fair agent baseline, one primary test) |

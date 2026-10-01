# Insurance benchmark: full-ladder statistics (fl-* runs)

Generated 2026-09-29 21:21 UTC by `analyze.py` from `work/insurance/runs/fl-*/<level>/<set>/report.json`. Read-only on the results. Held-out sets are shown as counts and rates only.

Levels: **P** = plain model, one-shot SQL from the full DDL (baseline-full); **L0** dbt only; **L1** +modeling; **L2** +dbt MetricFlow metrics; **L3** +skills; **LB** +business layer; **W0** warehouse only (no dbt); **W1** +modeling; **W2** +native metrics; **WB** +business layer.

Sets: **heldout-3** (40 sealed questions, the publishable set); **all** (41 development questions); **heldout-3-unanswerable** (10; a correct stop counts as passed).

## Models

| Run | Model | Provider | Effort (P / DQL) | Status |
|---|---|---|---|---|
| fl-opus | claude-opus-5-5 | claude-code | high / route default | complete |
| fl-sonnet | claude-sonnet-5 | claude-code | high / route default | complete |
| fl-qwen | qwen3.8:27b | ollama | high / route default | complete; heldout-3 + unanswerable only |
| fl-luna | gpt-6-luna | codex | max / max | INCOMPLETE (still running) |
| fl-sol | gpt-6-sol | codex | medium / medium | INCOMPLETE (still running) |
| fl-terra | gpt-5.6-terra | codex | high / high | INCOMPLETE (still running) |

## Data problems and provenance

**Missing or invalid reports** (treated as missing):

| Run | Level | Set | Why |
|---|---|---|---|
| fl-luna | L0 | all | INVALID: the AI provider refused calls during the run (40 questions) |
| fl-luna | L0 | heldout-3-unanswerable | not run (no directory) |
| fl-luna | L1 | all | not run (no directory) |
| fl-luna | L1 | heldout-3-unanswerable | not run (no directory) |
| fl-luna | L2 | all | not run (no directory) |
| fl-luna | L2 | heldout-3-unanswerable | not run (no directory) |
| fl-luna | L3 | all | not run (no directory) |
| fl-luna | L3 | heldout-3-unanswerable | not run (no directory) |
| fl-luna | LB | heldout-3 | not run (no directory) |
| fl-luna | LB | all | not run (no directory) |
| fl-luna | LB | heldout-3-unanswerable | not run (no directory) |
| fl-luna | W0 | all | not run (no directory) |
| fl-luna | W0 | heldout-3-unanswerable | not run (no directory) |
| fl-luna | W1 | all | not run (no directory) |
| fl-luna | W1 | heldout-3-unanswerable | not run (no directory) |
| fl-luna | W2 | all | not run (no directory) |
| fl-luna | W2 | heldout-3-unanswerable | not run (no directory) |
| fl-luna | WB | heldout-3 | not run (no directory) |
| fl-luna | WB | all | not run (no directory) |
| fl-luna | WB | heldout-3-unanswerable | not run (no directory) |
| fl-sol | L0 | heldout-3-unanswerable | not run (no directory) |
| fl-sol | L1 | heldout-3-unanswerable | not run (no directory) |
| fl-sol | L2 | heldout-3-unanswerable | not run (no directory) |
| fl-sol | L3 | heldout-3-unanswerable | not run (no directory) |
| fl-sol | LB | all | not run (no directory) |
| fl-sol | LB | heldout-3-unanswerable | not run (no directory) |
| fl-sol | W0 | all | INVALID: the AI provider refused calls during the run (29 questions) |
| fl-sol | W0 | heldout-3-unanswerable | not run (no directory) |
| fl-sol | W1 | all | not run (no directory) |
| fl-sol | W1 | heldout-3-unanswerable | not run (no directory) |
| fl-sol | W2 | all | not run (no directory) |
| fl-sol | W2 | heldout-3-unanswerable | not run (no directory) |
| fl-sol | WB | heldout-3 | not run (no directory) |
| fl-sol | WB | all | not run (no directory) |
| fl-sol | WB | heldout-3-unanswerable | not run (no directory) |
| fl-terra | L0 | heldout-3-unanswerable | not run (no directory) |
| fl-terra | L1 | heldout-3-unanswerable | not run (no directory) |
| fl-terra | L2 | heldout-3-unanswerable | not run (no directory) |
| fl-terra | L3 | heldout-3-unanswerable | not run (no directory) |
| fl-terra | LB | all | not run (no directory) |
| fl-terra | LB | heldout-3-unanswerable | not run (no directory) |
| fl-terra | W0 | heldout-3-unanswerable | not run (no directory) |
| fl-terra | W1 | heldout-3-unanswerable | not run (no directory) |
| fl-terra | W2 | all | INVALID: the AI provider refused calls during the run (11 questions) |
| fl-terra | W2 | heldout-3-unanswerable | not run (no directory) |
| fl-terra | WB | heldout-3 | not run (no directory) |
| fl-terra | WB | all | not run (no directory) |
| fl-terra | WB | heldout-3-unanswerable | not run (no directory) |

**Build exceptions** (expected DQL 49c0e1cb, and 627009a1 for LB/WB):

- fl-sol LB heldout-3: ran on **49c0e1cb**, expected 627009a1
- fl-terra LB heldout-3: ran on **49c0e1cb**, expected 627009a1

P (baseline-full) does not use DQL; its `identity.dql.commit` is the harness repo commit: fl-luna b24809bd, fl-opus 3fab9135, fl-qwen 2a2c09f0, fl-sol 2a2c09f0, fl-sonnet 2a2c09f0, fl-terra 2a2c09f0.

**Resumed reports** (questions kept from an earlier attempt that hit a provider limit; only the refused questions were re-run): fl-luna L1 heldout-3 kept 36; fl-luna L2 heldout-3 kept 33; fl-luna L3 heldout-3 kept 20; fl-luna W0 heldout-3 kept 10; fl-luna W2 heldout-3 kept 12; fl-sol L1 all kept 8; fl-sol L2 all kept 38; fl-sol L2 heldout-3 kept 2; fl-sol LB heldout-3 kept 10; fl-sol W1 heldout-3 kept 39; fl-sonnet WB heldout-3 kept 35; fl-terra L2 all kept 18; fl-terra L2 heldout-3 kept 31; fl-terra LB heldout-3 kept 31; fl-terra W0 all kept 39.

Superseded attempt directories beside the canonical ones (ignored): 23 (21 invalid, 2 without report.json).

Trust states seen: blocked, governed, none, not_applicable, review_required. No answer was `certified`; every trusted answer is `governed`. `not_applicable` and `review_required` are not trusted.

## Held-out-3 accuracy, models x levels

k/40 execution-matched. `*` = significantly different from the same model's P (exact McNemar, p<0.05); `+`/`-` give the direction.

| Model | P | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 30/40 (75%) | 24/40 (60%) | 34/40 (85%) | 29/40 (72%) | 33/40 (82%) | 29/40 (72%) | 33/40 (82%) | 32/40 (80%) | 36/40 (90%) | 34/40 (85%) |
| Sonnet 5 | 25/40 (62%) | 20/40 (50%) | 33/40 (82%) | 34/40 (85%) *+ | 29/40 (72%) | 29/40 (72%) | 29/40 (72%) | 35/40 (88%) *+ | 36/40 (90%) *+ | 34/40 (85%) *+ |
| Qwen 3.8 27B (local) | 18/40 (45%) | 10/40 (25%) *- | 28/40 (70%) *+ | 27/40 (68%) *+ | 26/40 (65%) *+ | 23/40 (57%) | 23/40 (57%) | 29/40 (72%) *+ | 27/40 (68%) *+ | 31/40 (78%) *+ |
| GPT-6 Luna (max) | 25/40 (62%) | 19/40 (48%) | 32/40 (80%) | 32/40 (80%) | 32/40 (80%) | missing | 30/40 (75%) | 34/40 (85%) *+ | 31/40 (78%) | missing |
| GPT-6 Sol (medium) | 26/40 (65%) | 20/40 (50%) | 30/40 (75%) | 31/40 (78%) | 33/40 (82%) | 29/40 (72%) | 30/40 (75%) | 32/40 (80%) | 35/40 (88%) *+ | missing |
| GPT-5.6 Terra (high) | 26/40 (65%) | 17/40 (42%) *- | 30/40 (75%) | 30/40 (75%) | 31/40 (78%) | 30/40 (75%) | 27/40 (68%) | 31/40 (78%) | 29/40 (72%) | missing |

## Which levels beat P on heldout-3

Per model: discordant pairs vs P as `+gained/-lost`, exact McNemar p. **Bold** = p<0.05.

| Model | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | +6/-12 p=0.238 | +7/-3 p=0.344 | +4/-5 p=1.000 | +5/-2 p=0.453 | +6/-7 p=1.000 | +7/-4 p=0.549 | +6/-4 p=0.754 | +7/-1 p=0.070 | +6/-2 p=0.289 |
| Sonnet 5 | +4/-9 p=0.267 | +12/-4 p=0.077 | **+12/-3 p=0.035** | +10/-6 p=0.454 | +11/-7 p=0.481 | +8/-4 p=0.388 | **+11/-1 p=0.006** | **+13/-2 p=0.007** | **+13/-4 p=0.049** |
| Qwen 3.8 27B (local) | **+1/-9 p=0.021** | **+12/-2 p=0.013** | **+11/-2 p=0.022** | **+9/-1 p=0.021** | +10/-5 p=0.302 | +9/-4 p=0.267 | **+13/-2 p=0.007** | **+12/-3 p=0.035** | **+14/-1 p=<0.001** |
| GPT-6 Luna (max) | +5/-11 p=0.210 | +9/-2 p=0.065 | +9/-2 p=0.065 | +10/-3 p=0.092 | missing | +8/-3 p=0.227 | **+10/-1 p=0.012** | +8/-2 p=0.109 | missing |
| GPT-6 Sol (medium) | +4/-10 p=0.180 | +6/-2 p=0.289 | +7/-2 p=0.180 | +9/-2 p=0.065 | +7/-4 p=0.549 | +8/-4 p=0.388 | +10/-4 p=0.180 | **+10/-1 p=0.012** | missing |
| GPT-5.6 Terra (high) | **+4/-13 p=0.049** | +8/-4 p=0.388 | +8/-4 p=0.388 | +8/-3 p=0.227 | +8/-4 p=0.388 | +5/-4 p=1.000 | +7/-2 p=0.180 | +7/-4 p=0.549 | missing |

Pooled across models (per level: models where the level is significantly above P, out of models with data; and a stratified exact McNemar that sums discordant pairs over models. The stratified test treats model x question pairs as independent, which they are not - the same 40 questions repeat - so read it as indicative).

| Level | Sig. above P | Sig. below P | Models with data | Pooled +gained/-lost | Pooled p |
|---|---|---|---|---|---|
| L0 | 0 (-) | 2 (fl-qwen, fl-terra) | 6 | +24/-64 | <0.001 |
| L1 | 1 (fl-qwen) | 0 (-) | 6 | +54/-17 | <0.001 |
| L2 | 2 (fl-sonnet, fl-qwen) | 0 (-) | 6 | +51/-18 | <0.001 |
| L3 | 1 (fl-qwen) | 0 (-) | 6 | +51/-17 | <0.001 |
| LB | 0 (-) | 0 (-) | 5 | +42/-27 | 0.091 |
| W0 | 0 (-) | 0 (-) | 6 | +45/-23 | 0.010 |
| W1 | 3 (fl-sonnet, fl-qwen, fl-luna) | 0 (-) | 6 | +57/-14 | <0.001 |
| W2 | 3 (fl-sonnet, fl-qwen, fl-sol) | 0 (-) | 6 | +57/-13 | <0.001 |
| WB | 2 (fl-sonnet, fl-qwen) | 0 (-) | 3 | +33/-7 | <0.001 |

## Per model, level and set

Columns: accuracy k/n with Wilson 95% CI; paired vs P and vs the level below as `+gained/-lost (p)`; trust as wrong/trusted and trust precision; stops (no SQL); median and p90 latency in seconds; mean provider dispatches per question.

### Opus 5.5 (fl-opus)

#### heldout-3

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 30/40 (75%) | 60%-86% | - | - | 0/0 | - | 0 | 5.8 | 11.3 | 1.00 | n/a |
| L0 | 24/40 (60%) | 45%-74% | +6/-12 (0.238) | (= vs P) | 0/0 | - | 10 | 25.4 | 55.1 | 3.38 | 49c0e1cb |
| L1 | 34/40 (85%) | 71%-93% | +7/-3 (0.344) | **+12/-2 (0.013)** | 0/0 | - | 1 | 20.9 | 36.6 | 3.15 | 49c0e1cb |
| L2 | 29/40 (72%) | 57%-84% | +4/-5 (1.000) | +0/-5 (0.062) | 0/4 | 100% | 4 | 21.0 | 38.8 | 2.90 | 49c0e1cb |
| L3 | 33/40 (82%) | 68%-91% | +5/-2 (0.453) | +5/-1 (0.219) | 0/4 | 100% | 2 | 21.5 | 41.3 | 3.00 | 49c0e1cb |
| LB | 29/40 (72%) | 57%-84% | +6/-7 (1.000) | +2/-6 (0.289) | **4/11** | 64% | 4 | 21.6 | 40.2 | 2.67 | 627009a1 |
| W0 | 33/40 (82%) | 68%-91% | +7/-4 (0.549) | (= vs P) | 0/0 | - | 0 | 11.2 | 22.3 | 2.02 | 49c0e1cb |
| W1 | 32/40 (80%) | 65%-90% | +6/-4 (0.754) | +0/-1 (1.000) | 0/0 | - | 0 | 12.1 | 22.7 | 2.10 | 49c0e1cb |
| W2 | 36/40 (90%) | 77%-96% | +7/-1 (0.070) | +5/-1 (0.219) | 0/0 | - | 0 | 16.1 | 38.5 | 2.62 | 49c0e1cb |
| WB | 34/40 (85%) | 71%-93% | +6/-2 (0.289) | +0/-2 (0.500) | **1/5** | 80% | 0 | 17.9 | 34.8 | 2.50 | 627009a1 |

#### all

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 31/41 (76%) | 61%-86% | - | - | 0/0 | - | 0 | 6.6 | 13.4 | 1.00 | n/a |
| L0 | 23/41 (56%) | 41%-70% | **+0/-8 (0.008)** | (= vs P) | 0/0 | - | 8 | 24.7 | 65.3 | 3.41 | 49c0e1cb |
| L1 | 33/41 (80%) | 66%-90% | +2/-0 (0.500) | **+10/-0 (0.002)** | 0/0 | - | 2 | 28.0 | 52.0 | 3.34 | 49c0e1cb |
| L2 | 31/41 (76%) | 61%-86% | +1/-1 (1.000) | +1/-3 (0.625) | **1/6** | 83% | 3 | 28.0 | 51.2 | 2.85 | 49c0e1cb |
| L3 | 32/41 (78%) | 63%-88% | +2/-1 (1.000) | +2/-1 (1.000) | 0/6 | 100% | 1 | 23.7 | 43.7 | 2.78 | 49c0e1cb |
| LB | 29/41 (71%) | 56%-82% | +1/-3 (0.625) | +1/-4 (0.375) | **2/15** | 87% | 2 | 14.9 | 51.6 | 2.10 | 627009a1 |
| W0 | 30/41 (73%) | 58%-84% | +2/-3 (1.000) | (= vs P) | 0/0 | - | 0 | 17.4 | 34.7 | 2.17 | 49c0e1cb |
| W1 | 32/41 (78%) | 63%-88% | +2/-1 (1.000) | +2/-0 (0.500) | 0/0 | - | 1 | 16.3 | 47.1 | 2.34 | 49c0e1cb |
| W2 | 32/41 (78%) | 63%-88% | +2/-1 (1.000) | +0/-0 (1.000) | 0/2 | 100% | 1 | 20.3 | 43.7 | 2.68 | 49c0e1cb |
| WB | 30/41 (73%) | 58%-84% | +1/-2 (1.000) | +1/-3 (0.625) | **1/8** | 88% | 0 | 18.1 | 32.3 | 2.27 | 627009a1 |

#### heldout-3-unanswerable

| Level | Correct stops k/n | Wilson 95% CI | vs level below | Stops | Wrong/trusted | Median s | p90 s | Dispatch |
|---|---|---|---|---|---|---|---|---|
| L0 | 10/10 (100%) | 72%-100% | - | 10 | 0/0 | 18.0 | 41.0 | 2.80 |
| L1 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 18.1 | 22.0 | 3.10 |
| L2 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 18.9 | 29.1 | 3.20 |
| L3 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 16.9 | 22.8 | 3.20 |
| LB | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 21.3 | 24.8 | 3.10 |
| W0 | 10/10 (100%) | 72%-100% | - | 10 | 0/0 | 16.8 | 23.1 | 2.90 |
| W1 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 16.7 | 29.6 | 2.80 |
| W2 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 21.2 | 28.2 | 2.80 |
| WB | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 13.7 | 16.4 | 2.10 |

### Sonnet 5 (fl-sonnet)

#### heldout-3

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 25/40 (62%) | 47%-76% | - | - | 0/0 | - | 0 | 5.4 | 35.5 | 1.00 | n/a |
| L0 | 20/40 (50%) | 35%-65% | +4/-9 (0.267) | (= vs P) | 0/0 | - | 16 | 41.1 | 174.5 | 3.20 | 49c0e1cb |
| L1 | 33/40 (82%) | 68%-91% | +12/-4 (0.077) | **+14/-1 (<0.001)** | 0/0 | - | 5 | 31.7 | 181.4 | 2.95 | 49c0e1cb |
| L2 | 34/40 (85%) | 71%-93% | **+12/-3 (0.035)** | +3/-2 (1.000) | 0/3 | 100% | 3 | 37.8 | 96.3 | 3.30 | 49c0e1cb |
| L3 | 29/40 (72%) | 57%-84% | +10/-6 (0.454) | +0/-5 (0.062) | 0/3 | 100% | 5 | 37.1 | 104.2 | 3.17 | 49c0e1cb |
| LB | 29/40 (72%) | 57%-84% | +11/-7 (0.481) | +6/-6 (1.000) | **4/11** | 64% | 6 | 36.7 | 104.6 | 2.98 | 627009a1 |
| W0 | 29/40 (72%) | 57%-84% | +8/-4 (0.388) | (= vs P) | 0/0 | - | 6 | 13.4 | 51.0 | 2.30 | 49c0e1cb |
| W1 | 35/40 (88%) | 74%-95% | **+11/-1 (0.006)** | +7/-1 (0.070) | 0/0 | - | 1 | 11.6 | 26.0 | 2.10 | 49c0e1cb |
| W2 | 36/40 (90%) | 77%-96% | **+13/-2 (0.007)** | +2/-1 (1.000) | 0/0 | - | 1 | 21.4 | 81.2 | 2.77 | 49c0e1cb |
| WB | 34/40 (85%) | 71%-93% | **+13/-4 (0.049)** | +2/-4 (0.688) | 0/4 | 100% | 2 | 23.0 | 59.6 | 2.60 | 627009a1 |

#### all

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 21/41 (51%) | 36%-66% | - | - | 0/0 | - | 0 | 11.5 | 55.9 | 1.00 | n/a |
| L0 | 10/41 (24%) | 14%-39% | **+2/-13 (0.007)** | (= vs P) | 0/0 | - | 21 | 55.5 | 148.3 | 2.98 | 49c0e1cb |
| L1 | 27/41 (66%) | 51%-78% | +9/-3 (0.146) | **+17/-0 (<0.001)** | 0/0 | - | 3 | 36.6 | 122.8 | 3.39 | 49c0e1cb |
| L2 | 30/41 (73%) | 58%-84% | **+12/-3 (0.035)** | +4/-1 (0.375) | 0/10 | 100% | 2 | 43.4 | 139.7 | 2.98 | 49c0e1cb |
| L3 | 29/41 (71%) | 56%-82% | **+10/-2 (0.039)** | +2/-3 (1.000) | **1/10** | 90% | 4 | 37.3 | 120.4 | 2.68 | 49c0e1cb |
| LB | 28/41 (68%) | 53%-80% | +10/-3 (0.092) | +2/-3 (1.000) | **3/19** | 84% | 4 | 9.5 | 31.8 | 1.85 | 627009a1 |
| W0 | 25/41 (61%) | 46%-74% | +7/-3 (0.344) | (= vs P) | 0/0 | - | 12 | 25.9 | 92.4 | 2.54 | 49c0e1cb |
| W1 | 33/41 (80%) | 66%-90% | **+13/-1 (0.002)** | **+8/-0 (0.008)** | 0/0 | - | 2 | 22.3 | 80.3 | 2.41 | 49c0e1cb |
| W2 | 29/41 (71%) | 56%-82% | **+10/-2 (0.039)** | +2/-6 (0.289) | 0/2 | 100% | 2 | 26.1 | 85.7 | 2.59 | 49c0e1cb |
| WB | 31/41 (76%) | 61%-86% | **+11/-1 (0.006)** | +3/-1 (0.625) | **2/14** | 86% | 0 | 8.4 | 21.7 | 1.73 | 627009a1 |

#### heldout-3-unanswerable

| Level | Correct stops k/n | Wilson 95% CI | vs level below | Stops | Wrong/trusted | Median s | p90 s | Dispatch |
|---|---|---|---|---|---|---|---|---|
| L0 | 10/10 (100%) | 72%-100% | - | 10 | 0/0 | 20.7 | 32.1 | 3.10 |
| L1 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 19.4 | 24.2 | 3.00 |
| L2 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 20.7 | 23.6 | 3.10 |
| L3 | 9/10 (90%) | 60%-98% | +0/-1 (1.000) | 9 | 0/0 | 19.3 | 34.9 | 3.00 |
| LB | 10/10 (100%) | 72%-100% | +1/-0 (1.000) | 10 | 0/0 | 12.6 | 15.9 | 3.00 |
| W0 | 10/10 (100%) | 72%-100% | - | 10 | 0/0 | 22.1 | 33.8 | 2.90 |
| W1 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 21.6 | 29.1 | 2.80 |
| W2 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 19.3 | 23.8 | 2.50 |
| WB | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 9.7 | 14.7 | 2.10 |

### Qwen 3.8 27B (local) (fl-qwen)

#### heldout-3

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 18/40 (45%) | 31%-60% | - | - | 0/0 | - | 0 | 10.7 | 24.7 | 1.00 | n/a |
| L0 | 10/40 (25%) | 14%-40% | **+1/-9 (0.021)** | (= vs P) | 0/0 | - | 26 | 108.1 | 169.6 | 3.20 | 49c0e1cb |
| L1 | 28/40 (70%) | 55%-82% | **+12/-2 (0.013)** | **+18/-0 (<0.001)** | 0/0 | - | 4 | 139.2 | 292.6 | 3.67 | 49c0e1cb |
| L2 | 27/40 (68%) | 52%-80% | **+11/-2 (0.022)** | +2/-3 (1.000) | 0/3 | 100% | 3 | 131.1 | 218.8 | 3.48 | 49c0e1cb |
| L3 | 26/40 (65%) | 50%-78% | **+9/-1 (0.021)** | +3/-4 (1.000) | 0/3 | 100% | 8 | 129.7 | 234.4 | 3.27 | 49c0e1cb |
| LB | 23/40 (57%) | 42%-71% | +10/-5 (0.302) | +3/-6 (0.508) | **3/11** | 73% | 10 | 116.3 | 238.6 | 2.55 | 627009a1 |
| W0 | 23/40 (57%) | 42%-71% | +9/-4 (0.267) | (= vs P) | 0/0 | - | 7 | 74.8 | 205.7 | 2.48 | 49c0e1cb |
| W1 | 29/40 (72%) | 57%-84% | **+13/-2 (0.007)** | **+6/-0 (0.031)** | 0/0 | - | 4 | 78.5 | 142.0 | 2.05 | 49c0e1cb |
| W2 | 27/40 (68%) | 52%-80% | **+12/-3 (0.035)** | +1/-3 (0.625) | **1/1** | 0% | 5 | 108.8 | 195.2 | 2.52 | 49c0e1cb |
| WB | 31/40 (78%) | 62%-88% | **+14/-1 (<0.001)** | +7/-3 (0.344) | **2/6** | 67% | 4 | 154.6 | 258.3 | 2.70 | 627009a1 |

#### heldout-3-unanswerable

| Level | Correct stops k/n | Wilson 95% CI | vs level below | Stops | Wrong/trusted | Median s | p90 s | Dispatch |
|---|---|---|---|---|---|---|---|---|
| L0 | 10/10 (100%) | 72%-100% | - | 10 | 0/0 | 98.8 | 110.3 | 3.00 |
| L1 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 129.3 | 135.4 | 3.00 |
| L2 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 122.9 | 138.3 | 2.90 |
| L3 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 128.8 | 176.9 | 3.10 |
| LB | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 151.0 | 176.7 | 3.20 |
| W0 | 10/10 (100%) | 72%-100% | - | 10 | 0/0 | 149.6 | 155.5 | 3.00 |
| W1 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 191.2 | 197.0 | 3.00 |
| W2 | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 159.4 | 171.2 | 2.70 |
| WB | 10/10 (100%) | 72%-100% | +0/-0 (1.000) | 10 | 0/0 | 156.7 | 172.2 | 2.10 |

### GPT-6 Luna (max) (fl-luna)

#### heldout-3

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 25/40 (62%) | 47%-76% | - | - | 0/0 | - | 0 | 14.7 | 43.9 | 1.00 | n/a |
| L0 | 19/40 (48%) | 33%-63% | +5/-11 (0.210) | (= vs P) | 0/0 | - | 15 | 105.4 | 390.8 | 3.50 | 49c0e1cb |
| L1 | 32/40 (80%) | 65%-90% | +9/-2 (0.065) | **+14/-1 (<0.001)** | 0/0 | - | 3 | 93.4 | 329.0 | 3.27 | 49c0e1cb |
| L2 | 32/40 (80%) | 65%-90% | +9/-2 (0.065) | +2/-2 (1.000) | 0/4 | 100% | 2 | 111.4 | 255.4 | 3.40 | 49c0e1cb |
| L3 | 32/40 (80%) | 65%-90% | +10/-3 (0.092) | +3/-3 (1.000) | 0/4 | 100% | 3 | 105.6 | 286.4 | 3.20 | 49c0e1cb |
| LB | missing: not run (no directory) | | | | | | | | | | |
| W0 | 30/40 (75%) | 60%-86% | +8/-3 (0.227) | (= vs P) | 0/0 | - | 5 | 34.0 | 137.8 | 2.27 | 49c0e1cb |
| W1 | 34/40 (85%) | 71%-93% | **+10/-1 (0.012)** | +4/-0 (0.125) | 0/0 | - | 0 | 26.4 | 76.7 | 2.02 | 49c0e1cb |
| W2 | 31/40 (78%) | 62%-88% | +8/-2 (0.109) | +1/-4 (0.375) | **1/1** | 0% | 1 | 51.0 | 289.4 | 2.60 | 49c0e1cb |
| WB | missing: not run (no directory) | | | | | | | | | | |

#### all

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 25/41 (61%) | 46%-74% | - | - | 0/0 | - | 0 | 23.1 | 66.1 | 1.00 | n/a |
| L0 | missing: INVALID: the AI provider refused calls during the run (40 questions) | | | | | | | | | | |
| L1 | missing: not run (no directory) | | | | | | | | | | |
| L2 | missing: not run (no directory) | | | | | | | | | | |
| L3 | missing: not run (no directory) | | | | | | | | | | |
| LB | missing: not run (no directory) | | | | | | | | | | |
| W0 | missing: not run (no directory) | | | | | | | | | | |
| W1 | missing: not run (no directory) | | | | | | | | | | |
| W2 | missing: not run (no directory) | | | | | | | | | | |
| WB | missing: not run (no directory) | | | | | | | | | | |

#### heldout-3-unanswerable

| Level | Correct stops k/n | Wilson 95% CI | vs level below | Stops | Wrong/trusted | Median s | p90 s | Dispatch |
|---|---|---|---|---|---|---|---|---|
| L0 | missing: not run (no directory) | | | | | | | |
| L1 | missing: not run (no directory) | | | | | | | |
| L2 | missing: not run (no directory) | | | | | | | |
| L3 | missing: not run (no directory) | | | | | | | |
| LB | missing: not run (no directory) | | | | | | | |
| W0 | missing: not run (no directory) | | | | | | | |
| W1 | missing: not run (no directory) | | | | | | | |
| W2 | missing: not run (no directory) | | | | | | | |
| WB | missing: not run (no directory) | | | | | | | |

### GPT-6 Sol (medium) (fl-sol)

#### heldout-3

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 26/40 (65%) | 50%-78% | - | - | 0/0 | - | 0 | 8.4 | 19.0 | 1.00 | n/a |
| L0 | 20/40 (50%) | 35%-65% | +4/-10 (0.180) | (= vs P) | 0/0 | - | 14 | 42.8 | 92.3 | 3.45 | 49c0e1cb |
| L1 | 30/40 (75%) | 60%-86% | +6/-2 (0.289) | **+11/-1 (0.006)** | 0/0 | - | 4 | 42.6 | 112.0 | 3.60 | 49c0e1cb |
| L2 | 31/40 (78%) | 62%-88% | +7/-2 (0.180) | +2/-1 (1.000) | 0/4 | 100% | 3 | 42.0 | 105.2 | 3.10 | 49c0e1cb |
| L3 | 33/40 (82%) | 68%-91% | +9/-2 (0.065) | +3/-1 (0.625) | 0/4 | 100% | 2 | 47.2 | 88.2 | 3.25 | 49c0e1cb |
| LB | 29/40 (72%) | 57%-84% | +7/-4 (0.549) | +3/-7 (0.344) | **3/10** | 70% | 3 | 41.9 | 82.5 | 3.02 | 49c0e1cb |
| W0 | 30/40 (75%) | 60%-86% | +8/-4 (0.388) | (= vs P) | 0/0 | - | 4 | 18.4 | 66.5 | 2.30 | 49c0e1cb |
| W1 | 32/40 (80%) | 65%-90% | +10/-4 (0.180) | +2/-0 (0.500) | 0/0 | - | 0 | 16.9 | 36.7 | 2.10 | 49c0e1cb |
| W2 | 35/40 (88%) | 74%-95% | **+10/-1 (0.012)** | +3/-0 (0.250) | 0/0 | - | 0 | 27.2 | 71.5 | 2.62 | 49c0e1cb |
| WB | missing: not run (no directory) | | | | | | | | | | |

#### all

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 22/41 (54%) | 39%-68% | - | - | 0/0 | - | 0 | 13.5 | 28.0 | 1.00 | n/a |
| L0 | 9/41 (22%) | 12%-37% | **+0/-13 (<0.001)** | (= vs P) | 0/0 | - | 29 | 46.7 | 91.6 | 3.02 | 49c0e1cb |
| L1 | 18/41 (44%) | 30%-59% | +4/-8 (0.388) | **+10/-1 (0.012)** | 0/0 | - | 12 | 49.4 | 94.9 | 3.54 | 49c0e1cb |
| L2 | 26/41 (63%) | 48%-76% | +7/-3 (0.344) | **+9/-1 (0.021)** | 0/5 | 100% | 5 | 53.2 | 83.6 | 3.07 | 49c0e1cb |
| L3 | 27/41 (66%) | 51%-78% | +8/-3 (0.227) | +3/-2 (1.000) | 0/5 | 100% | 6 | 47.9 | 106.4 | 3.17 | 49c0e1cb |
| LB | missing: not run (no directory) | | | | | | | | | | |
| W0 | missing: INVALID: the AI provider refused calls during the run (29 questions) | | | | | | | | | | |
| W1 | missing: not run (no directory) | | | | | | | | | | |
| W2 | missing: not run (no directory) | | | | | | | | | | |
| WB | missing: not run (no directory) | | | | | | | | | | |

#### heldout-3-unanswerable

| Level | Correct stops k/n | Wilson 95% CI | vs level below | Stops | Wrong/trusted | Median s | p90 s | Dispatch |
|---|---|---|---|---|---|---|---|---|
| L0 | missing: not run (no directory) | | | | | | | |
| L1 | missing: not run (no directory) | | | | | | | |
| L2 | missing: not run (no directory) | | | | | | | |
| L3 | missing: not run (no directory) | | | | | | | |
| LB | missing: not run (no directory) | | | | | | | |
| W0 | missing: not run (no directory) | | | | | | | |
| W1 | missing: not run (no directory) | | | | | | | |
| W2 | missing: not run (no directory) | | | | | | | |
| WB | missing: not run (no directory) | | | | | | | |

### GPT-5.6 Terra (high) (fl-terra)

#### heldout-3

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 26/40 (65%) | 50%-78% | - | - | 0/0 | - | 0 | 7.5 | 17.6 | 1.00 | n/a |
| L0 | 17/40 (42%) | 29%-58% | **+4/-13 (0.049)** | (= vs P) | 0/0 | - | 19 | 32.3 | 73.4 | 3.33 | 49c0e1cb |
| L1 | 30/40 (75%) | 60%-86% | +8/-4 (0.388) | **+14/-1 (<0.001)** | 0/0 | - | 4 | 38.9 | 84.1 | 3.52 | 49c0e1cb |
| L2 | 30/40 (75%) | 60%-86% | +8/-4 (0.388) | +3/-3 (1.000) | 0/3 | 100% | 3 | 38.0 | 71.7 | 3.50 | 49c0e1cb |
| L3 | 31/40 (78%) | 62%-88% | +8/-3 (0.227) | +2/-1 (1.000) | 0/4 | 100% | 3 | 37.2 | 92.3 | 3.33 | 49c0e1cb |
| LB | 30/40 (75%) | 60%-86% | +8/-4 (0.388) | +4/-5 (1.000) | **1/7** | 86% | 4 | 33.7 | 76.2 | 3.38 | 49c0e1cb |
| W0 | 27/40 (68%) | 52%-80% | +5/-4 (1.000) | (= vs P) | 0/0 | - | 7 | 17.5 | 41.8 | 2.23 | 49c0e1cb |
| W1 | 31/40 (78%) | 62%-88% | +7/-2 (0.180) | +4/-0 (0.125) | 0/0 | - | 3 | 15.6 | 36.0 | 2.17 | 49c0e1cb |
| W2 | 29/40 (72%) | 57%-84% | +7/-4 (0.549) | +2/-4 (0.688) | **1/1** | 0% | 4 | 25.1 | 52.2 | 2.58 | 49c0e1cb |
| WB | missing: not run (no directory) | | | | | | | | | | |

#### all

| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P | 17/41 (41%) | 28%-57% | - | - | 0/0 | - | 0 | 10.5 | 21.3 | 1.00 | n/a |
| L0 | 11/41 (27%) | 16%-42% | +3/-9 (0.146) | (= vs P) | 0/0 | - | 24 | 34.1 | 53.9 | 3.37 | 49c0e1cb |
| L1 | 25/41 (61%) | 46%-74% | **+10/-2 (0.039)** | **+15/-1 (<0.001)** | 0/0 | - | 8 | 43.6 | 75.6 | 3.59 | 49c0e1cb |
| L2 | 27/41 (66%) | 51%-78% | **+11/-1 (0.006)** | +4/-2 (0.688) | **1/11** | 91% | 5 | 32.1 | 108.4 | 2.90 | 49c0e1cb |
| L3 | 30/41 (73%) | 58%-84% | **+13/-0 (<0.001)** | +4/-1 (0.375) | **1/11** | 91% | 1 | 36.2 | 89.0 | 2.95 | 49c0e1cb |
| LB | missing: not run (no directory) | | | | | | | | | | |
| W0 | 21/41 (51%) | 36%-66% | +6/-2 (0.289) | (= vs P) | 0/0 | - | 15 | 21.0 | 69.8 | 2.46 | 49c0e1cb |
| W1 | 25/41 (61%) | 46%-74% | **+9/-1 (0.021)** | +7/-3 (0.344) | 0/0 | - | 10 | 23.4 | 114.9 | 2.56 | 49c0e1cb |
| W2 | missing: INVALID: the AI provider refused calls during the run (11 questions) | | | | | | | | | | |
| WB | missing: not run (no directory) | | | | | | | | | | |

#### heldout-3-unanswerable

| Level | Correct stops k/n | Wilson 95% CI | vs level below | Stops | Wrong/trusted | Median s | p90 s | Dispatch |
|---|---|---|---|---|---|---|---|---|
| L0 | missing: not run (no directory) | | | | | | | |
| L1 | missing: not run (no directory) | | | | | | | |
| L2 | missing: not run (no directory) | | | | | | | |
| L3 | missing: not run (no directory) | | | | | | | |
| LB | missing: not run (no directory) | | | | | | | |
| W0 | missing: not run (no directory) | | | | | | | |
| W1 | missing: not run (no directory) | | | | | | | |
| W2 | missing: not run (no directory) | | | | | | | |
| WB | missing: not run (no directory) | | | | | | | |

## Trust: wrong/trusted by model and level

Trusted = `certified` or `governed`. Wrong = not execution-matched (answerable sets) or not a correct stop (unanswerable). Shown as wrong/trusted with trust precision in brackets; `0/0` = no trusted answers.

### heldout-3

| Model | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 0/0 | 0/0 | 0/4 (100%) | 0/4 (100%) | **4/11 (64%)** | 0/0 | 0/0 | 0/0 | **1/5 (80%)** |
| Sonnet 5 | 0/0 | 0/0 | 0/3 (100%) | 0/3 (100%) | **4/11 (64%)** | 0/0 | 0/0 | 0/0 | 0/4 (100%) |
| Qwen 3.8 27B (local) | 0/0 | 0/0 | 0/3 (100%) | 0/3 (100%) | **3/11 (73%)** | 0/0 | 0/0 | **1/1 (0%)** | **2/6 (67%)** |
| GPT-6 Luna (max) | 0/0 | 0/0 | 0/4 (100%) | 0/4 (100%) | missing | 0/0 | 0/0 | **1/1 (0%)** | missing |
| GPT-6 Sol (medium) | 0/0 | 0/0 | 0/4 (100%) | 0/4 (100%) | **3/10 (70%)** | 0/0 | 0/0 | 0/0 | missing |
| GPT-5.6 Terra (high) | 0/0 | 0/0 | 0/3 (100%) | 0/4 (100%) | **1/7 (86%)** | 0/0 | 0/0 | **1/1 (0%)** | missing |

### all

| Model | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 0/0 | 0/0 | **1/6 (83%)** | 0/6 (100%) | **2/15 (87%)** | 0/0 | 0/0 | 0/2 (100%) | **1/8 (88%)** |
| Sonnet 5 | 0/0 | 0/0 | 0/10 (100%) | **1/10 (90%)** | **3/19 (84%)** | 0/0 | 0/0 | 0/2 (100%) | **2/14 (86%)** |
| GPT-6 Luna (max) | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-6 Sol (medium) | 0/0 | 0/0 | 0/5 (100%) | 0/5 (100%) | missing | missing | missing | missing | missing |
| GPT-5.6 Terra (high) | 0/0 | 0/0 | **1/11 (91%)** | **1/11 (91%)** | missing | 0/0 | 0/0 | missing | missing |

### heldout-3-unanswerable

| Model | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| Sonnet 5 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| Qwen 3.8 27B (local) | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| GPT-6 Luna (max) | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-6 Sol (medium) | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-5.6 Terra (high) | missing | missing | missing | missing | missing | missing | missing | missing | missing |

Wrong trusted answers on the development set (`all`), by question id:

- fl-opus L2: what-is-the-total-amount-of-premiums-that-a-poli-8f378a
- fl-opus LB: return-agents-and-the-policy-they-have-sold-that-4e8737, return-policy-holders-and-the-claims-they-have-m-daf6d8
- fl-opus WB: return-agents-and-the-policy-they-have-sold-that-4e8737
- fl-sonnet L3: return-all-the-policies-and-their-policy-holder-e78512
- fl-sonnet LB: return-agents-and-the-policy-they-have-sold-that-4e8737, what-is-the-premium-amount-of-all-policies-by-po-8a3e98, return-policy-holders-and-the-claims-they-have-m-daf6d8
- fl-sonnet WB: what-is-the-premium-amount-of-all-policies-by-po-8a3e98, return-policy-holders-and-the-claims-they-have-m-daf6d8
- fl-terra L2: return-all-the-policies-and-their-policy-holder-e78512
- fl-terra L3: return-all-the-policies-and-their-policy-holder-e78512

Across all models and levels on heldout-3: 21/111 trusted answers were wrong.

## Stops

Answers with no SQL (DQL stopped). On answerable sets a stop is a missed answer; on the unanswerable set the correct-stop rate is the accuracy column above.

### heldout-3

| Model | P | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 0/40 | 10/40 | 1/40 | 4/40 | 2/40 | 4/40 | 0/40 | 0/40 | 0/40 | 0/40 |
| Sonnet 5 | 0/40 | 16/40 | 5/40 | 3/40 | 5/40 | 6/40 | 6/40 | 1/40 | 1/40 | 2/40 |
| Qwen 3.8 27B (local) | 0/40 | 26/40 | 4/40 | 3/40 | 8/40 | 10/40 | 7/40 | 4/40 | 5/40 | 4/40 |
| GPT-6 Luna (max) | 0/40 | 15/40 | 3/40 | 2/40 | 3/40 | missing | 5/40 | 0/40 | 1/40 | missing |
| GPT-6 Sol (medium) | 0/40 | 14/40 | 4/40 | 3/40 | 2/40 | 3/40 | 4/40 | 0/40 | 0/40 | missing |
| GPT-5.6 Terra (high) | 0/40 | 19/40 | 4/40 | 3/40 | 3/40 | 4/40 | 7/40 | 3/40 | 4/40 | missing |

### all

| Model | P | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 0/41 | 8/41 | 2/41 | 3/41 | 1/41 | 2/41 | 0/41 | 1/41 | 1/41 | 0/41 |
| Sonnet 5 | 0/41 | 21/41 | 3/41 | 2/41 | 4/41 | 4/41 | 12/41 | 2/41 | 2/41 | 0/41 |
| GPT-6 Luna (max) | 0/41 | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-6 Sol (medium) | 0/41 | 29/41 | 12/41 | 5/41 | 6/41 | missing | missing | missing | missing | missing |
| GPT-5.6 Terra (high) | 0/41 | 24/41 | 8/41 | 5/41 | 1/41 | missing | 15/41 | 10/41 | missing | missing |

### heldout-3-unanswerable

| Model | P | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | n/a | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) |
| Sonnet 5 | n/a | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 9/10 (correct 9/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) |
| Qwen 3.8 27B (local) | n/a | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) | 10/10 (correct 10/10) |
| GPT-6 Luna (max) | n/a | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-6 Sol (medium) | n/a | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-5.6 Terra (high) | n/a | missing | missing | missing | missing | missing | missing | missing | missing | missing |

## Latency (indicative only)

Median / p90 of per-question `durationMs`, in seconds. Runs were executed in parallel lanes that shared the machine and provider quotas, and some reports were resumed after provider limits, so these numbers are indicative only and not a latency benchmark.

### heldout-3

| Model | P | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 6 / 11 | 25 / 55 | 21 / 37 | 21 / 39 | 22 / 41 | 22 / 40 | 11 / 22 | 12 / 23 | 16 / 39 | 18 / 35 |
| Sonnet 5 | 5 / 35 | 41 / 174 | 32 / 181 | 38 / 96 | 37 / 104 | 37 / 105 | 13 / 51 | 12 / 26 | 21 / 81 | 23 / 60 |
| Qwen 3.8 27B (local) | 11 / 25 | 108 / 170 | 139 / 293 | 131 / 219 | 130 / 234 | 116 / 239 | 75 / 206 | 78 / 142 | 109 / 195 | 155 / 258 |
| GPT-6 Luna (max) | 15 / 44 | 105 / 391 | 93 / 329 | 111 / 255 | 106 / 286 | missing | 34 / 138 | 26 / 77 | 51 / 289 | missing |
| GPT-6 Sol (medium) | 8 / 19 | 43 / 92 | 43 / 112 | 42 / 105 | 47 / 88 | 42 / 83 | 18 / 67 | 17 / 37 | 27 / 71 | missing |
| GPT-5.6 Terra (high) | 8 / 18 | 32 / 73 | 39 / 84 | 38 / 72 | 37 / 92 | 34 / 76 | 18 / 42 | 16 / 36 | 25 / 52 | missing |

### all

| Model | P | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 7 / 13 | 25 / 65 | 28 / 52 | 28 / 51 | 24 / 44 | 15 / 52 | 17 / 35 | 16 / 47 | 20 / 44 | 18 / 32 |
| Sonnet 5 | 11 / 56 | 55 / 148 | 37 / 123 | 43 / 140 | 37 / 120 | 9 / 32 | 26 / 92 | 22 / 80 | 26 / 86 | 8 / 22 |
| GPT-6 Luna (max) | 23 / 66 | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-6 Sol (medium) | 14 / 28 | 47 / 92 | 49 / 95 | 53 / 84 | 48 / 106 | missing | missing | missing | missing | missing |
| GPT-5.6 Terra (high) | 10 / 21 | 34 / 54 | 44 / 76 | 32 / 108 | 36 / 89 | missing | 21 / 70 | 23 / 115 | missing | missing |

### heldout-3-unanswerable

| Model | P | L0 | L1 | L2 | L3 | LB | W0 | W1 | W2 | WB |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | n/a | 18 / 41 | 18 / 22 | 19 / 29 | 17 / 23 | 21 / 25 | 17 / 23 | 17 / 30 | 21 / 28 | 14 / 16 |
| Sonnet 5 | n/a | 21 / 32 | 19 / 24 | 21 / 24 | 19 / 35 | 13 / 16 | 22 / 34 | 22 / 29 | 19 / 24 | 10 / 15 |
| Qwen 3.8 27B (local) | n/a | 99 / 110 | 129 / 135 | 123 / 138 | 129 / 177 | 151 / 177 | 150 / 155 | 191 / 197 | 159 / 171 | 157 / 172 |
| GPT-6 Luna (max) | n/a | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-6 Sol (medium) | n/a | missing | missing | missing | missing | missing | missing | missing | missing | missing |
| GPT-5.6 Terra (high) | n/a | missing | missing | missing | missing | missing | missing | missing | missing | missing |

## Tokens and cost

No report records a dollar cost (`costUsd` is null everywhere: subscription CLIs and a local model). Token usage is recorded only where listed below; for all other cells tokens are **unmeasured**. Mean provider dispatches per question (in the per-model tables) is the only cost proxy available everywhere.

| Run | Level | Set | Source | Questions | Total tokens | Input | Cache read | Cache write | Output | Median/question | Calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fl-opus | P | heldout-3 | per-result usage | 40 | 262,075 | 80 | 21,240 | 222,293 | 18,462 | 6,339 | - |
| fl-opus | P | all | per-result usage | 41 | 277,383 | 82 | 21,771 | 227,434 | 28,096 | 6,515 | - |
| fl-sonnet | P | heldout-3 | per-result usage | 40 | 539,245 | 80 | 135,880 | 364,613 | 38,672 | 12,734 | - |
| fl-sonnet | P | all | per-result usage | 41 | 598,427 | 82 | 139,277 | 373,301 | 85,767 | 13,319 | - |
| fl-qwen | P | heldout-3 | per-result usage | 40 | 67,871 | 60,733 | 0 | 0 | 7,138 | 1,629 | - |
| fl-qwen | L0 | heldout-3 | report usage.byQuestion | 40 | 475,032 | 455,193 | 0 | 0 | 19,839 | 11,373 | 128 |
| fl-qwen | L1 | heldout-3 | report usage.byQuestion | 40 | 708,408 | 680,405 | 0 | 0 | 28,003 | 18,888 | 147 |
| fl-qwen | L2 | heldout-3 | report usage.byQuestion | 40 | 646,591 | 622,616 | 0 | 0 | 23,975 | 15,626 | 139 |
| fl-qwen | L3 | heldout-3 | report usage.byQuestion | 40 | 639,882 | 617,087 | 0 | 0 | 22,795 | 15,632 | 131 |
| fl-qwen | LB | heldout-3 | report usage.byQuestion | 40 | 675,981 | 654,867 | 0 | 0 | 21,114 | 13,890 | 102 |
| fl-qwen | W0 | heldout-3 | report usage.byQuestion | 40 | 395,984 | 380,972 | 0 | 0 | 15,012 | 6,009 | 99 |
| fl-qwen | W1 | heldout-3 | report usage.byQuestion | 40 | 347,191 | 336,268 | 0 | 0 | 10,923 | 7,258 | 82 |
| fl-qwen | W2 | heldout-3 | report usage.byQuestion | 40 | 501,537 | 485,612 | 0 | 0 | 15,925 | 13,657 | 101 |
| fl-qwen | WB | heldout-3 | report usage.byQuestion | 40 | 755,192 | 735,845 | 0 | 0 | 19,347 | 17,756 | 108 |
| fl-qwen | L0 | heldout-3-unanswerable | report usage.byQuestion | 10 | 100,186 | 98,150 | 0 | 0 | 2,036 | 9,758 | 30 |
| fl-qwen | L1 | heldout-3-unanswerable | report usage.byQuestion | 10 | 131,579 | 130,041 | 0 | 0 | 1,538 | 13,199 | 30 |
| fl-qwen | L2 | heldout-3-unanswerable | report usage.byQuestion | 10 | 132,568 | 130,594 | 0 | 0 | 1,974 | 12,792 | 29 |
| fl-qwen | L3 | heldout-3-unanswerable | report usage.byQuestion | 10 | 149,669 | 147,355 | 0 | 0 | 2,314 | 14,525 | 31 |
| fl-qwen | LB | heldout-3-unanswerable | report usage.byQuestion | 10 | 191,523 | 189,410 | 0 | 0 | 2,113 | 17,272 | 32 |
| fl-qwen | W0 | heldout-3-unanswerable | report usage.byQuestion | 10 | 163,512 | 161,923 | 0 | 0 | 1,589 | 16,280 | 30 |
| fl-qwen | W1 | heldout-3-unanswerable | report usage.byQuestion | 10 | 216,625 | 215,230 | 0 | 0 | 1,395 | 21,606 | 30 |
| fl-qwen | W2 | heldout-3-unanswerable | report usage.byQuestion | 10 | 180,179 | 177,807 | 0 | 0 | 2,372 | 19,314 | 27 |
| fl-qwen | WB | heldout-3-unanswerable | report usage.byQuestion | 10 | 179,045 | 177,634 | 0 | 0 | 1,411 | 17,149 | 21 |

Unmeasured: fl-luna L0, L1, L2, L3, P, W0, W1, W2; fl-opus L0, L1, L2, L3, LB, W0, W1, W2, WB; fl-sol L0, L1, L2, L3, LB, P, W0, W1, W2; fl-sonnet L0, L1, L2, L3, LB, W0, W1, W2, WB; fl-terra L0, L1, L2, L3, LB, P, W0, W1, W2.

## Reading the numbers

- **Sample size.** n=40 per level on heldout-3 gives Wilson 95% intervals roughly +/-14 points around the middle of the range (for example 28/40 = 70%, CI 55%-82%). Differences under about 15 points between two levels are rarely significant on their own; the paired McNemar test is more sensitive than comparing intervals because it uses only the questions that changed, but with a handful of discordant pairs even a 5-1 split is p=0.22.
- **Unanswerable set.** n=10 is small: 10/10 correct stops has a Wilson lower bound of 72%; 9/10 has 60%. Treat it as a smoke check of the stop behaviour, not a rate estimate.
- **Development set (`all`).** These 41 questions were used to build and tune the layers, so gains there are optimistic. heldout-3 is the publishable set.
- **Multiple comparisons.** This report runs many tests (up to 9 levels x 2 references x 6 models x 3 sets). At p<0.05, a few 'significant' results are expected by chance; weigh patterns that repeat across models over any single cell. No correction is applied.
- **Trust.** Wrong trusted answers are always shown with their denominator (wrong/trusted). A small denominator gives a weak precision estimate: 0/4 is consistent with a true wrong-trusted rate well above zero.
- **Incomplete runs.** The GPT runs (luna, sol, terra) are still running; missing cells are marked and any number for them may change. Some of their reports were resumed after provider usage limits.
- **Latency** is indicative only (parallel lanes).


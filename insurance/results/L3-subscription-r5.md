## L3 · all · run sub-r5

DQL 1.17.2 (env @ 629db0f9) · claude-code / claude-sonnet-5 · harness 9e88cb6 · 2026-09-17T09:19:03.982Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 23/41 | 56.1% | 41.0–70.1% |
| Accepted answer key | 23/41 | 56.1% | 41.0–70.1% |
| dbt Labs' 11 | 10/11 | 90.9% | 62.3–98.4% |
| LQLS (low question complexity, low schema complexity) | 8/10 | 80.0% | 49.0–94.3% |
| LQHS (low question complexity, high schema complexity) | 2/10 | 20.0% | 5.7–51.0% |
| HQLS (high question complexity, low schema complexity) | 10/11 | 90.9% | 62.3–98.4% |
| HQHS (high question complexity, high schema complexity) | 3/10 | 30.0% | 10.8–60.3% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 23 |
| declined | 5 |
| wrong | 12 |
| asked to clarify | 1 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| governed | 3 | 1 |
| review_required | 20 | 11 |
| blocked | 0 | 5 |
| not_applicable | 0 | 1 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 36.2 s · 95th percentile 117.0 s · slowest 182.0 s · AI calls per question: mean 2.4, max 5 · cost: not measured on this provider route

### Data sent to the AI model

99 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

21 right answers read exactly the correct query's tables. 2 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-average-policy-size-which-is-the-the-bd6c95`: missing policy_coverage_detail
- `what-is-the-total-amount-of-premiums-that-a-poli-6ba963`: missing agreement_party_role

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | governed | 9.0 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | right | review_required | 44.1 s | 3 |  |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | right | governed | 15.9 s | 1 |  |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | declined | blocked | 86.2 s | 3 | no data answer was returned |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 42.7 s | 3 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | right | review_required | 18.5 s | 2 |  |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 50.9 s | 3 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | right | review_required | 23.0 s | 2 |  |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 31.4 s | 2 |  |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 18.5 s | 2 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 117.0 s | 5 | a column of the correct answer is missing from the result |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 31.4 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | right | review_required | 36.2 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | right | review_required | 68.1 s | 3 |  |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | governed | 15.7 s | 1 | returned 1 column(s); the correct answer needs 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | right | review_required | 55.1 s | 3 |  |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | right | review_required | 21.4 s | 2 |  |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 114.4 s | 3 | returned 2 row(s); the correct answer has 1 |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | declined | blocked | 33.3 s | 3 | no data answer was returned |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | wrong | review_required | 64.9 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | declined | blocked | 182.0 s | 4 | no data answer was returned |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 30.8 s | 2 |  |
| ★ How many claims have been placed by policy number? | HQLS | right | review_required | 25.6 s | 2 |  |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 73.8 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | review_required | 25.6 s | 2 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 55.2 s | 4 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | review_required | 55.6 s | 3 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | review_required | 26.2 s | 2 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | review_required | 28.1 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 49.4 s | 2 | a column of the correct answer is missing from the result |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 37.7 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | wrong | review_required | 63.6 s | 2 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 68.2 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 31.3 s | 2 | a column of the correct answer is missing from the result |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | review_required | 28.4 s | 2 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 130.1 s | 3 | no data answer was returned |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | asked to clarify | not_applicable | 72.2 s | 1 | no data answer was returned |
| What are the loss payment amount of all claims by claim number? | LQLS | right | review_required | 34.4 s | 2 |  |
| ★ How many policies do we have? | HQLS | right | governed | 8.8 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 29.5 s | 2 | a column of the correct answer is missing from the result |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 43.4 s | 2 | a column of the correct answer is missing from the result |

★ one of dbt Labs' 11 questions.


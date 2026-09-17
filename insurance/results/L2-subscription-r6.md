## L2 · all · run sub-r6

DQL 1.17.2 (env @ f064f023) · claude-code / claude-sonnet-5 · harness ab22ac7 · 2026-09-17T16:10:29.242Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 22/41 | 53.7% | 38.7–67.9% |
| Accepted answer key | 22/41 | 53.7% | 38.7–67.9% |
| dbt Labs' 11 | 9/11 | 81.8% | 52.3–94.9% |
| LQLS (low question complexity, low schema complexity) | 8/10 | 80.0% | 49.0–94.3% |
| LQHS (low question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |
| HQLS (high question complexity, low schema complexity) | 9/11 | 81.8% | 52.3–94.9% |
| HQHS (high question complexity, high schema complexity) | 4/10 | 40.0% | 16.8–68.7% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 22 |
| wrong | 15 |
| declined | 4 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| governed | 2 | 0 |
| review_required | 20 | 15 |
| blocked | 0 | 4 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 35.9 s · 95th percentile 115.5 s · slowest 165.0 s · AI calls per question: mean 2.3, max 4 · cost: not measured on this provider route

### Data sent to the AI model

96 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

18 right answers read exactly the correct query's tables. 4 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-average-policy-size-which-is-the-the-bd6c95`: missing policy_coverage_detail
- `how-many-policies-have-agents-sold-by-agent-id-792e79`: missing policy
- `what-is-the-total-amount-of-premiums-that-a-poli-6ba963`: missing agreement_party_role
- `what-is-the-total-loss-of-each-policy-that-an-ag-b0f277`: missing claim, policy_coverage_detail; also read policy_amount

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | governed | 10.0 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | wrong | review_required | 41.8 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | right | review_required | 28.8 s | 2 |  |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | wrong | review_required | 124.7 s | 3 | a column of the correct answer is missing from the result |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 25.7 s | 2 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | right | review_required | 19.6 s | 2 |  |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 53.2 s | 2 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | right | review_required | 43.6 s | 2 |  |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 26.6 s | 2 |  |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 45.8 s | 3 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 74.4 s | 2 | returned 2 row(s); the correct answer has 1 |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 30.1 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | right | review_required | 40.4 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | right | review_required | 114.0 s | 4 |  |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | declined | blocked | 26.7 s | 1 | no data answer was returned |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | declined | blocked | 48.3 s | 3 | no data answer was returned |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | right | review_required | 26.5 s | 2 |  |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 101.5 s | 4 |  |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | wrong | review_required | 62.1 s | 2 | returned 2 row(s); the correct answer has 1 |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | wrong | review_required | 32.2 s | 2 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | declined | blocked | 115.5 s | 3 | no data answer was returned |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 26.4 s | 2 |  |
| ★ How many claims have been placed by policy number? | HQLS | right | review_required | 25.5 s | 2 |  |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 113.2 s | 4 |  |
| ★ What is the total amount of premiums paid by policy number? | HQLS | declined | blocked | 22.2 s | 1 | no data answer was returned |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 50.7 s | 3 | returned 2 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | review_required | 32.5 s | 2 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | review_required | 30.0 s | 2 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | review_required | 24.0 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 32.5 s | 2 | a column of the correct answer is missing from the result |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 25.8 s | 2 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | wrong | review_required | 93.2 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | wrong | review_required | 109.0 s | 4 | a column of the correct answer is missing from the result |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 35.9 s | 2 | a column of the correct answer is missing from the result |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | review_required | 37.7 s | 2 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 55.8 s | 2 | returned 2 row(s); the correct answer has 1 |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | wrong | review_required | 165.0 s | 4 | a column of the correct answer is missing from the result |
| What are the loss payment amount of all claims by claim number? | LQLS | right | review_required | 30.4 s | 2 |  |
| ★ How many policies do we have? | HQLS | right | governed | 10.7 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 36.0 s | 2 | a column of the correct answer is missing from the result |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 32.5 s | 2 | a column of the correct answer is missing from the result |

★ one of dbt Labs' 11 questions.


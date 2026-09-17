## L1 · all · run sub-r6

DQL 1.17.2 (env @ f064f023) · claude-code / claude-sonnet-5 · harness ab22ac7 · 2026-09-17T15:29:04.194Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 17/41 | 41.5% | 27.8–56.6% |
| Accepted answer key | 17/41 | 41.5% | 27.8–56.6% |
| dbt Labs' 11 | 7/11 | 63.6% | 35.4–84.8% |
| LQLS (low question complexity, low schema complexity) | 7/10 | 70.0% | 39.7–89.2% |
| LQHS (low question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |
| HQLS (high question complexity, low schema complexity) | 7/11 | 63.6% | 35.4–84.8% |
| HQHS (high question complexity, high schema complexity) | 2/10 | 20.0% | 5.7–51.0% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 17 |
| declined | 11 |
| wrong | 13 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 17 | 13 |
| blocked | 0 | 11 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 37.5 s · 95th percentile 186.6 s · slowest 205.7 s · AI calls per question: mean 2.8, max 6 · cost: not measured on this provider route

### Data sent to the AI model

114 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

13 right answers read exactly the correct query's tables. 4 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-average-policy-size-which-is-the-the-bd6c95`: missing policy_coverage_detail
- `how-many-policies-have-agents-sold-by-agent-id-792e79`: missing policy
- `what-are-the-total-loss-which-is-the-sum-of-loss-56c35a`: missing policy_coverage_detail; also read policy_amount
- `what-is-the-total-amount-of-premiums-that-a-poli-6ba963`: missing agreement_party_role

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | review_required | 18.6 s | 3 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | declined | blocked | 62.2 s | 3 | no data answer was returned |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | wrong | review_required | 33.6 s | 2 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | wrong | review_required | 114.3 s | 3 | returned 6 row(s); the correct answer has 2 |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 24.9 s | 2 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | declined | blocked | 39.8 s | 4 | no data answer was returned |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 25.9 s | 2 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | right | review_required | 20.1 s | 2 |  |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 30.3 s | 2 |  |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 25.8 s | 2 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 95.0 s | 4 | a column of the correct answer is missing from the result |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 23.1 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | wrong | review_required | 46.3 s | 3 | a column of the correct answer is missing from the result |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | declined | blocked | 47.0 s | 3 | no data answer was returned |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | review_required | 35.1 s | 2 | returned 1 column(s); the correct answer needs 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | right | review_required | 94.2 s | 4 |  |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | right | review_required | 24.7 s | 2 |  |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 106.1 s | 4 | no data answer was returned |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | declined | blocked | 37.5 s | 3 | no data answer was returned |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | wrong | review_required | 60.5 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | wrong | review_required | 120.8 s | 3 | returned 6 row(s); the correct answer has 2 |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | declined | blocked | 37.5 s | 3 | no data answer was returned |
| ★ How many claims have been placed by policy number? | HQLS | right | review_required | 16.8 s | 2 |  |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 42.6 s | 2 | returned 2 row(s); the correct answer has 1 |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | review_required | 30.3 s | 2 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 30.6 s | 2 | returned 2 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | review_required | 38.0 s | 3 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | review_required | 18.1 s | 2 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | review_required | 22.8 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 58.4 s | 3 | no data answer was returned |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 25.7 s | 2 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | wrong | review_required | 189.9 s | 4 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 147.3 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 123.1 s | 3 | no data answer was returned |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | review_required | 35.2 s | 2 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 42.5 s | 2 | returned 2 row(s); the correct answer has 1 |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | wrong | review_required | 99.4 s | 3 | returned 2 row(s); the correct answer has 1 |
| What are the loss payment amount of all claims by claim number? | LQLS | right | review_required | 25.4 s | 2 |  |
| ★ How many policies do we have? | HQLS | right | review_required | 20.6 s | 3 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 205.7 s | 6 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 186.6 s | 5 | no data answer was returned |

★ one of dbt Labs' 11 questions.


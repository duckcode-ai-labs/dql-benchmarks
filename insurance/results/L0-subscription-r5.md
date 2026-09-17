## L0 · all · run sub-r5

DQL 1.17.2 (env @ 629db0f9) · claude-code / claude-sonnet-5 · harness 9e88cb6 · 2026-09-17T07:22:03.754Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 10/41 | 24.4% | 13.8–39.3% |
| Accepted answer key | 10/41 | 24.4% | 13.8–39.3% |
| dbt Labs' 11 | 4/11 | 36.4% | 15.2–64.6% |
| LQLS (low question complexity, low schema complexity) | 5/10 | 50.0% | 23.7–76.3% |
| LQHS (low question complexity, high schema complexity) | 0/10 | 0.0% | 0.0–27.8% |
| HQLS (high question complexity, low schema complexity) | 4/11 | 36.4% | 15.2–64.6% |
| HQHS (high question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 10 |
| asked to clarify | 11 |
| wrong | 6 |
| declined | 14 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 10 | 6 |
| not_applicable | 0 | 11 |
| blocked | 0 | 14 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 45.8 s · 95th percentile 177.5 s · slowest 195.3 s · AI calls per question: mean 2.5, max 5 · cost: not measured on this provider route

### Data sent to the AI model

102 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

7 right answers read exactly the correct query's tables. 2 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-total-loss-of-each-claim-by-claim-nu-786db2`: missing expense_payment, expense_reserve, loss_payment, loss_reserve
- `what-are-all-our-policies-that-have-a-claim-asso-6bdbbd`: missing policy_coverage_detail; also read policy_amount

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | review_required | 11.8 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | asked to clarify | not_applicable | 33.9 s | 2 | no data answer was returned |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | wrong | review_required | 145.9 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | declined | blocked | 83.3 s | 3 | no data answer was returned |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | declined | blocked | 74.5 s | 4 | no data answer was returned |
| ★ What is the average time to settle a claim by policy number? | HQLS | declined | blocked | 86.8 s | 4 | no data answer was returned |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 37.2 s | 2 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | asked to clarify | not_applicable | 42.2 s | 2 | no data answer was returned |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 43.2 s | 3 |  |
| ★ How many policies have agents sold by agent id? | HQLS | declined | blocked | 23.3 s | 3 | no data answer was returned |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | asked to clarify | not_applicable | 41.4 s | 1 | no data answer was returned |
| What is the premium amount of all policies by policy number? | LQLS | asked to clarify | not_applicable | 38.7 s | 1 | no data answer was returned |
| Return all the policies and their policy holder by id | LQLS | asked to clarify | not_applicable | 29.7 s | 1 | no data answer was returned |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | wrong | review_required | 55.8 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | declined | blocked | 42.8 s | 3 | no data answer was returned |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | asked to clarify | not_applicable | 45.8 s | 2 | no data answer was returned |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | wrong | review_required | 35.3 s | 2 | a column of the correct answer is missing from the result |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | asked to clarify | not_applicable | 66.4 s | 1 | no data answer was returned |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | declined | blocked | 25.8 s | 3 | no data answer was returned |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | asked to clarify | not_applicable | 59.5 s | 2 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | asked to clarify | not_applicable | 170.2 s | 3 | no data answer was returned |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 42.0 s | 3 |  |
| ★ How many claims have been placed by policy number? | HQLS | declined | blocked | 60.0 s | 4 | no data answer was returned |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 137.8 s | 5 | no data answer was returned |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | review_required | 27.7 s | 2 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 33.4 s | 2 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | wrong | review_required | 54.5 s | 2 | a column of the correct answer is missing from the result |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | review_required | 34.4 s | 2 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | review_required | 47.5 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 42.8 s | 3 | no data answer was returned |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 18.4 s | 2 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | declined | blocked | 183.1 s | 3 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 146.1 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 98.2 s | 5 | no data answer was returned |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | wrong | review_required | 26.9 s | 2 | a column of the correct answer is missing from the result |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | asked to clarify | not_applicable | 69.0 s | 1 | no data answer was returned |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | declined | blocked | 195.3 s | 3 | no data answer was returned |
| What are the loss payment amount of all claims by claim number? | LQLS | right | review_required | 50.7 s | 2 |  |
| ★ How many policies do we have? | HQLS | right | review_required | 13.0 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | asked to clarify | not_applicable | 60.8 s | 1 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 177.5 s | 3 | no data answer was returned |

★ one of dbt Labs' 11 questions.


## L2 · all · run sub-r5

DQL 1.17.2 (env @ 629db0f9) · claude-code / claude-sonnet-5 · harness 9e88cb6 · 2026-09-17T08:48:53.892Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 21/41 | 51.2% | 36.5–65.7% |
| Accepted answer key | 21/41 | 51.2% | 36.5–65.7% |
| dbt Labs' 11 | 9/11 | 81.8% | 52.3–94.9% |
| LQLS (low question complexity, low schema complexity) | 7/10 | 70.0% | 39.7–89.2% |
| LQHS (low question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |
| HQLS (high question complexity, low schema complexity) | 9/11 | 81.8% | 52.3–94.9% |
| HQHS (high question complexity, high schema complexity) | 4/10 | 40.0% | 16.8–68.7% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 21 |
| wrong | 14 |
| declined | 6 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| governed | 3 | 1 |
| review_required | 18 | 13 |
| blocked | 0 | 6 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 39.3 s · 95th percentile 104.4 s · slowest 132.5 s · AI calls per question: mean 2.3, max 3 · cost: not measured on this provider route

### Data sent to the AI model

94 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

18 right answers read exactly the correct query's tables. 3 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-are-the-total-loss-which-is-the-sum-of-loss-561f55`: missing expense_payment, expense_reserve, loss_payment, loss_reserve
- `what-is-the-total-amount-of-premiums-that-a-poli-6ba963`: missing agreement_party_role
- `what-is-the-average-loss-of-each-policy-by-polic-1391b3`: missing expense_payment, expense_reserve, loss_payment, loss_reserve

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | governed | 13.5 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | wrong | review_required | 39.8 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | right | review_required | 34.8 s | 2 |  |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | declined | blocked | 104.4 s | 3 | no data answer was returned |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 36.9 s | 3 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | right | review_required | 21.8 s | 2 |  |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 51.4 s | 3 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | declined | blocked | 28.9 s | 3 | no data answer was returned |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 24.8 s | 2 |  |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 19.2 s | 2 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 109.8 s | 3 | returned 2 row(s); the correct answer has 1 |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 23.6 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | right | review_required | 39.7 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | right | review_required | 49.6 s | 2 |  |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | governed | 17.8 s | 1 | returned 1 column(s); the correct answer needs 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | right | review_required | 58.4 s | 3 |  |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | right | review_required | 34.6 s | 2 |  |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 40.0 s | 2 | returned 2 row(s); the correct answer has 1 |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | wrong | review_required | 48.7 s | 2 | returned 2 row(s); the correct answer has 1 |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | wrong | review_required | 41.9 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | wrong | review_required | 132.5 s | 2 | a column of the correct answer is missing from the result |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 26.8 s | 2 |  |
| ★ How many claims have been placed by policy number? | HQLS | right | review_required | 18.5 s | 2 |  |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 76.3 s | 2 |  |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | review_required | 34.7 s | 2 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 28.3 s | 2 | returned 2 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | review_required | 54.3 s | 3 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | review_required | 28.3 s | 2 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | governed | 12.1 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 43.0 s | 3 | a column of the correct answer is missing from the result |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 39.3 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | wrong | review_required | 86.4 s | 2 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 64.0 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 27.0 s | 2 | a column of the correct answer is missing from the result |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | declined | blocked | 77.5 s | 2 | no data answer was returned |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 47.3 s | 3 | no data answer was returned |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | declined | blocked | 60.3 s | 3 | no data answer was returned |
| What are the loss payment amount of all claims by claim number? | LQLS | right | review_required | 21.7 s | 2 |  |
| ★ How many policies do we have? | HQLS | right | governed | 15.9 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 28.8 s | 2 | a column of the correct answer is missing from the result |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 44.6 s | 3 | a column of the correct answer is missing from the result |

★ one of dbt Labs' 11 questions.


## L2 · all · run sub-r4

DQL 1.17.2 (env @ d0c91022) · claude-code / claude-sonnet-5 · harness 1fbc1da · 2026-09-17T04:24:52.974Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 10/41 | 24.4% | 13.8–39.3% |
| Accepted answer key | 10/41 | 24.4% | 13.8–39.3% |
| dbt Labs' 11 | 6/11 | 54.5% | 28.0–78.7% |
| LQLS (low question complexity, low schema complexity) | 3/10 | 30.0% | 10.8–60.3% |
| LQHS (low question complexity, high schema complexity) | 0/10 | 0.0% | 0.0–27.8% |
| HQLS (high question complexity, low schema complexity) | 6/11 | 54.5% | 28.0–78.7% |
| HQHS (high question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 10 |
| declined | 21 |
| wrong | 9 |
| asked to clarify | 1 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 10 | 9 |
| blocked | 0 | 21 |
| not_applicable | 0 | 1 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 51.3 s · 95th percentile 138.9 s · slowest 160.1 s · AI calls per question: mean 3.2, max 7 · cost: not measured on this provider route

### Data sent to the AI model

131 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

8 right answers read exactly the correct query's tables. 2 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-total-loss-of-each-claim-by-claim-nu-786db2`: missing expense_payment, expense_reserve, loss_payment, loss_reserve
- `what-is-the-total-amount-of-premiums-that-a-poli-6ba963`: missing agreement_party_role

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | review_required | 20.5 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | declined | blocked | 138.9 s | 7 | no data answer was returned |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | wrong | review_required | 26.6 s | 2 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | declined | blocked | 68.5 s | 3 | no data answer was returned |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 34.6 s | 3 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | declined | blocked | 76.2 s | 5 | no data answer was returned |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 71.4 s | 3 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | declined | blocked | 26.8 s | 3 | no data answer was returned |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | declined | blocked | 51.6 s | 4 | no data answer was returned |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 59.6 s | 4 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | asked to clarify | not_applicable | 42.6 s | 1 | no data answer was returned |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 36.1 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | wrong | review_required | 44.9 s | 3 | a column of the correct answer is missing from the result |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | declined | blocked | 72.0 s | 3 | no data answer was returned |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | review_required | 28.1 s | 3 | returned 1 column(s); the correct answer needs 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | declined | blocked | 68.2 s | 3 | no data answer was returned |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | right | review_required | 21.7 s | 2 |  |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 51.3 s | 3 | no data answer was returned |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | wrong | review_required | 71.8 s | 3 | returned 2 row(s); the correct answer has 1 |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | wrong | review_required | 54.9 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | declined | blocked | 117.8 s | 3 | no data answer was returned |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 22.8 s | 2 |  |
| ★ How many claims have been placed by policy number? | HQLS | wrong | review_required | 19.8 s | 2 | a column of the correct answer is missing from the result |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 160.1 s | 4 | no data answer was returned |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | review_required | 31.5 s | 2 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 34.7 s | 2 | returned 2 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | declined | blocked | 30.8 s | 3 | no data answer was returned |
| What are the expense reserve amount of all claims by claim number? | LQLS | declined | blocked | 63.4 s | 4 | no data answer was returned |
| What are the loss reserve amount of all claims by claim number? | LQLS | declined | blocked | 70.4 s | 6 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 120.0 s | 4 | no data answer was returned |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 39.3 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | declined | blocked | 132.9 s | 4 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 56.0 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 23.7 s | 3 | no data answer was returned |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | review_required | 37.7 s | 3 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 149.5 s | 5 | no data answer was returned |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | declined | blocked | 91.1 s | 3 | no data answer was returned |
| What are the loss payment amount of all claims by claim number? | LQLS | declined | blocked | 37.4 s | 4 | no data answer was returned |
| ★ How many policies do we have? | HQLS | right | review_required | 13.1 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 38.3 s | 3 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 99.0 s | 4 | a column of the correct answer is missing from the result |

★ one of dbt Labs' 11 questions.


## L1 · all · run sub-r3

DQL 1.17.2 (env @ d0c91022) · claude-code / claude-sonnet-5 · harness ac30cf2 · 2026-09-17T02:07:16.520Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 11/41 | 26.8% | 15.7–41.9% |
| Accepted answer key | 11/41 | 26.8% | 15.7–41.9% |
| dbt Labs' 11 | 5/11 | 45.5% | 21.3–72.0% |
| LQLS (low question complexity, low schema complexity) | 3/10 | 30.0% | 10.8–60.3% |
| LQHS (low question complexity, high schema complexity) | 0/10 | 0.0% | 0.0–27.8% |
| HQLS (high question complexity, low schema complexity) | 5/11 | 45.5% | 21.3–72.0% |
| HQHS (high question complexity, high schema complexity) | 3/10 | 30.0% | 10.8–60.3% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 11 |
| wrong | 9 |
| declined | 21 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 11 | 9 |
| blocked | 0 | 21 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 45.1 s · 95th percentile 100.8 s · slowest 169.9 s · AI calls per question: mean 2.9, max 5 · cost: not measured on this provider route

### Data sent to the AI model

120 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

6 right answers read exactly the correct query's tables. 4 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-total-loss-of-each-claim-by-claim-nu-786db2`: missing expense_payment, expense_reserve, loss_payment, loss_reserve
- `how-many-policies-have-agents-sold-by-agent-id-792e79`: missing policy
- `what-is-the-average-loss-of-each-policy-by-polic-859638`: missing claim, expense_payment, expense_reserve, loss_payment, loss_reserve, policy_coverage_detail; also read loss_per_claim, policy_amount
- `what-is-the-average-loss-of-each-policy-by-polic-1391b3`: missing claim, expense_payment, expense_reserve, loss_payment, loss_reserve, policy_coverage_detail; also read claim_loss, claim_policy, policy_amount

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | review_required | 22.5 s | 3 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | wrong | review_required | 51.5 s | 2 | a column of the correct answer is missing from the result |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | declined | blocked | 31.7 s | 3 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | declined | blocked | 169.9 s | 5 | no data answer was returned |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 24.1 s | 2 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | declined | blocked | 42.2 s | 3 | no data answer was returned |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 44.6 s | 2 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | declined | blocked | 62.4 s | 4 | no data answer was returned |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | declined | blocked | 42.3 s | 3 | no data answer was returned |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 25.7 s | 2 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 77.7 s | 3 |  |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 25.0 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | wrong | review_required | 58.5 s | 4 | a column of the correct answer is missing from the result |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | wrong | review_required | 61.0 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | right | review_required | 64.5 s | 5 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | declined | blocked | 67.7 s | 3 | no data answer was returned |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | declined | blocked | 32.4 s | 3 | no data answer was returned |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 80.7 s | 2 | returned 2 row(s); the correct answer has 1 |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | declined | blocked | 34.2 s | 3 | no data answer was returned |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | declined | blocked | 122.3 s | 3 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | declined | blocked | 95.5 s | 3 | no data answer was returned |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | declined | blocked | 28.6 s | 3 | no data answer was returned |
| ★ How many claims have been placed by policy number? | HQLS | declined | blocked | 36.0 s | 3 | no data answer was returned |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 74.8 s | 4 |  |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | review_required | 23.4 s | 2 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 26.0 s | 2 | returned 2 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | declined | blocked | 50.5 s | 3 | no data answer was returned |
| What are the expense reserve amount of all claims by claim number? | LQLS | wrong | review_required | 32.7 s | 2 | a column of the correct answer is missing from the result |
| What are the loss reserve amount of all claims by claim number? | LQLS | declined | blocked | 28.8 s | 3 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 67.5 s | 3 | no data answer was returned |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 20.3 s | 2 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | wrong | review_required | 99.3 s | 3 | returned 4 column(s); the correct answer needs 5 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 86.2 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 42.0 s | 3 | no data answer was returned |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | review_required | 38.0 s | 3 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 100.8 s | 3 | no data answer was returned |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | wrong | review_required | 67.5 s | 2 | returned 2 row(s); the correct answer has 1 |
| What are the loss payment amount of all claims by claim number? | LQLS | declined | blocked | 58.9 s | 4 | no data answer was returned |
| ★ How many policies do we have? | HQLS | right | review_required | 24.3 s | 3 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 49.5 s | 3 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 45.1 s | 3 | no data answer was returned |

★ one of dbt Labs' 11 questions.


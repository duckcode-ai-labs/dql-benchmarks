## L1 · all · run sub-r5

DQL 1.17.2 (env @ 629db0f9) · claude-code / claude-sonnet-5 · harness 9e88cb6 · 2026-09-17T08:07:19.665Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 20/41 | 48.8% | 34.3–63.5% |
| Accepted answer key | 20/41 | 48.8% | 34.3–63.5% |
| dbt Labs' 11 | 9/11 | 81.8% | 52.3–94.9% |
| LQLS (low question complexity, low schema complexity) | 7/10 | 70.0% | 39.7–89.2% |
| LQHS (low question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |
| HQLS (high question complexity, low schema complexity) | 9/11 | 81.8% | 52.3–94.9% |
| HQHS (high question complexity, high schema complexity) | 3/10 | 30.0% | 10.8–60.3% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 20 |
| declined | 12 |
| asked to clarify | 2 |
| wrong | 7 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 20 | 7 |
| blocked | 0 | 12 |
| not_applicable | 0 | 2 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 42.1 s · 95th percentile 187.0 s · slowest 216.5 s · AI calls per question: mean 2.5, max 5 · cost: not measured on this provider route

### Data sent to the AI model

104 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

12 right answers read exactly the correct query's tables. 8 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-total-loss-of-each-claim-by-claim-nu-786db2`: missing expense_payment, expense_reserve, loss_payment, loss_reserve
- `what-is-the-average-policy-size-which-is-the-the-bd6c95`: missing policy, policy_coverage_detail
- `how-many-policies-have-agents-sold-by-agent-id-792e79`: missing policy
- `what-are-the-total-loss-which-is-the-sum-of-loss-561f55`: missing expense_payment, expense_reserve, loss_payment, loss_reserve
- `what-is-the-total-amount-of-premiums-that-a-poli-6ba963`: missing agreement_party_role
- `how-many-policies-does-each-policy-holder-have-b-b0ccc5`: missing policy
- `what-is-the-average-loss-of-each-policy-by-polic-1391b3`: missing claim, expense_payment, expense_reserve, loss_payment, loss_reserve
- `what-is-the-premium-amount-of-all-policies-by-po-ff7e17`: missing premium

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | review_required | 27.0 s | 3 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | declined | blocked | 59.2 s | 3 | no data answer was returned |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | right | review_required | 48.6 s | 2 |  |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | declined | blocked | 119.5 s | 3 | no data answer was returned |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | asked to clarify | not_applicable | 17.2 s | 1 | no data answer was returned |
| ★ What is the average time to settle a claim by policy number? | HQLS | asked to clarify | not_applicable | 38.1 s | 2 | no data answer was returned |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 19.4 s | 2 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | right | review_required | 23.7 s | 2 |  |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 27.1 s | 2 |  |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 19.6 s | 2 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 82.4 s | 3 | no data answer was returned |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 16.9 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | right | review_required | 37.7 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | right | review_required | 46.4 s | 2 |  |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | review_required | 42.1 s | 2 | returned 1 column(s); the correct answer needs 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | wrong | review_required | 49.3 s | 2 | returned 2 row(s); the correct answer has 1 |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | right | review_required | 29.0 s | 2 |  |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 68.2 s | 2 | returned 2 row(s); the correct answer has 1 |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | declined | blocked | 37.5 s | 3 | no data answer was returned |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | declined | blocked | 46.4 s | 3 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | declined | blocked | 75.7 s | 3 | no data answer was returned |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 24.9 s | 2 |  |
| ★ How many claims have been placed by policy number? | HQLS | right | review_required | 25.2 s | 2 |  |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 52.4 s | 2 |  |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | review_required | 29.3 s | 2 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 29.0 s | 2 | returned 2 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | review_required | 61.1 s | 3 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | review_required | 29.7 s | 2 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | review_required | 23.7 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 56.5 s | 2 | a column of the correct answer is missing from the result |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 17.0 s | 2 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | declined | blocked | 185.3 s | 4 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 187.0 s | 5 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 51.6 s | 3 | no data answer was returned |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | review_required | 63.3 s | 2 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | review_required | 61.1 s | 2 | returned 2 row(s); the correct answer has 1 |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | declined | blocked | 183.0 s | 3 | no data answer was returned |
| What are the loss payment amount of all claims by claim number? | LQLS | right | review_required | 27.1 s | 2 |  |
| ★ How many policies do we have? | HQLS | right | review_required | 28.6 s | 3 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 207.9 s | 5 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 216.5 s | 5 | no data answer was returned |

★ one of dbt Labs' 11 questions.


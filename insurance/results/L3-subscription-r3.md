## L3 · all · run sub-r3

DQL 1.17.2 (env @ d0c91022) · claude-code / claude-sonnet-5 · harness 5bae75c · 2026-09-17T03:24:59.513Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 10/41 | 24.4% | 13.8–39.3% |
| Accepted answer key | 10/41 | 24.4% | 13.8–39.3% |
| dbt Labs' 11 | 6/11 | 54.5% | 28.0–78.7% |
| LQLS (low question complexity, low schema complexity) | 4/10 | 40.0% | 16.8–68.7% |
| LQHS (low question complexity, high schema complexity) | 0/10 | 0.0% | 0.0–27.8% |
| HQLS (high question complexity, low schema complexity) | 6/11 | 54.5% | 28.0–78.7% |
| HQHS (high question complexity, high schema complexity) | 0/10 | 0.0% | 0.0–27.8% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 10 |
| wrong | 9 |
| declined | 20 |
| asked to clarify | 2 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 10 | 9 |
| blocked | 0 | 20 |
| not_applicable | 0 | 2 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 46.3 s · 95th percentile 142.7 s · slowest 182.3 s · AI calls per question: mean 3.1, max 5 · cost: not measured on this provider route

### Data sent to the AI model

127 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

6 right answers read exactly the correct query's tables. 4 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-average-policy-size-which-is-the-the-bd6c95`: missing policy_coverage_detail; also read filtered_policy_amount, total_amount
- `what-are-all-our-policies-that-have-a-claim-asso-6bdbbd`: missing policy_coverage_detail; also read policy_amount
- `how-many-policies-have-agents-sold-by-agent-id-792e79`: missing policy
- `what-is-the-total-amount-of-premiums-that-a-poli-6ba963`: missing agreement_party_role

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | review_required | 14.9 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | wrong | review_required | 56.4 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | wrong | review_required | 27.5 s | 2 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | declined | blocked | 182.3 s | 4 | no data answer was returned |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | asked to clarify | not_applicable | 46.3 s | 4 | no data answer was returned |
| ★ What is the average time to settle a claim by policy number? | HQLS | declined | blocked | 47.8 s | 4 | no data answer was returned |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | declined | blocked | 46.0 s | 3 | no data answer was returned |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | right | review_required | 26.0 s | 2 |  |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 51.5 s | 4 |  |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 22.0 s | 2 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 113.8 s | 5 | no data answer was returned |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 25.8 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | right | review_required | 41.1 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | wrong | review_required | 64.9 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | review_required | 21.8 s | 2 | returned 1 column(s); the correct answer needs 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | declined | blocked | 69.8 s | 3 | no data answer was returned |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | right | review_required | 29.7 s | 2 |  |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 51.4 s | 3 | no data answer was returned |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | asked to clarify | not_applicable | 29.6 s | 1 | no data answer was returned |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | declined | blocked | 127.2 s | 4 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | declined | blocked | 177.9 s | 4 | no data answer was returned |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 27.1 s | 2 |  |
| ★ How many claims have been placed by policy number? | HQLS | wrong | review_required | 25.7 s | 2 | a column of the correct answer is missing from the result |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 133.8 s | 5 | no data answer was returned |
| ★ What is the total amount of premiums paid by policy number? | HQLS | wrong | review_required | 30.5 s | 3 | a column of the correct answer is missing from the result |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 54.0 s | 3 | returned 1 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | declined | blocked | 33.1 s | 3 | no data answer was returned |
| What are the expense reserve amount of all claims by claim number? | LQLS | declined | blocked | 53.1 s | 3 | no data answer was returned |
| What are the loss reserve amount of all claims by claim number? | LQLS | declined | blocked | 41.2 s | 4 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 62.7 s | 3 | no data answer was returned |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 32.6 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | wrong | review_required | 73.3 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 50.8 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 82.9 s | 5 | no data answer was returned |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | review_required | 34.5 s | 3 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 142.7 s | 5 | no data answer was returned |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | declined | blocked | 139.9 s | 4 | no data answer was returned |
| What are the loss payment amount of all claims by claim number? | LQLS | declined | blocked | 31.4 s | 3 | no data answer was returned |
| ★ How many policies do we have? | HQLS | right | review_required | 16.8 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 32.2 s | 3 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 63.3 s | 3 | no data answer was returned |

★ one of dbt Labs' 11 questions.


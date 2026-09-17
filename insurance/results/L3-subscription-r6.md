## L3 · all · run sub-r6

DQL 1.17.2 (env @ f064f023) · claude-code / claude-sonnet-5 · harness f3c5bb5 · 2026-09-17T16:45:12.306Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 26/41 | 63.4% | 48.1–76.4% |
| Accepted answer key | 26/41 | 63.4% | 48.1–76.4% |
| dbt Labs' 11 | 10/11 | 90.9% | 62.3–98.4% |
| LQLS (low question complexity, low schema complexity) | 7/10 | 70.0% | 39.7–89.2% |
| LQHS (low question complexity, high schema complexity) | 2/10 | 20.0% | 5.7–51.0% |
| HQLS (high question complexity, low schema complexity) | 10/11 | 90.9% | 62.3–98.4% |
| HQHS (high question complexity, high schema complexity) | 7/10 | 70.0% | 39.7–89.2% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 26 |
| wrong | 12 |
| declined | 3 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| governed | 4 | 0 |
| review_required | 22 | 12 |
| blocked | 0 | 3 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 33.1 s · 95th percentile 126.7 s · slowest 146.5 s · AI calls per question: mean 2.3, max 3 · cost: not measured on this provider route

### Data sent to the AI model

96 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

23 right answers read exactly the correct query's tables. 3 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-average-policy-size-which-is-the-the-bd6c95`: missing policy_coverage_detail
- `what-is-the-total-amount-of-premiums-that-a-poli-6ba963`: missing agreement_party_role
- `what-is-the-average-loss-of-each-policy-by-polic-1391b3`: missing claim

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | governed | 11.0 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | right | review_required | 58.3 s | 3 |  |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | right | review_required | 31.7 s | 2 |  |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | wrong | review_required | 129.7 s | 3 | returned 4 row(s); the correct answer has 2 |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 40.8 s | 3 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | right | review_required | 21.5 s | 2 |  |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 29.5 s | 2 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | right | review_required | 27.6 s | 2 |  |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 35.3 s | 3 |  |
| ★ How many policies have agents sold by agent id? | HQLS | right | review_required | 24.4 s | 2 |  |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 93.8 s | 3 |  |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 27.0 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | right | review_required | 38.8 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | right | review_required | 51.7 s | 3 |  |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | declined | blocked | 20.1 s | 1 | no data answer was returned |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | right | review_required | 48.5 s | 3 |  |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | right | review_required | 24.5 s | 2 |  |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 66.8 s | 3 |  |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | declined | blocked | 29.7 s | 3 | no data answer was returned |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | wrong | review_required | 40.5 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | wrong | review_required | 126.7 s | 3 | returned 4 row(s); the correct answer has 2 |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 24.0 s | 2 |  |
| ★ How many claims have been placed by policy number? | HQLS | right | review_required | 19.1 s | 2 |  |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 57.8 s | 3 |  |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | governed | 16.1 s | 1 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | declined | blocked | 41.0 s | 3 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | review_required | 33.1 s | 2 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | review_required | 32.9 s | 2 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | review_required | 20.4 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 31.6 s | 2 | a column of the correct answer is missing from the result |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 26.7 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | wrong | review_required | 111.1 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | wrong | review_required | 86.3 s | 3 | a column of the correct answer is missing from the result |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | wrong | review_required | 35.6 s | 2 | a column of the correct answer is missing from the result |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | wrong | review_required | 27.6 s | 2 | a column of the correct answer is missing from the result |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | review_required | 40.8 s | 3 |  |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | wrong | review_required | 146.5 s | 3 | a column of the correct answer is missing from the result |
| What are the loss payment amount of all claims by claim number? | LQLS | right | governed | 22.7 s | 1 |  |
| ★ How many policies do we have? | HQLS | right | governed | 10.1 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 37.1 s | 2 | a column of the correct answer is missing from the result |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | wrong | review_required | 50.8 s | 2 | a column of the correct answer is missing from the result |

★ one of dbt Labs' 11 questions.


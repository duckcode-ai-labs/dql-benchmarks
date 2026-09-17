## L0 · all · run sub-r6

DQL 1.17.2 (env @ f064f023) · claude-code / claude-sonnet-5 · harness ab22ac7 · 2026-09-17T14:44:18.114Z

> **Not publishable:** DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 14/41 | 34.1% | 21.6–49.5% |
| Accepted answer key | 14/41 | 34.1% | 21.6–49.5% |
| dbt Labs' 11 | 5/11 | 45.5% | 21.3–72.0% |
| LQLS (low question complexity, low schema complexity) | 7/10 | 70.0% | 39.7–89.2% |
| LQHS (low question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |
| HQLS (high question complexity, low schema complexity) | 5/11 | 45.5% | 21.3–72.0% |
| HQHS (high question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 14 |
| declined | 14 |
| wrong | 9 |
| asked to clarify | 4 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 14 | 9 |
| blocked | 0 | 14 |
| not_applicable | 0 | 4 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 47.3 s · 95th percentile 156.2 s · slowest 206.2 s · AI calls per question: mean 2.7, max 6 · cost: not measured on this provider route

### Data sent to the AI model

112 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

10 right answers read exactly the correct query's tables. 1 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-are-all-our-policies-that-have-a-claim-asso-6bdbbd`: missing policy_coverage_detail; also read policy_amount

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | review_required | 12.4 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | declined | blocked | 102.9 s | 4 | no data answer was returned |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | right | review_required | 61.5 s | 2 |  |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | declined | blocked | 64.2 s | 3 | no data answer was returned |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 47.3 s | 3 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | declined | blocked | 60.3 s | 4 | no data answer was returned |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | review_required | 49.8 s | 2 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | wrong | review_required | 35.1 s | 2 | a column of the correct answer is missing from the result |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | review_required | 32.4 s | 2 |  |
| ★ How many policies have agents sold by agent id? | HQLS | declined | blocked | 32.3 s | 3 | no data answer was returned |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 94.5 s | 4 | no data answer was returned |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 19.2 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | right | review_required | 42.7 s | 3 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | wrong | review_required | 73.4 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | review_required | 18.6 s | 2 | returned 1 column(s); the correct answer needs 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | declined | blocked | 156.2 s | 5 | no data answer was returned |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | wrong | review_required | 29.5 s | 2 | a column of the correct answer is missing from the result |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 130.2 s | 3 | no data answer was returned |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | wrong | review_required | 30.3 s | 2 | returned 2 column(s); the correct answer needs 3 |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | declined | blocked | 57.8 s | 4 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | wrong | review_required | 148.9 s | 3 | a column of the correct answer is missing from the result |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | right | review_required | 34.2 s | 3 |  |
| ★ How many claims have been placed by policy number? | HQLS | declined | blocked | 60.3 s | 3 | no data answer was returned |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 145.5 s | 6 | no data answer was returned |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | review_required | 30.8 s | 2 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 29.5 s | 2 | returned 2 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | review_required | 67.7 s | 2 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | review_required | 41.9 s | 3 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | review_required | 39.2 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | asked to clarify | not_applicable | 63.8 s | 1 | no data answer was returned |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 21.2 s | 2 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | declined | blocked | 206.2 s | 4 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 44.2 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | declined | blocked | 124.5 s | 4 | no data answer was returned |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | wrong | review_required | 27.4 s | 2 | a column of the correct answer is missing from the result |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 182.7 s | 4 | no data answer was returned |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | asked to clarify | not_applicable | 80.6 s | 1 | no data answer was returned |
| What are the loss payment amount of all claims by claim number? | LQLS | right | review_required | 25.4 s | 2 |  |
| ★ How many policies do we have? | HQLS | right | review_required | 15.0 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | asked to clarify | not_applicable | 99.0 s | 3 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | asked to clarify | not_applicable | 44.6 s | 1 | no data answer was returned |

★ one of dbt Labs' 11 questions.


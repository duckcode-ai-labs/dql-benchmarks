## L0 · all · run sub-L0-r2

DQL 1.17.2 (env @ d0c91022) · claude-code / claude-sonnet-5 · harness 185056e (uncommitted changes) · 2026-09-17T01:07:47.843Z

> **Not publishable:** benchmark repo has uncommitted changes; DQL came from the DQL_CLI override, not a release.

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 8/41 | 19.5% | 10.2–34.0% |
| Accepted answer key | 8/41 | 19.5% | 10.2–34.0% |
| dbt Labs' 11 | 2/11 | 18.2% | 5.1–47.7% |
| LQLS (low question complexity, low schema complexity) | 5/10 | 50.0% | 23.7–76.3% |
| LQHS (low question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |
| HQLS (high question complexity, low schema complexity) | 2/11 | 18.2% | 5.1–47.7% |
| HQHS (high question complexity, high schema complexity) | 0/10 | 0.0% | 0.0–27.8% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 8 |
| asked to clarify | 7 |
| wrong | 13 |
| declined | 13 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| review_required | 8 | 13 |
| not_applicable | 0 | 7 |
| blocked | 0 | 13 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 52.6 s · 95th percentile 169.9 s · slowest 197.6 s · AI calls per question: mean 2.5, max 5 · cost: not measured on this provider route

### Data sent to the AI model

104 AI calls recorded; result rows sent to the model: **0** (target 0).

### Right answers that read different tables than the correct query

6 right answers read exactly the correct query's tables. 0 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:


### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | review_required | 15.1 s | 3 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | asked to clarify | not_applicable | 42.8 s | 1 | no data answer was returned |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | wrong | review_required | 69.3 s | 2 | a column of the correct answer is missing from the result |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | wrong | review_required | 109.3 s | 3 | returned 7 column(s); the correct answer needs 9 |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | right | review_required | 36.2 s | 3 |  |
| ★ What is the average time to settle a claim by policy number? | HQLS | wrong | review_required | 61.1 s | 2 | returned 2 row(s); the correct answer has 1 |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | asked to clarify | not_applicable | 47.5 s | 1 | no data answer was returned |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | wrong | review_required | 19.5 s | 2 | a column of the correct answer is missing from the result |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | declined | blocked | 55.8 s | 3 | no data answer was returned |
| ★ How many policies have agents sold by agent id? | HQLS | declined | blocked | 34.0 s | 3 | no data answer was returned |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 197.6 s | 3 | no data answer was returned |
| What is the premium amount of all policies by policy number? | LQLS | wrong | review_required | 41.0 s | 2 | returned 2 row(s); the correct answer has 6 |
| Return all the policies and their policy holder by id | LQLS | wrong | review_required | 67.4 s | 5 | returned 0 row(s); the correct answer has 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | wrong | review_required | 47.2 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | review_required | 42.5 s | 3 | returned 1 column(s); the correct answer needs 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | wrong | review_required | 77.3 s | 3 | a column of the correct answer is missing from the result |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | wrong | review_required | 34.4 s | 2 | a column of the correct answer is missing from the result |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 72.7 s | 4 | no data answer was returned |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | asked to clarify | not_applicable | 46.4 s | 1 | no data answer was returned |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | declined | blocked | 46.2 s | 3 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | declined | blocked | 103.1 s | 3 | no data answer was returned |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | declined | blocked | 58.2 s | 3 | no data answer was returned |
| ★ How many claims have been placed by policy number? | HQLS | declined | blocked | 55.0 s | 3 | no data answer was returned |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | asked to clarify | not_applicable | 52.6 s | 1 | no data answer was returned |
| ★ What is the total amount of premiums paid by policy number? | HQLS | wrong | review_required | 26.7 s | 2 | a column of the correct answer is missing from the result |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | review_required | 27.9 s | 2 | returned 2 row(s); the correct answer has 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | review_required | 169.9 s | 4 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | declined | blocked | 38.0 s | 3 | no data answer was returned |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | review_required | 35.2 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | asked to clarify | not_applicable | 117.0 s | 2 | no data answer was returned |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | review_required | 16.8 s | 2 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | declined | blocked | 114.4 s | 3 | no data answer was returned |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | declined | blocked | 92.3 s | 3 | no data answer was returned |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | asked to clarify | not_applicable | 90.1 s | 2 | no data answer was returned |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | review_required | 38.7 s | 2 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | declined | blocked | 56.4 s | 3 | no data answer was returned |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | wrong | review_required | 118.6 s | 3 | returned 0 row(s); the correct answer has 1 |
| What are the loss payment amount of all claims by claim number? | LQLS | right | review_required | 25.1 s | 2 |  |
| ★ How many policies do we have? | HQLS | right | review_required | 11.9 s | 2 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | asked to clarify | not_applicable | 67.9 s | 1 | no data answer was returned |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | declined | blocked | 181.8 s | 4 | no data answer was returned |

★ one of dbt Labs' 11 questions.


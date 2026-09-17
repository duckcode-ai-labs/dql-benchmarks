## baseline-small · all · run sub-r4

DQL none (plain text-to-SQL) (none @ 1fbc1da0) · claude-code / claude-sonnet-5 · harness 1fbc1da · 2026-09-17T05:53:17.957Z

### Accuracy

| Questions | Right | Accuracy | 95% CI |
|---|---:|---:|---|
| All | 19/41 | 46.3% | 32.1–61.3% |
| Accepted answer key | 19/41 | 46.3% | 32.1–61.3% |
| dbt Labs' 11 | 7/11 | 63.6% | 35.4–84.8% |
| LQLS (low question complexity, low schema complexity) | 6/10 | 60.0% | 31.3–83.2% |
| LQHS (low question complexity, high schema complexity) | 1/10 | 10.0% | 1.8–40.4% |
| HQLS (high question complexity, low schema complexity) | 7/11 | 63.6% | 35.4–84.8% |
| HQHS (high question complexity, high schema complexity) | 5/10 | 50.0% | 23.7–76.3% |

### What each answer was

| Outcome | Questions |
|---|---:|
| right | 19 |
| wrong | 22 |

### Trust label against correctness

| Trust label | Right | Wrong or no answer |
|---|---:|---:|
| none | 19 | 22 |

**Wrong but labelled certified: 0** (target 0).

### Speed and AI calls

Median 6.2 s · 95th percentile 23.9 s · slowest 31.6 s · AI calls per question: mean 1.0, max 1 · cost: not measured on this provider route

### Data sent to the AI model

Recorded for 0 of 41 answers.

### Right answers that read different tables than the correct query

16 right answers read exactly the correct query's tables. 3 right answers left out a table the correct query reads; each is reviewed by hand before a number is published:

- `what-is-the-average-policy-size-which-is-the-the-bd6c95`: missing policy_coverage_detail
- `what-is-the-average-loss-of-each-policy-by-polic-859638`: missing claim; also read claim_loss, claim_policy, loss_amounts
- `what-is-the-average-loss-of-each-policy-by-polic-1391b3`: missing claim; also read claim_loss, policy_claims

### Every question

| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |
|---|---|---|---|---:|---:|---|
| ★ How many claims do we have? | HQLS | right | none | 3.2 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding catastrophe it had. | LQHS | wrong | none | 9.5 s | 1 | row count 0 does not match gold 2 |
| ★ What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number? | HQLS | right | none | 4.5 s | 1 |  |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid and the agent who sold it? | LQHS | wrong | none | 30.3 s | 1 | a gold column has no matching result column |
| Return all the policies and the agents that sold them by policy number and agent id | LQLS | wrong | none | 5.9 s | 1 | row count 0 does not match gold 2 |
| ★ What is the average time to settle a claim by policy number? | HQLS | right | none | 5.7 s | 1 |  |
| What is the total loss of each claim by claim number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount? | HQHS | right | none | 6.5 s | 1 |  |
| ★ What is the average policy size which is the the total amount of premium divided by the number of policies? | HQLS | right | none | 4.0 s | 1 |  |
| What are all our policies that have a claim associated to them by policy and claim number? | LQLS | right | none | 4.3 s | 1 |  |
| ★ How many policies have agents sold by agent id? | HQLS | wrong | none | 4.5 s | 1 | row count 0 does not match gold 1 |
| What is the average loss of each policy by policy number where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | none | 16.8 s | 1 |  |
| What is the premium amount of all policies by policy number? | LQLS | wrong | none | 4.3 s | 1 | row count 2 does not match gold 6 |
| Return all the policies and their policy holder by id | LQLS | wrong | none | 4.1 s | 1 | row count 0 does not match gold 2 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number, catastrophe and corresponding policy number? | HQHS | right | none | 11.0 s | 1 |  |
| ★ What is the total amount of premiums that a policy holder has paid? | HQLS | wrong | none | 6.6 s | 1 | row count 0 does not match gold 1 |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by catastrophe and policy number? | HQHS | wrong | none | 13.1 s | 1 | a gold column has no matching result column |
| ★ What is the total amount of premiums that a policy holder has paid by policy number? | HQLS | wrong | none | 5.4 s | 1 | row count 0 does not match gold 2 |
| What is the total loss of each policy that an agent has sold by agent id where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | wrong | none | 13.0 s | 1 | row count 0 does not match gold 1 |
| What is the loss ratio of each policy and agent who sold it by policy number and agent id? | HQHS | wrong | none | 19.9 s | 1 | row count 0 does not match gold 1 |
| Return policy holders and the claims they have made and the correspoinding catastrophe | LQHS | wrong | none | 8.5 s | 1 | row count 0 does not match gold 2 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder, premium amount paid, the catastrophe it had, and the agent who sold it? | LQHS | wrong | none | 31.6 s | 1 | a gold column has no matching result column |
| ★ How many policies does each policy holder have by policy holder id? | HQLS | wrong | none | 4.5 s | 1 | row count 0 does not match gold 1 |
| ★ How many claims have been placed by policy number? | HQLS | right | none | 5.2 s | 1 |  |
| What is the average loss of each policy by policy number and number of claims where loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | none | 12.5 s | 1 |  |
| ★ What is the total amount of premiums paid by policy number? | HQLS | right | none | 5.5 s | 1 |  |
| What are all the premiums that have been paid by policy holders? | LQLS | wrong | none | 5.0 s | 1 | row count 0 does not match gold 6 |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number? | LQHS | right | none | 7.6 s | 1 |  |
| What are the expense reserve amount of all claims by claim number? | LQLS | right | none | 4.2 s | 1 |  |
| What are the loss reserve amount of all claims by claim number? | LQLS | right | none | 5.0 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding expense payment amount by agent id, policy number and claim number | LQHS | wrong | none | 6.2 s | 1 | row count 0 does not match gold 2 |
| Return all the claims we have by claim number, open date and close date? | LQLS | right | none | 4.4 s | 1 |  |
| What are the total loss, which is the sum of loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | HQHS | wrong | none | 23.9 s | 1 | a gold column has no matching result column |
| What are the loss payment, loss reserve, expense payment, expense reserve amount by claim number and corresponding policy number, policy holder and premium amount paid? | LQHS | wrong | none | 22.1 s | 1 | a gold column has no matching result column |
| Return agents and the policies they have sold that have had a claim and the corresponding loss payment amount by agent id, policy number and claim number | LQHS | wrong | none | 6.1 s | 1 | row count 0 does not match gold 2 |
| What is the premium amount of all policies by policy number, coverage effective date and coverage expiration date | LQLS | right | none | 6.6 s | 1 |  |
| What is the total loss of each policy by policy number where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amounts? | HQHS | right | none | 11.2 s | 1 |  |
| What is the loss ratio, number of claims, total loss by policy number and premium where total loss is the sum of loss payment, loss reserve, expense payment, expense reserve amount and loss ratio is total loss divided by premium? | HQHS | wrong | none | 17.9 s | 1 | a gold column has no matching result column |
| What are the loss payment amount of all claims by claim number? | LQLS | right | none | 4.4 s | 1 |  |
| ★ How many policies do we have? | HQLS | right | none | 3.9 s | 1 |  |
| Return agents and the policy they have sold that have had a claim and the corresponding loss reserve amount by agent id, policy number and claim number | LQHS | wrong | none | 7.6 s | 1 | row count 0 does not match gold 2 |
| Return agents and the policy they have sold that have had a claim and the corresponding expense reserve amount by agent id, policy number and claim number | LQHS | wrong | none | 12.4 s | 1 | row count 0 does not match gold 2 |

★ one of dbt Labs' 11 questions.


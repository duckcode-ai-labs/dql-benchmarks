# Output format

Write `questions-5.json` in this folder:

```json
{
  "questions": [
    { "question": "…", "goldSql": "SELECT …", "quadrant": "LQLS|LQHS|HQLS|HQHS", "shape": "scalar|list|grouped|ranked", "note": "optional: definitions used" }
  ],
  "unanswerable": [
    { "question": "…", "why": "one sentence naming what the data does not hold" }
  ]
}
```

Rules checked by `python3 validate.py`:
- 200 answerable questions, 50 per quadrant; 50 unanswerable questions.
- quadrant: L/H question complexity × L/H schema complexity. High schema complexity = needs 3+ tables or
  a bridge table (party roles, claim coverage). High question complexity = aggregation with conditions,
  ratios, rankings or multi-part asks.
- goldSql: exactly one SELECT (or WITH … SELECT), tables written as main.<table>, returning exactly the
  columns the question asks for. It must run on acme_insurance.duckdb and return at least one row.
- No duplicate questions.

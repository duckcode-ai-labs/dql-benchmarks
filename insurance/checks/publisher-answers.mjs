#!/usr/bin/env node
// Cross-check our warehouse against dbt Labs' published results.
//
// dbt Labs' results database (dbt-llm-sl-bench/llm_bench_dashboard.db) keeps
// the SQL of every text-to-SQL answer and whether their grader marked it
// correct. If our build of the data is right, the answers they marked correct
// should also match our correct answers here. Their SQL was written for a
// cloud warehouse, so some of it does not run on DuckDB; those are counted
// separately, never as disagreements.
//
//   node insurance/checks/publisher-answers.mjs

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from '../../lib/dql.mjs';
import { rowsMatch } from '../../lib/row-match.mjs';

const PYTHON = join(REPO_ROOT, '.venv', 'bin', 'python');
const RESULTS_DB = join(REPO_ROOT, 'data', 'insurance', 'dbt-llm-sl-bench', 'llm_bench_dashboard.db');
const WAREHOUSE = join(REPO_ROOT, 'work', 'insurance', 'projects', 'L0', 'acme_insurance.duckdb');
const gold = JSON.parse(readFileSync(join(REPO_ROOT, 'work', 'insurance', 'gold', 'answers.json'), 'utf-8'));

function python(code, input) {
  const result = spawnSync(PYTHON, ['-c', code], { input, encoding: 'utf-8', maxBuffer: 256 * 1024 * 1024 });
  if (result.status !== 0) throw new Error(result.stderr);
  return JSON.parse(result.stdout);
}

const published = python(`
import duckdb, json
c = duckdb.connect(${JSON.stringify(RESULTS_DB)}, read_only=True)
rows = c.execute("select challenge_text, sql, is_correct, count(*) from sql_answers where method = 'sql' and sql is not null group by all").fetchall()
print(json.dumps([{"question": q, "sql": s, "correct": bool(ok), "times": n} for q, s, ok, n in rows]))
`);

const byQuestion = new Map(gold.cases.map((c) => [c.question, c]));
const queries = published.map((answer, index) => ({ id: String(index), sql: answer.sql }));
const results = python(readFileSync(join(REPO_ROOT, 'lib', 'duckdb_query.py'), 'utf-8'), JSON.stringify({ database: WAREHOUSE, queries }));

const summary = { markedCorrect: { agree: 0, disagree: 0, doesNotRun: 0 }, markedWrong: { agree: 0, disagree: 0, doesNotRun: 0 } };
const disagreements = [];
published.forEach((answer, index) => {
  const target = byQuestion.get(answer.question);
  if (!target) return;
  const bucket = answer.correct ? summary.markedCorrect : summary.markedWrong;
  const result = results[String(index)];
  if (result.error) { bucket.doesNotRun += 1; return; }
  // dbt Labs' grader allows extra columns, so the check does too.
  const ours = rowsMatch(result.rows, target.gold.rows, { allowExtraColumns: true }).match;
  if (ours === answer.correct) bucket.agree += 1;
  else {
    bucket.disagree += 1;
    disagreements.push({ question: answer.question, theirVerdict: answer.correct, ourVerdict: ours, sql: answer.sql, ourRows: result.rows, goldRows: target.gold.rows });
  }
});

const out = { note: 'Distinct SQL strings from dbt Labs text-to-SQL runs, checked on our warehouse.', summary, disagreements };
writeFileSync(join(REPO_ROOT, 'work', 'insurance', 'check-publisher-answers.json'), `${JSON.stringify(out, null, 2)}\n`);
console.log(JSON.stringify(summary, null, 2));
console.log(`${disagreements.length} disagreement(s) written to work/insurance/check-publisher-answers.json`);

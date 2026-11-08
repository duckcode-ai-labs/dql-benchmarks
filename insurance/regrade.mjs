#!/usr/bin/env node
// Grade one run several ways, not just one.
//
//   node insurance/regrade.mjs work/insurance/runs/<run>/<layer>/all/report.json
//
// A single accuracy figure hides what a buyer wants to know. This re-runs each
// answer's recorded SQL against that layer's warehouse (read-only) and reports:
//
//   strict   — the rows match the correct answer's rows, ignoring column names
//              and order. This is the published number, and the rule dbt Labs'
//              own grader uses.
//   measures — the numbers the question asks for are all present, even if the
//              answer leaves out a label or id column the correct answer has.
//              Benchmarks that judge the query rather than the rows, and
//              vendors quoting "column precision/recall", sit nearer this line.
//   tables   — the answer read the same tables as the correct query.
//
// and splits accuracy by the path that answered (a governed metric or a
// certified block, against SQL the AI wrote), because "how much of this comes
// from governed definitions" is the question a semantic-layer buyer asks.

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { rowsMatch, valuesCovered } from '../lib/row-match.mjs';
import { wilsonInterval } from '../lib/stats.mjs';
import { tableCheck } from './score.mjs';
import { heldoutPaths, heldoutSetOf } from './heldout.mjs';
import { forPublic } from '../lib/public.mjs';

const PYTHON = join(REPO_ROOT, '.venv', 'bin', 'python');

function runSql(database, queries) {
  if (queries.length === 0) return {};
  const result = spawnSync(PYTHON, [join(REPO_ROOT, 'lib', 'duckdb_query.py')], {
    input: JSON.stringify({ database, queries }), encoding: 'utf-8', maxBuffer: 256 * 1024 * 1024,
  });
  if (result.status !== 0) throw new Error(result.stderr);
  return JSON.parse(result.stdout);
}

const AGGREGATE = /\b(sum|count|avg|average|min|max|datediff|date_diff)\s*\(/i;
const MEASURE_NAME = /(sum|count|avg|average|total|amount|ratio|size|no_?of|number_of|days|time)/i;
// A name that identifies the thing counted, not the number: Policy_Number,
// Party_Identifier, Claim_Amount_Identifier, Catastrophe_Name.
const IDENTIFIER_NAME = /(identifier|_id$|^id$|_number$|_code$|_name$|_date$)/i;

/**
 * THE COLUMNS THAT CARRY THE NUMBERS. A correct answer names the thing asked
 * about (a policy number, a party id) and the number asked for (a total, a
 * count, an average). The measure columns are those the correct query
 * aggregates, found from its own projection, falling back to the column names
 * it gave them. Used for the measure-level grading beside the strict one.
 */
export function measureColumnIndexes(goldSql, columns) {
  const projection = /select\s+([\s\S]*?)\sfrom\s/i.exec(goldSql ?? '')?.[1];
  const expressions = [];
  if (projection) {
    let depth = 0;
    let current = '';
    for (const character of projection) {
      if (character === '(') depth += 1;
      if (character === ')') depth -= 1;
      if (character === ',' && depth === 0) { expressions.push(current); current = ''; continue; }
      current += character;
    }
    expressions.push(current);
  }
  return columns.map((column, index) => {
    const expression = expressions[index];
    // An aggregate in the correct query's own projection, or a column it named
    // like a number (LossAmount, TotalPremium, avgPolicySize) when the
    // expression is arithmetic rather than a function call.
    const aggregated = expression ? AGGREGATE.test(expression) : false;
    return aggregated || (MEASURE_NAME.test(column) && !IDENTIFIER_NAME.test(column)) ? index : -1;
  }).filter((index) => index >= 0);
}

/**
 * Do the answer's values carry every number the correct answer's measures
 * hold? A correct answer with no measure column at all (a listing question)
 * has nothing to loosen, so the caller keeps the strict verdict.
 */
export function measuresCovered(actualRows, goldRows, measureIndexes) {
  if (measureIndexes.length === 0) return { match: false, reason: 'no measure column' };
  const wanted = goldRows.map((row) => measureIndexes.map((index) => (Array.isArray(row) ? row[index] : Object.values(row)[index])));
  return valuesCovered(actualRows, wanted);
}

/** Which path produced the answer, in the words a reader needs. */
export function answeredBy(result) {
  const tier = result.answer?.tier;
  if (result.kind === 'no_answer' || result.route === 'clarify') return 'stopped';
  if (tier === 'certified') return 'certified block';
  if (tier === 'semantic') return 'governed metric';
  if (tier) return 'AI-written SQL';
  return 'no SQL recorded';
}

export function regrade(report, gold, rowsBySql) {
  const byId = new Map(gold.cases.map((c) => [c.id, c]));
  return report.results.map((result) => {
    const question = byId.get(result.name);
    const sql = result.answer?.sql;
    const executed = sql ? rowsBySql[sql] : undefined;
    const goldRows = question?.gold.rows ?? [];
    const strict = result.executionMatched === true;
    const measureIndexes = question ? measureColumnIndexes(question.gold.ranSql ?? question.goldSql, question.gold.columns ?? []) : [];
    const measures = measureIndexes.length === 0 || !executed?.rows
      ? strict
      : measuresCovered(executed.rows, goldRows, measureIndexes).match;
    const exact = executed?.rows ? rowsMatch(executed.rows, goldRows, { allowExtraColumns: true }).match : strict;
    return {
      id: result.name,
      quadrant: question?.quadrant ?? null,
      dbtLabs: Boolean(question?.dbtLabsSelected),
      answeredBy: answeredBy(result),
      trust: result.answer?.trustState ?? 'none',
      strict,
      // The rerun of the recorded SQL should agree with the run's own verdict;
      // a disagreement means the warehouse or the recording changed.
      rerunAgrees: executed?.rows ? exact === strict : null,
      measures,
      tables: sql && question ? tableCheck(sql, question.gold.ranSql ?? question.goldSql) : null,
      durationMs: result.durationMs,
    };
  });
}

const pct = (k, n) => (n ? `${((k / n) * 100).toFixed(1)}%` : '—');

export function renderRegrade(rows, label, { sealed = false } = {}) {
  const lines = [`## ${label}: the same answers, graded several ways`, ''];
  const strict = rows.filter((row) => row.strict).length;
  const measures = rows.filter((row) => row.measures).length;
  const sameTables = rows.filter((row) => row.strict && row.tables?.same).length;
  const ci = (k) => { const { low, high } = wilsonInterval(k, rows.length); return `${(low * 100).toFixed(1)}–${(high * 100).toFixed(1)}%`; };
  lines.push('| Grading | Right | Share | 95% CI |', '|---|---:|---:|---|');
  lines.push(`| Strict: the rows match the correct answer | ${strict}/${rows.length} | ${pct(strict, rows.length)} | ${ci(strict)} |`);
  lines.push(`| Measure-level: every number the question asks for is present (a listing question keeps its strict verdict) | ${measures}/${rows.length} | ${pct(measures, rows.length)} | ${ci(measures)} |`);
  lines.push(`| Strict **and** read the correct query's tables | ${sameTables}/${rows.length} | ${pct(sameTables, rows.length)} | ${ci(sameTables)} |`);
  lines.push('');

  lines.push('### What answered, and how often it was right', '', '| Answered by | Questions | Right (strict) | Numbers right |', '|---|---:|---:|---:|');
  for (const path of ['certified block', 'governed metric', 'AI-written SQL', 'stopped', 'no SQL recorded']) {
    const group = rows.filter((row) => row.answeredBy === path);
    if (group.length === 0) continue;
    lines.push(`| ${path} | ${group.length} | ${group.filter((row) => row.strict).length} | ${group.filter((row) => row.measures).length} |`);
  }
  lines.push('');

  lines.push('### By question difficulty', '', '| Quadrant | Questions | Strict | Numbers right |', '|---|---:|---:|---:|');
  for (const quadrant of ['LQLS', 'HQLS', 'LQHS', 'HQHS']) {
    const group = rows.filter((row) => row.quadrant === quadrant);
    if (group.length === 0) continue;
    lines.push(`| ${quadrant} | ${group.length} | ${pct(group.filter((row) => row.strict).length, group.length)} | ${pct(group.filter((row) => row.measures).length, group.length)} |`);
  }
  const eleven = rows.filter((row) => row.dbtLabs);
  lines.push(`| dbt Labs' 11 | ${eleven.length} | ${pct(eleven.filter((row) => row.strict).length, eleven.length)} | ${pct(eleven.filter((row) => row.measures).length, eleven.length)} |`, '');

  const disagreed = rows.filter((row) => row.rerunAgrees === false);
  if (sealed) {
    lines.push(`Held-out set: questions are sealed. Re-run disagreements: ${disagreed.length}. Numbers right but rejected by the strict rule: ${rows.filter((row) => !row.strict && row.measures).length}.`, '');
    return lines.join('\n');
  }
  if (disagreed.length) lines.push(`> **${disagreed.length} answer(s) graded differently when their SQL was run again** — the warehouse or the recording changed: ${disagreed.map((row) => row.id).join(', ')}.`, '');
  const gained = rows.filter((row) => !row.strict && row.measures);
  if (gained.length) {
    lines.push('Answers whose numbers are right but which the strict rule rejects (a missing label or id column, or extra rows):', '');
    for (const row of gained) lines.push(`- \`${row.id}\` (${row.answeredBy})`);
    lines.push('');
  }
  return lines.join('\n');
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const file = process.argv[2];
  if (!file) {
    console.error('Usage: node insurance/regrade.mjs <report.json>');
    process.exit(1);
  }
  const report = JSON.parse(readFileSync(file, 'utf-8'));
  const sealed = Boolean(report.run?.set?.startsWith('heldout'));
  const gold = JSON.parse(readFileSync(sealed ? heldoutPaths(heldoutSetOf(report.run.set).number).gold : join(REPO_ROOT, 'work', 'insurance', 'gold', 'answers.json'), 'utf-8'));
  const database = join(REPO_ROOT, 'work', 'insurance', 'projects', report.run.layer, 'acme_insurance.duckdb');
  const statements = [...new Set(report.results.map((result) => result.answer?.sql).filter(Boolean))];
  const executed = runSql(database, statements.map((sql, index) => ({ id: String(index), sql })));
  const rowsBySql = Object.fromEntries(statements.map((sql, index) => [sql, executed[String(index)]]));
  const rows = regrade(report, gold, rowsBySql);
  const out = file.replace(/report\.json$/, 'regrade.json');
  writeFileSync(out, forPublic(`${JSON.stringify({ run: report.run, identity: report.identity, rows }, null, 2)}\n`));
  console.log(renderRegrade(rows, `${report.run.layer} · run ${report.run.id}`, { sealed }));
}

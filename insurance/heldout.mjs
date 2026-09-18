#!/usr/bin/env node
// The held-out insurance questions: a second, sealed question set.
//
//   node insurance/heldout.mjs import <heldout-questions.json>
//   node insurance/heldout.mjs gold
//
// The 41 headline questions were read, run and failed many times while DQL was
// being fixed, so a gain on them can be a gain on those questions only. The
// held-out set answers "does it generalize?". It was written by a separate
// agent that saw only the warehouse schema and data — not the 41 questions,
// not any results, not DQL — and DQL is never changed because of a held-out
// failure. It is run at release checkpoints, and its scorecard reports totals
// only (see score.mjs), so a developer reading results does not learn the
// questions one by one.
//
// `import` checks the file's shape and copies it to insurance/heldout/;
// `gold` runs every correct query on the built warehouse and writes
// work/insurance/gold/heldout.json. Neither prints a question.

import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { caseId, QUADRANTS } from './questions.mjs';

export const HELDOUT_FILE = join(REPO_ROOT, 'insurance', 'heldout', 'questions.json');
export const HELDOUT_GOLD = join(REPO_ROOT, 'work', 'insurance', 'gold', 'heldout.json');
const PYTHON = join(REPO_ROOT, '.venv', 'bin', 'python');

export const heldoutId = (question) => `heldout-${caseId(question)}`;

/** Problems with a held-out file's shape; empty when it can be used. */
export function checkHeldout(file) {
  const problems = [];
  if (!Array.isArray(file?.questions) || file.questions.length === 0) problems.push('no questions');
  const seen = new Set();
  (file?.questions ?? []).forEach((entry, index) => {
    const where = `questions[${index}]`;
    if (typeof entry.question !== 'string' || !entry.question.trim()) problems.push(`${where}: question is required`);
    if (typeof entry.goldSql !== 'string' || !/^\s*(with|select)\b/i.test(entry.goldSql)) problems.push(`${where}: goldSql must be one SELECT`);
    if (!Object.keys(QUADRANTS).includes(entry.quadrant)) problems.push(`${where}: quadrant must be one of ${Object.keys(QUADRANTS).join(', ')}`);
    const id = entry.question ? heldoutId(entry.question) : null;
    if (id && seen.has(id)) problems.push(`${where}: duplicate question`);
    if (id) seen.add(id);
  });
  (file?.unanswerable ?? []).forEach((entry, index) => {
    if (typeof entry.question !== 'string' || !entry.why) problems.push(`unanswerable[${index}]: question and why are required`);
  });
  return problems;
}

/** Held-out questions the data cannot answer, in the shape run.mjs asks. */
export function heldoutUnanswerableCases(path = HELDOUT_FILE) {
  const { unanswerable = [] } = JSON.parse(readFileSync(path, 'utf-8'));
  return unanswerable.map((entry) => ({ id: `heldout-unanswerable-${caseId(entry.question)}`, question: entry.question, why: entry.why, unanswerable: true }));
}

function runGold(database, questions) {
  const result = spawnSync(PYTHON, [join(REPO_ROOT, 'lib', 'duckdb_query.py')], {
    input: JSON.stringify({ database, queries: questions.map((q) => ({ id: heldoutId(q.question), sql: q.goldSql })) }),
    encoding: 'utf-8', maxBuffer: 256 * 1024 * 1024,
  });
  if (result.status !== 0) throw new Error(result.stderr);
  return JSON.parse(result.stdout);
}

function counts(questions) {
  const by = (key) => Object.entries(questions.reduce((acc, q) => ({ ...acc, [q[key] ?? '—']: (acc[q[key] ?? '—'] ?? 0) + 1 }), {})).map(([k, n]) => `${k} ${n}`).join(', ');
  return `${questions.length} questions (${by('quadrant')}; shapes: ${by('shape')})`;
}

function main() {
  const [command, path] = process.argv.slice(2);
  if (command === 'import') {
    if (!path) throw new Error('Usage: node insurance/heldout.mjs import <file>');
    const file = JSON.parse(readFileSync(path, 'utf-8'));
    const problems = checkHeldout(file);
    if (problems.length) throw new Error(problems.join('\n'));
    mkdirSync(join(REPO_ROOT, 'insurance', 'heldout'), { recursive: true });
    writeFileSync(HELDOUT_FILE, `${JSON.stringify(file, null, 2)}\n`);
    console.log(`imported ${counts(file.questions)} and ${(file.unanswerable ?? []).length} unanswerable → insurance/heldout/questions.json`);
    return;
  }
  if (command === 'gold') {
    const file = JSON.parse(readFileSync(HELDOUT_FILE, 'utf-8'));
    const database = join(REPO_ROOT, 'work', 'insurance', 'projects', 'L0', 'acme_insurance.duckdb');
    if (!existsSync(database)) throw new Error('Build L0 first: node insurance/build.mjs --layer L0');
    const results = runGold(database, file.questions);
    const cases = file.questions.map((q) => {
      const id = heldoutId(q.question);
      const result = results[id];
      return {
        id, question: q.question, quadrant: q.quadrant, shape: q.shape ?? null, goldSql: q.goldSql,
        gold: result.error ? { error: result.error } : { columns: result.columns, rowCount: result.rows.length, rows: result.rows },
      };
    });
    const broken = cases.filter((c) => c.gold.error || c.gold.rowCount === 0).length;
    mkdirSync(join(REPO_ROOT, 'work', 'insurance', 'gold'), { recursive: true });
    writeFileSync(HELDOUT_GOLD, `${JSON.stringify({ builtAt: new Date().toISOString(), database: 'L0', cases }, null, 2)}\n`);
    console.log(`correct answers for ${cases.length} held-out questions; ${broken} did not run or returned no rows → work/insurance/gold/heldout.json`);
    if (broken) process.exitCode = 1;
    return;
  }
  throw new Error('Usage: node insurance/heldout.mjs import <file> | gold');
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  try {
    main();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

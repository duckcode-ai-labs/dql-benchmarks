#!/usr/bin/env node
// The held-out insurance questions: a second, sealed question set.
//
//   node insurance/heldout.mjs [--number N] import <heldout-questions.json>
//   node insurance/heldout.mjs [--number N] gold
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

/**
 * Held-out sets are numbered. A set is spent once a DQL change is made because
 * of what it showed, and the next checkpoint uses a fresh one. Set 1 keeps its
 * original file names; set N lives in questions-N.json and heldout-N.json.
 * Run-set names: heldout, heldout-unanswerable (set 1); heldout-2,
 * heldout-2-unanswerable (set 2) …
 */
export function heldoutPaths(number = 1) {
  if (number === 1) return { file: HELDOUT_FILE, gold: HELDOUT_GOLD };
  return { file: join(REPO_ROOT, 'insurance', 'heldout', `questions-${number}.json`), gold: join(REPO_ROOT, 'work', 'insurance', 'gold', `heldout-${number}.json`) };
}

/** The held-out set a run-set name refers to, or undefined for a non-held-out set. */
export function heldoutSetOf(set) {
  const match = /^heldout(?:-(\d+))?(-unanswerable)?$/.exec(set ?? '');
  return match ? { number: match[1] ? Number(match[1]) : 1, unanswerable: Boolean(match[2]) } : undefined;
}
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
  const args = process.argv.slice(2);
  const at = args.indexOf('--number');
  const number = at >= 0 ? Number(args.splice(at, 2)[1]) : 1;
  const paths = heldoutPaths(number);
  const [command, path] = args;
  if (command === 'import') {
    if (!path) throw new Error('Usage: node insurance/heldout.mjs import <file>');
    const file = JSON.parse(readFileSync(path, 'utf-8'));
    const problems = checkHeldout(file);
    if (problems.length) throw new Error(problems.join('\n'));
    mkdirSync(join(REPO_ROOT, 'insurance', 'heldout'), { recursive: true });
    if (existsSync(paths.file)) throw new Error(`held-out set ${number} already exists; a set is never overwritten, use a new --number`);
    writeFileSync(paths.file, `${JSON.stringify(file, null, 2)}\n`);
    console.log(`imported set ${number}: ${counts(file.questions)} and ${(file.unanswerable ?? []).length} unanswerable → ${paths.file.slice(REPO_ROOT.length + 1)}`);
    return;
  }
  if (command === 'gold') {
    const file = JSON.parse(readFileSync(paths.file, 'utf-8'));
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
    writeFileSync(paths.gold, `${JSON.stringify({ builtAt: new Date().toISOString(), database: 'L0', set: number, cases }, null, 2)}\n`);
    console.log(`correct answers for ${cases.length} questions of held-out set ${number}; ${broken} did not run or returned no rows → ${paths.gold.slice(REPO_ROOT.length + 1)}`);
    if (broken) process.exitCode = 1;
    return;
  }
  throw new Error('Usage: node insurance/heldout.mjs [--number N] import <file> | gold');
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  try {
    main();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

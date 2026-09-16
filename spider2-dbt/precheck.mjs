#!/usr/bin/env node
// Score a submission with the publisher's own evaluate.py.
//
//   node spider2-dbt/precheck.mjs <submission-dir> [--json out.json]
//
// evaluate.py prints each passing instance id and, last, "<ratio> <passed>
// <listed>". Its ratio uses the number of listed instances as the
// denominator; this script also reports the score over every graded task, and
// refuses a submission that does not list them all.

import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { REPO_ROOT } from '../lib/dql.mjs';
import { wilsonInterval } from '../lib/stats.mjs';
import { EVALUATE_PY, GOLD_DIR, readManifest } from './tasks.mjs';

const PYTHON = join(REPO_ROOT, '.venv', 'bin', 'python');

export function parseEvaluateOutput(stdout, instanceIds) {
  const lines = stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const summary = lines.at(-1)?.match(/^([\d.]+)\s+(\d+)\s+(\d+)$/);
  if (!summary) throw new Error(`evaluate.py did not print a summary line. Last output:\n${lines.slice(-5).join('\n')}`);
  const ids = new Set(instanceIds);
  // Passing ids are printed on their own lines just before the summary.
  const passed = new Set(lines.filter((line) => ids.has(line)));
  const reportedPassed = Number(summary[2]);
  if (passed.size !== reportedPassed) {
    throw new Error(`evaluate.py reported ${reportedPassed} passes but printed ${passed.size} passing ids.`);
  }
  return { passed, listed: Number(summary[3]), reportedRatio: Number(summary[1]) };
}

export function precheck(submissionDir) {
  const manifest = readManifest();
  const graded = manifest.tasks.map((task) => task.instanceId);
  const metadata = join(submissionDir, 'results_metadata.jsonl');
  if (!existsSync(metadata)) throw new Error(`${metadata} is missing.`);
  const listed = new Set(readFileSync(metadata, 'utf-8').split('\n').filter(Boolean).map((line) => JSON.parse(line).instance_id));
  const unlisted = graded.filter((id) => !listed.has(id));
  if (unlisted.length) {
    throw new Error(`The submission leaves out ${unlisted.length} graded task(s) (${unlisted.slice(0, 5).join(', ')}); `
      + 'evaluate.py would score only the rest and overstate accuracy.');
  }

  const run = spawnSync(PYTHON, [EVALUATE_PY, '--result_dir', resolve(submissionDir), '--gold_dir', GOLD_DIR], {
    cwd: join(EVALUATE_PY, '..'),
    encoding: 'utf-8',
    maxBuffer: 64 * 1024 * 1024,
  });
  if (run.status !== 0) throw new Error(`evaluate.py failed (${run.status}):\n${run.stderr.slice(-3000)}`);
  const { passed, listed: evaluatedCount } = parseEvaluateOutput(run.stdout, graded);
  if (evaluatedCount !== graded.length) {
    throw new Error(`evaluate.py scored ${evaluatedCount} instances; ${graded.length} are graded.`);
  }

  const withGold = manifest.tasks.filter((task) => task.goldPresent).map((task) => task.instanceId);
  const interval = wilsonInterval(passed.size, graded.length);
  return {
    benchmark: 'spider2-dbt',
    upstreamCommit: manifest.upstreamCommit,
    submission: resolve(submissionDir),
    passed: passed.size,
    graded: graded.length,
    accuracy: passed.size / graded.length,
    ci95: interval,
    // Over the tasks whose gold database was actually published.
    passedWithGold: withGold.filter((id) => passed.has(id)).length,
    gradedWithGold: withGold.length,
    cases: graded.map((id) => ({ caseId: id, passed: passed.has(id) })),
  };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  try {
    const args = process.argv.slice(2);
    const jsonIndex = args.indexOf('--json');
    const out = jsonIndex >= 0 ? args.splice(jsonIndex, 2)[1] : null;
    if (args.length !== 1) throw new Error('Usage: node spider2-dbt/precheck.mjs <submission-dir> [--json out.json]');
    const result = precheck(args[0]);
    if (out) writeFileSync(out, `${JSON.stringify(result, null, 2)}\n`);
    const pct = (value) => `${(value * 100).toFixed(1)}%`;
    console.log(`Spider 2.0-DBT: ${result.passed}/${result.graded} = ${pct(result.accuracy)} `
      + `(95% CI ${pct(result.ci95.low)}–${pct(result.ci95.high)}); `
      + `${result.passedWithGold}/${result.gradedWithGold} on tasks with a published gold database.`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

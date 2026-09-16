#!/usr/bin/env node
// Does each starting project parse with the pinned dbt? Parsing is done on a
// copy without the database, so the published task folders stay untouched.
// A project that does not parse is still attempted by the agent; this only
// shows how the environment treats the starting state.

import { cpSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { EXAMPLES_DIR, readManifest } from './tasks.mjs';

const DBT = join(REPO_ROOT, '.venv', 'bin', 'dbt');
const scratch = join(REPO_ROOT, 'work', 'spider2-dbt', 'env-check');
const manifest = readManifest();
const version = spawnSync(DBT, ['--version'], { encoding: 'utf-8' }).stdout.match(/installed:\s*([\d.]+)/)?.[1];
const results = [];
for (const task of manifest.tasks) {
  if (!task.hasTaskDir) continue;
  const dir = join(scratch, task.instanceId);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  cpSync(join(EXAMPLES_DIR, task.instanceId), dir, {
    recursive: true,
    filter: (source) => !/\.duckdb(\.wal)?$/.test(source),
  });
  const run = spawnSync(DBT, ['parse', '--project-dir', dir, '--profiles-dir', dir, '--no-use-colors'], {
    cwd: dir,
    encoding: 'utf-8',
    timeout: 300_000,
    env: { ...process.env, DBT_SEND_ANONYMOUS_USAGE_STATS: 'false' },
  });
  const output = `${run.stdout}${run.stderr}`;
  const error = run.status === 0 ? null : (output.match(/(Compilation Error|Parsing Error|Runtime Error)[\s\S]{0,300}/)?.[0] ?? output.slice(-300)).replace(/\s+/g, ' ').trim();
  results.push({ instanceId: task.instanceId, parses: run.status === 0, error });
  process.stdout.write(run.status === 0 ? '.' : 'x');
}
rmSync(scratch, { recursive: true, force: true });
const failing = results.filter((entry) => !entry.parses);
const report = { dbtCore: version, checked: results.length, parse: results.length - failing.length, failing };
writeFileSync(join(REPO_ROOT, 'spider2-dbt', 'reports', `env-check-dbt-${version}.json`), `${JSON.stringify(report, null, 2)}\n`);
console.log(`\ndbt ${version}: ${report.parse}/${report.checked} starting projects parse.`);
for (const entry of failing) console.log(`  ${entry.instanceId}: ${entry.error?.slice(0, 160)}`);

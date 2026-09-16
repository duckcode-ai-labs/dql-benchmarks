#!/usr/bin/env node
// Turn one Spider 2.0-DBT task into a DQL project, the way a customer would
// onboard their own dbt repository: copy it, parse it with dbt, `dql init`.
//
//   node spider2-dbt/import-task.mjs <instance_id> [--run <run-id>]
//
// Nothing task-specific is added. DQL reads the dbt project and the DuckDB
// database on its own; that is part of what is being measured.

import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { REPO_ROOT, resolveDqlCli, runDql } from '../lib/dql.mjs';
import { EXAMPLES_DIR, readManifest } from './tasks.mjs';

const DBT = join(REPO_ROOT, '.venv', 'bin', 'dbt');

const SHARED_CONNECTORS = join(REPO_ROOT, '.connectors');

/**
 * DQL loads the DuckDB driver from the project's `.dql/connectors`. Link the
 * repo's single install there instead of installing it per task; the
 * version is the one DQL's own CI uses (see scripts/install-connectors.mjs).
 */
function linkSharedConnectors(dir) {
  if (!existsSync(join(SHARED_CONNECTORS, 'node_modules', 'duckdb'))) {
    throw new Error('The shared DuckDB connector is not installed. Run: npm run connectors:install');
  }
  mkdirSync(join(dir, '.dql'), { recursive: true });
  const target = join(dir, '.dql', 'connectors');
  rmSync(target, { recursive: true, force: true });
  symlinkSync(SHARED_CONNECTORS, target, 'dir');
}

export function taskWorkDir(runId, instanceId) {
  return join(REPO_ROOT, 'work', 'spider2-dbt', 'runs', runId, instanceId);
}

function dbt(args, cwd) {
  // Same arguments DQL's own onboarding uses for `dbt parse`.
  const result = spawnSync(DBT, [...args, '--project-dir', cwd, '--profiles-dir', cwd], {
    cwd,
    encoding: 'utf-8',
    timeout: 300_000,
    env: { ...process.env, DBT_SEND_ANONYMOUS_USAGE_STATS: 'false' },
  });
  return { code: result.status, output: `${result.stdout ?? ''}${result.stderr ?? ''}` };
}

/**
 * @returns {{ instanceId, dir, database, dbtParse: {code}, dqlInit: {code}, config }}
 */
export function importTask(instanceId, { runId = 'dev', cli = resolveDqlCli() } = {}) {
  const manifest = readManifest();
  const task = manifest.tasks.find((entry) => entry.instanceId === instanceId);
  if (!task) throw new Error(`${instanceId} is not a graded Spider 2.0-DBT task.`);
  if (!task.startingDatabasePresent) throw new Error(`${instanceId} has no starting database in the published data.`);

  const dir = taskWorkDir(runId, instanceId);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  cpSync(join(EXAMPLES_DIR, instanceId), dir, { recursive: true });
  writeFileSync(join(dir, 'TASK.md'), `# ${instanceId}\n\n${task.instruction}\n`);

  const parse = dbt(['parse'], dir);
  const init = runDql(['init', dir], { cli, cwd: dir });
  linkSharedConnectors(dir);
  const configPath = join(dir, 'dql.config.json');
  const config = existsSync(configPath) ? JSON.parse(readFileSync(configPath, 'utf-8')) : null;

  const result = {
    instanceId,
    dir,
    database: task.database,
    dbtParse: { code: parse.code, tail: parse.output.split('\n').slice(-6).join('\n') },
    dqlInit: { code: init.code, tail: `${init.stdout}${init.stderr}`.split('\n').slice(-6).join('\n') },
    config,
  };
  writeFileSync(join(dir, '.import.json'), `${JSON.stringify(result, null, 2)}\n`);
  return result;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const args = process.argv.slice(2);
  const runIndex = args.indexOf('--run');
  const runId = runIndex >= 0 ? args.splice(runIndex, 2)[1] : 'dev';
  if (args.length !== 1) {
    console.error('Usage: node spider2-dbt/import-task.mjs <instance_id> [--run <run-id>]');
    process.exit(1);
  }
  try {
    const result = importTask(args[0], { runId });
    console.log(`${result.instanceId} → ${result.dir}`);
    console.log(`dbt parse exit ${result.dbtParse.code}; dql init exit ${result.dqlInit.code}`);
    console.log(`connection: ${JSON.stringify(result.config?.connections ?? null)}`);
    console.log(`dbt: ${JSON.stringify(result.config?.dbt ?? null)}`);
    if (result.dbtParse.code !== 0) console.log(result.dbtParse.tail);
    if (result.dqlInit.code !== 0) console.log(result.dqlInit.tail);
    process.exitCode = result.dbtParse.code === 0 && result.dqlInit.code === 0 ? 0 : 1;
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

#!/usr/bin/env node
// Build one DQL project per Spider 2.0-Lite SQLite database, for one condition.
//
//   node spider2/build.mjs --condition S0|S1a|E0|E1|E2 [--db <name>]
//
// S0:  the warehouse only. `dql init --warehouse-first` on a folder whose one
//      connection is the task database (opened read-only), then `dql sync
//      warehouse`. No dbt, no modeling, no documentation written by us.
// S1a: S0 + the model DQL drafts on its own (`dql model apply-discovery
//      --apply --validate`), unreviewed. Nothing is written by hand.

import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { REPO_ROOT, buildIdentity, resolveDqlCli, runDql, dqlVersion } from '../lib/dql.mjs';
import { LOCALDB, readTasks } from './tasks.mjs';

export const CONDITIONS = {
  S0: { description: 'warehouse only: DQL warehouse-first, schema synced', draft: false },
  S1a: { description: 'S0 + the model DQL drafts from the warehouse (apply-discovery --validate), not reviewed', draft: true },
  // The same project as S0, kept apart so a build under test never shares
  // projects with a run in progress. What E0 measures is the DQL build it runs.
  E0: { description: 'warehouse only, as S0: the arm for the drafter evidence work (whole schema, declared keys, dialect notes)', draft: false },
  // E0 with the column value profile switched on (agent.valueProfile
  // "sampled"): example values and ranges reach the drafter. A project
  // setting, off by default, because the values leave the machine.
  E1: { description: 'E0 + the column value profile (agent.valueProfile: sampled)', draft: false, valueProfile: true },
  // The E1 project for the result-review build: the review runs on every
  // warehouse-first project, so E2 differs from E1 by the DQL build alone.
  E2: { description: 'E1 on the result-review build (a second look at each AI-drafted result)', draft: false, valueProfile: true },
};
const WORK = join(REPO_ROOT, 'work', 'spider2');

export function build({ condition, only }) {
  if (!CONDITIONS[condition]) throw new Error(`--condition must be one of ${Object.keys(CONDITIONS).join(', ')}`);
  const cli = resolveDqlCli();
  const { tasks, missingDatabases } = readTasks();
  const databases = [...new Set(tasks.map((task) => task.db))].filter((db) => !only || db === only).sort();
  // The code that built the projects: a drafted model is as much a product of
  // DQL as an answer is, so a run on projects from another build is two
  // builds at once. run.mjs compares this with its own.
  const { patch: _patch, ...build } = buildIdentity(cli);
  const record = { condition, description: CONDITIONS[condition].description, builtAt: new Date().toISOString(), dql: { version: dqlVersion(cli), source: cli.source, build }, missingDatabases, databases: {} };
  for (const db of databases) {
    const dir = join(WORK, 'projects', condition, db);
    rmSync(dir, { recursive: true, force: true });
    mkdirSync(dir, { recursive: true });
    const steps = [];
    const run = (args, timeoutMs = 900_000) => {
      const result = runDql(args, { cli, cwd: dir, timeoutMs });
      steps.push({ command: `dql ${args.join(' ')}`.replace(dir, '<project>'), code: result.code, tail: `${result.stdout}${result.stderr}`.split('\n').filter(Boolean).slice(-6) });
      if (result.code !== 0) throw new Error(`${db}: dql ${args[0]} ${args[1] ?? ''} failed:\n${result.stderr || result.stdout}`);
      return result;
    };
    run(['init', dir, '--warehouse-first']);
    const configPath = join(dir, 'dql.config.json');
    const config = JSON.parse(readFileSync(configPath, 'utf-8'));
    config.project = db;
    config.defaultConnectionName = 'default';
    config.connections = { default: { driver: 'sqlite', filepath: join(LOCALDB, `${db}.sqlite`) } };
    if (CONDITIONS[condition].valueProfile) config.agent = { ...(config.agent ?? {}), valueProfile: { mode: 'sampled' } };
    writeFileSync(configPath, `${JSON.stringify(config, null, 2)}\n`);
    run(['sync', 'warehouse', dir, '--schemas', 'main']);
    let drafted = null;
    if (CONDITIONS[condition].draft) {
      run(['model', 'apply-discovery', dir, '--apply', '--validate']);
      const modelFiles = existsSync(join(dir, 'domains')) ? readdirSync(join(dir, 'domains'), { recursive: true }).map(String).filter((file) => file.endsWith('model.dql.yaml')) : [];
      const model = modelFiles.map((file) => readFileSync(join(dir, 'domains', file), 'utf-8')).join('\n');
      drafted = { entities: (model.match(/^  - id:/gm) ?? []).length - (model.split(/^relationships:/m)[1]?.match(/^  - id:/gm) ?? []).length, relationships: (model.split(/^relationships:/m)[1]?.match(/^  - id:/gm) ?? []).length, grains: (model.match(/^    grain:/gm) ?? []).length };
    }
    const catalog = JSON.parse(readFileSync(join(dir, '.dql', 'warehouse-catalog.json'), 'utf-8'));
    record.databases[db] = { projectDir: relative(REPO_ROOT, dir), tables: catalog.relations.length, declaredPrimaryKeys: catalog.relations.filter((relation) => relation.primaryKey?.length).length, declaredForeignKeys: catalog.relations.reduce((n, relation) => n + (relation.foreignKeys?.length ?? 0), 0), drafted, steps };
    console.log(`${condition}/${db}: ${catalog.relations.length} tables${drafted ? ` · drafted ${drafted.relationships} joins, ${drafted.grains} grains` : ''}`);
  }
  mkdirSync(WORK, { recursive: true });
  writeFileSync(join(WORK, `build-${condition}.json`), `${JSON.stringify(record, null, 2)}\n`);
  return record;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const value = (flag) => (args.includes(flag) ? args[args.indexOf(flag) + 1] : undefined);
  try {
    build({ condition: value('--condition') ?? 'S0', only: value('--db') });
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

#!/usr/bin/env node
// Build one arm's ZLens project on WideWorldImporters.
//
//   DQL_CLI=<zlens dist/index.js> node wwi/build.mjs --arm W0|W1a|WM
//
// Arms add up, and nothing in them is written by hand:
//   W0   a new project: connect, sync the schema.
//   W1a  W0 + ZLens's own draft of the model, unreviewed.
//   WM   W1a + every join that has a declared foreign key and passed on the
//        warehouse, certified; NVIDIA's 19 custom analyses imported and put
//        through ZLens's certify; sampled value profile on.
// WM stands in for a modelled project. The custom analyses are the same input
// NVIDIA's own ingestion gives its ontology arm on this dataset.

import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, symlinkSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT, resolveDqlCli } from '../lib/dql.mjs';

const WORK = join(REPO_ROOT, 'work', 'wwi');
const SCHEMAS = 'application,purchasing,sales,warehouse,website';
const CONNECTION = { driver: 'postgresql', host: '127.0.0.1', port: 55432, database: 'wideworldimporters', username: 'wwi_reader', sslMode: 'disable' };
const ENV = { ...process.env, DQL_TELEMETRY_DISABLED: '1', DQL_EMBEDDINGS_AUTODETECT: 'off' };
const OWNER = 'benchmark@zlens.test';

function zlens(cli, dir, args, record, timeout = 300_000, { mayFail = false } = {}) {
  const result = spawnSync(process.execPath, [cli.entry, ...args], { cwd: dir, env: ENV, encoding: 'utf-8', timeout, maxBuffer: 256 * 1024 * 1024 });
  record.steps.push({ command: `zlens ${args.join(' ')}`, code: result.status, tail: `${result.stdout}${result.stderr}`.trim().split('\n').slice(mayFail ? -40 : -3) });
  if (result.status !== 0 && !mayFail) throw new Error(`zlens ${args.join(' ')} failed:\n${result.stderr || result.stdout}`);
  return result.stdout;
}

function updateConfig(dir, change) {
  const path = join(dir, 'dql.config.json');
  const config = JSON.parse(readFileSync(path, 'utf-8'));
  change(config);
  writeFileSync(path, `${JSON.stringify(config, null, 2)}\n`);
}

// CL: the same data under cryptic, legacy-warehouse names (wwi/cryptic.py), legacy decoys included.
const CRYPTIC = { connection: { ...CONNECTION, database: 'wwicryptic' }, schemas: 'ap,pu,sl,wh,ws,lg' };

function baseProject(cli, dir, record, schemas = SCHEMAS, connection = CONNECTION) {
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  zlens(cli, WORK, ['init', dir, '--warehouse-first'], record);
  updateConfig(dir, (config) => {
    config.defaultConnection = 'default';
    config.connections = { default: connection };
  });
  mkdirSync(join(dir, '.dql'), { recursive: true });
  symlinkSync(join(WORK, 'connectors'), join(dir, '.dql', 'connectors'), 'dir');
  zlens(cli, dir, ['sync', 'warehouse', '.', '--schemas', schemas], record);
}

function modelFiles(dir) {
  const domains = join(dir, 'domains');
  return readdirSync(domains).map((name) => join(domains, name, 'modeling', 'model.dql.yaml')).filter((path) => existsSync(path) && statSync(path).isFile());
}

/** Relationship ids whose draft says a declared foreign key backs them. */
function foreignKeyRelationships(dir) {
  const ids = [];
  for (const path of modelFiles(dir)) {
    const domain = path.split('/').at(-3);
    const lines = readFileSync(path, 'utf-8').split('\n');
    let id = null;
    for (const line of lines) {
      const start = /^ {2}- id: (\S+)$/.exec(line);
      if (start) id = start[1];
      if (id && /^ {4}rationale: .*declares a foreign key/.test(line)) ids.push(`${domain}::relationship::${id}`);
    }
  }
  return ids;
}

function writeCustomAnalyses() {
  const folder = join(WORK, 'custom-sql');
  rmSync(folder, { recursive: true, force: true });
  mkdirSync(folder, { recursive: true });
  for (const analysis of JSON.parse(readFileSync(join(WORK, 'dataset', 'custom_analyses.json'), 'utf-8'))) {
    const slug = analysis.name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
    writeFileSync(join(folder, `${slug}.sql`), `-- ${analysis.name}: ${analysis.description}\n${analysis.sql.trim()}\n`);
  }
  return folder;
}

function main() {
  const armFlag = process.argv.indexOf('--arm');
  const arm = process.argv[armFlag + 1];
  if (armFlag < 0 || !['W0', 'W1a', 'WM', 'WL', 'CL'].includes(arm)) throw new Error('--arm W0|W1a|WM|WL|CL is required.');
  const cli = resolveDqlCli();
  const dir = join(WORK, 'projects', arm);
  const record = { arm, builtAt: new Date().toISOString(), cli: cli.entry, steps: [] };
  // WL: W0 plus the legacy schema, too large to show whole, so search does the work.
  if (arm === 'CL') baseProject(cli, dir, record, CRYPTIC.schemas, CRYPTIC.connection);
  else baseProject(cli, dir, record, arm === 'WL' ? `${SCHEMAS},legacy` : SCHEMAS);
  // WM keeps one domain: a default draft splits domains by schema with no exports
  // between them, so it fails `zlens model validate` on this database. W1a keeps
  // that default, because it is what a new user gets.
  if (arm === 'W1a') zlens(cli, dir, ['model', 'apply-discovery', '.', '--apply', '--validate'], record, 600_000);
  if (arm === 'WM') zlens(cli, dir, ['model', 'apply-discovery', '.', '--apply', '--validate', '--domain', 'wideworldimporters'], record, 600_000);
  if (arm === 'WM') {
    const ids = foreignKeyRelationships(dir);
    record.foreignKeyRelationships = ids.length;
    for (const id of ids) zlens(cli, dir, ['model', 'validate-relationship', id, '.', '--certify'], record);
    zlens(cli, dir, ['import', 'sql', writeCustomAnalyses(), '--domain', 'wideworldimporters', '--owner', OWNER, '--no-preview'], record, 600_000);
    // Exits non-zero when a draft fails its checks. That draft stays a draft, which is the right outcome.
    zlens(cli, dir, ['certify', '--from-import', '--apply'], record, 300_000, { mayFail: true });
    updateConfig(dir, (config) => {
      config.agent = { ...config.agent, valueProfile: { mode: 'sampled' } };
    });
    zlens(cli, dir, ['sync', 'warehouse', '.', '--schemas', SCHEMAS], record);
    zlens(cli, dir, ['model', 'validate', '.'], record);
  }
  writeFileSync(join(WORK, `build-${arm}.json`), `${JSON.stringify(record, null, 2)}\n`);
  console.log(`${arm}: ${record.steps.length} steps, ${record.foreignKeyRelationships ?? 0} foreign-key joins certified`);
}

main();

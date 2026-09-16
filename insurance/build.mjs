#!/usr/bin/env node
// Build the insurance benchmark: dbt Labs' ACME insurance dbt project, one
// copy per DQL layer, each with its own DuckDB warehouse, and the correct
// answer to every question computed on that warehouse.
//
//   node insurance/build.mjs [--layer L0] [--skip-gold]
//
// Every step writes what it did into work/insurance/build.json; REPORT.md
// explains the steps. The correct answers are written to work/insurance/gold/,
// outside every DQL project, so Ask has no way to read them.

import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { basename, join, relative } from 'node:path';
import { REPO_ROOT, resolveDqlCli, runDql, dqlVersion } from '../lib/dql.mjs';
import { readQuestions, DBT_LABS_SELECTED, QUADRANTS } from './questions.mjs';

const DATA = join(REPO_ROOT, 'data', 'insurance');
const SOURCE = join(DATA, 'semantic-layer-llm-benchmarking');
const QUESTION_FILE = join(DATA, 'dbt-llm-sl-bench', 'benchmark_questions.ttl');
const WORK = join(REPO_ROOT, 'work', 'insurance');
const PYTHON = join(REPO_ROOT, '.venv', 'bin', 'python');
const DBT = join(REPO_ROOT, '.venv', 'bin', 'dbt');
const SHARED_CONNECTORS = join(REPO_ROOT, '.connectors');
const DATABASE_FILE = 'acme_insurance.duckdb';
const SEED_DIR = join('ACME_Insurance', 'data');

/**
 * What each layer's project contains. Layers add up: each one is the previous
 * layer plus one thing. `overlay` folders hold files written for that layer
 * (from documentation only; see docs/methodology.md).
 */
export const LAYERS = {
  L0: { description: 'dbt project only', semanticLayer: false, overlays: [] },
  L1: { description: 'L0 + DQL modeling', semanticLayer: false, overlays: ['L1'] },
  L2: { description: 'L1 + dbt semantic layer (MetricFlow)', semanticLayer: true, overlays: ['L1'] },
  L3: { description: 'L2 + DQL skills', semanticLayer: true, overlays: ['L1', 'L3'] },
};

/**
 * The parts of dbt Labs' repository that make up the dbt project. Everything
 * else is left out on purpose: `ACME_Insurance/investigation/` and
 * `hex_notebook/` contain the questions with their correct SQL, `DDL/` and
 * `ontology/` are the benchmark's schema documents (inputs for writing L1, not
 * part of a dbt project), and the README describes the benchmark.
 */
const PROJECT_ENTRIES = ['dbt_project.yml', 'models', 'macros', 'analyses', 'snapshots', 'tests', 'LICENSE.txt'];
const SEMANTIC_DIR = join('models', 'omg_semantics');

function sh(command, args, { cwd, timeout = 600_000, input } = {}) {
  const result = spawnSync(command, args, {
    cwd,
    input,
    encoding: 'utf-8',
    timeout,
    maxBuffer: 256 * 1024 * 1024,
    env: { ...process.env, DBT_SEND_ANONYMOUS_USAGE_STATS: 'false', DO_NOT_TRACK: '1' },
  });
  if (result.error) throw result.error;
  return { code: result.status, stdout: result.stdout ?? '', stderr: result.stderr ?? '' };
}

function git(args) {
  const result = sh('git', ['-C', SOURCE, ...args]);
  if (result.code !== 0) throw new Error(`git ${args.join(' ')}: ${result.stderr}`);
  return result.stdout.trim();
}

function hashFiles(root, files) {
  const hash = createHash('sha256');
  for (const file of [...files].sort()) {
    hash.update(relative(root, file));
    hash.update(readFileSync(file));
  }
  return hash.digest('hex');
}

function listFiles(dir) {
  return readdirSync(dir, { withFileTypes: true, recursive: true })
    .filter((entry) => entry.isFile())
    .map((entry) => join(entry.parentPath ?? entry.path, entry.name));
}

function duckdbQuery(database, queries) {
  const result = sh(PYTHON, [join(REPO_ROOT, 'lib', 'duckdb_query.py')], { input: JSON.stringify({ database, queries }) });
  if (result.code !== 0) throw new Error(`duckdb_query.py failed: ${result.stderr}`);
  return JSON.parse(result.stdout);
}

function linkSharedConnectors(dir) {
  if (!existsSync(join(SHARED_CONNECTORS, 'node_modules', 'duckdb'))) {
    throw new Error('The shared DuckDB driver is not installed. Run: npm run connectors:install');
  }
  mkdirSync(join(dir, '.dql'), { recursive: true });
  const target = join(dir, '.dql', 'connectors');
  rmSync(target, { recursive: true, force: true });
  symlinkSync(SHARED_CONNECTORS, target, 'dir');
}

/**
 * dbt guesses a seed column's type from a sample of rows. dbt-duckdb turns a
 * whole-number column into a 32-bit INTEGER, and Policy.Policy_Number has
 * values above that range (dbt Labs built on a cloud warehouse with wider
 * numbers). Every CSV column holding a whole number outside the 32-bit range
 * is declared `bigint` in the project's seed config. The rule looks only at
 * the data files, never at the questions. Returns what was declared.
 */
function widenIntegerSeedColumns(dir) {
  const scan = sh(PYTHON, ['-c', [
    'import csv, glob, json, os, sys',
    'out = {}',
    'for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.csv"))):',
    '    with open(f, newline="") as h:',
    '        for row in csv.DictReader(h):',
    '            for k, v in row.items():',
    '                try: n = int(v)',
    '                except (ValueError, TypeError): continue',
    '                if abs(n) > 2**31 - 1: out.setdefault(os.path.basename(f)[:-4], set()).add(k)',
    'print(json.dumps({t: sorted(c) for t, c in out.items()}))',
  ].join('\n'), join(dir, SEED_DIR)]);
  if (scan.code !== 0) throw new Error(`seed column scan failed: ${scan.stderr}`);
  const wide = JSON.parse(scan.stdout);
  if (Object.keys(wide).length === 0) return wide;
  const projectFile = join(dir, 'dbt_project.yml');
  const text = readFileSync(projectFile, 'utf-8');
  // The published file ends with this block; refuse to patch anything else.
  if (!/\nseeds:\n  schema: _seed\s*$/.test(text)) throw new Error('dbt_project.yml no longer ends with the expected seeds block.');
  const lines = ['  cwd_benchmark_data:'];
  for (const [table, columns] of Object.entries(wide)) {
    lines.push(`    ${table}:`, '      +column_types:', ...columns.map((column) => `        ${column}: bigint`));
  }
  writeFileSync(projectFile, `${text.trimEnd()}\n${lines.join('\n')}\n`);
  return wide;
}

/** Copy the dbt project for one layer and write its dbt profile. */
function copyProject(layer, dir) {
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  for (const entry of PROJECT_ENTRIES) {
    if (existsSync(join(SOURCE, entry))) cpSync(join(SOURCE, entry), join(dir, entry), { recursive: true });
  }
  // Seeds: the CSV files only. The R2RML mapping in the same folder is an
  // ontology document, not data.
  mkdirSync(join(dir, SEED_DIR), { recursive: true });
  for (const name of readdirSync(join(SOURCE, SEED_DIR))) {
    if (name.endsWith('.csv')) cpSync(join(SOURCE, SEED_DIR, name), join(dir, SEED_DIR, name));
  }
  widenIntegerSeedColumns(dir);
  if (!LAYERS[layer].semanticLayer) rmSync(join(dir, SEMANTIC_DIR), { recursive: true, force: true });
  for (const overlay of LAYERS[layer].overlays) {
    const from = join(REPO_ROOT, 'insurance', 'layers', overlay);
    if (!existsSync(from)) throw new Error(`Layer ${layer} needs insurance/layers/${overlay}/, which has not been written yet.`);
    cpSync(from, dir, { recursive: true });
  }
  writeFileSync(
    join(dir, 'profiles.yml'),
    [
      'cwd_benchmark_data:',
      '  target: dev',
      '  outputs:',
      '    dev:',
      '      type: duckdb',
      `      path: ${JSON.stringify(join(dir, DATABASE_FILE))}`,
      '      threads: 4',
      '',
    ].join('\n'),
  );
}

function dbt(args, dir) {
  const result = sh(DBT, [...args, '--project-dir', dir, '--profiles-dir', dir], { cwd: dir });
  const output = `${result.stdout}${result.stderr}`;
  return { command: `dbt ${args.join(' ')}`, code: result.code, summary: output.split('\n').filter((line) => /Done\.|Completed|ERROR|error/i.test(line)).slice(-4) };
}

/** Every seed table has the rows of its CSV, and every model the rows of its seed. */
function checkRowCounts(dir) {
  const database = join(dir, DATABASE_FILE);
  const tables = duckdbQuery(database, [{
    id: 'tables',
    sql: "select table_schema, table_name, table_type from information_schema.tables where table_catalog = current_database() order by 1, 2",
  }]).tables;
  if (tables.error) throw new Error(tables.error);
  const seedSchema = tables.rows.find(([schema, name]) => name.toLowerCase() === 'claim' && schema !== 'main')?.[0];
  if (!seedSchema) throw new Error('No seed schema with a Claim table was built.');
  const csvs = readdirSync(join(dir, SEED_DIR)).filter((name) => name.endsWith('.csv'));
  // The CSV side is counted by a separate, unlocked DuckDB session.
  const csvCounts = JSON.parse(sh(PYTHON, ['-c', [
    'import duckdb, json, sys',
    'files = json.loads(sys.argv[1])',
    'out = {f: duckdb.sql(f"select count(*) from read_csv(\'{f}\', header=true)").fetchone()[0] for f in files}',
    'print(json.dumps(out))',
  ].join('\n'), JSON.stringify(csvs.map((name) => join(dir, SEED_DIR, name)))]).stdout);
  const tableCount = (schema, name) => {
    const result = duckdbQuery(database, [{ id: 'n', sql: `select count(*) from "${schema}"."${name}"` }]).n;
    return result.error ? null : result.rows[0][0];
  };
  const seeds = csvs.map((file) => {
    const table = basename(file, '.csv');
    const csvRows = csvCounts[join(dir, SEED_DIR, file)];
    const tableRows = tableCount(seedSchema, table);
    return { table, csvRows, tableRows, ok: csvRows === tableRows };
  });
  // A model is `select <columns> from ref('<Seed>')`, so it must have the seed's rows.
  const models = listFiles(join(dir, 'models', 'omg_models')).filter((file) => file.endsWith('.sql')).map((file) => {
    const model = basename(file, '.sql');
    const seed = /ref\('([^']+)'\)/.exec(readFileSync(file, 'utf-8'))?.[1] ?? null;
    const modelRows = tableCount('main', model);
    const seedRows = seed ? tableCount(seedSchema, seed) : null;
    return { model, seed, modelRows, seedRows, ok: modelRows !== null && modelRows === seedRows };
  });
  return { seedSchema, tables: tables.rows.map(([schema, name, type]) => `${schema}.${name} (${type})`), seeds, models };
}

/**
 * The publishers ran the correct SQL on cloud warehouses; a few spellings mean
 * something else in DuckDB. Each port changes spelling only, never meaning,
 * and every question it touched is recorded with the published SQL beside it.
 */
export const DIALECT_PORTS = [
  {
    pattern: /DATEDIFF\("(day)",/gi,
    replacement: "DATEDIFF('$1',",
    reason: 'Snowflake reads DATEDIFF("day", ...) as the date part; DuckDB reads "day" as a column name. The date part is written as a string instead.',
  },
];

export function portGoldSql(sql) {
  let ported = sql;
  const applied = [];
  for (const port of DIALECT_PORTS) {
    const next = ported.replace(port.pattern, port.replacement);
    if (next !== ported) applied.push(port.reason);
    ported = next;
  }
  return { sql: ported, applied };
}

/** Run every question's correct SQL on the warehouse and keep the rows. */
function computeGold(dir, questions) {
  const ported = new Map(questions.map((q) => [q.id, portGoldSql(q.goldSql)]));
  const results = duckdbQuery(join(dir, DATABASE_FILE), questions.map((q) => ({ id: q.id, sql: ported.get(q.id).sql })));
  const answers = {};
  for (const q of questions) {
    const result = results[q.id];
    const port = ported.get(q.id);
    const dialect = port.applied.length ? { ranSql: port.sql, dialectPorts: port.applied } : {};
    answers[q.id] = result.error
      ? { error: result.error, ...dialect }
      : { columns: result.columns, rowCount: result.rows.length, rows: result.rows, ...dialect };
  }
  return answers;
}

export function build({ layer = 'L0', skipGold = false } = {}) {
  if (!LAYERS[layer]) throw new Error(`Unknown layer ${layer}. Known: ${Object.keys(LAYERS).join(', ')}`);
  if (!existsSync(SOURCE)) throw new Error('Insurance data is missing. Run: insurance/download.sh');
  const cli = resolveDqlCli();
  const dir = join(WORK, 'projects', layer);
  const record = {
    layer,
    description: LAYERS[layer].description,
    builtAt: new Date().toISOString(),
    source: {
      repository: 'https://github.com/dbt-labs/semantic-layer-llm-benchmarking',
      commit: git(['rev-parse', 'HEAD']),
      branch: git(['rev-parse', '--abbrev-ref', 'HEAD']),
      dirty: git(['status', '--porcelain']) !== '',
      seedHash: hashFiles(SOURCE, listFiles(join(SOURCE, SEED_DIR)).filter((file) => file.endsWith('.csv'))),
    },
    tools: {
      dbt: sh(DBT, ['--version']).stdout.split('\n').filter((line) => /installed|duckdb/i.test(line)).map((line) => line.trim()),
      duckdbPython: sh(PYTHON, ['-c', 'import duckdb; print(duckdb.__version__)']).stdout.trim(),
      dql: { version: dqlVersion(cli), source: cli.source },
    },
    steps: [],
  };

  copyProject(layer, dir);
  record.projectDir = relative(REPO_ROOT, dir);
  record.projectFiles = listFiles(dir).map((file) => relative(dir, file)).sort();

  for (const args of [['seed'], ['run'], ['docs', 'generate']]) {
    const step = dbt(args, dir);
    record.steps.push(step);
    if (step.code !== 0) throw new Error(`${step.command} failed:\n${step.summary.join('\n')}`);
  }

  record.rowCounts = checkRowCounts(dir);
  const badSeeds = record.rowCounts.seeds.filter((seed) => !seed.ok);
  const badModels = record.rowCounts.models.filter((model) => !model.ok);
  if (badSeeds.length || badModels.length) {
    writeFileSync(join(WORK, `build-${layer}.json`), `${JSON.stringify(record, null, 2)}\n`);
    throw new Error(`Row counts differ from the data files: ${JSON.stringify({ badSeeds, badModels })}`);
  }

  const before = new Set(readdirSync(dir));
  const init = runDql(['init', dir], { cli, cwd: dir });
  record.steps.push({ command: 'dql init', code: init.code, summary: `${init.stdout}${init.stderr}`.split('\n').filter(Boolean).slice(-6) });
  if (init.code !== 0) throw new Error(`dql init failed:\n${init.stderr || init.stdout}`);
  record.addedByDqlInit = readdirSync(dir).filter((name) => !before.has(name)).sort();
  linkSharedConnectors(dir);
  const config = JSON.parse(readFileSync(join(dir, 'dql.config.json'), 'utf-8'));
  record.dqlConfig = { connections: config.connections, dbt: config.dbt, semanticLayer: config.semanticLayer ?? null, modeling: config.modeling ?? null };

  if (!skipGold) {
    const questions = readQuestions(QUESTION_FILE);
    const gold = computeGold(dir, questions);
    const goldDir = join(WORK, 'gold');
    mkdirSync(goldDir, { recursive: true });
    const selected = new Set(DBT_LABS_SELECTED);
    const cases = questions.map((q) => ({
      ...q,
      quadrantMeaning: QUADRANTS[q.quadrant] ?? null,
      dbtLabsSelected: selected.has(q.question),
      gold: gold[q.id],
    }));
    writeFileSync(join(goldDir, 'answers.json'), `${JSON.stringify({ builtFrom: layer, questionFile: relative(REPO_ROOT, QUESTION_FILE), cases }, null, 2)}\n`);
    record.gold = {
      questions: cases.length,
      ran: cases.filter((c) => !c.gold.error).length,
      failed: cases.filter((c) => c.gold.error).map((c) => ({ id: c.id, error: c.gold.error })),
      empty: cases.filter((c) => c.gold.rowCount === 0).map((c) => c.id),
      dialectPorted: cases.filter((c) => c.gold.dialectPorts).map((c) => c.id),
    };
  }

  mkdirSync(WORK, { recursive: true });
  writeFileSync(join(WORK, `build-${layer}.json`), `${JSON.stringify(record, null, 2)}\n`);
  return record;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const layerIndex = args.indexOf('--layer');
  const layer = layerIndex >= 0 ? args[layerIndex + 1] : 'L0';
  try {
    const record = build({ layer, skipGold: args.includes('--skip-gold') });
    const seeds = record.rowCounts.seeds;
    const models = record.rowCounts.models;
    console.log(`${layer}: ${record.projectDir}`);
    console.log(`seeds ${seeds.filter((s) => s.ok).length}/${seeds.length} match their CSV; models ${models.filter((m) => m.ok).length}/${models.length} match their seed`);
    console.log(`dql init added: ${record.addedByDqlInit.join(', ')}`);
    console.log(`connection: ${JSON.stringify(record.dqlConfig.connections)}`);
    if (record.gold) console.log(`gold: ${record.gold.ran}/${record.gold.questions} ran; failed ${record.gold.failed.length}; empty ${record.gold.empty.length}`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

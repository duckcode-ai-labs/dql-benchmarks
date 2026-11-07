#!/usr/bin/env node
// Build one arm's ZLens project on the owner's NBA dbt project (a copy).
//
//   DQL_CLI=<zlens dist/index.js> node nba/build.mjs --arm D0|D1|D2|W0|W1 [--sync-warehouse] [--out <dir>]
//
// Arms add up, and nothing in them is written by hand:
//   D0  the dbt project as a new user sets it up: `zlens init ./dql` from the dbt
//       repo root (it finds dbt_project.yml and the .duckdb file), then
//       `zlens sync dbt`. No meaning files.
//   D1  D0 + `zlens model draft-meanings` (dry run first), unreviewed.
//   D2  D1 + `zlens model draft-terms`.
//   W0  the same DuckDB file, warehouse-first (no dbt): init --warehouse-first,
//       sync warehouse. W1 = W0 + draft-meanings.
//   DA  D0 + `zlens model draft --apply --passed-only`: the model ZLens drafts, as drafted (P6).
//   DM  D0 + the hand-built model from R3 (nba/dm-model), for reference (P6).
//   WA  W0 + `zlens model draft --apply --passed-only`: warehouse-first, the model ZLens drafts.
//   WS  the same NBA tables on Snowflake (nba/snowflake), warehouse-first, as the read-only
//       key-pair user ZLENS_APP_SVC (SNOWFLAKE_ACCOUNT, NBA_SNOWFLAKE_KEY). WAS = WS + the draft,
//       applied as WA's is: WA vs WAS differ only in the engine.
//
// The dbt project is work/nba/dbt, a copy of /Users/Kranthi_1/dbt-projects/nba_analysis
// (models, macros, snapshots, dbt_project.yml), with local_duckdb/target as its target/
// and local_duckdb/profiles.yml as its profiles.yml. Nothing here reads or writes the
// owner's repo. Each project's paths are made absolute so a run can copy it anywhere;
// nba/run.mjs points the connection at a fresh copy of the database for each run.

import { spawnSync } from 'node:child_process';
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT, resolveDqlCli } from '../lib/dql.mjs';

export const WORK = join(REPO_ROOT, 'work', 'nba');
export const DBT = join(WORK, 'dbt');
export const SOURCE_DB = join(WORK, 'source', 'nba_analysis.duckdb');
const ENV = { ...process.env, DQL_TELEMETRY_DISABLED: '1', DQL_EMBEDDINGS_AUTODETECT: 'off' };
export const MODEL = 'claude-sonnet-5-5';
/** `--sync-warehouse`: run `zlens sync warehouse` after `sync dbt` (R2 on). */
const SYNC_WAREHOUSE = process.argv.includes('--sync-warehouse');
/** `--out <dir>`: where the build record goes (default work/nba). */
const RECORD_DIR = process.argv.includes('--out') ? process.argv[process.argv.indexOf('--out') + 1] : null;

function zlens(cli, dir, args, record, timeout = 600_000, { mayFail = false } = {}) {
  const started = Date.now();
  const result = spawnSync(process.execPath, [cli.entry, ...args], { cwd: dir, env: ENV, encoding: 'utf-8', timeout, maxBuffer: 256 * 1024 * 1024 });
  record.steps.push({ command: `zlens ${args.join(' ')}`, code: result.status, seconds: Math.round((Date.now() - started) / 1000), output: `${result.stdout}${result.stderr}`.trim().split('\n').slice(-200) });
  if (result.status !== 0 && !mayFail) throw new Error(`zlens ${args.join(' ')} failed:\n${result.stderr || result.stdout}`);
  return result.stdout;
}

function updateConfig(dir, change) {
  const path = join(dir, 'dql.config.json');
  const config = JSON.parse(readFileSync(path, 'utf-8'));
  change(config);
  writeFileSync(path, `${JSON.stringify(config, null, 2)}\n`);
}

export function writeProviderSettings(projectDir, model = MODEL) {
  mkdirSync(join(projectDir, '.dql'), { recursive: true });
  writeFileSync(join(projectDir, '.dql', 'provider-settings.json'), `${JSON.stringify({
    version: 1,
    activeProvider: 'claude-code',
    providers: { 'claude-code': { id: 'claude-code', enabled: true, model, updatedAt: new Date().toISOString() } },
  }, null, 2)}\n`, { mode: 0o600 });
}

function linkConnectors(dir) {
  mkdirSync(join(dir, '.dql'), { recursive: true });
  if (!existsSync(join(dir, '.dql', 'connectors'))) symlinkSync(join(WORK, 'connectors'), join(dir, '.dql', 'connectors'), 'dir');
}

/** D0: what `zlens init ./dql` and `zlens sync dbt` give a new user, with absolute paths. */
function dbtProject(cli, dir, record) {
  const initDir = join(DBT, 'dql');
  rmSync(initDir, { recursive: true, force: true });
  zlens(cli, DBT, ['init', './dql'], record);
  const config = JSON.parse(readFileSync(join(initDir, 'dql.config.json'), 'utf-8'));
  record.initConfig = config;
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(join(dir, '..'), { recursive: true });
  cpSync(initDir, dir, { recursive: true });
  rmSync(initDir, { recursive: true, force: true });
  updateConfig(dir, (cfg) => {
    cfg.dbt.projectDir = DBT;
    if (cfg.semanticLayer?.projectPath) cfg.semanticLayer.projectPath = DBT;
    // nba/run.mjs repoints this at a fresh copy of the database for each run.
    cfg.connections.default.filepath = join(DBT, 'nba_analysis.duckdb');
  });
  linkConnectors(dir);
  zlens(cli, dir, ['sync', 'dbt', '.'], record);
  // R2 (zlens#245): the documented step before drafting on dbt, so a draft sees every
  // column. R1 ran without it. Every dbt arm gets it, D0 too, so they start alike.
  if (SYNC_WAREHOUSE) record.syncWarehouse = zlens(cli, dir, ['sync', 'warehouse', '.', '--schemas', 'RAW,TRANSFORMED,dev'], record);
}

/** W0: the same database with no dbt, the way no-dbt.md sets it up. */
function warehouseProject(cli, dir, record) {
  rmSync(dir, { recursive: true, force: true });
  // `zlens init --warehouse-first` makes a dbt project anyway when dbt_project.yml is
  // in .., ../.., ../dbt or ../../dbt (work/nba/dbt is ../../dbt from projects/W0), so
  // it is initialised where no dbt project is near, then moved.
  const away = join(WORK, 'wh', 'projects', 'W0');
  rmSync(away, { recursive: true, force: true });
  mkdirSync(join(away, '..'), { recursive: true });
  zlens(cli, join(away, '..'), ['init', away, '--warehouse-first'], record);
  mkdirSync(join(dir, '..'), { recursive: true });
  cpSync(away, dir, { recursive: true });
  rmSync(join(WORK, 'wh'), { recursive: true, force: true });
  updateConfig(dir, (cfg) => {
    cfg.defaultConnection = 'default';
    cfg.connections = { default: { driver: 'duckdb', filepath: join(WORK, 'warehouse-db', 'nba_analysis.duckdb') } };
  });
  linkConnectors(dir);
  mkdirSync(join(WORK, 'warehouse-db'), { recursive: true });
  cpSync(SOURCE_DB, join(WORK, 'warehouse-db', 'nba_analysis.duckdb'));
  spawnSync('chmod', ['u+w', join(WORK, 'warehouse-db', 'nba_analysis.duckdb')]);
  zlens(cli, dir, ['sync', 'warehouse', '.', '--schemas', 'RAW,TRANSFORMED,dev'], record);
}

/** WS: the NBA tables on Snowflake (nba/snowflake/README.md), warehouse-first, the way a customer connects. */
function snowflakeWarehouseProject(cli, dir, record) {
  const account = process.env.SNOWFLAKE_ACCOUNT;
  if (!account) throw new Error('SNOWFLAKE_ACCOUNT is required for WS (orgname-accountname).');
  const key = process.env.NBA_SNOWFLAKE_KEY ?? join(process.env.HOME ?? '', '.zlens-bench', 'snowflake', 'reader.p8');
  rmSync(dir, { recursive: true, force: true });
  const away = join(WORK, 'wh', 'projects', 'WS');
  rmSync(away, { recursive: true, force: true });
  mkdirSync(join(away, '..'), { recursive: true });
  zlens(cli, join(away, '..'), ['init', away, '--warehouse-first'], record);
  mkdirSync(join(dir, '..'), { recursive: true });
  cpSync(away, dir, { recursive: true });
  rmSync(join(WORK, 'wh'), { recursive: true, force: true });
  updateConfig(dir, (cfg) => {
    cfg.defaultConnection = 'default';
    cfg.connections = { default: {
      driver: 'snowflake', account, username: 'ZLENS_APP_SVC', authMethod: 'key_pair', privateKeyPath: key,
      warehouse: 'ZLENS_BENCH_WH', database: 'NBA', schema: 'TRANSFORMED', role: 'ZLENS_READER',
    } };
  });
  zlens(cli, dir, ['sync', 'warehouse', '.', '--database', 'NBA', '--schemas', 'RAW,TRANSFORMED,DEV'], record);
}

function draftMeanings(cli, dir, record) {
  writeProviderSettings(dir);
  record.dryRun = zlens(cli, dir, ['model', 'draft-meanings', '.', '--dry-run', '--format', 'json'], record);
  record.dryRunHuman = zlens(cli, dir, ['model', 'draft-meanings', '.', '--dry-run'], record);
  const started = Date.now();
  record.draft = zlens(cli, dir, ['model', 'draft-meanings', '.', '--format', 'json'], record, 1_800_000);
  record.draftSeconds = Math.round((Date.now() - started) / 1000);
  record.status = zlens(cli, dir, ['model', 'meanings', '.'], record, 120_000, { mayFail: true });
  // What a second run would send: nothing, when every table was drafted or had nothing to add.
  record.rerunPlan = zlens(cli, dir, ['model', 'draft-meanings', '.', '--dry-run', '--format', 'json'], record);
}

function main() {
  const armFlag = process.argv.indexOf('--arm');
  const arm = process.argv[armFlag + 1];
  if (armFlag < 0 || !['D0', 'D1', 'D2', 'W0', 'W1', 'DA', 'DM', 'WA', 'WS', 'WAS'].includes(arm)) throw new Error('--arm D0|D1|D2|W0|W1|DA|DM|WA|WS|WAS is required.');
  const cli = resolveDqlCli();
  const dir = join(WORK, 'projects', arm);
  const record = { arm, builtAt: new Date().toISOString(), cli: cli.entry, steps: [] };
  if (arm === 'D0') dbtProject(cli, dir, record);
  if (arm === 'W0') warehouseProject(cli, dir, record);
  if (arm === 'WS') snowflakeWarehouseProject(cli, dir, record);
  // WA and WAS: the warehouse-first project plus the model ZLens drafts, applied as drafted.
  if (arm === 'WA' || arm === 'WAS') {
    const base = join(WORK, 'projects', arm === 'WA' ? 'W0' : 'WS');
    if (!existsSync(base)) throw new Error(`Build ${arm === 'WA' ? 'W0' : 'WS'} first.`);
    rmSync(dir, { recursive: true, force: true });
    cpSync(base, dir, { recursive: true, verbatimSymlinks: true });
    const started = Date.now();
    record.draft = zlens(cli, dir, ['model', 'draft', '.'], record, 1_800_000);
    record.apply = zlens(cli, dir, ['model', 'draft', '.', '--apply', '--passed-only'], record, 1_800_000);
    record.draftSeconds = Math.round((Date.now() - started) / 1000);
    record.validate = zlens(cli, dir, ['model', 'validate', '.'], record, 300_000, { mayFail: true });
  }
  if (arm === 'D1' || arm === 'W1') {
    const base = join(WORK, 'projects', arm === 'D1' ? 'D0' : 'W0');
    if (!existsSync(base)) throw new Error(`Build ${arm === 'D1' ? 'D0' : 'W0'} first.`);
    rmSync(dir, { recursive: true, force: true });
    cpSync(base, dir, { recursive: true, verbatimSymlinks: true });
    draftMeanings(cli, dir, record);
  }
  if (arm === 'D2') {
    const base = join(WORK, 'projects', 'D1');
    if (!existsSync(join(base, 'meanings'))) throw new Error('Build D1 first.');
    rmSync(dir, { recursive: true, force: true });
    cpSync(base, dir, { recursive: true, verbatimSymlinks: true });
    writeProviderSettings(dir);
    const started = Date.now();
    record.terms = zlens(cli, dir, ['model', 'draft-terms', '.', '--format', 'json'], record, 1_800_000);
    record.termsSeconds = Math.round((Date.now() - started) / 1000);
    zlens(cli, dir, ['sync', 'dbt', '.'], record);
  }
  // P6 (design "ZLens drafts the whole business model"): DA is D0 plus the model ZLens
  // drafts, applied as drafted (everything whose checks passed, no edits); DM is D0
  // plus the business model built blind by hand in R3 (nba/dm-model).
  if (arm === 'DA' || arm === 'DM') {
    const base = join(WORK, 'projects', 'D0');
    if (!existsSync(base)) throw new Error('Build D0 first.');
    rmSync(dir, { recursive: true, force: true });
    cpSync(base, dir, { recursive: true, verbatimSymlinks: true });
    if (arm === 'DA') {
      const started = Date.now();
      record.draft = zlens(cli, dir, ['model', 'draft', '.'], record, 1_800_000);
      record.apply = zlens(cli, dir, ['model', 'draft', '.', '--apply', '--passed-only'], record, 1_800_000);
      record.draftSeconds = Math.round((Date.now() - started) / 1000);
    } else {
      mkdirSync(join(dir, 'domains', 'nba', 'modeling'), { recursive: true });
      cpSync(join(REPO_ROOT, 'nba', 'dm-model', 'domain.dql'), join(dir, 'domains', 'nba', 'domain.dql'));
      cpSync(join(REPO_ROOT, 'nba', 'dm-model', 'model.dql.yaml'), join(dir, 'domains', 'nba', 'modeling', 'model.dql.yaml'));
    }
    record.validate = zlens(cli, dir, ['model', 'validate', '.'], record, 300_000, { mayFail: true });
  }
  writeFileSync(join(RECORD_DIR ?? WORK, `build-${arm}.json`), `${JSON.stringify(record, null, 2)}\n`);
  console.log(`${arm}: ${record.steps.length} steps`);
}

main();

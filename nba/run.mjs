#!/usr/bin/env node
// Ask the NBA questions through ZLens's Ask on one arm's project and save the SQL
// each answer ran, for nba/grade.py. Adapted from wwi/run.mjs.
//
//   DQL_CLI=<zlens dist/index.js> node nba/run.mjs --arm D0 --run <id> [--pass 1]
//        [--only 3,5] [--questions <file.json>] [--model claude-sonnet-5-5] [--keep-cache]
//
// Each run asks on a fresh copy of the built project and a fresh copy of the
// database (DuckDB lets one process open a file), so nothing one run leaves
// behind reaches another, and arms can run side by side. The gold SQL never
// enters the project or the eval file.

import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { appendFileSync, copyFileSync, chmodSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { basename, join, relative } from 'node:path';
import { REPO_ROOT, dqlVersion, resolveDqlCli } from '../lib/dql.mjs';
import { buildIdentity } from '../lib/build-identity.mjs';
import { startRuntime } from '../lib/runtime.mjs';
import { providerOutages } from '../insurance/run.mjs';
import { storedRuns } from '../wwi/run.mjs';

const WORK = join(REPO_ROOT, 'work', 'nba');
const SOURCE_DB = join(WORK, 'source', 'nba_analysis.duckdb');
const CASE_TIMEOUT_MS = 900_000;
const HOST_ROW_GUARD = /\nLIMIT 501\s*$/;
const RUN_ENV = { DQL_EMBEDDINGS_AUTODETECT: 'off', DQL_TELEMETRY_DISABLED: '1' };

function parseArgs(argv) {
  const options = { arm: null, run: null, pass: 1, only: null, questions: join(REPO_ROOT, 'nba', 'questions.json'), model: 'claude-sonnet-5-5', keepCache: false, sourceDb: null };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--arm') options.arm = argv[++index];
    else if (arg === '--run') options.run = argv[++index];
    else if (arg === '--pass') options.pass = Number(argv[++index]);
    else if (arg === '--only') options.only = new Set(argv[++index].split(',').map(Number));
    else if (arg === '--questions') options.questions = argv[++index];
    else if (arg === '--model') options.model = argv[++index];
    // Q5: an arm with its own warehouse (the NBA tables plus decoy schemas); the copy keeps the file name, which names the database.
    else if (arg === '--source-db') options.sourceDb = argv[++index];
    else if (arg === '--keep-cache') options.keepCache = true;
    else throw new Error(`Unknown option ${arg}`);
  }
  if (!options.arm || !options.run) throw new Error('--arm and --run are required.');
  return options;
}

function freshProject(arm, workDir, keepCache, sourceDb = SOURCE_DB) {
  const target = join(workDir, 'project');
  rmSync(target, { recursive: true, force: true });
  // R2 keeps .dql/cache: on a dbt project the drafts are checked against the schema sync
  // stored there, and without it every draft reads as stale until a new sync (R1 left it out).
  const copy = spawnSync('rsync', ['-a', '--exclude', '.dql/local', ...(keepCache ? [] : ['--exclude', '.dql/cache']), '--exclude', 'logs', `${join(WORK, 'projects', arm)}/`, `${target}/`], { encoding: 'utf-8' });
  if (copy.status !== 0) throw new Error(`copying the ${arm} project failed: ${copy.stderr}`);
  // This run's own database file.
  const database = join(workDir, basename(sourceDb));
  copyFileSync(sourceDb, database);
  chmodSync(database, 0o644);
  const configPath = join(target, 'dql.config.json');
  const config = JSON.parse(readFileSync(configPath, 'utf-8'));
  config.connections.default.filepath = database;
  writeFileSync(configPath, `${JSON.stringify(config, null, 2)}\n`);
  return target;
}

function writeProviderSettings(projectDir, model) {
  writeFileSync(join(projectDir, '.dql', 'provider-settings.json'), `${JSON.stringify({
    version: 1,
    activeProvider: 'claude-code',
    providers: { 'claude-code': { id: 'claude-code', enabled: true, model, updatedAt: new Date().toISOString() } },
  }, null, 2)}\n`, { mode: 0o600 });
}

function runEval(cli, projectDir, evalPath, runtimeBase, logPath, cassetteDir) {
  // Asynchronous, so the runtime's own output keeps draining while the eval runs.
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [
      cli.entry, 'agent', 'eval', relative(projectDir, evalPath), // an absolute path is joined to the cwd (bug)
      '--via', 'runtime', '--runtime-url', runtimeBase, '--format', 'json',
      '--case-timeout-ms', String(CASE_TIMEOUT_MS),
    ], { cwd: projectDir, env: { ...process.env, ...RUN_ENV, DQL_EVAL_CASSETTE_DIR: cassetteDir }, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; process.stderr.write(chunk); });
    child.on('error', reject);
    child.on('exit', (code) => {
      writeFileSync(logPath, stderr);
      resolve({ code, stdout });
    });
  });
}

/** Which tables the drafter was shown, and how they were chosen, from the run's story. */
function schemaStep(projectDir) {
  const store = join(projectDir, '.dql', 'local', 'agent-runs.sqlite');
  const result = spawnSync('sqlite3', ['-json', store, 'select question, payload_json from agent_runs order by rowid'], { encoding: 'utf-8', maxBuffer: 1024 * 1024 * 1024 });
  if (result.status !== 0 || !result.stdout.trim()) return new Map();
  const steps = new Map();
  for (const row of JSON.parse(result.stdout)) {
    const payload = JSON.parse(row.payload_json);
    const story = payload.diagnosticReceiptV9?.story ?? [];
    const schema = story.find((step) => /^(Chose the table|Showed the whole schema|Showed the whole model|Showed the .+ areas?:)/.test(step.title ?? ''));
    const answerText = JSON.stringify(payload).match(/used AI-drafted [^"\\]{0,300}/g) ?? [];
    if (!steps.has(row.question)) steps.set(row.question, { schemaTitle: schema?.title ?? null, schemaDetail: schema?.detail ?? null, draftedNotes: [...new Set(answerText)].slice(0, 4) });
  }
  return steps;
}

function prediction(question, run, outages) {
  if (!run) return { question_id: question.question_id, sql: null, failure: 'unknown_error' };
  const sql = run.executed && run.proposed ? run.proposed.replace(HOST_ROW_GUARD, '') : null;
  let failure = null;
  if (!sql) {
    if (outages.has(question.question)) failure = 'no_model_output';
    else if (run.status === 'failed' || run.status === 'error') failure = 'unknown_error';
    else failure = 'refused';
  }
  return { question_id: question.question_id, sql, failure, ...run };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const outDir = join(REPO_ROOT, 'results', 'nba', options.run, options.arm, `pass-${options.pass}`);
  const workDir = join(WORK, 'runs', options.run, options.arm, `pass-${options.pass}`);
  mkdirSync(outDir, { recursive: true });
  mkdirSync(workDir, { recursive: true });
  const questions = JSON.parse(readFileSync(options.questions, 'utf-8')).filter((question) => !options.only || options.only.has(question.question_id));
  const evalPath = join(workDir, 'evals.yml');
  writeFileSync(evalPath, `${JSON.stringify({ cases: questions.map((question) => ({ name: `q${question.question_id}`, question: question.question, expected: { answerable: true } })) }, null, 2)}\n`);

  const cli = resolveDqlCli();
  const projectDir = freshProject(options.arm, workDir, options.keepCache, options.sourceDb ?? undefined);
  writeProviderSettings(projectDir, options.model);
  const dataHash = createHash('sha256').update(readFileSync(SOURCE_DB)).digest('hex');
  const identity = buildIdentity({ cli, dqlVersion: dqlVersion(cli), benchmark: 'nba', condition: options.arm, provider: 'claude-code', model: options.model, cassetteMode: 'record', dataHash, tools: { claudeCli: spawnSync('claude', ['--version'], { encoding: 'utf-8' }).stdout.trim() } });
  const cassetteDir = join(workDir, 'cassettes');
  const runtime = await startRuntime(projectDir, { cli, env: RUN_ENV, cassetteMode: 'record', cassetteDir, startupTimeoutMs: 180_000 });
  let result;
  let synced = null;
  try {
    const response = await fetch(`${runtime.base}/api/connections/default/metadata-sync`, { method: 'POST' });
    synced = await response.json();
    if (!response.ok || synced.warehouseCatalog?.error) throw new Error(`Schema sync failed: ${JSON.stringify(synced).slice(0, 400)}`);
    console.error(`${options.arm} pass ${options.pass}: ${questions.length} question(s) on ${runtime.base}`);
    result = await runEval(cli, projectDir, evalPath, runtime.base, join(workDir, 'eval.stderr.log'), cassetteDir);
  } finally {
    writeFileSync(join(workDir, 'server.log'), runtime.logs());
    await runtime.close();
  }
  let report;
  try {
    report = JSON.parse(result.stdout);
  } catch {
    writeFileSync(join(workDir, 'eval.stdout.txt'), result.stdout);
    throw new Error(`zlens agent eval exited ${result.code} without a JSON report; see ${workDir}`);
  }
  const outages = providerOutages(projectDir);
  writeFileSync(join(outDir, `report${options.only ? '-resume' : ''}.json`), `${JSON.stringify({ identity, outages, metadataSync: synced, ...report }, null, 2)}\n`);
  const runs = storedRuns(projectDir);
  const steps = schemaStep(projectDir);
  const outageQuestions = new Set(outages.map((outage) => outage.question ?? outage));
  const seconds = new Map((report.results ?? []).map((item) => [item.name, Math.round((item.durationMs ?? 0) / 1000)]));
  const predictions = join(outDir, 'predictions.jsonl');
  for (const question of questions) {
    appendFileSync(predictions, `${JSON.stringify({ ...prediction(question, runs.get(question.question), outageQuestions), ...(steps.get(question.question) ?? {}), seconds: seconds.get(`q${question.question_id}`) })}\n`);
  }
  console.error(`done: ${report.results?.length ?? 0} result(s), provider outages: ${outages.length}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});

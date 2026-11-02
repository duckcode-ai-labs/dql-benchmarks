#!/usr/bin/env node
// Ask WideWorldImporters questions through ZLens's Ask on one arm's project and
// save the SQL each answer ran, for grade.py.
//
//   DQL_CLI=<zlens dist/index.js> node wwi/run.mjs --arm W0 --run <id> [--pass 1]
//        [--only 3,5] [--questions <file.json>] [--model claude-sonnet-5-5]
//
// Each pass asks on a fresh copy of the built project, the way insurance/run.mjs
// does, so nothing one pass leaves behind can reach another. The gold SQL never
// enters the project or the eval file: this script doesn't read it.

import { spawn, spawnSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { REPO_ROOT, dqlVersion, resolveDqlCli } from '../lib/dql.mjs';
import { buildIdentity } from '../lib/build-identity.mjs';
import { startRuntime } from '../lib/runtime.mjs';
import { providerOutages } from '../insurance/run.mjs';

const WORK = join(REPO_ROOT, 'work', 'wwi');
const CASE_TIMEOUT_MS = 900_000;
/** NVIDIA's arm gets this line through `shorten_answer`; its control gets it in the system prompt. */
export const PROJECTION_RULE = 'Return exactly the requested output fields and NO others.';
/** Gold SQL that doesn't run (grade.py --gold). NVIDIA's rule takes these out of the denominator. */
export const GOLD_FAILED = new Set([4, 27]);
const RUN_ENV = { DQL_EMBEDDINGS_AUTODETECT: 'off', DQL_TELEMETRY_DISABLED: '1' };

function parseArgs(argv) {
  const options = { arm: null, run: null, pass: 1, only: null, questions: null, model: 'claude-sonnet-5-5' };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--arm') options.arm = argv[++index];
    else if (arg === '--run') options.run = argv[++index];
    else if (arg === '--pass') options.pass = Number(argv[++index]);
    else if (arg === '--only') options.only = new Set(argv[++index].split(',').map(Number));
    else if (arg === '--questions') options.questions = argv[++index];
    else if (arg === '--model') options.model = argv[++index];
    else throw new Error(`Unknown option ${arg}`);
  }
  if (!options.arm || !options.run) throw new Error('--arm and --run are required.');
  return options;
}

function selectQuestions(options) {
  const file = options.questions ?? join(WORK, 'dataset', 'evaluation.json');
  return JSON.parse(readFileSync(file, 'utf-8'))
    .filter((question) => options.questions || !GOLD_FAILED.has(question.question_id))
    .filter((question) => !options.only || options.only.has(question.question_id));
}

function freshProject(arm, outDir) {
  const target = join(outDir, 'project');
  rmSync(target, { recursive: true, force: true });
  const copy = spawnSync('rsync', ['-a', '--exclude', '.dql/local', '--exclude', '.dql/cache', '--exclude', 'logs', `${join(WORK, 'projects', arm)}/`, `${target}/`], { encoding: 'utf-8' });
  if (copy.status !== 0) throw new Error(`copying the ${arm} project failed: ${copy.stderr}`);
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
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [
      cli.entry, 'agent', 'eval', relative(projectDir, evalPath),
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

/**
 * What each stored run ended with: the SQL ZLens ran, and how it got there. An
 * answer artifact can hold a draft that never ran, so SQL counts only when the
 * run's receipt says it was executed.
 */
export function storedRuns(projectDir) {
  const store = join(projectDir, '.dql', 'local', 'agent-runs.sqlite');
  if (!existsSync(store)) return new Map();
  const query = (sql) => {
    const result = spawnSync('sqlite3', ['-json', store, sql], { encoding: 'utf-8', maxBuffer: 1024 * 1024 * 1024 });
    if (result.status !== 0) throw new Error(`reading agent runs failed: ${result.stderr}`);
    return result.stdout.trim() ? JSON.parse(result.stdout) : [];
  };
  const artifacts = new Map();
  for (const row of query('select r.run_id, a.payload_json from agent_run_artifact_refs r join agent_run_artifacts a on a.fingerprint = r.fingerprint')) {
    const payload = JSON.parse(row.payload_json);
    if (payload.sql || payload.compiledSql) artifacts.set(row.run_id, payload);
  }
  const runs = new Map();
  for (const row of query('select id, question, payload_json from agent_runs order by rowid')) {
    const payload = JSON.parse(row.payload_json);
    const artifact = artifacts.get(row.id);
    const receipt = payload.diagnosticReceiptV9 ?? {};
    runs.set(row.question, {
      proposed: artifact?.sql ?? artifact?.compiledSql ?? null,
      executed: Boolean(receipt.executed),
      route: payload.route ?? null,
      trust: payload.trustState ?? null,
      status: payload.status ?? null,
      stop: payload.stopReason ?? null,
      tier: receipt.executed?.tier ?? null,
      dispatches: payload.telemetry?.providerRoundTrips ?? null,
    });
  }
  return runs;
}

function prediction(question, run, outages) {
  if (!run) return { question_id: question.question_id, sql: null, failure: 'unknown_error' };
  const sql = run.executed ? run.proposed : null;
  let failure = null;
  if (!sql) {
    if (outages.has(question.asked)) failure = 'no_model_output';
    else if (run.status === 'failed' || run.status === 'error') failure = 'unknown_error';
    else failure = 'refused';
  }
  return { question_id: question.question_id, sql, failure, ...run };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const outDir = join(REPO_ROOT, 'results', 'wwi', options.run, options.arm, `pass-${options.pass}`);
  const workDir = join(WORK, 'runs', options.run, options.arm, `pass-${options.pass}`);
  mkdirSync(outDir, { recursive: true });
  mkdirSync(workDir, { recursive: true });
  const questions = selectQuestions(options);
  const asked = questions.map((question) => ({ ...question, asked: `${question.question} ${PROJECTION_RULE}` }));
  const evalPath = join(workDir, 'evals.yml');
  writeFileSync(evalPath, `${JSON.stringify({ cases: asked.map((question) => ({ name: `q${question.question_id}`, question: question.asked, expected: { answerable: true } })) }, null, 2)}\n`);

  const cli = resolveDqlCli();
  const projectDir = freshProject(options.arm, workDir);
  writeProviderSettings(projectDir, options.model);
  const identity = buildIdentity({ cli, dqlVersion: dqlVersion(cli), benchmark: 'wwi', condition: options.arm, provider: 'claude-code', model: options.model, cassetteMode: 'record', dataHash: readFileSync(join(WORK, 'dataset', 'SOURCE_COMMIT'), 'utf-8').trim(), tools: { claudeCli: spawnSync('claude', ['--version'], { encoding: 'utf-8' }).stdout.trim() } });
  const cassetteDir = join(workDir, 'cassettes');
  const runtime = await startRuntime(projectDir, { cli, env: RUN_ENV, cassetteMode: 'record', cassetteDir, startupTimeoutMs: 180_000 });
  let result;
  try {
    const synced = await fetch(`${runtime.base}/api/connections/default/metadata-sync`, { method: 'POST' });
    const body = await synced.json();
    if (!synced.ok || body.warehouseCatalog?.error) throw new Error(`Schema sync failed: ${JSON.stringify(body).slice(0, 400)}`);
    console.error(`${options.arm} pass ${options.pass}: ${asked.length} question(s) on ${runtime.base}, ${body.warehouseCatalog?.relations} relations`);
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
  writeFileSync(join(outDir, `report${options.only ? '-resume' : ''}.json`), `${JSON.stringify({ identity, outages, ...report }, null, 2)}\n`);
  const runs = storedRuns(projectDir);
  const outageQuestions = new Set(outages.map((outage) => outage.question ?? outage));
  const seconds = new Map((report.results ?? []).map((item) => [item.name, Math.round((item.durationMs ?? 0) / 1000)]));
  const predictions = join(outDir, 'predictions.jsonl');
  for (const question of asked) {
    appendFileSync(predictions, `${JSON.stringify({ ...prediction(question, runs.get(question.asked), outageQuestions), seconds: seconds.get(`q${question.question_id}`) })}\n`);
  }
  console.error(`done: ${report.results?.length ?? 0} result(s), provider outages: ${outages.length}`);
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}

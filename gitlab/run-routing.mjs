#!/usr/bin/env node
// Simplification plan Z4: does Ask's area routing get the right table to the
// SQL writer more often than search alone, on GitLab's related areas?
//
//   DQL_CLI=<zlens dist/index.js> node gitlab/run-routing.mjs --project <dql dir> --db <duckdb>
//        --run <id> --arm on|off [--only 3,5] [--model claude-sonnet-5-5] [--questions <reworded.json>]
//
// --questions swaps in reworded question text by id (gitlab/rank/reworded-questions.json);
// the gold tables, subjects and overlap flags stay those of gitlab/routing-questions.json.
//
// The 40 questions were written blind from the table list (gitlab/routing-questions.json),
// each with the tables that answer it. GitLab's warehouse here holds the tables' shape and
// no rows, so this measures what the SQL writer is shown, not the answers: the schema step
// lists every table it showed (zlens#268). A question is a hit when its first gold table,
// or all its gold tables, were shown.

import { spawn, spawnSync } from 'node:child_process';
import { appendFileSync, chmodSync, copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { basename, join, relative } from 'node:path';
import { REPO_ROOT, resolveDqlCli } from '../lib/dql.mjs';
import { startRuntime } from '../lib/runtime.mjs';
import { providerOutages } from '../insurance/run.mjs';

const RUN_ENV = { DQL_EMBEDDINGS_AUTODETECT: 'off', DQL_TELEMETRY_DISABLED: '1' };
const QUESTIONS = join(REPO_ROOT, 'gitlab', 'routing-questions.json');

function parseArgs(argv) {
  const options = { project: null, db: null, run: null, arm: null, only: null, model: 'claude-sonnet-5-5', questions: null };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--project') options.project = argv[++index];
    else if (arg === '--db') options.db = argv[++index];
    else if (arg === '--run') options.run = argv[++index];
    else if (arg === '--arm') options.arm = argv[++index];
    else if (arg === '--only') options.only = new Set(argv[++index].split(',').map(Number));
    else if (arg === '--model') options.model = argv[++index];
    else if (arg === '--questions') options.questions = argv[++index];
    else throw new Error(`Unknown option ${arg}`);
  }
  if (!options.project || !options.db || !options.run || !['on', 'off'].includes(options.arm)) throw new Error('--project, --db, --run and --arm on|off are required.');
  return options;
}

/** A fresh copy of the dbt project and its dql folder, with this run's own database file. */
function freshProject(dqlDir, db, workDir) {
  const dbtDir = join(dqlDir, '..');
  const target = join(workDir, 'dbt');
  rmSync(target, { recursive: true, force: true });
  const copy = spawnSync('rsync', ['-a', '--exclude', 'dql/.dql/local', '--exclude', 'logs', `${dbtDir}/`, `${target}/`], { encoding: 'utf-8' });
  if (copy.status !== 0) throw new Error(`copying the project failed: ${copy.stderr}`);
  const database = join(workDir, basename(db));
  copyFileSync(db, database);
  chmodSync(database, 0o644);
  const project = join(target, basename(dqlDir));
  const configPath = join(project, 'dql.config.json');
  const config = JSON.parse(readFileSync(configPath, 'utf-8'));
  config.connections.default.filepath = database;
  writeFileSync(configPath, `${JSON.stringify(config, null, 2)}\n`);
  return project;
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
      '--via', 'runtime', '--runtime-url', runtimeBase, '--format', 'json', '--case-timeout-ms', '900000',
    ], { cwd: projectDir, env: { ...process.env, ...RUN_ENV, DQL_EVAL_CASSETTE_DIR: cassetteDir }, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; process.stderr.write(chunk); });
    child.on('error', reject);
    child.on('exit', (code) => { writeFileSync(logPath, stderr); writeFileSync(logPath.replace(/stderr\.log$/, 'stdout.json'), stdout); resolve({ code, stdout }); });
  });
}

/** The schema step of each question's first run: its title and every table it showed. */
function schemaSteps(projectDir) {
  const store = join(projectDir, '.dql', 'local', 'agent-runs.sqlite');
  const result = spawnSync('sqlite3', ['-json', store, 'select question, payload_json from agent_runs order by rowid'], { encoding: 'utf-8', maxBuffer: 1024 * 1024 * 1024 });
  const steps = new Map();
  if (result.status !== 0 || !result.stdout.trim()) return steps;
  for (const row of JSON.parse(result.stdout)) {
    if (steps.has(row.question)) continue;
    const story = JSON.parse(row.payload_json).diagnosticReceiptV9?.story ?? [];
    const schema = story.find((step) => step.phase === 'schema' && Array.isArray(step.relations));
    steps.set(row.question, { title: schema?.title ?? null, relations: schema?.relations ?? [] });
  }
  return steps;
}

const tableOf = (name) => (String(name).split('.').pop() ?? '').replace(/["`]/g, '').toLowerCase();

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.arm === 'off') process.env.ZLENS_ASK_AREA_ROUTING = 'off';
  else delete process.env.ZLENS_ASK_AREA_ROUTING;
  const outDir = join(REPO_ROOT, 'results', 'gitlab', options.run, options.arm);
  const workDir = join(REPO_ROOT, 'work', 'gitlab', 'runs', options.run, options.arm);
  rmSync(outDir, { recursive: true, force: true });
  mkdirSync(outDir, { recursive: true });
  mkdirSync(workDir, { recursive: true });
  const reworded = options.questions ? new Map(JSON.parse(readFileSync(options.questions, 'utf-8')).questions.map((item) => [item.id, item.question])) : undefined;
  const questions = JSON.parse(readFileSync(QUESTIONS, 'utf-8')).questions
    .filter((question) => !options.only || options.only.has(question.id))
    .map((question) => (reworded?.has(question.id) ? { ...question, question: reworded.get(question.id) } : question));
  const evalPath = join(workDir, 'evals.yml');
  writeFileSync(evalPath, `${JSON.stringify({ cases: questions.map((question) => ({ name: `q${question.id}`, question: question.question, expected: { answerable: true } })) }, null, 2)}\n`);

  const cli = resolveDqlCli();
  const projectDir = freshProject(options.project, options.db, workDir);
  writeProviderSettings(projectDir, options.model);
  // The gold tables by the name the warehouse knows them by (a dbt alias, if any).
  const manifest = JSON.parse(readFileSync(join(projectDir, '..', 'target', 'manifest.json'), 'utf-8'));
  const goldName = (id) => tableOf(manifest.nodes[id]?.relation_name ?? manifest.nodes[id]?.alias ?? id);
  const cassetteDir = join(workDir, 'cassettes');
  const runtime = await startRuntime(projectDir, { cli, env: RUN_ENV, cassetteMode: 'record', cassetteDir, startupTimeoutMs: 300_000 });
  let result;
  try {
    console.error(`routing ${options.arm}: ${questions.length} question(s) on ${runtime.base}`);
    result = await runEval(cli, projectDir, evalPath, runtime.base, join(workDir, 'eval.stderr.log'), cassetteDir);
  } finally {
    writeFileSync(join(workDir, 'server.log'), runtime.logs());
    await runtime.close();
  }
  const outages = providerOutages(projectDir);
  const steps = schemaSteps(projectDir);
  const shownPath = join(outDir, 'shown.jsonl');
  let primary = 0;
  let all = 0;
  for (const question of questions) {
    const ran = steps.has(question.question);
    const step = steps.get(question.question) ?? { title: null, relations: [] };
    const shown = new Set(step.relations.map(tableOf));
    const gold = question.gold.map(goldName);
    const row = { id: question.id, subject: question.subject, overlap: question.overlap, ran, title: step.title, shown: step.relations.length, gold, primaryShown: shown.has(gold[0]), allShown: gold.every((name) => shown.has(name)) };
    primary += Number(row.primaryShown);
    all += Number(row.allShown);
    appendFileSync(shownPath, `${JSON.stringify({ ...row, relations: step.relations })}\n`);
  }
  console.error(`routing ${options.arm}: first gold table shown ${primary}/${questions.length}, all gold tables shown ${all}/${questions.length}, provider outages ${outages.length}, eval exit ${result.code}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});

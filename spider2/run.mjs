#!/usr/bin/env node
// Ask Spider 2.0-Lite's SQLite questions through DQL's Ask, one database at a
// time, and keep each answer's final SQL for the official grader.
//
//   node spider2/run.mjs --condition S0|S1a|E0|E1|E2 --run <id> [--provider codex] [--model <model>] [--db <name>] [--only id,id] [--set quick] [--jobs N]
//
// --set quick runs the 22 tasks of spider2/quick-set.json (minutes, not hours);
// --jobs N answers N databases at once, each on its own runtime.
//
// Output: work/spider2/runs/<run>/<condition>/<db>/ (project copy, eval file,
// DQL report, server log, recorded AI calls) and .../predictions/<id>.sql.
// Grade with spider2/score.py, which runs the official Spider 2.0 comparison.

import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { REPO_ROOT, buildIdentity, dqlVersion, resolveDqlCli } from '../lib/dql.mjs';
import { startRuntime } from '../lib/runtime.mjs';
import { CODEX_DIRS, RUN_ENV, providerOutages } from '../insurance/run.mjs';
import { questionText, readTasks } from './tasks.mjs';
import { taskSet } from './sets.mjs';
import { forPublic } from '../lib/public.mjs';

const WORK = join(REPO_ROOT, 'work', 'spider2');
const DEFAULT_CASE_TIMEOUT_MS = 900_000;
const codexPath = () => [...CODEX_DIRS, process.env.PATH ?? ''].join(':');

function parseArgs(argv) {
  const options = { condition: 'S0', run: null, provider: 'claude-code', model: 'claude-sonnet-5', db: null, only: null, set: null, jobs: 1, caseTimeoutMs: DEFAULT_CASE_TIMEOUT_MS };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    if (arg === '--condition') options.condition = next();
    else if (arg === '--run') options.run = next();
    else if (arg === '--provider') options.provider = next();
    else if (arg === '--model') options.model = next();
    else if (arg === '--db') options.db = next();
    else if (arg === '--only') options.only = next().split(',');
    else if (arg === '--set') options.set = next();
    else if (arg === '--jobs') options.jobs = Math.max(1, Number(next()) || 1);
    else if (arg === '--case-timeout-ms') options.caseTimeoutMs = Math.max(30_000, Number(next()) || DEFAULT_CASE_TIMEOUT_MS);
    else throw new Error(`Unknown argument ${arg}`);
  }
  if (!options.run) throw new Error('--run <id> is required');
  return options;
}

function writeProviderSettings(projectDir, provider, model) {
  mkdirSync(join(projectDir, '.dql'), { recursive: true });
  writeFileSync(join(projectDir, '.dql', 'provider-settings.json'), `${JSON.stringify({ version: 1, activeProvider: provider, providers: { [provider]: { id: provider, enabled: true, model, updatedAt: new Date().toISOString() } } }, null, 2)}\n`, { mode: 0o600 });
}

function yamlString(value) {
  return JSON.stringify(value);
}

function runEval(cli, projectDir, evalPath, runtimeBase, logPath, cassetteDir, env, caseTimeoutMs) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cli.entry, 'agent', 'eval', relative(projectDir, evalPath), '--via', 'runtime', '--runtime-url', runtimeBase, '--format', 'json', '--case-timeout-ms', String(caseTimeoutMs)], {
      cwd: projectDir,
      env: { ...process.env, ...env, DQL_EVAL_CASSETTE_DIR: cassetteDir },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('exit', (code) => { writeFileSync(logPath, stderr); resolve({ code, stdout }); });
  });
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const cli = resolveDqlCli();
  const { tasks, missingDatabases } = readTasks();
  const inSet = taskSet(options.set);
  const selected = tasks.filter((task) => (!options.db || task.db === options.db) && (!options.only || options.only.includes(task.id)) && (!inSet || inSet.has(task.id)));
  const runDir = join(WORK, 'runs', options.run, options.condition);
  mkdirSync(join(runDir, 'predictions'), { recursive: true });
  const env = {
    ...RUN_ENV,
    ...(options.provider === 'codex' ? { PATH: codexPath() } : {}),
  };
  const byDb = new Map();
  for (const task of selected) byDb.set(task.db, [...(byDb.get(task.db) ?? []), task]);
  // The code behind the number: commit, uncommitted edits (saved as a patch),
  // and the DQL_* switches the run sets. A dist older than its source is
  // refused, because it would run code the identity does not describe.
  const { patch, ...build } = buildIdentity(cli, { env: { ...process.env, ...env } });
  if (build.distOlderThanSource && !process.env.SPIDER2_ALLOW_STALE_DIST) throw new Error(`${cli.entry} was built before the latest source edit in ${build.root}; rebuild DQL first (or set SPIDER2_ALLOW_STALE_DIST=1 to record it as stale).`);
  // The projects must come from the same code: S1a's drafted model is DQL's
  // output too, and a run over projects built by another build measures two.
  const projectsRecordPath = join(WORK, `build-${options.condition}.json`);
  const projects = existsSync(projectsRecordPath) ? JSON.parse(readFileSync(projectsRecordPath, 'utf-8')) : null;
  const projectsBuild = projects?.dql?.build ?? null;
  const sameCode = (a, b) => Boolean(a && b && a.head === b.head && (a.patchSha256 ?? null) === (b.patchSha256 ?? null));
  if (!sameCode(projectsBuild, build) && !process.env.SPIDER2_ALLOW_MIXED_BUILD) throw new Error(`the ${options.condition} projects were built ${projectsBuild ? `on ${projectsBuild.head?.slice(0, 8)}${projectsBuild.dirty ? ` + patch ${projectsBuild.patchSha256?.slice(0, 8)}` : ''}` : 'by an unrecorded build'}, not this build (${build.head?.slice(0, 8)}${build.dirty ? ` + patch ${build.patchSha256?.slice(0, 8)}` : ''}). Rebuild: node spider2/build.mjs --condition ${options.condition} (or set SPIDER2_ALLOW_MIXED_BUILD=1 to record it as mixed).`);
  const buildPath = join(runDir, 'build.json');
  if (existsSync(buildPath)) {
    // A resumed run must be the same build, or its databases mix two codes.
    const before = JSON.parse(readFileSync(buildPath, 'utf-8'));
    if (before.head !== build.head || before.patchSha256 !== build.patchSha256) throw new Error(`run ${options.run}/${options.condition} was started on ${before.head?.slice(0, 8)}${before.dirty ? ` + patch ${before.patchSha256?.slice(0, 8)}` : ''}; this build is ${build.head?.slice(0, 8)}${build.dirty ? ` + patch ${build.patchSha256?.slice(0, 8)}` : ''}. Use a new --run id.`);
  } else {
    writeFileSync(buildPath, `${JSON.stringify(build, null, 2)}\n`);
    if (patch && build.dirty) writeFileSync(join(runDir, 'build.patch'), patch);
  }
  const summary = { run: options.run, condition: options.condition, provider: options.provider, model: options.model, dql: { version: dqlVersion(cli), source: cli.source, entry: cli.entry, build }, projects: { builtAt: projects?.builtAt ?? null, build: projectsBuild, sameBuild: sameCode(projectsBuild, build) }, set: options.set ?? 'full', caseTimeoutMs: options.caseTimeoutMs, startedAt: new Date().toISOString(), missingDatabases, tasks: selected.length, databases: {}, invalid: [] };
  const retried = new Set();
  const queue = [...byDb.entries()].sort(([a], [b]) => a.localeCompare(b));
  // One database per worker at a time; a worker takes the next from the queue.
  let stopped = false;
  const worker = async () => { while (queue.length && !stopped) {
    const [db, dbTasks] = queue.shift();
    const built = join(WORK, 'projects', options.condition, db);
    if (!existsSync(join(built, 'dql.config.json'))) throw new Error(`Build ${options.condition}/${db} first: node spider2/build.mjs --condition ${options.condition}`);
    const outDir = join(runDir, db);
    if (existsSync(join(outDir, 'report.json'))) {
      // A database answered by an earlier invocation of this run still belongs
      // in the summary: a run resumed database by database was otherwise
      // scored on the last invocation's databases alone.
      const done = JSON.parse(readFileSync(join(outDir, 'report.json'), 'utf-8'));
      const answeredBefore = [];
      for (const item of done.results ?? []) {
        const sql = item.answer?.sql;
        if (typeof sql !== 'string' || !sql.trim()) continue;
        writeFileSync(join(runDir, 'predictions', `${item.name}.sql`), `${sql.trim()}\n`);
        answeredBefore.push(item.name);
      }
      summary.databases[db] = { tasks: dbTasks.map((task) => task.id), answered: answeredBefore, outcomes: Object.fromEntries((done.results ?? []).map((item) => [item.name, { trust: item.answer?.trustState ?? null, route: item.route, durationMs: item.durationMs }])), resumed: true };
      console.error(`${db}: already done, kept ${answeredBefore.length}/${dbTasks.length}`);
      continue;
    }
    rmSync(outDir, { recursive: true, force: true });
    mkdirSync(outDir, { recursive: true });
    const projectDir = join(outDir, 'project');
    const copy = spawnSync('rsync', ['-a', '--exclude', '.dql/local', '--exclude', '.dql/cache', `${built}/`, `${projectDir}/`], { encoding: 'utf-8' });
    if (copy.status !== 0) throw new Error(`copying ${db} failed: ${copy.stderr}`);
    writeProviderSettings(projectDir, options.provider, options.model);
    const evalPath = join(outDir, 'evals.yml');
    writeFileSync(evalPath, `cases:\n${dbTasks.map((task) => `  - name: ${yamlString(task.id)}\n    question: ${yamlString(questionText(task))}\n    expected:\n      answerable: true\n`).join('')}`);
    const runtime = await startRuntime(projectDir, { cli, env, cassetteMode: 'record', cassetteDir: join(outDir, 'cassettes'), startupTimeoutMs: 180_000 });
    let result;
    let runtimeAlive = true;
    let runtimeEnded = null;
    try {
      // Ask's schema index lives in .dql/cache, which the copy leaves out.
      const synced = await fetch(`${runtime.base}/api/connections/default/metadata-sync`, { method: 'POST' });
      if (!synced.ok) throw new Error(`${db}: schema sync failed: ${(await synced.text()).slice(0, 300)}`);
      console.error(`${options.condition}/${db}: ${dbTasks.length} question(s)`);
      result = await runEval(cli, projectDir, evalPath, runtime.base, join(outDir, 'eval.stderr.log'), join(outDir, 'cassettes'), env, options.caseTimeoutMs);
    } finally {
      runtimeAlive = runtime.alive?.() ?? true;
      runtimeEnded = runtime.ended?.() ?? null;
      writeFileSync(join(outDir, 'server.log'), forPublic(runtime.logs()));
      await runtime.close();
    }
    // A dead runtime is not an answer. Its cases say "fetch failed"; they are
    // recorded as invalid and the database is run again once, rather than
    // counted as questions DQL declined.
    const brokenRuntime = !runtimeAlive || /fetch failed|ECONNREFUSED|socket hang up/.test(result.stdout);
    if (brokenRuntime && !retried.has(db)) {
      retried.add(db);
      rmSync(outDir, { recursive: true, force: true });
      console.error(`${db}: the runtime died mid-run (${runtimeEnded ? `code=${runtimeEnded.code} signal=${runtimeEnded.signal}` : 'no exit recorded'}); running it again`);
      queue.push([db, dbTasks]);
      continue;
    }
    const outages = providerOutages(projectDir);
    let report;
    try { report = JSON.parse(result.stdout); } catch { throw new Error(`${db}: DQL returned no JSON report (exit ${result.code}); see ${relative(REPO_ROOT, join(outDir, 'eval.stderr.log'))}`); }
    writeFileSync(join(outDir, 'report.json'), forPublic(`${JSON.stringify(report, null, 2)}\n`));
    const answered = [];
    for (const item of report.results ?? []) {
      const sql = item.answer?.sql;
      if (typeof sql === 'string' && sql.trim()) {
        writeFileSync(join(runDir, 'predictions', `${item.name}.sql`), `${sql.trim()}\n`);
        answered.push(item.name);
      }
    }
    summary.databases[db] = { tasks: dbTasks.map((task) => task.id), answered, outcomes: Object.fromEntries((report.results ?? []).map((item) => [item.name, { trust: item.answer?.trustState ?? null, route: item.route, durationMs: item.durationMs }])) };
    if (outages.length) {
      summary.invalid.push({ db, outages });
      console.error(`INVALID RUN: the provider refused calls on ${db}: ${outages[0]}`);
      writeFileSync(join(runDir, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
      process.exitCode = 3;
      stopped = true;
      return;
    }
    console.error(`${options.condition}/${db}: ${answered.length}/${dbTasks.length} returned SQL`);
  } };
  // Workers start two seconds apart: each takes a free port for its runtime,
  // and two asking at the same instant could be handed the same one.
  await Promise.all(Array.from({ length: Math.min(options.jobs, queue.length) || 1 }, (_, index) => new Promise((done) => setTimeout(done, index * 2_000)).then(worker)));
  if (stopped) return;
  summary.finishedAt = new Date().toISOString();
  writeFileSync(join(runDir, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
  console.log(`${options.condition}: ${Object.values(summary.databases).reduce((n, item) => n + item.answered.length, 0)}/${selected.length} returned SQL → ${relative(REPO_ROOT, runDir)}`);
}

main().catch((error) => { console.error(error.message); process.exitCode = 1; });

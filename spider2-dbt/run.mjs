#!/usr/bin/env node
// Run the DQL dbt-task agent on Spider 2.0-DBT tasks and score the result with
// the publisher's grader.
//
//   node spider2-dbt/run.mjs --run <run-id> --condition bare
//     [--tasks a001,b002 | --all] [--cassette record|replay|live]
//     [--model claude-sonnet-5] [--provider claude-code]
//     [--scored]   exclude development tasks and refuse to run them
//     [--resume]   keep tasks this run already finished
//
// Every graded task is listed in the submission; tasks not run in this
// invocation are listed without a database and score 0, so the reported
// accuracy is always over all 68.

import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { buildIdentity } from '../lib/build-identity.mjs';
import { REPO_ROOT, dqlVersion, resolveDqlCli } from '../lib/dql.mjs';
import { importTask, taskMetaDir, taskWorkDir } from './import-task.mjs';
import { precheck } from './precheck.mjs';
import { writeSubmission } from './submission.mjs';
import { readManifest } from './tasks.mjs';

const CONDITIONS = new Set(['bare']);
const DEV_TASKS_PATH = join(REPO_ROOT, 'spider2-dbt', 'dev-tasks.json');

function readDevTasks() {
  const file = JSON.parse(readFileSync(DEV_TASKS_PATH, 'utf-8'));
  return new Set(file.tasks.map((entry) => entry.instanceId));
}
const DBT_BIN = join(REPO_ROOT, '.venv', 'bin', 'dbt');
const PROVIDER_WORKSPACE = join(REPO_ROOT, '.provider-workspace');

function parseArgs(argv) {
  const options = { run: null, condition: 'bare', tasks: null, all: false, scored: false, resume: false, cassette: 'record', model: 'claude-sonnet-5', provider: 'claude-code' };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    if (arg === '--run') options.run = next();
    else if (arg === '--condition') options.condition = next();
    else if (arg === '--tasks') options.tasks = next().split(',').map((id) => id.trim()).filter(Boolean);
    else if (arg === '--all') options.all = true;
    else if (arg === '--scored') options.scored = true;
    else if (arg === '--resume') options.resume = true;
    else if (arg === '--cassette') options.cassette = next();
    else if (arg === '--model') options.model = next();
    else if (arg === '--provider') options.provider = next();
    else throw new Error(`Unknown option ${arg}`);
  }
  if (!options.run || !/^[\w.-]+$/.test(options.run)) throw new Error('--run <run-id> is required (letters, digits, . _ -).');
  if (!CONDITIONS.has(options.condition)) throw new Error(`--condition must be one of ${[...CONDITIONS].join(', ')}.`);
  if (!['record', 'replay', 'live'].includes(options.cassette)) throw new Error('--cassette must be record, replay or live.');
  if (!options.all && !options.tasks?.length) throw new Error('Choose --tasks a,b or --all.');
  return options;
}

function runAgent(cli, runFile) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [cli.entry, 'agent', 'dbt-task', runFile], {
      env: { ...process.env, DQL_TELEMETRY_DISABLED: '1' },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}

/** e.g. { dbt: '1.12.5', 'dbt-duckdb': '1.11.0' } from `dbt --version`. */
function dbtVersions() {
  const result = spawnSync(DBT_BIN, ['--version'], { encoding: 'utf-8', timeout: 60_000 });
  const text = `${result.stdout ?? ''}`;
  const core = text.match(/installed:\s*([\d.]+)/)?.[1] ?? null;
  const duckdb = text.match(/duckdb:\s*([\d.]+)/)?.[1] ?? null;
  return { dbt: core, 'dbt-duckdb': duckdb };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const manifest = readManifest();
  const cli = resolveDqlCli();
  const version = dqlVersion(cli);
  const graded = new Map(manifest.tasks.map((task) => [task.instanceId, task]));
  const selected = options.all
    ? manifest.tasks
      .filter((task) => task.startingDatabasePresent)
      .filter((task) => !options.scored || !readDevTasks().has(task.instanceId))
      .map((task) => task.instanceId)
    : options.tasks;
  for (const id of selected) if (!graded.has(id)) throw new Error(`${id} is not a graded task.`);
  // Tasks used while building the harness are never part of a scored run.
  const devTasks = readDevTasks();
  const devSelected = selected.filter((id) => devTasks.has(id));
  if (options.scored && devSelected.length) {
    throw new Error(`A scored run cannot include development tasks: ${devSelected.join(', ')}.`);
  }
  mkdirSync(PROVIDER_WORKSPACE, { recursive: true });

  const runDir = join(REPO_ROOT, 'work', 'spider2-dbt', 'runs', options.run);
  const cassetteRoot = join(REPO_ROOT, 'spider2-dbt', 'cassettes', options.run);
  const results = new Map();

  for (const [position, id] of selected.entries()) {
    const task = graded.get(id);
    process.stdout.write(`[${position + 1}/${selected.length}] ${id} … `);
    // A long run that stopped part-way keeps the tasks it finished.
    const earlier = join(taskMetaDir(options.run, id), 'result.json');
    if (options.resume && existsSync(earlier)) {
      const result = JSON.parse(readFileSync(earlier, 'utf-8'));
      results.set(id, result);
      console.log(`already run (${result.stop})`);
      continue;
    }
    const imported = importTask(id, { runId: options.run, cli });
    // A starting project that does not parse is still attempted: making it
    // build is often the task. Only a failed `dql init` stops a task.
    if (imported.dqlInit.code !== 0) {
      results.set(id, { error: 'dql init failed', import: imported });
      console.log('dql init failed');
      continue;
    }
    if (imported.dbtParse.code !== 0) process.stdout.write('(starting project does not parse) ');
    const meta = taskMetaDir(options.run, id);
    const runFile = join(meta, 'run.json');
    writeFileSync(runFile, `${JSON.stringify({
      version: 1,
      instanceId: id,
      taskDir: imported.dir,
      instructionFile: imported.instructionFile,
      database: task.database,
      hiddenPaths: imported.addedByDqlInit,
      dbtBin: DBT_BIN,
      provider: { id: options.provider, model: options.model, settingsProject: PROVIDER_WORKSPACE },
      cassette: { mode: options.cassette, dir: join(cassetteRoot, id) },
      trajectoryPath: join(meta, 'trajectory.jsonl'),
      outputPath: join(meta, 'result.json'),
    }, null, 2)}\n`);
    const started = Date.now();
    const run = await runAgent(cli, runFile);
    const resultPath = join(meta, 'result.json');
    const result = existsSync(resultPath) ? JSON.parse(readFileSync(resultPath, 'utf-8')) : null;
    if (!result) {
      writeFileSync(join(meta, 'agent-stderr.txt'), run.stderr);
      results.set(id, { error: `agent exited ${run.code} without a result`, wallMs: Date.now() - started });
      console.log(`no result (exit ${run.code}; see ${join(meta, 'agent-stderr.txt')})`);
      continue;
    }
    result.startingProjectParses = imported.dbtParse.code === 0;
    results.set(id, result);
    console.log(`${result.stop}, ${result.toolCalls} tool calls, ${result.providerDispatches} AI calls, `
      + `${Math.round(result.wallMs / 1000)} s, final dbt run exit ${result.finalDbtRun.exitCode}`);
  }

  const submissionDir = join(runDir, 'submission');
  writeSubmission(submissionDir, manifest.tasks, (task) => (
    results.has(task.instanceId) && !results.get(task.instanceId).error
      ? join(taskWorkDir(options.run, task.instanceId), task.database)
      : null
  ));
  const scored = precheck(submissionDir);

  const ran = [...results.values()];
  const allRecorded = options.cassette !== 'live'
    && ran.length > 0
    && ran.every((result) => result.cassette?.evidence?.realProviderQualityEligible === true);
  const identity = buildIdentity({
    cli,
    dqlVersion: version,
    benchmark: 'spider2-dbt',
    condition: options.condition,
    provider: options.provider,
    model: options.model,
    cassetteMode: options.cassette,
    dataHash: manifest.upstreamCommit,
    tools: dbtVersions(),
  });
  const report = {
    identity,
    scored: options.scored,
    developmentTasks: [...devTasks].sort(),
    provenance: {
      realProviderQualityEligible: allRecorded,
      tasksRun: selected.length,
      tasksWithResult: ran.filter((result) => !result.error).length,
    },
    score: {
      passed: scored.passed,
      graded: scored.graded,
      accuracy: scored.accuracy,
      ci95: scored.ci95,
      passedWithGold: scored.passedWithGold,
      gradedWithGold: scored.gradedWithGold,
    },
    cases: scored.cases.map(({ caseId, passed }) => {
      const result = results.get(caseId);
      return {
        caseId,
        passed,
        ran: Boolean(result),
        ...(result && !result.error ? {
          startingProjectParses: result.startingProjectParses ?? null,
          stop: result.stop,
          terminated: result.terminated,
          budgetTripped: result.budgetTripped,
          durationMs: result.wallMs,
          dispatches: result.providerDispatches,
          toolCalls: result.toolCalls,
          dbtRuns: result.dbtRuns,
          finalDbtExit: result.finalDbtRun.exitCode,
          filesWritten: result.filesWritten.length,
        } : {}),
        ...(result?.error ? { error: result.error } : {}),
      };
    }),
  };
  const reportDir = join(REPO_ROOT, 'spider2-dbt', 'reports');
  mkdirSync(reportDir, { recursive: true });
  const reportPath = join(reportDir, `${options.run}.json`);
  writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);

  const pct = (value) => `${(value * 100).toFixed(1)}%`;
  const passedRun = report.cases.filter((entry) => entry.ran && entry.passed).map((entry) => entry.caseId);
  console.log(`\nRan ${selected.length} task(s); passed among them: ${passedRun.join(', ') || 'none'}.`);
  console.log(`Score over all ${scored.graded}: ${scored.passed} = ${pct(scored.accuracy)}; `
    + `${scored.passedWithGold}/${scored.gradedWithGold} with published gold.`);
  console.log(`Report: ${reportPath}${identity.publishable ? '' : ` (not publishable: ${identity.notPublishableBecause.join('; ')})`}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});

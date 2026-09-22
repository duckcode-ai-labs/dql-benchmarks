#!/usr/bin/env node
// Ask every insurance question through DQL's Ask on one layer's project and
// score the answers against the correct rows.
//
//   node insurance/run.mjs --layer L0 --set dbt-labs --run <run-id>
//        [--cassette record|replay] [--provider claude-code] [--model claude-sonnet-5]
//
// Sets: `all` (the 43 questions), `dbt-labs` (dbt Labs' 11), `dev` (declared
// development questions), `unanswerable`, and the sealed `heldout` and
// `heldout-unanswerable` sets (insurance/heldout.mjs). Development questions
// are left out of `all` and `dbt-labs` so headline numbers never include a
// question we looked at while building the harness.
//
// Everything a run produces goes to work/insurance/runs/<run-id>/<layer>/<set>/:
// the eval file, DQL's JSON report, the recorded AI calls and the server log.

import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { REPO_ROOT, dqlVersion, resolveDqlCli } from '../lib/dql.mjs';
import { buildIdentity } from '../lib/build-identity.mjs';
import { loadAudit, unauditedCases } from '../lib/gold-audit.mjs';
import { startRuntime } from '../lib/runtime.mjs';
import { caseId } from './questions.mjs';
import { attributeUsage, loadPricing, readLedger, runSpans } from '../lib/usage.mjs';
import { heldoutPaths, heldoutSetOf, heldoutUnanswerableCases } from './heldout.mjs';

const WORK = join(REPO_ROOT, 'work', 'insurance');
const SETS = ['all', 'dbt-labs', 'dev', 'unanswerable'];
const stopsAreRight = (set) => set.endsWith('unanswerable');
/** claude-code: the `claude` command's subscription login. anthropic: the Messages API with ANTHROPIC_API_KEY. */
const PROVIDERS = ['claude-code', 'anthropic', 'codex', 'ollama'];
/**
 * Where the Codex command lives when it is not on PATH: the ChatGPT desktop app
 * bundles it. Prepended to PATH for codex runs only.
 */
export const CODEX_DIRS = ['/Applications/ChatGPT.app/Contents/Resources'];
const codexPath = () => [...CODEX_DIRS, process.env.PATH ?? ''].join(':');
/** How long one question may take before the harness records it as unanswered. Ask's own limits apply first. */
const CASE_TIMEOUT_MS = 900_000;

/**
 * Settings pinned for every run and recorded in its report.
 * DQL switches to local Ollama embeddings on its own when a machine serves
 * them, in the background after the server starts; that would make results
 * depend on the machine and on timing. Scored runs use DQL's built-in
 * retrieval, which is what a machine without Ollama gets.
 */
export const RUN_ENV = {
  DQL_EMBEDDINGS_AUTODETECT: 'off',
  DQL_TELEMETRY_DISABLED: '1',
  // DQL runs the first `mf` it finds; the machine's own may lack the DuckDB
  // adapter (it did on the first L2 run, and every semantic compile failed).
  DQL_METRICFLOW_BIN: join(REPO_ROOT, '.venv-mf', 'bin', 'mf'),
};

/**
 * A local model is measured for accuracy, not speed: its runs get DQL's
 * largest deadline (20 × the Ask budget) so a slow machine does not turn a
 * reading into a stop. Recorded in the report's settings.
 */
function LOCAL_ENV(provider) {
  return provider === 'ollama' ? { DQL_AGENT_DEADLINE_SCALE: '20' } : {};
}

function codexEffort() {
  try {
    const text = readFileSync(join(process.env.HOME ?? '', '.codex', 'config.toml'), 'utf-8');
    return `model_reasoning_effort=${/^model_reasoning_effort\s*=\s*"?([a-z]+)/m.exec(text)?.[1] ?? 'unset'} (~/.codex/config.toml)`;
  } catch { return 'model_reasoning_effort unknown'; }
}

function parseArgs(argv) {
  const options = { layer: 'L0', set: 'dbt-labs', run: null, cassette: 'record', provider: 'claude-code', model: 'claude-sonnet-5', only: null, debugCli: false, readingEffort: null };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    if (arg === '--layer') options.layer = next();
    else if (arg === '--set') options.set = next();
    else if (arg === '--run') options.run = next();
    else if (arg === '--cassette') options.cassette = next();
    else if (arg === '--provider') options.provider = next();
    else if (arg === '--model') options.model = next();
    else if (arg === '--only') options.only = next().split(',');
    else if (arg === '--debug-cli') options.debugCli = true;
    else if (arg === '--reading-effort') options.readingEffort = next();
    else throw new Error(`Unknown argument ${arg}`);
  }
  if (!options.run) throw new Error('--run <run-id> is required');
  if (!SETS.includes(options.set) && !heldoutSetOf(options.set)) throw new Error(`--set must be one of ${SETS.join(', ')}, heldout[-N][-unanswerable]`);
  if (!['record', 'replay'].includes(options.cassette)) throw new Error('--cassette must be record or replay');
  if (!PROVIDERS.includes(options.provider)) throw new Error(`--provider must be one of ${PROVIDERS.join(', ')}`);
  // The API key comes from the environment of whoever runs the harness. It is
  // never written to the project, the report or a log.
  if (options.provider === 'anthropic' && options.cassette === 'record' && !process.env.ANTHROPIC_API_KEY) throw new Error('--provider anthropic needs ANTHROPIC_API_KEY in the environment');
  return options;
}

/** Which questions a set asks, after the audit and dev-question rules. */
export function selectCases(gold, audit, devIds, set) {
  const unaudited = unauditedCases(gold.cases.map((c) => c.id), audit);
  if (unaudited.length) throw new Error(`Questions without an answer-key audit line: ${unaudited.join(', ')}`);
  const broken = gold.cases.filter((c) => c.gold.error);
  if (broken.length) throw new Error(`Correct answers that did not run: ${broken.map((c) => c.id).join(', ')}`);
  if (set === 'dev') return gold.cases.filter((c) => devIds.has(c.id));
  const headline = gold.cases.filter((c) => !devIds.has(c.id));
  return set === 'dbt-labs' ? headline.filter((c) => c.dbtLabsSelected) : headline;
}

/**
 * Questions this data cannot answer (insurance/unanswerable.json, written from
 * the schema by the layer author). Stopping, by declining or asking back, is
 * the right outcome; answering is the failure.
 */
export function unanswerableCases(file = join(REPO_ROOT, 'insurance', 'unanswerable.json')) {
  const { questions } = JSON.parse(readFileSync(file, 'utf-8'));
  return questions.map((entry) => ({ id: `unanswerable-${caseId(entry.question)}`, question: entry.question, why: entry.why, unanswerable: true }));
}

/**
 * Questions whose run stopped because the AI provider refused the call (a
 * usage limit, a rate limit, an expired login). Those are not DQL's answers:
 * the run is marked invalid and scored nowhere, instead of counting as wrong
 * answers or as correct stops.
 */
export function providerOutages(projectDir) {
  const store = join(projectDir, '.dql', 'local', 'agent-runs.sqlite');
  if (!existsSync(store)) return [];
  const result = spawnSync('sqlite3', ['-json', store, "select question, payload_json from agent_runs where payload_json like '%limit%' or payload_json like '%quota%' or payload_json like '%not logged in%'"], { encoding: 'utf-8', maxBuffer: 512 * 1024 * 1024 });
  if (result.status !== 0) throw new Error(`could not read the run store: ${result.stderr}`);
  const rows = result.stdout.trim() ? JSON.parse(result.stdout) : [];
  // A refusal is the provider's message, never a word the question used
  // ("…the sales quota for each year" is a question, not an outage).
  const REFUSAL = /(usage limit[^".]*|rate limit[^".]*|exceeded your (?:current )?quota[^".]*|quota exceeded[^".]*|insufficient_quota[^".]*|not logged in[^".]*)/i;
  return rows.flatMap((row) => {
    const text = String(row.payload_json ?? '').split(String(row.question ?? '')).join(' ');
    const found = REFUSAL.exec(text);
    return found ? [found[1]] : [];
  });
}

/** The eval file DQL reads. The correct rows sit here, outside the project. */
export function evalFile(cases) {
  return {
    cases: cases.map((c) => c.unanswerable ? {
      name: c.id,
      question: c.question,
      expected: { answerable: false },
    } : ({
      name: c.id,
      question: c.question,
      expected: {
        answerable: true,
        goldRows: c.gold.rows,
        goldSql: c.gold.ranSql ?? c.goldSql,
        // dbt Labs' grader lets an answer carry extra columns; so does ours.
        goldAllowExtraColumns: true,
        goldOrdered: false,
      },
    })),
  };
}

/**
 * Select the AI provider for this project. A subscription provider needs no
 * key: it uses the `claude` (or `codex`) command's own login. Written into the
 * project's own settings file, never copied from a user workspace.
 */
function writeProviderSettings(projectDir, provider, model) {
  const path = join(projectDir, '.dql', 'provider-settings.json');
  mkdirSync(join(projectDir, '.dql'), { recursive: true });
  writeFileSync(path, `${JSON.stringify({
    version: 1,
    activeProvider: provider,
    providers: { [provider]: { id: provider, enabled: true, model, updatedAt: new Date().toISOString() } },
  }, null, 2)}\n`, { mode: 0o600 });
}

/**
 * Each run asks its questions on a fresh copy of the built project, so nothing
 * one run leaves in DQL's local state (run history, memory, caches) can reach
 * another run. The built project itself is never served.
 */
function freshProject(layer, outDir) {
  const source = join(WORK, 'projects', layer);
  const target = join(outDir, 'project');
  rmSync(target, { recursive: true, force: true });
  const copy = spawnSync('rsync', ['-a', '--exclude', '.dql/local', '--exclude', '.dql/cache', '--exclude', 'logs', `${source}/`, `${target}/`], { encoding: 'utf-8' });
  if (copy.status !== 0) throw new Error(`copying the ${layer} project failed: ${copy.stderr}`);
  // The dbt profile names the database by absolute path; point it at the copy.
  // A warehouse layer (no dbt) has no profile: its connection path is relative.
  const profile = join(target, 'profiles.yml');
  if (existsSync(profile)) writeFileSync(profile, readFileSync(profile, 'utf-8').split(source).join(target));
  return target;
}

function runEval(cli, projectDir, evalPath, runtimeBase, logPath, cassetteDir) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [
      cli.entry, 'agent', 'eval', relative(projectDir, evalPath),
      '--via', 'runtime', '--runtime-url', runtimeBase, '--format', 'json',
      '--case-timeout-ms', String(CASE_TIMEOUT_MS),
    ], {
      cwd: projectDir,
      // The CLI reads the server's cassette folder to report provenance.
      env: { ...process.env, ...RUN_ENV, DQL_EVAL_CASSETTE_DIR: cassetteDir },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; process.stderr.write(chunk); });
    child.on('error', reject);
    child.on('exit', (code) => {
      writeFileSync(logPath, stderr);
      resolve({ code, stdout, stderr });
    });
  });
}

/**
 * The server records AI calls itself, so the CLI report carries no evidence
 * about them. Every recording must come from a real provider for a run to count.
 */
export function cassetteEvidence(dir, mode) {
  const files = existsSync(dir) ? readdirSync(dir).filter((name) => name.endsWith('.json')) : [];
  const kinds = {};
  let ineligible = 0;
  for (const name of files) {
    const provenance = JSON.parse(readFileSync(join(dir, name), 'utf-8')).provenance ?? {};
    kinds[provenance.kind ?? 'unknown'] = (kinds[provenance.kind ?? 'unknown'] ?? 0) + 1;
    if (provenance.kind !== 'recorded_provider' || provenance.providerQuality !== 'eligible') ineligible += 1;
  }
  const reasons = [
    ...(files.length === 0 ? ['no recorded AI calls'] : []),
    ...(ineligible ? [`${ineligible} recording(s) are not from a real provider`] : []),
  ];
  return { source: 'harness scan of the server cassette folder', mode, recordings: files.length, kinds, realProviderQualityEligible: reasons.length === 0, reasons };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (!existsSync(RUN_ENV.DQL_METRICFLOW_BIN)) throw new Error('MetricFlow for the benchmark is not installed. Run: ./scripts/setup-python.sh');
  const builtDir = join(WORK, 'projects', options.layer);
  if (!existsSync(join(builtDir, 'dql.config.json'))) throw new Error(`Build the ${options.layer} project first: node insurance/build.mjs --layer ${options.layer}`);
  const gold = JSON.parse(readFileSync(join(WORK, 'gold', 'answers.json'), 'utf-8'));
  const audit = loadAudit(join(REPO_ROOT, 'insurance', 'gold-audit.jsonl'));
  if (audit.problems.length) throw new Error(audit.problems.join('\n'));
  const dev = JSON.parse(readFileSync(join(REPO_ROOT, 'insurance', 'dev-questions.json'), 'utf-8'));
  const devIds = new Set(dev.questions.map((q) => q.caseId));
  let cases;
  const heldout = heldoutSetOf(options.set);
  if (options.set === 'unanswerable') cases = unanswerableCases();
  else if (heldout?.unanswerable) cases = heldoutUnanswerableCases(heldoutPaths(heldout.number).file);
  else if (heldout) {
    const { gold: goldFile } = heldoutPaths(heldout.number);
    if (!existsSync(goldFile)) throw new Error(`Compute the held-out answers first: node insurance/heldout.mjs --number ${heldout.number} gold`);
    cases = JSON.parse(readFileSync(goldFile, 'utf-8')).cases;
    const broken = cases.filter((c) => c.gold.error || c.gold.rowCount === 0);
    if (broken.length) throw new Error(`${broken.length} held-out correct answers did not run or returned no rows`);
  } else cases = selectCases(gold, audit, devIds, options.set);
  if (options.only) cases = cases.filter((c) => options.only.includes(c.id));
  if (cases.length === 0) throw new Error('No questions selected.');

  const outDir = join(WORK, 'runs', options.run, options.layer, options.set);
  if (options.cassette === 'record' && existsSync(join(outDir, 'report.json'))) {
    throw new Error(`Run ${options.run} already has ${options.layer}/${options.set}; pick a new run id or replay it.`);
  }
  // A recording run starts with no recordings. An interrupted attempt leaves
  // some behind, and recording reuses any it finds: those answers would take
  // no AI call and report a few seconds, and their speed would be false.
  const cassetteDir = join(outDir, 'cassettes');
  if (options.cassette === 'record' && existsSync(cassetteDir) && readdirSync(cassetteDir).length > 0) {
    throw new Error(`${relative(REPO_ROOT, cassetteDir)} already holds recordings from an earlier attempt; delete ${relative(REPO_ROOT, outDir)} or pick a new run id.`);
  }
  mkdirSync(outDir, { recursive: true });
  const projectDir = freshProject(options.layer, outDir);
  const evalPath = join(outDir, 'evals.yml');
  // JSON is valid YAML, so no YAML library is needed.
  writeFileSync(evalPath, `${JSON.stringify(evalFile(cases), null, 2)}\n`);

  const cli = resolveDqlCli();
  const version = dqlVersion(cli);
  const build = JSON.parse(readFileSync(join(WORK, `build-${options.layer}.json`), 'utf-8'));
  const identity = buildIdentity({
    cli,
    dqlVersion: version,
    benchmark: 'insurance',
    condition: options.layer,
    provider: options.provider,
    model: options.model,
    cassetteMode: options.cassette,
    dataHash: build.source.seedHash,
    tools: {
      dbt: build.tools.dbt.join('; '),
      duckdbPython: build.tools.duckdbPython,
      source: build.source.commit,
      metricflow: spawnSync(RUN_ENV.DQL_METRICFLOW_BIN, ['--version'], { encoding: 'utf-8' }).stdout.trim(),
      claudeCli: options.provider === 'claude-code' ? spawnSync('claude', ['--version'], { encoding: 'utf-8' }).stdout.trim() : null,
      // Codex takes its reasoning effort from ~/.codex/config.toml; DQL passes none.
      codexCli: options.provider === 'codex' ? `${spawnSync('codex', ['--version'], { encoding: 'utf-8', env: { ...process.env, PATH: codexPath() } }).stdout.trim()}; ${codexEffort()}` : null,
    },
  });
  identity.settings = { ...RUN_ENV, ...LOCAL_ENV(options.provider), caseTimeoutMs: CASE_TIMEOUT_MS, debugCli: options.debugCli, readingEffort: options.readingEffort ?? 'default (route effort)' };

  writeProviderSettings(projectDir, options.provider, options.model);
  const runtime = await startRuntime(projectDir, {
    cli,
    env: { ...RUN_ENV, ...(options.provider === 'codex' ? { PATH: codexPath() } : {}), ...LOCAL_ENV(options.provider), DQL_PROVIDER_USAGE_LEDGER: join(outDir, 'usage.jsonl'), ...(options.readingEffort ? { DQL_ASK_READING_EFFORT: options.readingEffort } : {}), ...(options.debugCli ? { DQL_DEBUG_PROVIDER_CLI: '1' } : {}) },
    cassetteMode: options.cassette,
    cassetteDir: join(outDir, 'cassettes'),
    startupTimeoutMs: 180_000,
  });
  const startedAt = new Date().toISOString();
  let result;
  try {
    // A warehouse layer (no dbt): Ask's schema index lives in .dql/cache, which
    // the fresh copy leaves out, so sync it once, as the project's owner did
    // when it was set up. Metadata only; no AI call.
    const projectConfig = JSON.parse(readFileSync(join(projectDir, 'dql.config.json'), 'utf-8'));
    if (projectConfig.manifestVersion === 3 && ['warehouse-first', 'hybrid'].includes(projectConfig.modeling?.mode)) {
      const synced = await fetch(`${runtime.base}/api/connections/default/metadata-sync`, { method: 'POST' });
      const body = await synced.json();
      if (!synced.ok || body.warehouseCatalog?.error) throw new Error(`Schema sync failed: ${JSON.stringify(body).slice(0, 400)}`);
      identity.settings.warehouseSync = { relations: body.status?.relationCount, catalogRelations: body.warehouseCatalog?.relations };
    }
    console.error(`${options.layer}/${options.set}: ${cases.length} question(s) on ${runtime.base}`);
    result = await runEval(cli, projectDir, evalPath, runtime.base, join(outDir, 'eval.stderr.log'), join(outDir, 'cassettes'));
  } finally {
    writeFileSync(join(outDir, 'server.log'), runtime.logs());
    await runtime.close();
  }
  let report;
  try {
    report = JSON.parse(result.stdout);
  } catch {
    writeFileSync(join(outDir, 'eval.stdout.txt'), result.stdout);
    throw new Error(`dql agent eval exited ${result.code} without a JSON report; see ${relative(REPO_ROOT, outDir)}`);
  }
  const outages = providerOutages(projectDir);
  // Tokens and cost per question, from DQL's usage ledger (API providers only).
  const ledger = readLedger(join(outDir, 'usage.jsonl'));
  const usage = ledger.length ? attributeUsage(ledger, runSpans(projectDir), loadPricing()) : null;
  const out = {
    identity,
    provenance: cassetteEvidence(join(outDir, 'cassettes'), options.cassette),
    ...(outages.length ? { invalid: { reason: 'the AI provider refused calls during the run', questions: outages.length, messages: [...new Set(outages)].slice(0, 3) } } : {}),
    run: { id: options.run, layer: options.layer, set: options.set, startedAt, finishedAt: new Date().toISOString(), evalExitCode: result.code },
    questions: cases.length,
    ...report,
    ...(usage ? { usage } : {}),
  };
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(out, null, 2)}\n`);
  const results = report.results ?? [];
  if (!out.provenance.realProviderQualityEligible) console.error(`not publishable: ${out.provenance.reasons.join('; ')}`);
  if (out.invalid) {
    console.error(`INVALID RUN: the AI provider refused calls on ${out.invalid.questions} question(s): ${out.invalid.messages.join(' | ')}`);
    process.exitCode = 3;
  }
  const correct = results.filter((r) => (stopsAreRight(options.set) ? r.passed : r.executionMatched === true)).length;
  console.log(`${options.layer}/${options.set}: ${correct}/${results.length} ${stopsAreRight(options.set) ? 'stopped correctly' : 'correct'} → ${relative(REPO_ROOT, join(outDir, 'report.json'))}`);
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}

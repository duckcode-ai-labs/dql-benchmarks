#!/usr/bin/env node
// Plain text-to-SQL, the way dbt Labs' benchmark does it, on our warehouse.
//
//   node insurance/baseline-text2sql.mjs --run <id> [--set all|dbt-labs] [--ddl small]
//        [--model claude-sonnet-5] [--effort medium] [--repeat 1] [--replay]
//
// One AI call per question: dbt Labs' own prompt (dbt-llm-sl-bench
// src/llm_bench/services/query_generation.py, SQLStrategy) with their schema
// file pasted in, asking for SQL only. The SQL is run on the L0 warehouse and
// graded with the same rule as Ask (lib/row-match.mjs, extra columns allowed,
// which is dbt Labs' own grading rule).
//
// Two disclosed differences from dbt Labs' runner, both so the baseline is not
// penalised by running on DuckDB instead of their cloud warehouse:
//   1. one line is added to the prompt: "The database is DuckDB."
//   2. a Markdown code fence around the reply is removed before running it.
// Every reply is saved, so a run can be re-graded without calling the model.

import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { spawn, spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, relative } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { rowsMatch } from '../lib/row-match.mjs';
import { loadAudit } from '../lib/gold-audit.mjs';
import { buildIdentity } from '../lib/build-identity.mjs';
import { selectCases } from './run.mjs';

const WORK = join(REPO_ROOT, 'work', 'insurance');
const PYTHON = join(REPO_ROOT, '.venv', 'bin', 'python');
const DDL_FILES = {
  small: join(REPO_ROOT, 'data', 'insurance', 'dbt-llm-sl-bench', 'ACME_small.ddl'),
};

/** dbt Labs' prompt, verbatim, with the one disclosed dialect line. */
export function baselinePrompt(ddl, question) {
  return `
        Given the database described by the following DDL:
        ${ddl}

        The database is DuckDB.

        Write a SQL query that answers the following question. Do not explain the query. return just the query, so it can be run
        verbatim from your response.

        Here's the question:
        ${question}
        `;
}

/** Remove one Markdown code fence around the reply, if there is one. */
export function stripFence(text) {
  const match = /^\s*```[a-zA-Z]*\s*\n([\s\S]*?)\n?```\s*$/.exec(text);
  return (match ? match[1] : text).trim();
}

function parseArgs(argv) {
  const options = { run: null, set: 'all', ddl: 'small', model: 'claude-sonnet-5', effort: 'medium', repeat: 1, replay: false };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    if (arg === '--run') options.run = next();
    else if (arg === '--set') options.set = next();
    else if (arg === '--ddl') options.ddl = next();
    else if (arg === '--model') options.model = next();
    else if (arg === '--effort') options.effort = next();
    else if (arg === '--repeat') options.repeat = Number(next());
    else if (arg === '--replay') options.replay = true;
    else throw new Error(`Unknown argument ${arg}`);
  }
  if (!options.run) throw new Error('--run <id> is required');
  if (!DDL_FILES[options.ddl]) throw new Error(`--ddl must be one of ${Object.keys(DDL_FILES).join(', ')}`);
  return options;
}

function askClaude(prompt, { model, effort }) {
  return new Promise((resolve) => {
    const cwd = mkdtempSync(join(tmpdir(), 'baseline-claude-'));
    const started = Date.now();
    const child = spawn('claude', [
      '-p', '--output-format', 'json', '--tools', '', '--max-turns', '1',
      '--permission-mode', 'dontAsk', '--strict-mcp-config', '--no-session-persistence',
      '--model', model, '--effort', effort,
    ], { cwd, stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    const timer = setTimeout(() => child.kill('SIGTERM'), 300_000);
    child.on('exit', (code) => {
      clearTimeout(timer);
      rmSync(cwd, { recursive: true, force: true });
      let parsed = null;
      try { parsed = JSON.parse(stdout); } catch { /* reported below */ }
      resolve({
        ms: Date.now() - started,
        code,
        text: parsed?.result ?? '',
        isError: parsed ? Boolean(parsed.is_error) : true,
        usage: parsed?.usage ? { input: parsed.usage.input_tokens, cacheRead: parsed.usage.cache_read_input_tokens, cacheWrite: parsed.usage.cache_creation_input_tokens, output: parsed.usage.output_tokens } : null,
        apiMs: parsed?.duration_api_ms ?? null,
        error: parsed ? null : (stderr || stdout).slice(0, 300),
      });
    });
    child.stdin.end(prompt);
  });
}

function runSql(database, queries) {
  const result = spawnSync(PYTHON, [join(REPO_ROOT, 'lib', 'duckdb_query.py')], {
    input: JSON.stringify({ database, queries }), encoding: 'utf-8', maxBuffer: 256 * 1024 * 1024,
  });
  if (result.status !== 0) throw new Error(result.stderr);
  return JSON.parse(result.stdout);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const gold = JSON.parse(readFileSync(join(WORK, 'gold', 'answers.json'), 'utf-8'));
  const audit = loadAudit(join(REPO_ROOT, 'insurance', 'gold-audit.jsonl'));
  const dev = JSON.parse(readFileSync(join(REPO_ROOT, 'insurance', 'dev-questions.json'), 'utf-8'));
  const cases = selectCases(gold, audit, new Set(dev.questions.map((q) => q.caseId)), options.set);
  const ddl = readFileSync(DDL_FILES[options.ddl], 'utf-8');
  const outDir = join(WORK, 'runs', options.run, `baseline-${options.ddl}`, options.set);
  mkdirSync(outDir, { recursive: true });
  const repliesFile = join(outDir, 'replies.json');
  const saved = existsSync(repliesFile) ? JSON.parse(readFileSync(repliesFile, 'utf-8')) : {};
  if (options.replay && !Object.keys(saved).length) throw new Error('Nothing recorded to replay.');

  const replies = { ...saved };
  for (let round = 1; round <= options.repeat; round += 1) {
    for (const c of cases) {
      const key = `${c.id}#${round}`;
      if (replies[key]) continue;
      if (options.replay) throw new Error(`No recorded reply for ${key}`);
      const reply = await askClaude(baselinePrompt(ddl, c.question), options);
      replies[key] = reply;
      writeFileSync(repliesFile, `${JSON.stringify(replies, null, 2)}\n`);
      console.error(`${key}: ${Math.round(reply.ms / 1000)}s${reply.isError ? ' (error)' : ''}`);
    }
  }

  const database = join(WORK, 'projects', 'L0', 'acme_insurance.duckdb');
  const keys = Object.keys(replies).filter((key) => cases.some((c) => key.startsWith(`${c.id}#`)));
  const executed = runSql(database, keys.map((key) => ({ id: key, sql: stripFence(replies[key].text) })));
  const results = keys.map((key) => {
    const [id, round] = key.split('#');
    const c = cases.find((item) => item.id === id);
    const reply = replies[key];
    const run = executed[key];
    const match = run.error ? { match: false, reason: `the SQL did not run: ${run.error.slice(0, 200)}` } : rowsMatch(run.rows, c.gold.rows, { allowExtraColumns: true });
    return {
      name: id,
      round: Number(round),
      passed: match.match,
      executionMatched: match.match,
      ...(match.reason ? { goldMatchReason: match.reason } : {}),
      durationMs: reply.ms,
      providerDispatchCount: 1,
      kind: 'uncertified',
      answer: { trustState: 'none', sql: stripFence(reply.text), ...(run.rows ? { rowCount: run.rows.length } : {}) },
      usage: reply.usage,
      ...(reply.isError ? { runtimeError: reply.error ?? 'the model returned an error' } : {}),
    };
  });

  const cli = { source: 'none', entry: '' };
  const identity = buildIdentity({
    cli, dqlVersion: 'none (plain text-to-SQL)', benchmark: 'insurance', condition: `baseline-${options.ddl}`,
    provider: 'claude-code', model: options.model, cassetteMode: 'record',
    tools: { claudeCli: spawnSync('claude', ['--version'], { encoding: 'utf-8' }).stdout.trim(), effort: options.effort },
  });
  identity.notPublishableBecause = identity.notPublishableBecause.filter((reason) => !/DQL/.test(reason));
  identity.publishable = identity.notPublishableBecause.length === 0;
  const report = {
    identity,
    provenance: { source: 'saved model replies', recordings: keys.length, realProviderQualityEligible: keys.length > 0, reasons: [] },
    run: { id: options.run, layer: `baseline-${options.ddl}`, set: options.set, startedAt: new Date().toISOString(), repeat: options.repeat },
    method: {
      prompt: "dbt Labs' SQLStrategy prompt with one added line, 'The database is DuckDB.'",
      extraction: 'a Markdown code fence around the reply is removed',
      schema: relative(REPO_ROOT, DDL_FILES[options.ddl]),
    },
    results,
  };
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  const right = results.filter((r) => r.executionMatched).length;
  const ran = results.filter((r) => !r.goldMatchReason?.startsWith('the SQL did not run')).length;
  console.log(`baseline-${options.ddl}/${options.set}: ${right}/${results.length} right; ${ran}/${results.length} ran on DuckDB → ${relative(REPO_ROOT, join(outDir, 'report.json'))}`);
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}

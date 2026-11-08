#!/usr/bin/env node
// Agentic text-to-SQL: a model that explores the warehouse itself before it
// answers. The strongest reasonable opponent without DQL (see AGENT-BASELINE.md).
//
//   node insurance/baseline-agent.mjs --run <id> [--set all|dbt-labs|dev|unanswerable|heldout-N[-unanswerable]]
//        [--context none|ddl|dbt-docs|modeling] [--level L0|W0|W2]
//        [--provider claude-code|codex|ollama|anthropic|fake] [--model <id>] [--effort <level>]
//        [--max-turns 12] [--max-tool-calls 20] [--max-wall-s 900] [--call-timeout-s 300]
//        [--codex-home <dir>] [--only id,id] [--replay] [--out <dir>]
//        [--fixture <file> [--fake-refuse <caseId>@<turn>]]      (provider fake only)
//
// Per question: a fresh conversation. The model sees a fixed system prompt, the
// question (with the chosen context) and the results of its own tool calls, and
// nothing else. Tools: list_tables, describe_table, sample_rows, run_sql. It
// ends with final_sql (run in full and graded with lib/row-match.mjs, as the
// one-shot baseline P is) or cannot_answer (a correct stop on an unanswerable
// set, a wrong answer on an answerable one).
//
// Subscription CLIs (`claude -p`, `codex exec`) are single-shot, so they speak a
// text protocol: one JSON action per reply, and every turn is a fresh call that
// carries the whole transcript so far. Ollama gets the same protocol as chat
// messages. The Messages API route (`anthropic`) uses native tool use behind
// the same loop; it has not been run.
//
// Every finished question is saved to transcripts.json. A provider refusal
// (usage limit, rate limit, sign-in, timeout) stops the run with exit code 3;
// running the same command again keeps the finished questions and asks the
// refused one again from its first turn.

import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync, mkdtempSync, appendFileSync } from 'node:fs';
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import { join, relative } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { rowsMatch } from '../lib/row-match.mjs';
import { loadAudit } from '../lib/gold-audit.mjs';
import { buildIdentity } from '../lib/build-identity.mjs';
import { CODEX_DIRS, selectCases, unanswerableCases, useIsolatedCodexHome } from './run.mjs';
import { heldoutPaths, heldoutSetOf, heldoutUnanswerableCases } from './heldout.mjs';
import { loadPricing, priceUsage } from '../lib/usage.mjs';
import { forPublic } from '../lib/public.mjs';

const WORK = join(REPO_ROOT, 'work', 'insurance');
const PYTHON = join(REPO_ROOT, '.venv', 'bin', 'python');
const TOOLS_PY = join(REPO_ROOT, 'insurance', 'agent_tools.py');
const QUERY_PY = join(REPO_ROOT, 'lib', 'duckdb_query.py');

export const CONTEXTS = ['none', 'ddl', 'dbt-docs', 'modeling'];
export const LEVELS = ['L0', 'W0', 'W2'];
export const PROVIDERS = ['claude-code', 'codex', 'ollama', 'anthropic', 'fake'];
const SETS = ['all', 'dbt-labs', 'dev', 'unanswerable'];
export const TOOL_ACTIONS = ['list_tables', 'describe_table', 'sample_rows', 'run_sql'];
export const END_ACTIONS = ['final_sql', 'cannot_answer'];

/** Budgets and tool limits; every one is a flag and is recorded in the report. */
export const DEFAULT_LIMITS = {
  maxTurns: 12, // model calls per question
  maxToolCalls: 20, // executed tool actions per question
  maxWallMs: 900_000, // per question, checked before each model call
  callTimeoutMs: 300_000, // one model call (as baseline-text2sql.mjs)
  rowCap: 50, // rows a query shows the model
  cellChars: 200, // characters of one cell the model is shown
  sampleMax: 5, // rows sample_rows returns at most
  statementTimeoutS: 30, // one statement the model runs
};

// ---------------------------------------------------------------------------
// The fixed prompt
// ---------------------------------------------------------------------------

/** The system prompt, identical for every question of a run. Written out in AGENT-BASELINE.md. */
export function systemPrompt(limits = DEFAULT_LIMITS, protocol = 'text') {
  const actions = protocol === 'native'
    ? `Tools:
- list_tables: every table and view you can query, with its type and column count.
- describe_table(table): the table's columns and types.
- sample_rows(table, n): up to ${limits.sampleMax} rows of the table.
- run_sql(sql): run one read-only query and see at most ${limits.rowCap} rows of its result.
Finish by calling exactly one of:
- final_sql(sql): the query whose full result answers the question.
- cannot_answer(reason): the data does not hold what the question needs.`
    : `Actions (reply with exactly one JSON object per reply, and nothing else):
{"action": "list_tables"}                             every table and view you can query
{"action": "describe_table", "table": "<name>"}       the table's columns and types
{"action": "sample_rows", "table": "<name>", "n": 3}  up to ${limits.sampleMax} rows of the table
{"action": "run_sql", "sql": "<query>"}               run one read-only query; you see at most ${limits.rowCap} rows
Finish with exactly one of:
{"action": "final_sql", "sql": "<query>"}             the query whose full result answers the question
{"action": "cannot_answer", "reason": "<why>"}        the data does not hold what the question needs
(A reply that starts with CANNOT_ANSWER: <reason> also finishes with cannot_answer.)`;
  return `You are a data analyst. You answer one business question by writing one SQL query against a DuckDB database. You cannot see the database: you explore it through the actions below, and after each reply you are shown what your action returned.

${actions}

Rules:
- The database is DuckDB and read-only.
- Your final query's full result is the answer, and it is checked by its values: return the columns and rows the question asks for, not a preview. The ${limits.rowCap}-row limit applies only to what you are shown while exploring.
- If a query fails, you are shown the error and may try again. If your final query fails to run, you are shown the error and may send a corrected final_sql.
- Use cannot_answer only when the data does not hold what the question needs (a missing measure, attribute, entity or period). Do not substitute a different measure.
- You have at most ${limits.maxTurns} replies and ${limits.maxToolCalls} tool calls for this question. A question left without final_sql or cannot_answer when they run out gets no answer.${protocol === 'text' ? '\n- Reply with one JSON object only: no prose, no Markdown.' : ''}`;
}

/** The first user message: the question and, for the ddl and dbt-docs variants, the schema text. */
export function firstMessage(question, contextText = '') {
  return `Question: ${String(question).trim()}${contextText ? `\n\nSchema you were given:\n${contextText.trim()}` : ''}`;
}

function turnNote({ turn, maxTurns, toolsLeft, lastTurn }) {
  return `Reply ${turn} of ${maxTurns}; tool calls left: ${toolsLeft}.${lastTurn ? ' This is your last reply: it must be final_sql or cannot_answer.' : ''}`;
}

/** What the model is shown for one executed action. */
export function renderObservation(observation) {
  return JSON.stringify(observation);
}

function stepText(step) {
  return step.actions.map((action) => `Your reply ${step.turn}: ${String(step.reply ?? '').trim() || '(empty)'}\nResult: ${renderObservation(action.observation)}`).join('\n');
}

/**
 * The single prompt a single-shot CLI (claude -p, codex exec) gets on one turn:
 * the fixed instructions, the question, and the whole transcript so far.
 */
export function renderTextPrompt({ system, first, steps, turn, maxTurns, toolsLeft, lastTurn }) {
  const history = steps.length ? `\n\nWhat you have done so far, oldest first:\n\n${steps.map(stepText).join('\n\n')}` : '';
  return `${system}\n\n${first}${history}\n\n${turnNote({ turn, maxTurns, toolsLeft, lastTurn })}\nYour next action, as one JSON object:`;
}

/** The same transcript as chat messages (Ollama). */
export function renderChatMessages({ system, first, steps, turn, maxTurns, toolsLeft, lastTurn }) {
  const messages = [{ role: 'system', content: system }];
  const note = (k) => turnNote({ turn: k, maxTurns, toolsLeft, lastTurn: k === turn && lastTurn });
  messages.push({ role: 'user', content: `${first}\n\n${steps.length ? `Reply 1 of ${maxTurns}.` : note(turn)}` });
  steps.forEach((step, index) => {
    messages.push({ role: 'assistant', content: String(step.reply ?? '') });
    const results = step.actions.map((action) => `Result: ${renderObservation(action.observation)}`).join('\n');
    messages.push({ role: 'user', content: `${results}\n\n${index === steps.length - 1 ? note(turn) : `Reply ${step.turn + 1} of ${maxTurns}.`}` });
  });
  return messages;
}

// ---------------------------------------------------------------------------
// Reading a reply
// ---------------------------------------------------------------------------

/** The first balanced {...} in a text, respecting JSON strings; null if none. */
function firstJsonObject(text) {
  const start = text.indexOf('{');
  if (start < 0) return null;
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let index = start; index < text.length; index += 1) {
    const char = text[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') inString = false;
    } else if (char === '"') inString = true;
    else if (char === '{') depth += 1;
    else if (char === '}') {
      depth -= 1;
      if (depth === 0) return text.slice(start, index + 1);
    }
  }
  return null;
}

const ALIASES = { final: 'final_sql', answer: 'final_sql', sql: 'run_sql', query: 'run_sql', describe: 'describe_table', sample: 'sample_rows', tables: 'list_tables', cannot: 'cannot_answer' };

/** Normalize an action object (text protocol or a native tool call) to { action, ...args }. */
export function normalizeAction(raw) {
  if (!raw || typeof raw !== 'object') return { action: 'invalid', error: 'the reply held no action object' };
  let name = String(raw.action ?? raw.tool ?? raw.name ?? '').trim().toLowerCase();
  name = ALIASES[name] ?? name;
  const args = raw.input && typeof raw.input === 'object' ? raw.input : raw;
  if (!TOOL_ACTIONS.includes(name) && !END_ACTIONS.includes(name)) return { action: 'invalid', error: `unknown action ${JSON.stringify(name)}; use one of ${[...TOOL_ACTIONS, ...END_ACTIONS].join(', ')}` };
  if ((name === 'run_sql' || name === 'final_sql') && (typeof args.sql !== 'string' || !args.sql.trim())) return { action: 'invalid', error: `${name} needs a "sql" string` };
  if ((name === 'describe_table' || name === 'sample_rows') && (typeof args.table !== 'string' || !args.table.trim())) return { action: 'invalid', error: `${name} needs a "table" string` };
  const out = { action: name };
  if (args.sql !== undefined && (name === 'run_sql' || name === 'final_sql')) out.sql = stripFence(String(args.sql));
  if (args.table !== undefined) out.table = String(args.table);
  if (name === 'sample_rows') out.n = Number.isFinite(Number(args.n)) ? Number(args.n) : 3;
  if (name === 'cannot_answer') out.reason = String(args.reason ?? '').trim();
  return out;
}

/** Remove one Markdown code fence around a text, if there is one (as baseline-text2sql.mjs). */
export function stripFence(text) {
  const match = /^\s*```[a-zA-Z]*\s*\n([\s\S]*?)\n?```\s*$/.exec(text);
  return (match ? match[1] : text).trim();
}

/** One text-protocol reply to one action. A reply that is not one action becomes an "invalid" action the model is told about. */
export function parseAction(text) {
  const body = String(text ?? '').trim();
  const cannot = /^\s*(?:```[a-z]*\s*)?CANNOT_ANSWER\s*:\s*([\s\S]*?)(?:```)?\s*$/i.exec(body);
  if (cannot) return { action: 'cannot_answer', reason: cannot[1].trim() };
  const json = firstJsonObject(stripFence(body)) ?? firstJsonObject(body);
  if (!json) return { action: 'invalid', error: 'the reply was not a JSON action' };
  try {
    return normalizeAction(JSON.parse(json));
  } catch (error) {
    return { action: 'invalid', error: `the reply's JSON did not parse: ${String(error.message).slice(0, 120)}` };
  }
}

// ---------------------------------------------------------------------------
// The warehouse and its tools
// ---------------------------------------------------------------------------

/**
 * A per-run copy of the level's warehouse. It keeps the file name: the dbt
 * views name their catalog ("acme_insurance"), and a renamed copy cannot read them.
 */
export function warehouseCopy(level, dir, source = join(WORK, 'projects', level, 'acme_insurance.duckdb')) {
  if (!existsSync(source)) throw new Error(`No warehouse at ${relative(REPO_ROOT, source)}: build ${level} first (node insurance/build.mjs --layer ${level}).`);
  mkdirSync(dir, { recursive: true });
  const target = join(dir, 'acme_insurance.duckdb');
  copyFileSync(source, target);
  return target;
}

/** Execute one tool action on the copy; returns the observation the model is shown. */
export function callTool(database, action, limits = DEFAULT_LIMITS) {
  const result = spawnSync(PYTHON, [TOOLS_PY], {
    input: JSON.stringify({ database, schema: 'main', rowCap: limits.rowCap, cellChars: limits.cellChars, sampleMax: limits.sampleMax, timeoutS: limits.statementTimeoutS, request: action }),
    encoding: 'utf-8',
    maxBuffer: 64 * 1024 * 1024,
    timeout: (limits.statementTimeoutS + 30) * 1000,
  });
  if (result.error || result.status !== 0) return { error: `the tool failed: ${String(result.error?.message ?? result.stderr).slice(0, 300)}` };
  try { return JSON.parse(result.stdout); } catch { return { error: 'the tool returned no result' }; }
}

/** Run final statements in full with the scorer's own runner (lib/duckdb_query.py), as baseline P does. */
function runFull(database, queries) {
  if (!queries.length) return {};
  const result = spawnSync(PYTHON, [QUERY_PY], { input: JSON.stringify({ database, queries }), encoding: 'utf-8', maxBuffer: 256 * 1024 * 1024, timeout: 600_000 });
  if (result.status !== 0) throw new Error(result.stderr || String(result.error));
  return JSON.parse(result.stdout);
}

/** CREATE TABLE text for every relation in main: the same text baseline P's `--ddl full` uses. */
export function ddlContext(database) {
  const cols = runFull(database, [{ id: 'cols', sql: "select table_name, column_name, data_type from information_schema.columns where table_schema = 'main' order by table_name, ordinal_position" }]).cols;
  if (cols.error) throw new Error(cols.error);
  const byTable = new Map();
  for (const [table, column, type] of cols.rows) {
    if (!byTable.has(table)) byTable.set(table, []);
    byTable.get(table).push(`  ${column} ${type}`);
  }
  return [...byTable].map(([table, columns]) => `CREATE TABLE ${table} (\n${columns.join(',\n')}\n);`).join('\n\n') + '\n';
}

/**
 * What L0's dbt project documents, as DQL reads it: each model with its
 * description, what it is built from, and its columns with types and
 * descriptions (manifest.json + catalog.json from `dbt docs generate`). This
 * dbt project ships no schema yml, so every description is empty; the text
 * says so rather than hiding it.
 */
export function dbtDocsContext(projectDir = join(WORK, 'projects', 'L0')) {
  const manifestPath = join(projectDir, 'target', 'manifest.json');
  const catalogPath = join(projectDir, 'target', 'catalog.json');
  if (!existsSync(manifestPath) || !existsSync(catalogPath)) throw new Error(`--context dbt-docs needs ${relative(REPO_ROOT, manifestPath)} and catalog.json: build L0 first.`);
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
  const catalog = JSON.parse(readFileSync(catalogPath, 'utf-8'));
  const models = Object.values(manifest.nodes).filter((node) => node.resource_type === 'model').sort((a, b) => a.name.localeCompare(b.name));
  const nameOf = (id) => manifest.nodes[id]?.name ?? manifest.sources?.[id]?.name ?? id;
  const blocks = models.map((model) => {
    const cat = catalog.nodes?.[model.unique_id];
    const described = model.columns ?? {};
    const columns = Object.values(cat?.columns ?? {}).sort((a, b) => a.index - b.index).map((column) => {
      const doc = described[column.name] ?? described[column.name.toLowerCase()] ?? Object.values(described).find((item) => item.name?.toLowerCase() === column.name.toLowerCase());
      return `  - ${column.name} (${column.type})${doc?.description ? `: ${doc.description}` : ''}`;
    });
    const parents = (model.depends_on?.nodes ?? []).map(nameOf);
    return [
      `model ${model.name} (${model.config?.materialized ?? cat?.metadata?.type ?? 'model'})`,
      `  description: ${model.description?.trim() || '(none)'}`,
      ...(parents.length ? [`  built from: ${parents.join(', ')}`] : []),
      '  columns:',
      ...columns,
    ].join('\n');
  });
  return `dbt project ${manifest.metadata?.project_name ?? ''} — ${models.length} models in schema main\n\n${blocks.join('\n\n')}\n`;
}

/**
 * The fair comparison with DQL's W2 level: the same table definitions P gets, plus the business
 * model and approved metric definitions DQL has at W2 (entities, keys, certified relationships,
 * measures, metrics and the computed dimensions their filters use), rendered once into
 * insurance/contexts/w2-modeling.txt by insurance/contexts/render-modeling.cjs.
 */
export function modelingContext(database, file = join(REPO_ROOT, 'insurance', 'contexts', 'w2-modeling.txt')) {
  if (!existsSync(file)) throw new Error(`--context modeling needs ${relative(REPO_ROOT, file)}`);
  return `${ddlContext(database).trim()}\n\n${readFileSync(file, 'utf-8')}`;
}

// ---------------------------------------------------------------------------
// Providers: one interface, { protocol, turn(state) → reply }
// ---------------------------------------------------------------------------

const refusal = (started, error) => ({ ms: Date.now() - started, text: '', isError: true, usage: null, error: String(error).slice(0, 300) });

function askClaude(prompt, { model, effort, callTimeoutMs }) {
  return new Promise((resolve) => {
    const cwd = mkdtempSync(join(tmpdir(), 'agent-claude-'));
    const started = Date.now();
    // As baseline-text2sql.mjs: an empty directory, no tools of its own, one turn, nothing saved.
    const child = spawn('claude', [
      '-p', '--output-format', 'json', '--tools', '', '--max-turns', '1',
      '--permission-mode', 'dontAsk', '--strict-mcp-config', '--no-session-persistence',
      '--model', model, '--effort', effort,
    ], { cwd, stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', (error) => { rmSync(cwd, { recursive: true, force: true }); resolve(refusal(started, error)); });
    const timer = setTimeout(() => child.kill('SIGTERM'), callTimeoutMs);
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
        error: parsed ? (parsed.is_error ? String(parsed.result ?? 'error').slice(0, 300) : null) : (stderr || stdout).slice(0, 300),
      });
    });
    child.stdin.end(prompt);
  });
}

function askCodex(prompt, { model, effort, callTimeoutMs }) {
  return new Promise((resolve) => {
    const cwd = mkdtempSync(join(tmpdir(), 'agent-codex-'));
    const outFile = join(cwd, 'last-message.txt');
    const started = Date.now();
    // As baseline-text2sql.mjs: read-only sandbox, an empty directory, nothing saved, effort pinned.
    const child = spawn('codex', [
      'exec', '-', '--sandbox', 'read-only', '--skip-git-repo-check', '--cd', cwd, '--ephemeral',
      '--output-last-message', outFile, '--model', model, '-c', `model_reasoning_effort="${effort}"`,
    ], { cwd, stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, PATH: [...CODEX_DIRS, process.env.PATH ?? ''].join(':') } });
    let log = '';
    child.stdout.on('data', (chunk) => { log += chunk; });
    child.stderr.on('data', (chunk) => { log += chunk; });
    child.on('error', (error) => { rmSync(cwd, { recursive: true, force: true }); resolve(refusal(started, error)); });
    const timer = setTimeout(() => child.kill('SIGTERM'), callTimeoutMs);
    child.on('exit', (code) => {
      clearTimeout(timer);
      let text = '';
      try { text = readFileSync(outFile, 'utf-8'); } catch { /* reported below */ }
      rmSync(cwd, { recursive: true, force: true });
      // The tail of Codex's own log is kept so an auditor can see whether it
      // ran any command of its own (its sandbox can read files; see AGENT-BASELINE.md).
      resolve({ ms: Date.now() - started, code, text, isError: code !== 0 || !text.trim(), usage: null, error: code === 0 && text.trim() ? null : log.slice(-300), codexLogTail: log.slice(-2000) });
    });
    child.stdin.end(prompt);
  });
}

async function askOllama(messages, { model, callTimeoutMs }) {
  const started = Date.now();
  const chars = messages.reduce((sum, message) => sum + message.content.length, 0);
  // A context window that fits the transcript, as baseline-text2sql.mjs sizes it.
  const numCtx = Math.min(65_536, Math.max(8192, Math.ceil((Math.ceil(chars / 3) + 8192 + 512) / 4096) * 4096));
  try {
    const response = await fetch(`${process.env.OLLAMA_BASE_URL ?? 'http://127.0.0.1:11434'}/api/chat`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      signal: AbortSignal.timeout(callTimeoutMs),
      body: JSON.stringify({ model, stream: false, think: false, messages, options: { temperature: 0.2, num_predict: 8192, num_ctx: numCtx } }),
    });
    const body = await response.json().catch(() => null);
    return { ms: Date.now() - started, code: response.status, text: body?.message?.content ?? '', isError: !response.ok, usage: body ? { input: body.prompt_eval_count, output: body.eval_count } : null, error: response.ok ? null : JSON.stringify(body).slice(0, 300) };
  } catch (error) {
    return refusal(started, error);
  }
}

/** Native tool definitions for the Messages API route. */
export const ANTHROPIC_TOOLS = [
  { name: 'list_tables', description: 'Every table and view you can query, with its type and column count.', input_schema: { type: 'object', properties: {} } },
  { name: 'describe_table', description: "The table's columns and types.", input_schema: { type: 'object', properties: { table: { type: 'string' } }, required: ['table'] } },
  { name: 'sample_rows', description: 'Up to 5 rows of the table.', input_schema: { type: 'object', properties: { table: { type: 'string' }, n: { type: 'integer', minimum: 1, maximum: 5 } }, required: ['table'] } },
  { name: 'run_sql', description: 'Run one read-only DuckDB query; you see at most 50 rows of its result.', input_schema: { type: 'object', properties: { sql: { type: 'string' } }, required: ['sql'] } },
  { name: 'final_sql', description: 'Finish: the query whose full result answers the question.', input_schema: { type: 'object', properties: { sql: { type: 'string' } }, required: ['sql'] } },
  { name: 'cannot_answer', description: 'Finish: the data does not hold what the question needs.', input_schema: { type: 'object', properties: { reason: { type: 'string' } }, required: ['reason'] } },
];

/** The transcript as Messages API turns: assistant content blocks, then tool_result blocks. */
export function renderAnthropicMessages({ first, steps, turn, maxTurns, toolsLeft, lastTurn }) {
  const note = turnNote({ turn, maxTurns, toolsLeft, lastTurn });
  const messages = [{ role: 'user', content: steps.length ? first : `${first}\n\n${note}` }];
  steps.forEach((step, index) => {
    messages.push({ role: 'assistant', content: step.content ?? [{ type: 'text', text: String(step.reply ?? '') }] });
    const blocks = step.actions.map((action) => (action.toolUseId
      ? { type: 'tool_result', tool_use_id: action.toolUseId, content: renderObservation(action.observation), ...(action.observation?.error ? { is_error: true } : {}) }
      : { type: 'text', text: `Result: ${renderObservation(action.observation)}` }));
    blocks.push({ type: 'text', text: index === steps.length - 1 ? note : `Reply ${step.turn + 1} of ${maxTurns}.` });
    messages.push({ role: 'user', content: blocks });
  });
  return messages;
}

/** Actions in a Messages API reply: every tool_use block; a reply with none is read as text. */
export function actionsFromContent(content = []) {
  const uses = content.filter((block) => block.type === 'tool_use');
  if (!uses.length) return [parseAction(content.filter((block) => block.type === 'text').map((block) => block.text).join(''))];
  return uses.map((block) => ({ ...normalizeAction({ action: block.name, input: block.input }), toolUseId: block.id }));
}

async function askAnthropic(state, { model, effort, callTimeoutMs }) {
  const started = Date.now();
  try {
    const response = await fetch(`${process.env.ANTHROPIC_BASE_URL ?? 'https://api.anthropic.com'}/v1/messages`, {
      method: 'POST',
      headers: { 'x-api-key': process.env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
      signal: AbortSignal.timeout(callTimeoutMs),
      body: JSON.stringify({ model, max_tokens: 8192, system: state.system, tools: ANTHROPIC_TOOLS, messages: renderAnthropicMessages(state), output_config: { effort } }),
    });
    const body = await response.json().catch(() => null);
    const content = body?.content ?? [];
    return {
      ms: Date.now() - started,
      code: response.status,
      text: content.filter((block) => block.type === 'text').map((block) => block.text).join(''),
      content,
      isError: !response.ok,
      usage: body?.usage ? { input: body.usage.input_tokens, cacheRead: body.usage.cache_read_input_tokens, cacheWrite: body.usage.cache_creation_input_tokens, output: body.usage.output_tokens } : null,
      error: response.ok ? null : JSON.stringify(body?.error ?? body).slice(0, 300),
    };
  } catch (error) {
    return refusal(started, error);
  }
}

/**
 * The test provider: replies come from a scripted fixture, keyed by case id,
 * one reply per turn. It renders the same prompt the CLIs get (and keeps it,
 * so a test can check the transcript grows). `refuse` ("<caseId>@<turn>")
 * makes that turn a provider refusal, to test resume.
 */
export function fakeProvider(fixture, { refuse = null } = {}) {
  const [refuseId, refuseTurn] = refuse ? refuse.split('@') : [];
  return {
    protocol: 'text',
    async turn(state) {
      const prompt = renderTextPrompt(state);
      if (state.caseId === refuseId && state.turn === Number(refuseTurn)) return { ms: 1, text: '', isError: true, usage: null, error: "You've hit your usage limit (scripted refusal)", prompt };
      const script = fixture.scripts?.[state.caseId] ?? [];
      const entry = script[state.turn - 1];
      if (entry && typeof entry === 'object' && entry.refuse) return { ms: 1, text: '', isError: true, usage: null, error: entry.refuse, prompt };
      const text = entry === undefined ? '' : typeof entry === 'string' ? entry : JSON.stringify(entry);
      return { ms: 1, text, isError: false, usage: { input: Math.ceil(prompt.length / 4), output: Math.ceil(text.length / 4) }, error: null, prompt };
    },
  };
}

export function makeProvider(options) {
  const settings = { model: options.model, effort: options.effort, callTimeoutMs: options.limits.callTimeoutMs };
  if (options.provider === 'fake') {
    if (!options.fixture) throw new Error('--provider fake needs --fixture <file>');
    return fakeProvider(JSON.parse(readFileSync(options.fixture, 'utf-8')), { refuse: options.fakeRefuse });
  }
  if (options.provider === 'anthropic') return { protocol: 'native', turn: (state) => askAnthropic(state, settings) };
  if (options.provider === 'ollama') return { protocol: 'text', turn: (state) => askOllama(renderChatMessages(state), settings) };
  const ask = options.provider === 'codex' ? askCodex : askClaude;
  return { protocol: 'text', turn: (state) => ask(renderTextPrompt(state), settings) };
}

// ---------------------------------------------------------------------------
// The loop
// ---------------------------------------------------------------------------

function addUsage(total, usage) {
  if (!usage) return total;
  const out = total ?? { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 };
  out.input += usage.input ?? 0;
  out.output += usage.output ?? 0;
  out.cacheRead += usage.cacheRead ?? 0;
  out.cacheWrite += usage.cacheWrite ?? 0;
  return out;
}

/**
 * One question, one fresh conversation. Returns a finished record, or
 * { refused: true, ... } when the provider refused a call (the caller stops
 * the run; the question is asked again from its first turn next time).
 */
export async function runQuestion({ caseId, question, contextText = '', provider, database, limits = DEFAULT_LIMITS, now = Date.now }) {
  const started = now();
  const system = systemPrompt(limits, provider.protocol);
  const first = firstMessage(question, contextText);
  const steps = [];
  let toolCalls = 0;
  let sqlStatementsRun = 0;
  let protocolErrors = 0;
  let usage = null;
  let lastPromptChars = 0;
  const finish = (end) => ({
    ...end,
    turns: steps.length,
    toolCalls,
    sqlStatementsRun,
    protocolErrors,
    totalMs: now() - started,
    modelMs: steps.reduce((sum, step) => sum + (step.ms ?? 0), 0),
    lastPromptChars,
    usage,
    steps,
  });
  for (let turn = 1; turn <= limits.maxTurns; turn += 1) {
    if (now() - started > limits.maxWallMs) return finish({ stop: 'wall', finalSql: null });
    const lastTurn = turn === limits.maxTurns;
    const state = { caseId, system, first, steps, turn, maxTurns: limits.maxTurns, toolsLeft: Math.max(0, limits.maxToolCalls - toolCalls), lastTurn };
    const reply = await provider.turn(state);
    if (reply.isError) return { refused: true, error: reply.error ?? 'the provider returned an error', turn, steps };
    usage = addUsage(usage, reply.usage);
    lastPromptChars = reply.prompt?.length ?? lastPromptChars;
    const actions = provider.protocol === 'native' ? actionsFromContent(reply.content) : [parseAction(reply.text)];
    const step = {
      turn,
      ms: reply.ms,
      reply: reply.text,
      ...(reply.content ? { content: reply.content } : {}),
      ...(reply.usage ? { usage: reply.usage } : {}),
      ...(reply.prompt ? { prompt: reply.prompt } : {}),
      ...(reply.codexLogTail ? { codexLogTail: reply.codexLogTail } : {}),
      actions: [],
    };
    steps.push(step);
    for (const action of actions) {
      const record = (observation) => step.actions.push({ ...action, observation });
      if (action.action === 'cannot_answer') {
        record({ accepted: true });
        return finish({ stop: 'cannot_answer', finalSql: null, reason: action.reason });
      }
      if (action.action === 'final_sql') {
        // The final query is tried first (capped, with the statement limit):
        // one that does not run is sent back, like any failed query, while
        // replies remain. Graded later in full.
        const check = callTool(database, { action: 'run_sql', sql: action.sql }, limits);
        sqlStatementsRun += 1;
        if (check.error && !lastTurn) {
          record({ error: check.error, note: 'Your final query did not run. Send a corrected final_sql, or continue exploring.' });
          continue;
        }
        record(check.error ? { error: check.error } : { accepted: true, rowCount: check.rowCount, truncated: Boolean(check.truncated) });
        return finish({ stop: 'final_sql', finalSql: action.sql });
      }
      if (action.action === 'invalid') {
        protocolErrors += 1;
        record({ error: `${action.error}. Reply with one JSON action.` });
        continue;
      }
      if (toolCalls >= limits.maxToolCalls) {
        record({ error: 'no tool calls left: reply with final_sql or cannot_answer' });
        continue;
      }
      toolCalls += 1;
      if (action.action === 'run_sql') sqlStatementsRun += 1;
      record(callTool(database, action, limits));
    }
  }
  return finish({ stop: 'turns', finalSql: null });
}

// ---------------------------------------------------------------------------
// Scoring and the report
// ---------------------------------------------------------------------------

/**
 * One result in baseline-text2sql.mjs's shape, plus the agent's own counts.
 * Answerable: right when the final query's full result matches (extra columns
 * allowed). Unanswerable: right when the agent stopped with cannot_answer.
 * A question the budget ended is "no answer" on both (never a correct stop).
 */
export function scoreRecord(c, record, executed, { provider, model, pricing } = {}) {
  const stopped = record.stop === 'cannot_answer';
  const exhausted = record.stop === 'turns' || record.stop === 'wall';
  let match = { match: false };
  if (!c.unanswerable && record.stop === 'final_sql') {
    match = executed?.error ? { match: false, reason: `the SQL did not run: ${executed.error.slice(0, 200)}` } : rowsMatch(executed?.rows ?? [], c.gold.rows, { allowExtraColumns: true });
  } else if (!c.unanswerable && stopped) match = { match: false, reason: `the agent declined: ${String(record.reason ?? '').slice(0, 200)}` };
  const usage = record.usage;
  const costUsd = provider === 'anthropic' && usage ? priceUsage({ inputTokens: usage.input ?? 0, outputTokens: usage.output ?? 0, cacheReadTokens: usage.cacheRead ?? 0, cacheWriteTokens: usage.cacheWrite ?? 0 }, model, pricing) : null;
  return {
    name: c.id,
    round: 1,
    passed: c.unanswerable ? stopped : match.match,
    executionMatched: c.unanswerable ? false : match.match,
    ...(match.reason ? { goldMatchReason: match.reason } : {}),
    durationMs: record.totalMs,
    providerDispatchCount: record.turns,
    kind: stopped ? 'no_answer' : 'uncertified',
    answer: {
      // The agent has no trust labels: every answer it gives is unlabelled.
      trustState: 'none',
      ...(record.finalSql ? { sql: record.finalSql } : {}),
      ...(executed?.rows ? { rowCount: executed.rows.length } : {}),
      ...(stopped ? { declineReason: record.reason } : {}),
    },
    usage,
    costUsd,
    ...(exhausted ? { runtimeError: record.stop === 'wall' ? 'the wall-time budget ran out before a final answer' : 'the turn budget ran out before a final answer' } : {}),
    // The agent's own counts.
    stop: record.stop,
    turns: record.turns,
    toolCalls: record.toolCalls,
    sqlStatementsRun: record.sqlStatementsRun,
    protocolErrors: record.protocolErrors,
    totalMs: record.totalMs,
    modelMs: record.modelMs,
    finalSql: record.finalSql ?? null,
  };
}

function parseArgs(argv) {
  const options = { run: null, set: 'all', context: 'ddl', level: 'L0', provider: 'claude-code', model: 'claude-sonnet-5', effort: 'medium', replay: false, only: null, out: null, codexHome: null, fixture: null, fakeRefuse: null, limits: { ...DEFAULT_LIMITS } };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    const positive = (name) => { const value = Number(next()); if (!Number.isFinite(value) || value <= 0) throw new Error(`${name} must be a positive number`); return value; };
    if (arg === '--run') options.run = next();
    else if (arg === '--set') options.set = next();
    else if (arg === '--context') options.context = next();
    else if (arg === '--level') options.level = next();
    else if (arg === '--provider') options.provider = next();
    else if (arg === '--model') options.model = next();
    else if (arg === '--effort' || arg === '--codex-effort') options.effort = next();
    else if (arg === '--max-turns') options.limits.maxTurns = Math.floor(positive(arg));
    else if (arg === '--max-tool-calls') options.limits.maxToolCalls = Math.floor(positive(arg));
    else if (arg === '--max-wall-s') options.limits.maxWallMs = positive(arg) * 1000;
    else if (arg === '--call-timeout-s') options.limits.callTimeoutMs = positive(arg) * 1000;
    else if (arg === '--statement-timeout-s') options.limits.statementTimeoutS = positive(arg);
    else if (arg === '--replay') options.replay = true;
    else if (arg === '--only') options.only = next().split(',');
    else if (arg === '--out') options.out = next();
    else if (arg === '--codex-home') options.codexHome = next();
    else if (arg === '--fixture') options.fixture = next();
    else if (arg === '--fake-refuse') options.fakeRefuse = next();
    else throw new Error(`Unknown argument ${arg}`);
  }
  if (!options.run) throw new Error('--run <id> is required');
  if (!CONTEXTS.includes(options.context)) throw new Error(`--context must be one of ${CONTEXTS.join(', ')}`);
  if (!LEVELS.includes(options.level)) throw new Error(`--level must be one of ${LEVELS.join(', ')}`);
  if (options.context === 'dbt-docs' && options.level !== 'L0') throw new Error('--context dbt-docs reads the dbt project, which only L0 has');
  if (options.context === 'modeling' && options.level !== 'W2') throw new Error('--context modeling is the knowledge DQL has at W2: use --level W2');
  if (!PROVIDERS.includes(options.provider)) throw new Error(`--provider must be one of ${PROVIDERS.join(', ')}`);
  if (!SETS.includes(options.set) && !heldoutSetOf(options.set)) throw new Error(`--set must be one of ${SETS.join(', ')}, heldout[-N][-unanswerable]`);
  if ((options.fixture || options.fakeRefuse) && options.provider !== 'fake') throw new Error('--fixture and --fake-refuse are for --provider fake only');
  if (options.provider === 'anthropic' && !options.replay && !process.env.ANTHROPIC_API_KEY) throw new Error('--provider anthropic needs ANTHROPIC_API_KEY in the environment');
  return options;
}

/** The questions a set asks, by the same rules as run.mjs and baseline-text2sql.mjs. */
export function loadCases(set) {
  const heldout = heldoutSetOf(set);
  if (set === 'unanswerable') return unanswerableCases();
  if (heldout?.unanswerable) return heldoutUnanswerableCases(heldoutPaths(heldout.number).file);
  if (heldout) return JSON.parse(readFileSync(heldoutPaths(heldout.number).gold, 'utf-8')).cases;
  const gold = JSON.parse(readFileSync(join(WORK, 'gold', 'answers.json'), 'utf-8'));
  const audit = loadAudit(join(REPO_ROOT, 'insurance', 'gold-audit.jsonl'));
  const dev = JSON.parse(readFileSync(join(REPO_ROOT, 'insurance', 'dev-questions.json'), 'utf-8'));
  return selectCases(gold, audit, new Set(dev.questions.map((q) => q.caseId)), set);
}

/** Settings a saved transcript file was made with; a resumed run must use the same. */
function runSettings(options, promptSha256) {
  return { provider: options.provider, model: options.model, effort: options.effort, context: options.context, level: options.level, limits: options.limits, systemPromptSha256: promptSha256 };
}

function toolVersions(options, codexHomeNote) {
  if (options.provider === 'claude-code') return { claudeCli: spawnSync('claude', ['--version'], { encoding: 'utf-8' }).stdout?.trim() ?? null };
  if (options.provider === 'codex') {
    const version = spawnSync('codex', ['--version'], { encoding: 'utf-8', env: { ...process.env, PATH: [...CODEX_DIRS, process.env.PATH ?? ''].join(':') } }).stdout?.trim() ?? 'unknown';
    return { codexCli: `${version}; model_reasoning_effort=${options.effort}; ${codexHomeNote}` };
  }
  if (options.provider === 'ollama') return { ollama: process.env.OLLAMA_BASE_URL ?? 'http://127.0.0.1:11434' };
  if (options.provider === 'anthropic') return { api: 'Anthropic Messages API, native tool use' };
  return { fake: `scripted replies from ${options.fixture}` };
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const codexHomeNote = options.codexHome ? useIsolatedCodexHome(options.codexHome) : `CODEX_HOME=${process.env.CODEX_HOME ?? '~/.codex'} (the operator's own)`;
  let cases = loadCases(options.set);
  if (options.only) cases = cases.filter((c) => options.only.includes(c.id));
  if (!cases.length) throw new Error('No questions selected.');
  const condition = `agent-${options.context}`;
  const outDir = options.out ?? join(WORK, 'runs', options.run, condition, options.set);
  mkdirSync(outDir, { recursive: true });
  const database = warehouseCopy(options.level, join(outDir, 'warehouse'));
  try {
    const provider = options.provider === 'fake' || !options.replay ? makeProvider(options) : { protocol: options.provider === 'anthropic' ? 'native' : 'text' };
    const system = systemPrompt(options.limits, provider.protocol);
    const promptSha256 = createHash('sha256').update(system).digest('hex');
    const contextText = options.context === 'ddl' ? ddlContext(database) : options.context === 'dbt-docs' ? dbtDocsContext() : options.context === 'modeling' ? modelingContext(database) : '';
    const settings = runSettings(options, promptSha256);

    const transcriptsFile = join(outDir, 'transcripts.json');
    const saved = existsSync(transcriptsFile) ? JSON.parse(readFileSync(transcriptsFile, 'utf-8')) : { settings, records: {} };
    if (JSON.stringify(saved.settings) !== JSON.stringify(settings)) throw new Error(`${relative(REPO_ROOT, transcriptsFile)} was made with other settings (${JSON.stringify(saved.settings)}); pick a new run id.`);
    if (options.replay && !Object.keys(saved.records).length) throw new Error('Nothing recorded to replay.');
    const records = saved.records;

    for (const c of cases) {
      const key = `${c.id}#1`;
      if (records[key]) continue;
      if (options.replay) throw new Error(`No recorded transcript for ${key}`);
      const record = await runQuestion({ caseId: c.id, question: c.question, contextText, provider, database, limits: options.limits });
      // A refused call is not an answer the model gave. The run stops, marked
      // invalid (exit 3), as baseline-text2sql.mjs does; the finished questions
      // are kept and the refused one is asked again from scratch next time.
      if (record.refused) {
        appendFileSync(join(outDir, 'refused-attempts.jsonl'), forPublic(`${JSON.stringify({ key, at: new Date().toISOString(), turn: record.turn, error: record.error, steps: record.steps.length })}\n`));
        console.error(`INVALID RUN: the provider refused the call for ${key} at turn ${record.turn}: ${String(record.error).slice(0, 300)}`);
        process.exitCode = 3;
        return null;
      }
      records[key] = record;
      writeFileSync(transcriptsFile, `${JSON.stringify({ settings, records }, null, 2)}\n`);
      console.error(`${key}: ${record.stop} after ${record.turns} turn(s), ${record.toolCalls} tool call(s), ${Math.round(record.totalMs / 1000)}s`);
    }

    const pricing = loadPricing();
    const keys = cases.map((c) => `${c.id}#1`).filter((key) => records[key]);
    const executed = runFull(database, keys.filter((key) => records[key].finalSql).map((key) => ({ id: key, sql: records[key].finalSql })));
    const results = keys.map((key) => scoreRecord(cases.find((c) => `${c.id}#1` === key), records[key], executed[key], { provider: options.provider, model: options.model, pricing }));

    const identity = buildIdentity({
      cli: { source: 'none', entry: '' }, dqlVersion: 'none (agentic text-to-SQL)', benchmark: 'insurance', condition,
      provider: options.provider, model: options.model, cassetteMode: 'record',
      tools: { ...toolVersions(options, codexHomeNote), effort: options.effort },
    });
    identity.notPublishableBecause = identity.notPublishableBecause.filter((reason) => !/DQL/.test(reason));
    if (options.provider === 'fake') identity.notPublishableBecause.push('scripted fake provider: no model was asked');
    identity.publishable = identity.notPublishableBecause.length === 0;
    const report = {
      identity,
      provenance: {
        source: 'saved agent transcripts',
        recordings: keys.length,
        realProviderQualityEligible: keys.length > 0 && options.provider !== 'fake',
        reasons: options.provider === 'fake' ? ['scripted fake provider'] : [],
      },
      run: { id: options.run, layer: condition, set: options.set, warehouse: options.level, startedAt: new Date().toISOString(), repeat: 1 },
      method: {
        design: 'insurance/AGENT-BASELINE.md',
        protocol: provider.protocol === 'native' ? 'Messages API native tool use' : 'text protocol: one JSON action per reply; each turn is a fresh call carrying the whole transcript',
        systemPrompt: system,
        systemPromptSha256: promptSha256,
        context: options.context,
        contextSha256: contextText ? createHash('sha256').update(contextText).digest('hex') : null,
        tools: [...TOOL_ACTIONS, ...END_ACTIONS],
        limits: options.limits,
        grading: 'final query run in full on the warehouse copy; lib/row-match.mjs with extra columns allowed (as baseline P); cannot_answer is a correct stop only on an unanswerable set',
      },
      results,
    };
    if (options.provider === 'anthropic') {
      const byQuestion = Object.fromEntries(results.map((result) => {
        const usage = result.usage ?? {};
        const question = cases.find((c) => c.id === result.name)?.question ?? result.name;
        return [question, { calls: result.turns, inputTokens: usage.input ?? 0, outputTokens: usage.output ?? 0, cacheReadTokens: usage.cacheRead ?? 0, cacheWriteTokens: usage.cacheWrite ?? 0, reasoningTokens: 0, costUsd: result.costUsd, priced: result.costUsd != null }];
      }));
      const priced = Object.values(byQuestion).every((item) => item.priced);
      report.usage = { byQuestion, outside: null, totalCostUsd: priced ? Object.values(byQuestion).reduce((sum, item) => sum + item.costUsd, 0) : null, pricingAsOf: pricing.asOf ?? null };
    }
    writeFileSync(join(outDir, 'report.json'), forPublic(`${JSON.stringify(report, null, 2)}\n`));
    const unanswerable = cases.some((c) => c.unanswerable);
    const passed = results.filter((r) => r.passed).length;
    const turns = results.reduce((sum, r) => sum + r.turns, 0);
    console.log(`${condition}/${options.set}: ${passed}/${results.length} ${unanswerable ? 'stopped correctly' : 'right'}; ${(turns / Math.max(1, results.length)).toFixed(1)} model calls per question → ${relative(REPO_ROOT, join(outDir, 'report.json'))}`);
    return report;
  } finally {
    rmSync(join(outDir, 'warehouse'), { recursive: true, force: true });
  }
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}

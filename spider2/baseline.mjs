// Spider 2.0-Lite, SQLite subset: the model on its own.
//
//   node spider2/baseline.mjs --run <id> [--provider claude-code|codex] [--model <model>] [--effort high] [--db <name>] [--set quick]
//
// The control arm for the DQL conditions: the SAME questions, the SAME model,
// the SAME scorer, with no DQL between them. The model is given the whole
// schema as the database declares it (every CREATE statement) and the question
// as Spider poses it, and writes one SQLite statement. This is what a plain
// text-to-SQL prompt achieves here, so the DQL numbers can be read against the
// model's own ceiling rather than in the abstract.
//
// Predictions land in the same layout a DQL run writes, so `score.py` grades
// both the same way.

import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, relative } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { CODEX_DIRS } from '../insurance/run.mjs';
import { LOCALDB, readTasks, questionText } from './tasks.mjs';
import { taskSet } from './sets.mjs';

const WORK = join(REPO_ROOT, 'work', 'spider2');
const CASE_TIMEOUT_MS = 300_000;

function parseArgs(argv) {
  // The baseline writes SQL at the effort DQL's own SQL drafter uses on the
  // same provider (DQL drafts at "high", the sql_cell route effort), so the
  // comparison differs in DQL alone, never in how hard the model thought.
  const options = { run: null, provider: 'claude-code', model: 'claude-sonnet-5', effort: 'high', db: null, only: null, set: null };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === '--run') options.run = argv[++index];
    else if (flag === '--model') options.model = argv[++index];
    else if (flag === '--provider') options.provider = argv[++index];
    else if (flag === '--effort') options.effort = argv[++index];
    else if (flag === '--db') options.db = argv[++index];
    else if (flag === '--only') options.only = new Set(argv[++index].split(',').map((item) => item.trim()));
    else if (flag === '--set') options.set = argv[++index];
    else throw new Error(`unknown flag ${flag}`);
  }
  if (!options.run) throw new Error('--run <id> is required');
  return options;
}

/** Every CREATE statement the database declares: the whole schema, nothing summarized. */
function schemaOf(db) {
  const file = join(LOCALDB, `${db}.sqlite`);
  const result = spawnSync('sqlite3', [file, "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY type DESC, name"], { encoding: 'utf-8', maxBuffer: 64 * 1024 * 1024 });
  if (result.status !== 0) throw new Error(`reading the schema of ${db} failed: ${result.stderr}`);
  return result.stdout.trim();
}

function prompt(task, schema) {
  return [
    'You are answering a question against a SQLite database.',
    '',
    'Schema (every table and view, as the database declares them):',
    schema,
    '',
    `Question: ${questionText(task)}`,
    '',
    'Write ONE SQLite SELECT statement that answers the question.',
    'Return only the SQL, with no explanation and no code fence.',
  ].join('\n');
}

/** One Codex call: `codex exec` at the effort in ~/.codex/config.toml. */
function askCodex(input, options) {
  return spawnSync('codex', ['exec', '--ephemeral', '--model', options.model, '-'], {
    input,
    encoding: 'utf-8',
    timeout: CASE_TIMEOUT_MS,
    maxBuffer: 64 * 1024 * 1024,
    env: { ...process.env, PATH: [...CODEX_DIRS, process.env.PATH ?? ''].join(':') },
  });
}

/**
 * One Claude call, with the flags DQL's own Claude provider uses: no tools,
 * one turn, no session, no ambient MCP or project settings (isolated cwd).
 * Returns the shape spawnSync gives, with the reply text as stdout.
 */
function askClaude(input, options) {
  const cwd = mkdtempSync(join(tmpdir(), 'spider2-baseline-claude-'));
  try {
    const result = spawnSync('claude', ['-p', '--output-format', 'json', '--tools', '', '--max-turns', '1', '--permission-mode', 'dontAsk', '--strict-mcp-config', '--no-session-persistence', '--model', options.model, '--effort', options.effort], {
      input, cwd, encoding: 'utf-8', timeout: CASE_TIMEOUT_MS, maxBuffer: 64 * 1024 * 1024,
    });
    let parsed = null;
    try { parsed = JSON.parse(result.stdout ?? ''); } catch { /* reported as a failed call */ }
    const text = typeof parsed?.result === 'string' ? parsed.result : '';
    const failed = result.status !== 0 || !parsed || parsed.is_error === true;
    return { status: failed ? (result.status || 1) : 0, stdout: failed ? `${result.stdout ?? ''}` : text, stderr: `${result.stderr ?? ''}${failed && parsed?.result ? `\n${parsed.result}` : ''}` };
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
}

/** The SQL out of a model answer: the fenced block when there is one, else the text. */
function sqlFrom(text) {
  const fenced = /```(?:sql)?\s*([\s\S]*?)```/i.exec(text);
  const body = (fenced ? fenced[1] : text).trim();
  const start = body.search(/\b(?:WITH|SELECT)\b/i);
  return start >= 0 ? body.slice(start).trim() : '';
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const { tasks, missingDatabases } = readTasks();
  const inSet = taskSet(options.set);
  const selected = tasks.filter((task) => (!options.db || task.db === options.db) && (!options.only || options.only.has(task.id)) && (!inSet || inSet.has(task.id)));
  const runDir = join(WORK, 'runs', options.run, 'baseline');
  mkdirSync(join(runDir, 'predictions'), { recursive: true });
  const byDb = new Map();
  for (const task of selected) byDb.set(task.db, [...(byDb.get(task.db) ?? []), task]);

  const summary = {
    run: options.run,
    condition: 'baseline',
    description: 'the model alone: full schema in the prompt, no DQL',
    provider: options.provider,
    model: options.model,
    effort: options.provider === 'claude-code' ? options.effort : 'from ~/.codex/config.toml',
    // No DQL in this arm: that is the point of the control.
    dql: null,
    startedAt: new Date().toISOString(),
    missingDatabases,
    tasks: selected.length,
    databases: {},
    invalid: [],
  };

  for (const [db, dbTasks] of [...byDb.entries()].sort(([a], [b]) => a.localeCompare(b))) {
    const schema = schemaOf(db);
    const answered = [];
    const outcomes = {};
    for (const task of dbTasks) {
      const startedAt = Date.now();
      const result = options.provider === 'codex' ? askCodex(prompt(task, schema), options) : askClaude(prompt(task, schema), options);
      const durationMs = Date.now() - startedAt;
      // A call the provider refused (usage limit, quota, sign-in) is not an
      // answer the model gave: scored as "no SQL" it counts as the model being
      // wrong. The run stops and is marked invalid instead, as the DQL runner does.
      // Only a failed call is examined, and only its error output: a model's
      // SQL can name a column `total_quota`, which is not a quota error.
      const said = `${result.stderr ?? ''}`;
      const codexRefusal = options.provider === 'codex' && /^ERROR:.*(usage limit|rate limit|quota)/im.test(`${result.stdout ?? ''}\n${said}`);
      if (result.status !== 0 || codexRefusal) {
        const reason = said.split('\n').filter((line) => /error|limit|quota|unauthori|login/i.test(line)).slice(-3).join(' ').slice(0, 400) || `exit ${result.status}`;
        summary.invalid.push({ db, task: task.id, reason });
        summary.databases[db] = { tasks: dbTasks.map((item) => item.id), answered, outcomes };
        writeFileSync(join(runDir, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
        console.error(`INVALID RUN: the provider refused the call for ${task.id}: ${reason}`);
        process.exitCode = 3;
        return;
      }
      const sql = sqlFrom(result.stdout ?? '');
      if (sql) {
        writeFileSync(join(runDir, 'predictions', `${task.id}.sql`), `${sql}\n`);
        answered.push(task.id);
      }
      outcomes[task.id] = { trust: null, route: 'model_only', durationMs, ...(sql ? {} : { error: (result.stderr ?? '').trim().slice(0, 200) || `exit ${result.status}` }) };
    }
    summary.databases[db] = { tasks: dbTasks.map((task) => task.id), answered, outcomes };
    console.error(`baseline/${db}: ${answered.length}/${dbTasks.length} returned SQL`);
  }

  summary.finishedAt = new Date().toISOString();
  writeFileSync(join(runDir, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
  const total = Object.values(summary.databases).reduce((n, item) => n + item.answered.length, 0);
  console.log(`baseline: ${total}/${selected.length} returned SQL → ${relative(REPO_ROOT, runDir)}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});

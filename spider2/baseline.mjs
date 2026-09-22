// Spider 2.0-Lite, SQLite subset: the model on its own.
//
//   node spider2/baseline.mjs --run <id> [--model gpt-5.6-luna] [--db <name>]
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
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { CODEX_DIRS } from '../insurance/run.mjs';
import { LOCALDB, readTasks, questionText } from './tasks.mjs';

const WORK = join(REPO_ROOT, 'work', 'spider2');
const CASE_TIMEOUT_MS = 300_000;

function parseArgs(argv) {
  const options = { run: null, model: 'gpt-5.6-luna', db: null, only: null };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === '--run') options.run = argv[++index];
    else if (flag === '--model') options.model = argv[++index];
    else if (flag === '--db') options.db = argv[++index];
    else if (flag === '--only') options.only = new Set(argv[++index].split(',').map((item) => item.trim()));
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
  const selected = tasks.filter((task) => (!options.db || task.db === options.db) && (!options.only || options.only.has(task.id)));
  const runDir = join(WORK, 'runs', options.run, 'baseline');
  mkdirSync(join(runDir, 'predictions'), { recursive: true });
  const byDb = new Map();
  for (const task of selected) byDb.set(task.db, [...(byDb.get(task.db) ?? []), task]);

  const summary = {
    run: options.run,
    condition: 'baseline',
    description: 'the model alone: full schema in the prompt, no DQL',
    provider: 'codex',
    model: options.model,
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
      const result = spawnSync('codex', ['exec', '--ephemeral', '--model', options.model, '-'], {
        input: prompt(task, schema),
        encoding: 'utf-8',
        timeout: CASE_TIMEOUT_MS,
        maxBuffer: 64 * 1024 * 1024,
        env: { ...process.env, PATH: [...CODEX_DIRS, process.env.PATH ?? ''].join(':') },
      });
      const durationMs = Date.now() - startedAt;
      const sql = result.status === 0 ? sqlFrom(result.stdout ?? '') : '';
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

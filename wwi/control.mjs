#!/usr/bin/env node
// The control arm: NVIDIA's schema-only baseline on WideWorldImporters.
//
//   node wwi/control.mjs --run <id> [--pass 1] [--model claude-sonnet-5-5] [--limit 3]
//
// The prompt is built the way ontology_sql_eval/gym/tasks.py builds it for
// NVIDIA's `schema_only` arm: its system prompt, its user turn, and the DDL
// files in sorted order. One shot, no tools. Replies are saved, so a run can be
// graded again without calling the model. Extraction and grading are in grade.py.

import { spawn } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';

const DATASET = join(REPO_ROOT, 'work', 'wwi', 'dataset');
const WORKERS = 4;
const ATTEMPTS = 3;

const FIRST_LINE = 'Please reason step by step, and put your final answer within the tags "```sql" and "```".';
export const SYSTEM_PROMPT = `${FIRST_LINE}\nReturn exactly the requested output fields and NO others.`;

export function schemaDump(ddlDir = join(DATASET, 'ddl')) {
  const files = readdirSync(ddlDir).filter((name) => name.endsWith('.sql')).sort();
  return files.map((name) => `-- ${name}\n${readFileSync(join(ddlDir, name), 'utf-8').trim()}`).join('\n\n');
}

export function userPrompt(question, schema) {
  return [
    `### Question\n${question}`,
    'Write a single postgres query that answers the question.',
    `The following is a SQL dump that describes the database and the tables in it.\n${schema}`,
  ].join('\n\n');
}

function ask(prompt, model, system) {
  return new Promise((resolve) => {
    const cwd = mkdtempSync(join(tmpdir(), 'wwi-control-'));
    const started = Date.now();
    const child = spawn('claude', [
      '-p', '--output-format', 'json', '--tools', '', '--max-turns', '1',
      '--permission-mode', 'dontAsk', '--strict-mcp-config', '--no-session-persistence',
      '--model', model, '--system-prompt', system,
    ], { cwd, stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    const timer = setTimeout(() => child.kill('SIGTERM'), 300_000);
    child.on('exit', () => {
      clearTimeout(timer);
      rmSync(cwd, { recursive: true, force: true });
      let parsed = null;
      try { parsed = JSON.parse(stdout); } catch { /* reported below */ }
      const failed = !parsed || parsed.is_error || !parsed.result;
      resolve({
        ms: Date.now() - started,
        reply: failed ? null : parsed.result,
        error: failed ? String(parsed?.result ?? (stderr || stdout)).slice(0, 300) : null,
        usage: parsed?.usage ? { input: parsed.usage.input_tokens, output: parsed.usage.output_tokens } : null,
      });
    });
    child.stdin.end(prompt);
  });
}

function parseArgs(argv) {
  const options = { run: null, pass: 1, model: 'claude-sonnet-5-5', limit: null, line: true, questions: null };
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === '--run') options.run = argv[++index];
    else if (argv[index] === '--pass') options.pass = Number(argv[++index]);
    else if (argv[index] === '--model') options.model = argv[++index];
    else if (argv[index] === '--limit') options.limit = Number(argv[++index]);
    else if (argv[index] === '--no-line') options.line = false;
    else if (argv[index] === '--questions') options.questions = argv[++index];
    else throw new Error(`Unknown option ${argv[index]}`);
  }
  if (!options.run) throw new Error('--run <id> is required.');
  return options;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const outDir = join(REPO_ROOT, 'results', 'wwi', options.run, 'C', `pass-${options.pass}`);
  mkdirSync(outDir, { recursive: true });
  const outPath = join(outDir, 'predictions.jsonl');
  const done = new Set(existsSync(outPath)
    ? readFileSync(outPath, 'utf-8').split('\n').filter(Boolean).map((line) => JSON.parse(line)).filter((row) => row.reply).map((row) => row.question_id)
    : []);
  const schema = schemaDump();
  const system = options.line ? SYSTEM_PROMPT : FIRST_LINE;
  const questions = JSON.parse(readFileSync(options.questions ?? join(DATASET, 'evaluation.json'), 'utf-8'))
    .slice(0, options.limit ?? undefined)
    .filter((question) => !done.has(question.question_id));
  writeFileSync(join(outDir, 'settings.json'), `${JSON.stringify({ model: options.model, systemPrompt: system, schemaChars: schema.length, tools: 'none', startedAt: new Date().toISOString() }, null, 2)}\n`);

  let next = 0;
  await Promise.all(Array.from({ length: WORKERS }, async () => {
    while (next < questions.length) {
      const question = questions[next];
      next += 1;
      let answer;
      for (let attempt = 1; attempt <= ATTEMPTS; attempt += 1) {
        answer = await ask(userPrompt(question.question, schema), options.model, system);
        if (answer.reply) break;
        await new Promise((done_) => setTimeout(done_, attempt * 20_000));
      }
      appendFileSync(outPath, `${JSON.stringify({
        question_id: question.question_id,
        reply: answer.reply,
        failure: answer.reply ? null : 'no_model_output',
        error: answer.error,
        ms: answer.ms,
        usage: answer.usage,
      })}\n`);
      console.error(`q${question.question_id}: ${answer.reply ? 'ok' : `failed: ${answer.error}`} (${Math.round(answer.ms / 1000)} s)`);
    }
  }));
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}

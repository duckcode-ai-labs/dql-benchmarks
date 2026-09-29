import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import {
  DEFAULT_LIMITS, actionsFromContent, dbtDocsContext, fakeProvider, loadCases, main, parseAction,
  renderAnthropicMessages, renderChatMessages, runQuestion, scoreRecord, systemPrompt, warehouseCopy,
} from './baseline-agent.mjs';

const FIXTURE = join(REPO_ROOT, 'insurance', 'fixtures', 'agent-fake-transcripts.json');
const L0_DB = join(REPO_ROOT, 'work', 'insurance', 'projects', 'L0', 'acme_insurance.duckdb');
const W0_DB = join(REPO_ROOT, 'work', 'insurance', 'projects', 'W0', 'acme_insurance.duckdb');
// The end-to-end tests need the built warehouse, the correct answers and the
// Python environment, none of which a fresh clone has (work/ is not in git).
const built = existsSync(L0_DB) && existsSync(W0_DB) && existsSync(join(REPO_ROOT, '.venv', 'bin', 'python'))
  && existsSync(join(REPO_ROOT, 'work', 'insurance', 'gold', 'answers.json'));
const skip = built ? false : 'needs the built L0/W0 warehouses, gold answers and .venv (node insurance/build.mjs)';

const EXPENSE = 'what-are-the-expense-payment-amount-of-all-claim-aec397';
const POLICIES = 'return-all-the-policies-we-have-by-policy-number-dacb83';
const CREDIT = 'unanswerable-what-is-the-average-credit-score-of-our-policy-h-d340e7';

test('a text reply is read as one action, tolerating a fence, prose around the JSON and CANNOT_ANSWER', () => {
  assert.deepEqual(parseAction('{"action":"list_tables"}'), { action: 'list_tables' });
  assert.deepEqual(parseAction('```json\n{"action": "describe_table", "table": "claim"}\n```'), { action: 'describe_table', table: 'claim' });
  assert.deepEqual(parseAction('Sure: {"action":"run_sql","sql":"select \'{x}\' as a"} done'), { action: 'run_sql', sql: "select '{x}' as a" });
  assert.deepEqual(parseAction('{"action":"final_sql","sql":"```sql\\nselect 1\\n```"}'), { action: 'final_sql', sql: 'select 1' });
  assert.deepEqual(parseAction('CANNOT_ANSWER: no credit score'), { action: 'cannot_answer', reason: 'no credit score' });
  assert.deepEqual(parseAction('{"action":"cannot_answer","reason":"missing"}'), { action: 'cannot_answer', reason: 'missing' });
  assert.equal(parseAction('select 1').action, 'invalid');
  assert.equal(parseAction('{"action":"drop_table"}').action, 'invalid');
  assert.equal(parseAction('{"action":"run_sql"}').action, 'invalid');
  assert.equal(parseAction('{"action": "run_sql", "sql": ').action, 'invalid');
});

test('native tool calls map to the same actions, and the Messages transcript pairs every tool_use with a result', () => {
  const content = [{ type: 'text', text: 'looking' }, { type: 'tool_use', id: 'tu1', name: 'describe_table', input: { table: 'claim' } }];
  const actions = actionsFromContent(content);
  assert.deepEqual(actions, [{ action: 'describe_table', table: 'claim', toolUseId: 'tu1' }]);
  assert.deepEqual(actionsFromContent([{ type: 'text', text: 'CANNOT_ANSWER: nothing' }]), [{ action: 'cannot_answer', reason: 'nothing' }]);
  const steps = [{ turn: 1, reply: 'looking', content, actions: [{ ...actions[0], observation: { table: 'claim', columns: [] } }] }];
  const messages = renderAnthropicMessages({ first: 'Question: Q?', steps, turn: 2, maxTurns: 3, toolsLeft: 19, lastTurn: false });
  assert.equal(messages.length, 3);
  assert.equal(messages[1].role, 'assistant');
  assert.equal(messages[2].content[0].type, 'tool_result');
  assert.equal(messages[2].content[0].tool_use_id, 'tu1');
});

test('chat messages alternate and carry each observation once', () => {
  const steps = [
    { turn: 1, reply: '{"action":"list_tables"}', actions: [{ action: 'list_tables', observation: { tables: [{ name: 'claim' }] } }] },
    { turn: 2, reply: 'oops', actions: [{ action: 'invalid', observation: { error: 'not JSON' } }] },
  ];
  const messages = renderChatMessages({ system: 'S', first: 'Question: Q?', steps, turn: 3, maxTurns: 3, toolsLeft: 19, lastTurn: true });
  assert.deepEqual(messages.map((m) => m.role), ['system', 'user', 'assistant', 'user', 'assistant', 'user']);
  assert.match(messages[3].content, /"name":"claim"/);
  assert.match(messages.at(-1).content, /last reply: it must be final_sql or cannot_answer/);
});

test('the system prompt names every tool and budget and nothing about DQL', () => {
  const prompt = systemPrompt(DEFAULT_LIMITS, 'text');
  for (const word of ['list_tables', 'describe_table', 'sample_rows', 'run_sql', 'final_sql', 'cannot_answer', 'CANNOT_ANSWER', 'DuckDB', '12 replies', '20 tool calls', '50']) assert.ok(prompt.includes(word), word);
  assert.doesNotMatch(prompt, /DQL|certified|governed/i);
});

test('scoring: a stop is right only on an unanswerable question; a spent budget is never a stop', () => {
  const record = (stop, extra = {}) => ({ stop, turns: 3, toolCalls: 2, sqlStatementsRun: 1, protocolErrors: 0, totalMs: 10, modelMs: 5, usage: null, finalSql: null, ...extra });
  const answerable = { id: 'a', gold: { rows: [[1]] } };
  const unanswerable = { id: 'u', unanswerable: true };
  assert.equal(scoreRecord(answerable, record('final_sql', { finalSql: 'select 1' }), { columns: ['x'], rows: [[1]] }).passed, true);
  assert.equal(scoreRecord(answerable, record('final_sql', { finalSql: 'select 2' }), { columns: ['x'], rows: [[2]] }).passed, false);
  const declined = scoreRecord(answerable, record('cannot_answer', { reason: 'no' }), undefined);
  assert.equal(declined.passed, false);
  assert.equal(declined.kind, 'no_answer');
  assert.equal(scoreRecord(unanswerable, record('cannot_answer', { reason: 'no' }), undefined).passed, true);
  assert.equal(scoreRecord(unanswerable, record('final_sql', { finalSql: 'select 1' }), { rows: [[1]] }).passed, false);
  const spent = scoreRecord(unanswerable, record('turns'), undefined);
  assert.equal(spent.passed, false);
  assert.match(spent.runtimeError, /turn budget/);
  assert.equal(spent.answer.trustState, 'none');
});

test('the turn budget ends a question that never finishes, and the last turn says so', { skip }, async () => {
  const dir = mkdtempSync(join(tmpdir(), 'agent-budget-'));
  try {
    const database = warehouseCopy('W0', dir);
    const provider = fakeProvider({ scripts: { q: ['{"action":"list_tables"}', '{"action":"run_sql","sql":"select count(*) from claim"}', '{"action":"list_tables"}'] } });
    const limits = { ...DEFAULT_LIMITS, maxTurns: 3, maxToolCalls: 1 };
    const record = await runQuestion({ caseId: 'q', question: 'How many claims?', provider, database, limits });
    assert.equal(record.stop, 'turns');
    assert.equal(record.turns, 3);
    assert.equal(record.toolCalls, 1);
    assert.match(JSON.stringify(record.steps[1].actions[0].observation), /no tool calls left/);
    assert.match(record.steps[2].prompt, /This is your last reply/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('the tools run on a read-only copy: row cap, bad table, writes refused', { skip }, async () => {
  const dir = mkdtempSync(join(tmpdir(), 'agent-tools-'));
  try {
    const database = warehouseCopy('L0', dir);
    const provider = fakeProvider({ scripts: { q: [
      '{"action":"run_sql","sql":"select * from range(80)"}',
      '{"action":"sample_rows","table":"no_such","n":2}',
      '{"action":"run_sql","sql":"create table x (a int)"}',
      '{"action":"final_sql","sql":"select count(*) from claim"}',
    ] } });
    const record = await runQuestion({ caseId: 'q', question: 'How many claims?', provider, database });
    const [capped, missing, write] = record.steps.map((step) => step.actions[0].observation);
    assert.equal(capped.rows.length, 50);
    assert.match(capped.truncated, /more than 50 rows/);
    assert.match(missing.error, /no table or view named/);
    assert.match(write.error, /read-only/);
    assert.equal(record.stop, 'final_sql');
    assert.equal(record.sqlStatementsRun, 3);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('dbt docs: every L0 model with its columns, and the missing descriptions said plainly', { skip }, () => {
  const text = dbtDocsContext();
  assert.match(text, /29 models in schema main/);
  assert.match(text, /model claim \(view\)\n {2}description: \(none\)\n {2}built from: Claim/);
  assert.match(text, /- Company_Claim_Number \(INTEGER\)/);
});

test('end to end on the development questions: refusal, resume from scratch, grading, report', { skip }, async () => {
  const out = mkdtempSync(join(tmpdir(), 'agent-e2e-'));
  const args = ['--run', 'test', '--set', 'dev', '--context', 'ddl', '--provider', 'fake', '--fixture', FIXTURE, '--out', out];
  try {
    const order = loadCases('dev').map((c) => c.id);
    assert.deepEqual([...order].sort(), [EXPENSE, POLICIES].sort());
    const second = order[1];
    // First attempt: the provider refuses turn 2 of the second question.
    const refused = await main([...args, '--fake-refuse', `${second}@2`]);
    assert.equal(refused, null);
    assert.equal(process.exitCode, 3);
    process.exitCode = 0;
    assert.equal(existsSync(join(out, 'report.json')), false);
    assert.equal(existsSync(join(out, 'warehouse')), false, 'the warehouse copy is removed');
    const partial = JSON.parse(readFileSync(join(out, 'transcripts.json'), 'utf-8'));
    assert.deepEqual(Object.keys(partial.records), [`${order[0]}#1`]);
    assert.equal(readFileSync(join(out, 'refused-attempts.jsonl'), 'utf-8').trim().split('\n').length, 1);

    // Second attempt: the kept question is not asked again; the refused one starts over.
    const report = await main(args);
    assert.equal(process.exitCode, 0);
    const transcripts = JSON.parse(readFileSync(join(out, 'transcripts.json'), 'utf-8'));
    assert.deepEqual(transcripts.records[`${order[0]}#1`], partial.records[`${order[0]}#1`]);
    const fixture = JSON.parse(readFileSync(FIXTURE, 'utf-8'));
    const redone = transcripts.records[`${second}#1`];
    assert.equal(redone.steps[0].turn, 1);
    assert.equal(redone.turns, fixture.scripts[second].length);

    // Report shape: baseline-text2sql.mjs's fields plus the agent's counts.
    assert.equal(report.identity.condition, 'agent-ddl');
    assert.equal(report.run.layer, 'agent-ddl');
    assert.equal(report.provenance.realProviderQualityEligible, false);
    assert.ok(report.identity.notPublishableBecause.some((reason) => /fake provider/.test(reason)));
    assert.equal(report.results.length, 2);
    for (const result of report.results) {
      assert.equal(result.passed, true, result.name);
      assert.equal(result.executionMatched, true);
      assert.equal(result.answer.trustState, 'none');
      assert.equal(result.providerDispatchCount, result.turns);
      for (const field of ['toolCalls', 'sqlStatementsRun', 'totalMs', 'finalSql']) assert.ok(result[field] !== undefined, field);
    }
    const expense = report.results.find((result) => result.name === EXPENSE);
    assert.equal(expense.turns, 7);
    assert.equal(expense.toolCalls, 4);
    assert.equal(expense.sqlStatementsRun, 3); // the failed run_sql and both final_sql checks
    assert.equal(expense.protocolErrors, 1);

    // Each turn carries the transcript so far: the 7th prompt holds turn 1's error and the DDL.
    const lastPrompt = transcripts.records[`${EXPENSE}#1`].steps.at(-1).prompt;
    assert.match(lastPrompt, /expense_payments does not exist/);
    assert.match(lastPrompt, /Your final query did not run/);
    assert.match(lastPrompt, /CREATE TABLE claim_amount/);
    assert.match(lastPrompt, /Reply 7 of 12/);

    // Replay grades the saved transcripts again without asking anyone.
    const replayed = await main([...args, '--replay']);
    assert.deepEqual(replayed.results.map((r) => r.passed), report.results.map((r) => r.passed));
    // A resumed run must use the settings it started with.
    await assert.rejects(() => main([...args, '--max-turns', '5']), /other settings/);
  } finally {
    process.exitCode = 0;
    rmSync(out, { recursive: true, force: true });
  }
});

test('end to end on an unanswerable question, warehouse only (W0), no context: CANNOT_ANSWER is a correct stop', { skip }, async () => {
  const out = mkdtempSync(join(tmpdir(), 'agent-unans-'));
  try {
    const report = await main(['--run', 'test', '--set', 'unanswerable', '--only', CREDIT, '--context', 'none', '--level', 'W0', '--provider', 'fake', '--fixture', FIXTURE, '--out', out]);
    assert.equal(report.results.length, 1);
    const [result] = report.results;
    assert.equal(result.passed, true);
    assert.equal(result.kind, 'no_answer');
    assert.equal(result.stop, 'cannot_answer');
    assert.equal(result.answer.declineReason, 'no table or column records a credit score');
    assert.equal(report.run.warehouse, 'W0');
    const transcripts = JSON.parse(readFileSync(join(out, 'transcripts.json'), 'utf-8'));
    assert.doesNotMatch(transcripts.records[`${CREDIT}#1`].steps[0].prompt, /Schema you were given/);
  } finally {
    process.exitCode = 0;
    rmSync(out, { recursive: true, force: true });
  }
});

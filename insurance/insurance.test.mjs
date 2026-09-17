import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { portGoldSql } from './build.mjs';
import { caseId } from './questions.mjs';
import { cassetteEvidence, evalFile, selectCases } from './run.mjs';
import { parseAudit } from '../lib/gold-audit.mjs';

test('the dialect port changes only the Snowflake date-part spelling', () => {
  const ported = portGoldSql('select avg(DATEDIFF("day", a, b)) from t where "day" = 1');
  assert.equal(ported.sql, `select avg(DATEDIFF('day', a, b)) from t where "day" = 1`);
  assert.equal(ported.applied.length, 1);
  assert.deepEqual(portGoldSql('select 1').applied, []);
});

test('case ids are stable and distinct for near-identical questions', () => {
  assert.equal(caseId('How many claims do we have?'), caseId('How many claims do we have?'));
  assert.notEqual(caseId('Return agents and the policy they sold A'), caseId('Return agents and the policy they sold B'));
});

const gold = {
  cases: [
    { id: 'a', question: 'A?', dbtLabsSelected: true, goldSql: 'select 1', gold: { rows: [[1]] } },
    { id: 'b', question: 'B?', dbtLabsSelected: false, goldSql: 'select 2', gold: { rows: [[2]], ranSql: 'select 2 -- ported' } },
    { id: 'dev', question: 'D?', dbtLabsSelected: true, goldSql: 'select 3', gold: { rows: [[3]] } },
  ],
};
const auditFor = (ids) => parseAudit(ids.map((id) => JSON.stringify({ caseId: id, status: 'accepted', reviewer: 'r', reviewedAt: '2026-09-16' })).join('\n'));

test('headline sets leave development questions out', () => {
  const audit = auditFor(['a', 'b', 'dev']);
  const dev = new Set(['dev']);
  assert.deepEqual(selectCases(gold, audit, dev, 'all').map((c) => c.id), ['a', 'b']);
  assert.deepEqual(selectCases(gold, audit, dev, 'dbt-labs').map((c) => c.id), ['a']);
  assert.deepEqual(selectCases(gold, audit, dev, 'dev').map((c) => c.id), ['dev']);
});

test('an unaudited or broken correct answer stops the run', () => {
  assert.throws(() => selectCases(gold, auditFor(['a', 'b']), new Set(), 'all'), /without an answer-key audit/);
  const broken = { cases: [{ ...gold.cases[0], gold: { error: 'boom' } }] };
  assert.throws(() => selectCases(broken, auditFor(['a']), new Set(), 'all'), /did not run/);
});

test('the eval file carries the rows that ran and allows extra columns', () => {
  const file = evalFile([gold.cases[1]]);
  assert.equal(file.cases[0].name, 'b');
  assert.equal(file.cases[0].expected.goldSql, 'select 2 -- ported');
  assert.equal(file.cases[0].expected.goldAllowExtraColumns, true);
});

test('provenance counts only real-provider recordings', () => {
  const dir = mkdtempSync(join(tmpdir(), 'cassettes-'));
  assert.equal(cassetteEvidence(dir, 'record').realProviderQualityEligible, false);
  writeFileSync(join(dir, 'a.json'), JSON.stringify({ provenance: { kind: 'recorded_provider', providerQuality: 'eligible' } }));
  assert.equal(cassetteEvidence(dir, 'record').realProviderQualityEligible, true);
  writeFileSync(join(dir, 'b.json'), JSON.stringify({ provenance: { kind: 'synthetic_fixture' } }));
  const evidence = cassetteEvidence(dir, 'record');
  assert.equal(evidence.realProviderQualityEligible, false);
  assert.deepEqual(evidence.kinds, { recorded_provider: 1, synthetic_fixture: 1 });
});

import { tableCheck, tablesIn } from './score.mjs';

test('reads table names from quoted, qualified and plain SQL', () => {
  assert.deepEqual(tablesIn('SELECT 1 FROM "acme"."main"."claim" c JOIN main.Policy p ON 1=1 left join premium on 1=1'), ['claim', 'policy', 'premium']);
  assert.deepEqual(tablesIn('select count(*) from (select 1 from claim) t'), ['claim']);
});

test('flags a right answer that skipped a table the correct query reads', () => {
  assert.deepEqual(tableCheck('select count(*) from claim', 'SELECT COUNT(*) FROM claim'), { same: true, missing: [], extra: [] });
  assert.deepEqual(
    tableCheck('select sum(policy_amount) from policy_amount', 'select sum(policy_amount) from policy join policy_amount on 1=1 join premium on 1=1'),
    { same: false, missing: ['policy', 'premium'], extra: [] },
  );
});

import { baselinePrompt, stripFence } from './baseline-text2sql.mjs';

test("the baseline keeps dbt Labs' prompt and adds only the dialect line", () => {
  const prompt = baselinePrompt('CREATE TABLE t (a int);', 'How many?');
  assert.match(prompt, /Given the database described by the following DDL:\n\s+CREATE TABLE t \(a int\);/);
  assert.match(prompt, /The database is DuckDB\./);
  assert.match(prompt, /return just the query, so it can be run\n\s+verbatim from your response\./);
  assert.match(prompt, /Here's the question:\n\s+How many\?/);
});

test('a code fence around the reply is removed, nothing else', () => {
  assert.equal(stripFence('```sql\nSELECT 1;\n```'), 'SELECT 1;');
  assert.equal(stripFence('SELECT 1;'), 'SELECT 1;');
  assert.equal(stripFence('Here: ```sql\nSELECT 1\n```'), 'Here: ```sql\nSELECT 1\n```');
});

test('names defined by a WITH clause are not counted as tables', () => {
  assert.deepEqual(tablesIn('WITH claim_totals AS (SELECT 1 FROM main.claim_amount), "p" as (select 2 from policy) SELECT * FROM claim_totals JOIN p ON true JOIN main.claim c ON true'), ['claim', 'claim_amount', 'policy']);
});

import { outcome, summarizeRepeats } from './repeats.mjs';

test('reading several runs together: averages, pooled interval and stability', () => {
  const run = (label, outcomes) => ({ label, results: outcomes.map(([name, kind, trust]) => ({
    name,
    executionMatched: kind === 'right',
    ...(kind === 'stopped' ? { kind: 'no_answer' } : { kind: 'uncertified' }),
    answer: { trustState: trust ?? 'review_required' },
  })) });
  const runs = [
    run('a', [['q1', 'right'], ['q2', 'wrong'], ['q3', 'stopped'], ['q4', 'wrong', 'governed']]),
    run('b', [['q1', 'right'], ['q2', 'right'], ['q3', 'stopped'], ['q4', 'right']]),
  ];
  const summary = summarizeRepeats(runs);
  assert.deepEqual(summary.runs.map((r) => r.right), [1, 3]);
  assert.equal(summary.meanAccuracy, 0.5);
  assert.deepEqual([summary.pooled.right, summary.pooled.total], [4, 8]);
  assert.equal(summary.stability, 0.5);
  assert.equal(summary.alwaysRight, 1);
  assert.equal(summary.alwaysWrongOrStopped, 1);
  assert.equal(summary.wrongShownAsTrustworthy, 1);
  assert.deepEqual(summary.unstable.map((row) => row.name), ['q2', 'q4']);
});

test('an outcome is what the user saw', () => {
  assert.equal(outcome({ executionMatched: true, kind: 'uncertified' }), 'right');
  assert.equal(outcome({ executionMatched: false, kind: 'no_answer' }), 'stopped');
  assert.equal(outcome({ executionMatched: false, route: 'clarify', kind: 'uncertified' }), 'stopped');
  assert.equal(outcome({ runtimeError: 'timeout' }), 'no answer');
});

import { answeredBy, measureColumnIndexes, regrade } from './regrade.mjs';

test('the measure columns of a correct answer are the ones it aggregates or names as numbers', () => {
  assert.deepEqual(measureColumnIndexes('select policy_number, sum(policy_amount) from t', ['Policy_Number', 'sum(policy_amount)']), [1]);
  assert.deepEqual(measureColumnIndexes('SELECT company_claim_number, (a.claim_amount + b.claim_amount) as LossAmount FROM t', ['Company_Claim_Number', 'LossAmount']), [1]);
  assert.deepEqual(measureColumnIndexes('select policy_number, agentid from t', ['Policy_Number', 'agentid']), []);
  // A name that identifies the thing is not the number asked for.
  assert.deepEqual(measureColumnIndexes('select policy_number, company_claim_number from t', ['Policy_Number', 'Company_Claim_Number']), []);
  assert.deepEqual(measureColumnIndexes('select party_identifier, count(x) as NoOfPolicies from t', ['Party_Identifier', 'NoOfPolicies']), [1]);
  assert.deepEqual(measureColumnIndexes('select avg(DATEDIFF(\'day\', a, b)) from t', ['avg(datediff)']), [0]);
});

test('an answer is attributed to the path that produced it', () => {
  assert.equal(answeredBy({ answer: { tier: 'certified' } }), 'certified block');
  assert.equal(answeredBy({ answer: { tier: 'semantic' } }), 'governed metric');
  assert.equal(answeredBy({ answer: { tier: 'exploratory' } }), 'AI-written SQL');
  assert.equal(answeredBy({ kind: 'no_answer' }), 'stopped');
  assert.equal(answeredBy({ answer: {} }), 'no SQL recorded');
});

test('grading the same answers strictly and leniently', () => {
  const gold = { cases: [
    { id: 'a', quadrant: 'HQLS', dbtLabsSelected: true, goldSql: 'select party_identifier, sum(policy_amount) from t', gold: { columns: ['Party_Identifier', 'sum(policy_amount)'], rows: [[1, 98000]] } },
    { id: 'b', quadrant: 'LQLS', dbtLabsSelected: false, goldSql: 'select 2 from policy', gold: { columns: ['n'], rows: [[2]] } },
  ] };
  const report = { run: { layer: 'L3', id: 'r' }, results: [
    // Right values, missing the id column: strict no, lenient yes.
    { name: 'a', executionMatched: false, answer: { tier: 'semantic', trustState: 'governed', sql: 'select total' } },
    { name: 'b', executionMatched: true, answer: { tier: 'exploratory', trustState: 'review_required', sql: 'select 2 from main.policy' } },
  ] };
  const rows = regrade(report, gold, { 'select total': { rows: [[98000]] }, 'select 2 from main.policy': { rows: [[2]] } });
  // a: the number is right, the id column the correct answer has is missing.
  // b: a listing question with no measure keeps its strict verdict.
  assert.deepEqual(rows.map((row) => [row.id, row.strict, row.measures, row.answeredBy]), [
    ['a', false, true, 'governed metric'],
    ['b', true, true, 'AI-written SQL'],
  ]);
  assert.equal(rows[1].tables.same, true);
  assert.equal(rows[0].rerunAgrees, true);
});

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { acceptedCaseIds, parseAudit, unauditedCases } from './gold-audit.mjs';

const line = (entry) => JSON.stringify({ reviewer: 'kk', reviewedAt: '2026-09-16', ...entry });

test('accepted, disputed and corrected entries parse', () => {
  const audit = parseAudit([
    line({ caseId: 'a', status: 'accepted' }),
    line({ caseId: 'b', status: 'disputed', reason: 'gold counts refunds as revenue' }),
    line({ caseId: 'c', status: 'corrected', reason: 'join duplicates rows', evidenceSql: 'select 1' }),
    '',
  ].join('\n'));
  assert.deepEqual(audit.problems, []);
  assert.equal(audit.entries.size, 3);
  assert.deepEqual([...acceptedCaseIds(audit)], ['a']);
});

test('a dispute without a reason is rejected', () => {
  const audit = parseAudit(line({ caseId: 'b', status: 'disputed' }));
  assert.match(audit.problems[0], /needs a reason/);
});

test('a correction must carry its reference SQL', () => {
  const audit = parseAudit(line({ caseId: 'c', status: 'corrected', reason: 'wrong grain' }));
  assert.match(audit.problems[0], /needs evidenceSql/);
});

test('duplicates, bad statuses, bad dates and bad JSON are all reported', () => {
  const audit = parseAudit([
    line({ caseId: 'a', status: 'accepted' }),
    line({ caseId: 'a', status: 'accepted' }),
    line({ caseId: 'b', status: 'maybe' }),
    JSON.stringify({ caseId: 'c', status: 'accepted', reviewer: 'kk', reviewedAt: 'soon' }),
    '{not json',
  ].join('\n'));
  assert.equal(audit.problems.length, 4);
});

test('unaudited cases are listed so a scorer can stop', () => {
  const audit = parseAudit(line({ caseId: 'a', status: 'accepted' }));
  assert.deepEqual(unauditedCases(['a', 'b'], audit), ['b']);
});

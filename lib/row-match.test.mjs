import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalizeValue, rowsMatch, valuesCovered } from './row-match.mjs';

test('column names do not matter', () => {
  const gold = [{ region: 'East', total: 10 }, { region: 'West', total: 20 }];
  const actual = [{ region_name: 'West', revenue: 20 }, { region_name: 'East', revenue: 10 }];
  assert.deepEqual(rowsMatch(actual, gold), { match: true });
});

test('column order does not matter', () => {
  assert.equal(rowsMatch([[10, 'East']], [{ region: 'East', total: 10 }]).match, true);
});

test('numbers compare by value within tolerance', () => {
  assert.equal(rowsMatch([{ x: 0.1 + 0.2 }], [{ x: 0.3 }]).match, true);
  assert.equal(rowsMatch([{ x: '10.0' }], [{ x: 10 }]).match, true);
  assert.equal(rowsMatch([{ x: 10n }], [{ x: 10 }]).match, true);
  assert.equal(rowsMatch([{ x: 10.01 }], [{ x: 10 }]).match, false);
});

test('a date matches a midnight timestamp of the same day, not a later time', () => {
  assert.equal(rowsMatch([{ d: '2025-08-01T00:00:00Z' }], [{ d: '2025-08-01' }]).match, true);
  assert.equal(rowsMatch([{ d: '2025-08-01 00:00:00' }], [{ d: '2025-08-01' }]).match, true);
  assert.equal(rowsMatch([{ d: '2025-08-01T13:00:00' }], [{ d: '2025-08-01' }]).match, false);
});

test('duplicate rows must appear the same number of times', () => {
  const gold = [{ a: 1 }, { a: 1 }, { a: 2 }];
  assert.equal(rowsMatch([{ a: 1 }, { a: 2 }, { a: 2 }], gold).match, false);
  assert.equal(rowsMatch([{ a: 2 }, { a: 1 }, { a: 1 }], gold).match, true);
});

test('row count mismatches are reported', () => {
  const result = rowsMatch([{ a: 1 }], [{ a: 1 }, { a: 2 }]);
  assert.equal(result.match, false);
  assert.match(result.reason, /row count 1 does not match gold 2/);
});

test('ordered comparison requires the same order', () => {
  const gold = [{ a: 1 }, { a: 2 }];
  assert.equal(rowsMatch([{ a: 2 }, { a: 1 }], gold, { ordered: true }).match, false);
  assert.equal(rowsMatch([{ a: 1 }, { a: 2 }], gold, { ordered: true }).match, true);
});

test('extra result columns are allowed only when asked', () => {
  const gold = [{ total: 10 }, { total: 20 }];
  const actual = [{ id: 7, name: 'East', total: 10 }, { id: 8, name: 'West', total: 20 }];
  assert.equal(rowsMatch(actual, gold).match, false);
  assert.equal(rowsMatch(actual, gold, { allowExtraColumns: true }).match, true);
});

test('extra-column matching still checks values row by row', () => {
  const gold = [{ region: 'East', total: 10 }, { region: 'West', total: 20 }];
  // Each column on its own matches gold, but the pairing is swapped.
  const actual = [{ region: 'East', total: 20, extra: 1 }, { region: 'West', total: 10, extra: 2 }];
  assert.equal(rowsMatch(actual, gold, { allowExtraColumns: true }).match, false);
});

test('empty results match only empty gold', () => {
  assert.equal(rowsMatch([], []).match, true);
  assert.equal(rowsMatch([], [{ a: 1 }]).match, false);
});

test('null, booleans and text are distinguished', () => {
  assert.notEqual(normalizeValue(null), normalizeValue('null'));
  assert.notEqual(normalizeValue(true), normalizeValue('true'));
  assert.equal(normalizeValue('  East '), normalizeValue('East'));
});

test('the lenient reading asks only that every correct value is present', () => {
  const gold = [[1, 98000]];
  // The right total without the id column the question implies: lenient passes, strict does not.
  assert.equal(valuesCovered([[98000]], gold).match, false);
  assert.equal(valuesCovered([[98000, 1]], gold).match, true);
  assert.equal(valuesCovered([['1', 98000.0000001, 'extra']], gold).match, true);
  assert.equal(rowsMatch([[98000, 1, 'extra']], gold).match, false);
  // A wrong number is wrong either way.
  assert.equal(valuesCovered([[1, 86000]], gold).match, false);
  assert.match(valuesCovered([[1, 86000]], gold).reason, /1 value\(s\)/);
  // Duplicates must be present as often as the correct answer has them.
  assert.equal(valuesCovered([[5]], [[5], [5]]).match, false);
  assert.equal(valuesCovered([[5], [5]], [[5], [5]]).match, true);
});

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mcnemarExact, mean, pairedDifference, quantile, wilsonInterval } from './stats.mjs';

const close = (actual, expected, tolerance = 1e-4) => assert.ok(
  Math.abs(actual - expected) <= tolerance,
  `expected ${expected}, got ${actual}`,
);

test('Wilson interval matches the textbook value for 8 of 10', () => {
  const { low, high } = wilsonInterval(8, 10);
  close(low, 0.4902);
  close(high, 0.9433);
});

test('Wilson interval stays inside [0, 1] at the extremes', () => {
  const none = wilsonInterval(0, 20);
  assert.equal(none.low, 0);
  assert.ok(none.high > 0 && none.high < 0.2);
  const all = wilsonInterval(20, 20);
  assert.equal(all.high, 1);
  assert.ok(all.low > 0.8 && all.low < 1);
  assert.deepEqual(wilsonInterval(0, 0), { low: 0, high: 1 });
});

test('Wilson interval rejects impossible counts', () => {
  assert.throws(() => wilsonInterval(5, 4));
  assert.throws(() => wilsonInterval(-1, 4));
  assert.throws(() => wilsonInterval(1.5, 4));
});

test('exact McNemar: no disagreement is no evidence', () => {
  assert.equal(mcnemarExact(0, 0), 1);
  assert.equal(mcnemarExact(3, 3), 1);
});

test('exact McNemar matches the binomial tail', () => {
  // 1 vs 9 discordant: 2 * (C(10,0) + C(10,1)) / 2^10 = 22 / 1024.
  close(mcnemarExact(1, 9), 22 / 1024, 1e-12);
  close(mcnemarExact(9, 1), 22 / 1024, 1e-12);
  // 0 vs 5: 2 / 32.
  close(mcnemarExact(0, 5), 2 / 32, 1e-12);
});

test('exact McNemar stays finite for large benchmarks', () => {
  const p = mcnemarExact(40, 110);
  assert.ok(p > 0 && p < 1e-8, `p = ${p}`);
});

test('paired difference is centered on (c - b) / N', () => {
  const result = pairedDifference(2, 12, 68);
  close(result.difference, 10 / 68, 1e-12);
  assert.ok(result.low < result.difference && result.difference < result.high);
  assert.deepEqual(pairedDifference(0, 0, 10), { difference: 0, low: 0, high: 0 });
});

test('quantile and mean ignore missing values', () => {
  assert.equal(quantile([], 0.5), null);
  assert.equal(quantile([1, 2, 3, 4], 0.5), 2.5);
  assert.equal(quantile([5, null, 1], 0.95), 4.8);
  assert.equal(mean([1, null, 3]), 2);
  assert.equal(mean([null]), null);
});

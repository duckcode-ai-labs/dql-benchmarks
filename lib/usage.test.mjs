import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attributeUsage, priceUsage } from './usage.mjs';
import { costLine } from '../insurance/score.mjs';

const pricing = { asOf: '2026-09-18', models: { 'm-priced': { inputPerMillion: 3, outputPerMillion: 15, cacheReadPerMillion: 0.3, cacheWritePerMillion: 3.75 }, 'm-unchecked': { inputPerMillion: null, outputPerMillion: null } } };

test('a call is priced at list price, and not at all without a checked price', () => {
  assert.equal(priceUsage({ inputTokens: 1_000_000, outputTokens: 100_000 }, 'm-priced', pricing), 4.5);
  assert.equal(priceUsage({ inputTokens: 10, outputTokens: 10 }, 'm-unchecked', pricing), null);
  assert.equal(priceUsage({ inputTokens: 10, outputTokens: 10 }, 'unknown-model', pricing), null);
});

test('calls belong to the question whose time span holds them; the rest are counted apart', () => {
  const spans = [
    { question: 'Q1', start: Date.parse('2026-09-18T10:00:00Z'), end: Date.parse('2026-09-18T10:00:30Z') },
    { question: 'Q2', start: Date.parse('2026-09-18T10:00:31Z'), end: Date.parse('2026-09-18T10:01:00Z') },
  ];
  const lines = [
    { at: '2026-09-18T09:59:00Z', model: 'm-priced', inputTokens: 5, outputTokens: 5 },
    { at: '2026-09-18T10:00:10Z', model: 'm-priced', inputTokens: 1_000_000, outputTokens: 0 },
    { at: '2026-09-18T10:00:20Z', model: 'm-priced', inputTokens: 0, outputTokens: 100_000 },
    { at: '2026-09-18T10:00:40Z', model: 'm-unchecked', inputTokens: 10, outputTokens: 10 },
  ];
  const usage = attributeUsage(lines, spans, pricing);
  assert.equal(usage.byQuestion.Q1.calls, 2);
  assert.equal(usage.byQuestion.Q1.costUsd, 4.5);
  assert.equal(usage.byQuestion.Q2.costUsd, null);
  assert.equal(usage.outside.calls, 1);
  assert.equal(usage.totalCostUsd, null);
  assert.match(costLine(usage, 2), /prices not checked/);
  const priced = attributeUsage(lines.slice(0, 3), spans, pricing);
  assert.match(costLine(priced, 2), /cost \$4\.50 in all, \$2\.2500 per question at list prices of 2026-09-18/);
});

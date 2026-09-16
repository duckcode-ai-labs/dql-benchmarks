import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseAudit } from '../lib/gold-audit.mjs';
import { pairedCompare, renderMarkdown } from './paired-compare.mjs';

const identity = { publishable: true, notPublishableBecause: [] };
const evidence = { realProviderQualityEligible: true, realProviderQualityExclusionReasons: [] };

// Mirrors the JSON printed by `dql agent eval --format json`.
function evalReport(outcomes, extra = {}) {
  return {
    identity,
    cassetteEvidence: evidence,
    results: Object.entries(outcomes).map(([name, passed], index) => ({
      name,
      passed,
      durationMs: 1000 * (index + 1),
      providerDispatchCount: 2,
      ...extra,
    })),
  };
}

const ids = Array.from({ length: 10 }, (_, index) => `q${index}`);
const baseline = Object.fromEntries(ids.map((id, index) => [id, index === 0]));
const challenger = Object.fromEntries(ids.map((id) => [id, true]));

test('a report compared with itself shows no difference', () => {
  const result = pairedCompare([
    { label: 'a', report: evalReport(challenger) },
    { label: 'b', report: evalReport(challenger) },
  ]);
  const [comparison] = result.subsets[0].comparisons;
  assert.equal(comparison.mcnemarP, 1);
  assert.equal(comparison.difference.difference, 0);
  assert.deepEqual(result.subsets[0].conditions[0].ci95, result.subsets[0].conditions[1].ci95);
});

test('discordant pairs drive the test', () => {
  const result = pairedCompare([
    { label: 'raw', report: evalReport(baseline) },
    { label: 'modeled', report: evalReport(challenger) },
  ]);
  const [raw, modeled] = result.subsets[0].conditions;
  assert.equal(raw.correct, 1);
  assert.equal(modeled.correct, 10);
  const [comparison] = result.subsets[0].comparisons;
  assert.equal(comparison.onlyChallengerCorrect, 9);
  assert.equal(comparison.onlyBaselineCorrect, 0);
  assert.ok(Math.abs(comparison.mcnemarP - 2 / 512) < 1e-12);
  assert.ok(Math.abs(comparison.difference.difference - 0.9) < 1e-12);
  assert.match(renderMarkdown(result), /modeled vs raw:\*\* \+90\.0 points/);
});

test('reports over different questions are refused', () => {
  const shorter = Object.fromEntries(ids.slice(1).map((id) => [id, true]));
  assert.throws(
    () => pairedCompare([
      { label: 'a', report: evalReport(baseline) },
      { label: 'b', report: evalReport(shorter) },
    ]),
    /does not answer the same questions.*missing: q0/,
  );
});

test('unrecorded or synthetic runs are refused unless explicitly allowed, then labelled', () => {
  const synthetic = { ...evalReport(challenger), cassetteEvidence: { realProviderQualityEligible: false, realProviderQualityExclusionReasons: ['synthetic fixture'] } };
  const inputs = [
    { label: 'a', report: evalReport(baseline) },
    { label: 'b', report: synthetic },
  ];
  assert.throws(() => pairedCompare(inputs), /Not comparable for publication[\s\S]*synthetic fixture/);
  const result = pairedCompare(inputs, { allowUnpublishable: true });
  assert.equal(result.publishable, false);
  assert.match(renderMarkdown(result), /^> \*\*Not publishable\.\*\*/);
});

test('a report without an identity block is not publishable', () => {
  const { identity: _dropped, ...bare } = evalReport(baseline);
  assert.throws(
    () => pairedCompare([{ label: 'a', report: bare }, { label: 'b', report: evalReport(challenger) }]),
    /no identity block/,
  );
});

test('the audit adds an accepted-only subset and refuses unaudited cases', () => {
  const inputs = [
    { label: 'a', report: evalReport(baseline) },
    { label: 'b', report: evalReport(challenger) },
  ];
  const partial = parseAudit(JSON.stringify({ caseId: 'q0', status: 'accepted', reviewer: 'kk', reviewedAt: '2026-09-16' }));
  assert.throws(() => pairedCompare(inputs, { audit: partial }), /9 case\(s\) have no gold-audit line/);

  const audit = parseAudit(ids.map((id, index) => JSON.stringify({
    caseId: id,
    status: index < 7 ? 'accepted' : 'disputed',
    ...(index < 7 ? {} : { reason: 'gold is wrong' }),
    reviewer: 'kk',
    reviewedAt: '2026-09-16',
  })).join('\n'));
  const result = pairedCompare(inputs, { audit });
  assert.deepEqual(result.subsets.map((subset) => [subset.name, subset.n]), [['all', 10], ['accepted', 7]]);
});

test('cost is shown only when every question measured it', () => {
  const partialCost = evalReport(challenger);
  partialCost.results[0].costUsd = 0.01;
  const full = evalReport(challenger, { costUsd: 0.02 });
  const result = pairedCompare([
    { label: 'partial', report: partialCost },
    { label: 'full', report: full },
  ]);
  const [partial, measured] = result.subsets[0].conditions;
  assert.equal(partial.costPerQuestionUsd, null);
  assert.ok(Math.abs(measured.costPerQuestionUsd - 0.02) < 1e-12);
});

test('wrong answers labelled certified are counted', () => {
  const report = evalReport({ q0: false, q1: false, q2: true });
  report.results[0].trustState = 'certified';
  report.results[1].trustState = 'review_required';
  const result = pairedCompare([
    { label: 'a', report },
    { label: 'b', report: evalReport({ q0: true, q1: true, q2: true }) },
  ]);
  assert.equal(result.subsets[0].conditions[0].wrongCertified, 1);
});

test('the execution metric reads executionMatched', () => {
  const report = evalReport({ q0: true });
  assert.throws(
    () => pairedCompare([{ label: 'a', report }, { label: 'b', report }], { metric: 'execution' }),
    /no executionMatched result/,
  );
});

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { parseEvaluateOutput } from './precheck.mjs';
import { submissionRecord, writeSubmission } from './submission.mjs';

test('submission records use the shape evaluate.py reads', () => {
  assert.deepEqual(submissionRecord('airbnb001', 'airbnb.duckdb'), {
    instance_id: 'airbnb001',
    answer_type: 'file',
    answer_or_path: 'airbnb.duckdb',
  });
});

test('every task is listed, including those with no output database', () => {
  const root = mkdtempSync(join(tmpdir(), 'spider2-submission-'));
  try {
    const source = join(root, 'out.duckdb');
    writeFileSync(source, 'db');
    const written = writeSubmission(join(root, 'submission'), [
      { instanceId: 'a001', database: 'a.duckdb' },
      { instanceId: 'b001', database: 'b.duckdb' },
    ], (task) => (task.instanceId === 'a001' ? source : null));
    assert.deepEqual(written, { listed: 2, missing: ['b001'] });
    const lines = readFileSync(join(root, 'submission', 'results_metadata.jsonl'), 'utf-8').trim().split('\n');
    assert.equal(lines.length, 2);
    assert.deepEqual(readdirSync(join(root, 'submission')).sort(), ['a001', 'results_metadata.jsonl']);
    assert.equal(readFileSync(join(root, 'submission', 'a001', 'a.duckdb'), 'utf-8'), 'db');
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

const sampleOutput = [
  '68',
  "{'instance_id': 'mrr001', 'score': 1}",
  'mrr001',
  'retail001',
  '0.029411764705882353 2 68',
].join('\n');

test('grader output yields the passing ids and the listed count', () => {
  const parsed = parseEvaluateOutput(sampleOutput, ['mrr001', 'retail001', 'airbnb001']);
  assert.deepEqual([...parsed.passed].sort(), ['mrr001', 'retail001']);
  assert.equal(parsed.listed, 68);
});

test('grader output that disagrees with itself is refused', () => {
  assert.throws(
    () => parseEvaluateOutput(sampleOutput, ['mrr001']),
    /reported 2 passes but printed 1/,
  );
  assert.throws(() => parseEvaluateOutput('no summary here', []), /did not print a summary line/);
});

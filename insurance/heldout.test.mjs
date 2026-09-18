import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkHeldout, heldoutId } from './heldout.mjs';
import { renderSealed } from './score.mjs';

test('a held-out file needs a question, one SELECT and a known quadrant per entry', () => {
  assert.deepEqual(checkHeldout({ questions: [{ question: 'How many claims?', goldSql: 'select count(*) from claim', quadrant: 'LQLS' }] }), []);
  const problems = checkHeldout({ questions: [
    { question: 'A?', goldSql: 'delete from claim', quadrant: 'LQLS' },
    { question: 'B?', goldSql: 'select 1', quadrant: 'XX' },
    { question: 'B?', goldSql: 'select 1', quadrant: 'LQLS' },
  ] });
  assert.equal(problems.length, 3);
  assert.match(problems.join('\n'), /one SELECT[\s\S]*quadrant[\s\S]*duplicate/);
  assert.match(heldoutId('How many claims?'), /^heldout-how-many-claims-[0-9a-f]{6}$/);
});

test('a sealed scorecard keeps totals and names no question', () => {
  const markdown = [
    '### Accuracy', '', '| Questions | Right | Accuracy | 95% CI |', '|---|---:|---:|---|', '| All | 1/2 | 50.0% | x |', '',
    '### Right answers that read different tables than the correct query', '', '- `heldout-secret-one-abc123`: missing claim', '',
    '### Every question', '', '| Question | Quadrant | Outcome |', '| Secret question two? | LQLS | wrong |', '',
    '| Question | Outcome | Trust |', '|---|---|---|', '| Secret question three? | answered anyway | none |', '',
  ].join('\n');
  const sealed = renderSealed(markdown);
  assert.match(sealed, /\| Questions \| Right \| Accuracy/);
  assert.match(sealed, /\| All \| 1\/2 \|/);
  assert.doesNotMatch(sealed, /Secret|secret/);
});

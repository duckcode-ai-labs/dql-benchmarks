import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseTurtle, subjects } from './turtle.mjs';

const SAMPLE = `@prefix ex: <http://example.org/> .
@prefix dct: <http://purl.org/dc/terms/> .

ex:q1
        a              ex:Query ;
        ex:text        "SELECT \\"x\\"\\nFROM t" ;
        ex:links       ex:a , ex:b ;
        dct:title      """long
string""" .
`;

test('reads prefixed names, escapes, lists and long strings', () => {
  const { triples } = parseTurtle(SAMPLE);
  const graph = subjects(triples);
  const q1 = graph.get('http://example.org/q1');
  assert.equal(q1.get('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')[0].value, 'http://example.org/Query');
  assert.equal(q1.get('http://example.org/text')[0].value, 'SELECT "x"\nFROM t');
  assert.deepEqual(q1.get('http://example.org/links').map((o) => o.value), ['http://example.org/a', 'http://example.org/b']);
  assert.equal(q1.get('http://purl.org/dc/terms/title')[0].value, 'long\nstring');
});

test('refuses what it does not understand', () => {
  assert.throws(() => parseTurtle('@prefix ex: <http://e/> .\nex:a ex:b [ ex:c 1 ] .'), /blank nodes/);
  assert.throws(() => parseTurtle('@prefix ex: <http://e/> .\nex:a ex:b "x"@en .'), /language-tagged/);
  assert.throws(() => parseTurtle('ex:a ex:b ex:c .'), /undeclared prefix/);
  assert.throws(() => parseTurtle('@prefix ex: <http://e/> .\nex:a ex:b "open'), /unterminated|newline/);
});

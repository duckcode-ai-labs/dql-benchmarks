// Read the insurance benchmark questions from the publishers' Turtle files.
//
// Each question is a data.world `dwt:SqlQuery`: `dct:description` is the
// question, `QandA:queryText` is its correct SQL and `dct:title` starts with
// the paper's complexity quadrant ("HQLS: ..." = high question complexity,
// low schema complexity). This is how dbt Labs' own loader reads the file
// (llm_bench/utils/challenge_loader.py selects ?title ?description ?queryText
// from dwt:SqlQuery), so the question text here is the text their runs used.

import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { parseTurtle, subjects } from '../lib/turtle.mjs';

const RDF_TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type';
const SQL_QUERY = 'https://templates.data.world/SqlQuery';
const INQUIRY = 'http://models.data.world/benchmarks/QandA#Inquiry';
const QUERY_TEXT = 'http://models.data.world/benchmarks/QandA#queryText';
const EXPECTS = 'http://models.data.world/benchmarks/QandA#expects';
const PROMPT = 'http://models.data.world/benchmarks/QandA#prompt';
const DESCRIPTION = 'http://purl.org/dc/terms/description';
const TITLE = 'http://purl.org/dc/terms/title';

export const QUADRANTS = {
  LQLS: 'low question complexity, low schema complexity',
  LQHS: 'low question complexity, high schema complexity',
  HQLS: 'high question complexity, low schema complexity',
  HQHS: 'high question complexity, high schema complexity',
};

/** dbt Labs' 11 questions, copied from dbt-llm-sl-bench src/llm_bench/config/base.py (selected_challenges). */
export const DBT_LABS_SELECTED = [
  'What is the total amount of premiums that a policy holder has paid by policy number?',
  'What is the average time to settle a claim by policy number?',
  'What is the total amount of premiums that a policy holder has paid?',
  'How many policies have agents sold by agent id?',
  'What is the total loss amounts, which is the sum of loss payment, loss reserve amount by claim number?',
  'How many policies does each policy holder have by policy holder id?',
  'What is the total amount of premiums paid by policy number?',
  'How many claims have been placed by policy number?',
  'What is the average policy size which is the the total amount of premium divided by the number of policies?',
  'How many policies do we have?',
  'How many claims do we have?',
];

const one = (predicates, predicate) => predicates.get(predicate)?.[0]?.value;

/** A short, stable case id from the question text. */
export function caseId(question) {
  const slug = question.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48).replace(/-$/, '');
  const hash = createHash('sha256').update(question).digest('hex').slice(0, 6);
  return `${slug}-${hash}`;
}

/** Every SQL question in a question file, in file order. */
export function readQuestions(file) {
  const graph = subjects(parseTurtle(readFileSync(file, 'utf8')).triples);
  const inquiryOf = new Map();
  for (const [subject, predicates] of graph) {
    if (!(predicates.get(RDF_TYPE) ?? []).some((o) => o.value === INQUIRY)) continue;
    for (const expected of predicates.get(EXPECTS) ?? []) {
      inquiryOf.set(expected.value, { id: subject, prompt: one(predicates, PROMPT) });
    }
  }
  const questions = [];
  for (const [subject, predicates] of graph) {
    if (!(predicates.get(RDF_TYPE) ?? []).some((o) => o.value === SQL_QUERY)) continue;
    const question = one(predicates, DESCRIPTION);
    const title = one(predicates, TITLE) ?? '';
    const quadrant = /^([LH]Q[LH]S)\b/.exec(title)?.[1] ?? null;
    const inquiry = inquiryOf.get(subject) ?? null;
    questions.push({
      id: caseId(question),
      queryId: subject.replace(/^.*\//, ''),
      question,
      title,
      quadrant,
      goldSql: one(predicates, QUERY_TEXT),
      inquiryId: inquiry?.id.replace(/^.*\//, '') ?? null,
      inquiryPrompt: inquiry?.prompt ?? null,
    });
  }
  return questions;
}

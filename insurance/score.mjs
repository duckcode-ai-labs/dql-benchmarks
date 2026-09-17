#!/usr/bin/env node
// The scorecard for one insurance run (see docs/methodology.md, "The scorecard").
//
//   node insurance/score.mjs work/insurance/runs/<run>/<layer>/<set>/report.json [--json out.json]
//
// Prints a Markdown scorecard: accuracy (all, audited, by quadrant, dbt Labs'
// 11), trust against correctness, refusals and runtime errors, speed and AI
// calls, data sent to the model, and answers that matched while reading
// different tables than the correct query (possible chance matches on this
// very small dataset).

import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { acceptedCaseIds, loadAudit } from '../lib/gold-audit.mjs';
import { mean, quantile, wilsonInterval } from '../lib/stats.mjs';
import { QUADRANTS } from './questions.mjs';

/** Table names a statement reads, without database/schema or quoting, lower case. */
export function tablesIn(sql) {
  if (!sql) return [];
  const names = new Set();
  // Names a WITH clause defines are the statement's own, not tables.
  const cteNames = new Set([...sql.matchAll(/(?:\bwith\s+(?:recursive\s+)?|,\s*)("?[A-Za-z_][\w$]*"?)\s+as\s*\(/gi)].map((match) => match[1].replace(/"/g, '').toLowerCase()));
  const pattern = /\b(?:from|join)\s+((?:"[^"]+"|[A-Za-z_][\w$]*)(?:\s*\.\s*(?:"[^"]+"|[A-Za-z_][\w$]*))*)/gi;
  for (const match of sql.matchAll(pattern)) {
    const parts = match[1].split('.').map((part) => part.trim().replace(/^"|"$/g, ''));
    const name = parts[parts.length - 1].toLowerCase();
    if (name && name !== 'select' && name !== 'lateral' && !(parts.length === 1 && cteNames.has(name))) names.add(name);
  }
  return [...names].sort();
}

/** How an answer's tables compare with the correct query's. */
export function tableCheck(answerSql, goldSql) {
  const answer = new Set(tablesIn(answerSql));
  const gold = tablesIn(goldSql);
  const missing = gold.filter((name) => !answer.has(name));
  const extra = [...answer].filter((name) => !gold.includes(name));
  return { same: missing.length === 0 && extra.length === 0, missing, extra };
}

function outcomeOf(result) {
  if (result.runtimeError) return 'no answer (runtime error)';
  if (result.route === 'clarify' || result.clarificationOptionCount > 0) return 'asked to clarify';
  if (result.kind === 'no_answer') return 'declined';
  return result.executionMatched ? 'right' : 'wrong';
}

const pct = (k, n) => (n ? `${((k / n) * 100).toFixed(1)}%` : '—');
const ci = (k, n) => {
  if (!n) return '—';
  const { low, high } = wilsonInterval(k, n);
  return `${(low * 100).toFixed(1)}–${(high * 100).toFixed(1)}%`;
};
const secs = (ms) => (ms === null || ms === undefined ? '—' : `${(ms / 1000).toFixed(1)} s`);

/** Questions the data cannot answer: stopping is right, answering is not. */
export function renderUnanswerable(report) {
  const lines = [`## ${report.run.layer} · unanswerable questions · run ${report.run.id}`, ''];
  const rows = report.results.map((result) => ({
    question: result.name,
    outcome: outcomeOf({ ...result, executionMatched: false }).replace('wrong', 'answered anyway'),
    trust: result.answer?.trustState ?? 'none',
    sql: result.answer?.sql ?? '',
  }));
  const stopped = rows.filter((row) => row.outcome === 'declined' || row.outcome === 'asked to clarify').length;
  const answered = rows.filter((row) => row.outcome === 'answered anyway');
  lines.push(`**Stopped correctly: ${stopped}/${rows.length}** (declined or asked back). Answered anyway: ${answered.length}, of which labelled certified: ${answered.filter((row) => row.trust === 'certified').length}.`, '');
  lines.push('| Question | Outcome | Trust |', '|---|---|---|');
  for (const row of rows) lines.push(`| ${row.question} | ${row.outcome} | ${row.trust} |`);
  lines.push('');
  return lines.join('\n');
}

export function scorecard(report, gold, audit) {
  const byId = new Map(gold.cases.map((c) => [c.id, c]));
  const accepted = acceptedCaseIds(audit);
  const rows = report.results.map((result) => {
    const question = byId.get(result.name);
    if (!question) throw new Error(`Unknown question ${result.name}`);
    const right = result.executionMatched === true;
    return {
      id: result.name,
      question: question.question,
      quadrant: question.quadrant,
      dbtLabs: question.dbtLabsSelected,
      accepted: accepted.has(result.name),
      right,
      outcome: outcomeOf(result),
      trust: result.answer?.trustState ?? 'none',
      tier: result.answer?.tier ?? null,
      durationMs: result.durationMs,
      dispatches: result.providerDispatchCount ?? null,
      egress: result.answer?.egress ?? null,
      reason: result.goldMatchReason ?? result.runtimeError ?? null,
      tables: right && result.answer?.sql ? tableCheck(result.answer.sql, question.gold.ranSql ?? question.goldSql) : null,
    };
  });
  return { identity: report.identity, provenance: report.provenance, run: report.run, rows };
}

function accuracyLine(label, rows) {
  const k = rows.filter((row) => row.right).length;
  return `| ${label} | ${k}/${rows.length} | ${pct(k, rows.length)} | ${ci(k, rows.length)} |`;
}

export function renderScorecard(card) {
  const { rows } = card;
  const lines = [];
  const reasons = [
    ...(card.identity?.notPublishableBecause ?? []),
    ...(card.provenance?.realProviderQualityEligible ? [] : (card.provenance?.reasons ?? ['no recorded-provider evidence'])),
  ];
  lines.push(`## ${card.run.layer} · ${card.run.set} · run ${card.run.id}`, '');
  lines.push(`DQL ${card.identity.dql.version} (${card.identity.dql.source}${card.identity.dql.commit ? ` @ ${card.identity.dql.commit.slice(0, 8)}` : ''}) · ${card.identity.provider} / ${card.identity.model} · harness ${card.identity.repoCommit?.slice(0, 7)}${card.identity.repoDirty ? ' (uncommitted changes)' : ''} · ${card.run.startedAt}`, '');
  if (reasons.length) lines.push(`> **Not publishable:** ${reasons.join('; ')}.`, '');

  lines.push('### Accuracy', '', '| Questions | Right | Accuracy | 95% CI |', '|---|---:|---:|---|');
  lines.push(accuracyLine('All', rows));
  lines.push(accuracyLine('Accepted answer key', rows.filter((row) => row.accepted)));
  lines.push(accuracyLine("dbt Labs' 11", rows.filter((row) => row.dbtLabs)));
  for (const quadrant of Object.keys(QUADRANTS)) lines.push(accuracyLine(`${quadrant} (${QUADRANTS[quadrant]})`, rows.filter((row) => row.quadrant === quadrant)));
  lines.push('');

  lines.push('### What each answer was', '', '| Outcome | Questions |', '|---|---:|');
  const outcomes = {};
  for (const row of rows) outcomes[row.outcome] = (outcomes[row.outcome] ?? 0) + 1;
  for (const [outcome, count] of Object.entries(outcomes)) lines.push(`| ${outcome} | ${count} |`);
  lines.push('');

  lines.push('### Trust label against correctness', '', '| Trust label | Right | Wrong or no answer |', '|---|---:|---:|');
  const trusts = [...new Set(rows.map((row) => row.trust))];
  for (const trust of trusts) {
    const group = rows.filter((row) => row.trust === trust);
    lines.push(`| ${trust} | ${group.filter((row) => row.right).length} | ${group.filter((row) => !row.right).length} |`);
  }
  const wrongCertified = rows.filter((row) => !row.right && row.trust === 'certified').length;
  lines.push('', `**Wrong but labelled certified: ${wrongCertified}** (target 0).`, '');

  const durations = rows.map((row) => row.durationMs);
  const dispatches = rows.map((row) => row.dispatches).filter((value) => typeof value === 'number');
  lines.push('### Speed and AI calls', '');
  lines.push(`Median ${secs(quantile(durations, 0.5))} · 95th percentile ${secs(quantile(durations, 0.95))} · slowest ${secs(Math.max(...durations))} · AI calls per question: mean ${dispatches.length ? mean(dispatches).toFixed(1) : '—'}, max ${dispatches.length ? Math.max(...dispatches) : '—'} · cost: not measured on this provider route`, '');

  const egress = rows.map((row) => row.egress).filter(Boolean);
  lines.push('### Data sent to the AI model', '');
  lines.push(egress.length === rows.length
    ? `${egress.reduce((sum, e) => sum + e.receipts, 0)} AI calls recorded; result rows sent to the model: **${egress.reduce((sum, e) => sum + e.resultRows, 0)}** (target 0).`
    : `Recorded for ${egress.length} of ${rows.length} answers.`, '');

  const suspicious = rows.filter((row) => row.right && row.tables && row.tables.missing.length > 0);
  lines.push('### Right answers that read different tables than the correct query', '');
  lines.push(`${rows.filter((row) => row.right && row.tables?.same).length} right answers read exactly the correct query's tables. ${suspicious.length} right answers left out a table the correct query reads; each is reviewed by hand before a number is published:`, '');
  for (const row of suspicious) lines.push(`- \`${row.id}\`: missing ${row.tables.missing.join(', ')}${row.tables.extra.length ? `; also read ${row.tables.extra.join(', ')}` : ''}`);
  lines.push('');

  lines.push('### Every question', '', '| Question | Quadrant | Outcome | Trust | Time | AI calls | Why not right |', '|---|---|---|---|---:|---:|---|');
  for (const row of rows) {
    lines.push(`| ${row.dbtLabs ? '★ ' : ''}${row.question.replace(/\|/g, '/').trim()} | ${row.quadrant} | ${row.outcome} | ${row.trust} | ${secs(row.durationMs)} | ${row.dispatches ?? '—'} | ${row.right ? '' : (row.reason ?? '').replace(/\|/g, '/')} |`);
  }
  lines.push('', "★ one of dbt Labs' 11 questions.", '');
  return lines.join('\n');
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const jsonAt = args.indexOf('--json');
  const jsonOut = jsonAt >= 0 ? args.splice(jsonAt, 2)[1] : null;
  if (args.length !== 1) {
    console.error('Usage: node insurance/score.mjs <report.json> [--json out.json]');
    process.exit(1);
  }
  const report = JSON.parse(readFileSync(args[0], 'utf-8'));
  if (report.run?.set === 'unanswerable') {
    console.log(renderUnanswerable(report));
    process.exit(0);
  }
  const gold = JSON.parse(readFileSync(join(REPO_ROOT, 'work', 'insurance', 'gold', 'answers.json'), 'utf-8'));
  const audit = loadAudit(join(REPO_ROOT, 'insurance', 'gold-audit.jsonl'));
  const card = scorecard(report, gold, audit);
  if (jsonOut) writeFileSync(jsonOut, `${JSON.stringify(card, null, 2)}\n`);
  console.log(renderScorecard(card));
}

#!/usr/bin/env node
// Several runs of one condition, read together.
//
//   node insurance/repeats.mjs <label>=<report.json> [<label>=<report.json> ...]
//
// A single run of 41 questions swings by several questions, so a published
// number is the average of repeats. This prints, per condition: the accuracy
// of each run, the average, a confidence interval over the pooled answers, and
// **stability** — how often the same question came out the same way every time.
// Questions that were not always the same are listed, because an answer that
// changes run to run is a product problem a buyer will meet.

import { readFileSync } from 'node:fs';
import { basename } from 'node:path';
import { mean, wilsonInterval } from '../lib/stats.mjs';

/** right / wrong / stopped, the outcome a user would see. */
export function outcome(result) {
  if (result.runtimeError) return 'no answer';
  if (result.kind === 'no_answer' || result.route === 'clarify') return 'stopped';
  return result.executionMatched ? 'right' : 'wrong';
}

export function summarizeRepeats(runs) {
  const questions = [...new Set(runs.flatMap((run) => run.results.map((result) => result.name)))].sort();
  const perRun = runs.map((run) => {
    const right = run.results.filter((result) => result.executionMatched === true).length;
    return { label: run.label, n: run.results.length, right, accuracy: run.results.length ? right / run.results.length : 0 };
  });
  const rows = questions.map((name) => {
    const outcomes = runs.map((run) => {
      const result = run.results.find((item) => item.name === name);
      return result ? outcome(result) : 'missing';
    });
    const distinct = [...new Set(outcomes)];
    return { name, outcomes, stable: distinct.length === 1, always: distinct.length === 1 ? distinct[0] : null };
  });
  const pooledRight = perRun.reduce((sum, run) => sum + run.right, 0);
  const pooledTotal = perRun.reduce((sum, run) => sum + run.n, 0);
  const trusted = runs.flatMap((run) => run.results.filter((result) => outcome(result) === 'wrong'
    && ['certified', 'governed', 'none'].includes(result.answer?.trustState ?? result.trustState ?? 'review_required')));
  return {
    runs: perRun,
    meanAccuracy: mean(perRun.map((run) => run.accuracy)),
    pooled: { right: pooledRight, total: pooledTotal, accuracy: pooledTotal ? pooledRight / pooledTotal : 0, ci95: wilsonInterval(pooledRight, pooledTotal) },
    stability: rows.length ? rows.filter((row) => row.stable).length / rows.length : 0,
    alwaysRight: rows.filter((row) => row.always === 'right').length,
    alwaysWrongOrStopped: rows.filter((row) => row.always && row.always !== 'right').length,
    wrongShownAsTrustworthy: trusted.length,
    unstable: rows.filter((row) => !row.stable),
  };
}

export function renderRepeats(summary, label) {
  const pct = (value) => `${(value * 100).toFixed(1)}%`;
  const lines = [`## ${label}: ${summary.runs.length} runs`, ''];
  lines.push('| Run | Right | Accuracy |', '|---|---:|---:|');
  for (const run of summary.runs) lines.push(`| ${run.label} | ${run.right}/${run.n} | ${pct(run.accuracy)} |`);
  lines.push(`| **average** | | **${pct(summary.meanAccuracy)}** |`, '');
  lines.push(`Pooled over all runs: ${summary.pooled.right}/${summary.pooled.total} (${pct(summary.pooled.accuracy)}, 95% CI ${pct(summary.pooled.ci95.low)}–${pct(summary.pooled.ci95.high)}).`, '');
  lines.push(`**Stability: ${pct(summary.stability)}** of questions came out the same way in every run (${summary.alwaysRight} always right, ${summary.alwaysWrongOrStopped} always wrong or stopped). Wrong answers shown as trustworthy, counted over all runs: ${summary.wrongShownAsTrustworthy}.`, '');
  if (summary.unstable.length) {
    lines.push('Questions that changed between runs:', '', '| Question | Outcomes |', '|---|---|');
    for (const row of summary.unstable) lines.push(`| ${row.name} | ${row.outcomes.join(', ')} |`);
    lines.push('');
  }
  return lines.join('\n');
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node insurance/repeats.mjs [<label>=]<report.json> ...');
    process.exit(1);
  }
  const runs = args.map((spec) => {
    const at = spec.indexOf('=');
    const [label, file] = at > 0 ? [spec.slice(0, at), spec.slice(at + 1)] : [basename(spec), spec];
    const report = JSON.parse(readFileSync(file, 'utf-8'));
    return { label, results: report.results ?? [] };
  });
  const condition = runs[0].label.replace(/[-_]?\d+$/, '');
  console.log(renderRepeats(summarizeRepeats(runs), condition || 'condition'));
}

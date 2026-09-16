#!/usr/bin/env node
// Paired comparison of two or more benchmark reports over the same questions.
//
//   node paired/paired-compare.mjs baseline.json challenger.json [...more]
//     [--metric passed|execution] [--audit gold-audit.jsonl]
//     [--allow-unpublishable] [--json out.json]
//
// The first report is the baseline. Each report is either the JSON printed by
// `dql agent eval --format json` or a report written by this repository's
// adapters (both carry per-case results keyed by name).

import { readFileSync, writeFileSync } from 'node:fs';
import { basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { acceptedCaseIds, loadAudit, unauditedCases } from '../lib/gold-audit.mjs';
import { mcnemarExact, mean, pairedDifference, quantile, wilsonInterval } from '../lib/stats.mjs';

/** Bring either report shape to { label, identity, provenance, cases: Map }. */
export function normalizeReport(report, label, metric = 'passed') {
  const results = Array.isArray(report.results) ? report.results
    : Array.isArray(report.cases) ? report.cases
      : null;
  if (!results) throw new Error(`${label}: no "results" or "cases" array.`);
  const cases = new Map();
  for (const result of results) {
    const id = result.name ?? result.caseId ?? result.id ?? result.instanceId;
    if (!id) throw new Error(`${label}: a case has no name/caseId/id.`);
    if (cases.has(id)) throw new Error(`${label}: case ${id} appears twice.`);
    let correct;
    if (metric === 'execution') {
      correct = result.executionMatched;
      if (typeof correct !== 'boolean') throw new Error(`${label}: case ${id} has no executionMatched result.`);
    } else {
      correct = result.passed ?? result.correct ?? result.pass;
      if (typeof correct !== 'boolean') throw new Error(`${label}: case ${id} has no pass/fail result.`);
    }
    cases.set(id, {
      correct,
      durationMs: typeof result.durationMs === 'number' ? result.durationMs : (result.wallMs ?? null),
      dispatches: result.providerDispatchCount ?? result.dispatches ?? null,
      costUsd: typeof result.costUsd === 'number' ? result.costUsd : null,
      trustState: result.trustState ?? null,
    });
  }
  const eligible = report.provenance?.realProviderQualityEligible
    ?? report.cassetteEvidence?.realProviderQualityEligible
    ?? null;
  const reasons = [
    ...(eligible === true ? [] : [eligible === false
      ? `AI calls include non-provider fixtures (${(report.cassetteEvidence?.realProviderQualityExclusionReasons ?? []).join(', ') || 'see report'})`
      : 'no recorded-provider evidence in the report']),
    ...(report.identity && report.identity.publishable === false ? report.identity.notPublishableBecause ?? ['identity is not publishable'] : []),
    ...(report.identity ? [] : ['report has no identity block']),
  ];
  return { label, identity: report.identity ?? null, publishable: reasons.length === 0, reasons, cases };
}

function summarize(report, ids) {
  const rows = ids.map((id) => report.cases.get(id));
  const correct = rows.filter((row) => row.correct).length;
  const interval = wilsonInterval(correct, rows.length);
  const costs = rows.map((row) => row.costUsd);
  const allCostsMeasured = rows.length > 0 && costs.every((cost) => typeof cost === 'number');
  const wrongCertified = rows.filter((row) => !row.correct && row.trustState === 'certified').length;
  return {
    label: report.label,
    n: rows.length,
    correct,
    accuracy: rows.length ? correct / rows.length : 0,
    ci95: interval,
    latencyP50Ms: quantile(rows.map((row) => row.durationMs), 0.5),
    latencyP95Ms: quantile(rows.map((row) => row.durationMs), 0.95),
    dispatchesMean: mean(rows.map((row) => row.dispatches)),
    dispatchesMax: rows.some((row) => typeof row.dispatches === 'number')
      ? Math.max(...rows.map((row) => row.dispatches ?? 0))
      : null,
    // Cost is shown only when every case measured it; a partial sum would lie.
    costPerQuestionUsd: allCostsMeasured ? mean(costs) : null,
    wrongCertified,
  };
}

function compare(baseline, challenger, ids) {
  let b = 0;
  let c = 0;
  for (const id of ids) {
    const base = baseline.cases.get(id).correct;
    const next = challenger.cases.get(id).correct;
    if (base && !next) b += 1;
    if (!base && next) c += 1;
  }
  return {
    baseline: baseline.label,
    challenger: challenger.label,
    onlyBaselineCorrect: b,
    onlyChallengerCorrect: c,
    mcnemarP: mcnemarExact(b, c),
    difference: pairedDifference(b, c, ids.length),
  };
}

/**
 * @param {Array<{label: string, report: object}>} inputs  baseline first
 * @param {{ metric?: string, audit?: object|null, allowUnpublishable?: boolean }} options
 */
export function pairedCompare(inputs, options = {}) {
  if (inputs.length < 2) throw new Error('Give at least two reports: a baseline and a challenger.');
  const reports = inputs.map(({ label, report }) => normalizeReport(report, label, options.metric));

  const baseIds = [...reports[0].cases.keys()].sort();
  for (const report of reports.slice(1)) {
    const ids = [...report.cases.keys()].sort();
    const missing = baseIds.filter((id) => !report.cases.has(id));
    const extra = ids.filter((id) => !reports[0].cases.has(id));
    if (missing.length || extra.length) {
      throw new Error(`${report.label} does not answer the same questions as ${reports[0].label}`
        + ` (missing: ${missing.slice(0, 5).join(', ') || 'none'}; extra: ${extra.slice(0, 5).join(', ') || 'none'}).`);
    }
  }

  const unpublishable = reports.filter((report) => !report.publishable);
  if (unpublishable.length && !options.allowUnpublishable) {
    throw new Error(`Not comparable for publication:\n${unpublishable
      .map((report) => `  ${report.label}: ${report.reasons.join('; ')}`).join('\n')}\n`
      + 'Pass --allow-unpublishable to compare anyway; the output is then labelled as such.');
  }

  const subsets = [{ name: 'all', ids: baseIds }];
  if (options.audit) {
    const unaudited = unauditedCases(baseIds, options.audit);
    if (unaudited.length) {
      throw new Error(`${unaudited.length} case(s) have no gold-audit line, e.g. ${unaudited.slice(0, 5).join(', ')}.`);
    }
    const accepted = acceptedCaseIds(options.audit);
    subsets.push({ name: 'accepted', ids: baseIds.filter((id) => accepted.has(id)) });
  }

  return {
    metric: options.metric ?? 'passed',
    publishable: unpublishable.length === 0,
    notPublishable: unpublishable.map((report) => ({ label: report.label, reasons: report.reasons })),
    identities: reports.map((report) => ({ label: report.label, identity: report.identity })),
    subsets: subsets.map(({ name, ids }) => ({
      name,
      n: ids.length,
      conditions: reports.map((report) => summarize(report, ids)),
      comparisons: reports.slice(1).map((report) => compare(reports[0], report, ids)),
    })),
  };
}

const percent = (value) => `${(value * 100).toFixed(1)}%`;
const orDash = (value, format) => (value === null || value === undefined ? '—' : format(value));

export function renderMarkdown(result) {
  const lines = [];
  if (!result.publishable) {
    lines.push('> **Not publishable.** ' + result.notPublishable
      .map((entry) => `${entry.label}: ${entry.reasons.join('; ')}`).join(' — '), '');
  }
  for (const subset of result.subsets) {
    lines.push(`### ${subset.name === 'all' ? 'All questions' : 'Questions with an accepted answer key'} (n = ${subset.n})`, '');
    lines.push('| Condition | Correct | Accuracy | 95% CI | p50 latency | p95 latency | AI calls (mean / max) | $ / question | Wrong but certified |');
    lines.push('|---|---:|---:|---|---:|---:|---:|---:|---:|');
    for (const condition of subset.conditions) {
      lines.push(`| ${condition.label} | ${condition.correct}/${condition.n} | ${percent(condition.accuracy)} `
        + `| ${percent(condition.ci95.low)}–${percent(condition.ci95.high)} `
        + `| ${orDash(condition.latencyP50Ms, (ms) => `${(ms / 1000).toFixed(1)} s`)} `
        + `| ${orDash(condition.latencyP95Ms, (ms) => `${(ms / 1000).toFixed(1)} s`)} `
        + `| ${orDash(condition.dispatchesMean, (value) => value.toFixed(1))} / ${orDash(condition.dispatchesMax, String)} `
        + `| ${orDash(condition.costPerQuestionUsd, (value) => `$${value.toFixed(4)}`)} `
        + `| ${condition.wrongCertified} |`);
    }
    lines.push('');
    for (const comparison of subset.comparisons) {
      const { difference } = comparison;
      lines.push(`- **${comparison.challenger} vs ${comparison.baseline}:** `
        + `${difference.difference >= 0 ? '+' : ''}${(difference.difference * 100).toFixed(1)} points `
        + `(95% CI ${(difference.low * 100).toFixed(1)} to ${(difference.high * 100).toFixed(1)}); `
        + `only ${comparison.challenger} right on ${comparison.onlyChallengerCorrect}, `
        + `only ${comparison.baseline} right on ${comparison.onlyBaselineCorrect}; `
        + `exact McNemar p = ${comparison.mcnemarP < 0.0001 ? comparison.mcnemarP.toExponential(2) : comparison.mcnemarP.toFixed(4)}.`);
    }
    lines.push('');
  }
  return lines.join('\n');
}

function parseArgs(argv) {
  const files = [];
  const options = { metric: 'passed', audit: null, allowUnpublishable: false, json: null };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--metric') options.metric = argv[++index];
    else if (arg === '--audit') options.audit = argv[++index];
    else if (arg === '--allow-unpublishable') options.allowUnpublishable = true;
    else if (arg === '--json') options.json = argv[++index];
    else if (arg.startsWith('--')) throw new Error(`Unknown option ${arg}`);
    else files.push(arg);
  }
  if (!['passed', 'execution'].includes(options.metric)) throw new Error('--metric must be passed or execution');
  return { files, options };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  try {
    const { files, options } = parseArgs(process.argv.slice(2));
    let audit = null;
    if (options.audit) {
      audit = loadAudit(options.audit);
      if (audit.problems.length) throw new Error(`Gold audit is invalid:\n  ${audit.problems.join('\n  ')}`);
    }
    const inputs = files.map((file) => ({
      label: basename(file).replace(/\.json$/, ''),
      report: JSON.parse(readFileSync(file, 'utf-8')),
    }));
    const result = pairedCompare(inputs, { metric: options.metric, audit, allowUnpublishable: options.allowUnpublishable });
    if (options.json) writeFileSync(options.json, `${JSON.stringify(result, null, 2)}\n`);
    console.log(renderMarkdown(result));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

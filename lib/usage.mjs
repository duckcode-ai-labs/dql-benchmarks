// What each question cost.
//
// DQL writes one line per API call to the ledger named by
// DQL_PROVIDER_USAGE_LEDGER (time, provider, model, tokens; never text). A run
// asks its questions one after another, and the run store records when each
// question started and finished, so a line belongs to the question whose time
// span holds it. Prices come from pricing.json; a model without a checked
// price has no cost — cost is never estimated.

import { existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { REPO_ROOT } from './dql.mjs';

export function loadPricing(file = join(REPO_ROOT, 'pricing.json')) {
  return JSON.parse(readFileSync(file, 'utf-8'));
}

/** USD for one usage record at list price, or null when the price is not checked. */
export function priceUsage(usage, model, pricing) {
  const price = pricing?.models?.[model];
  if (!price || price.inputPerMillion == null || price.outputPerMillion == null) return null;
  const cacheRead = usage.cacheReadTokens ?? 0;
  const cacheWrite = usage.cacheWriteTokens ?? 0;
  if (cacheRead && price.cacheReadPerMillion == null) return null;
  if (cacheWrite && price.cacheWritePerMillion == null) return null;
  const perToken = (perMillion) => perMillion / 1_000_000;
  return usage.inputTokens * perToken(price.inputPerMillion)
    + usage.outputTokens * perToken(price.outputPerMillion)
    + cacheRead * perToken(price.cacheReadPerMillion ?? 0)
    + cacheWrite * perToken(price.cacheWritePerMillion ?? 0);
}

export function readLedger(file) {
  if (!existsSync(file)) return [];
  return readFileSync(file, 'utf-8').split('\n').filter(Boolean).map((line) => JSON.parse(line));
}

/** The run store's questions with their time spans. */
export function runSpans(projectDir) {
  const store = join(projectDir, '.dql', 'local', 'agent-runs.sqlite');
  if (!existsSync(store)) return [];
  const result = spawnSync('sqlite3', ['-json', store, 'select question, started_at, completed_at from agent_runs order by started_at'], { encoding: 'utf-8', maxBuffer: 64 * 1024 * 1024 });
  if (result.status !== 0) throw new Error(`could not read the run store: ${result.stderr}`);
  const rows = result.stdout.trim() ? JSON.parse(result.stdout) : [];
  return rows.map((row) => ({ question: row.question, start: Date.parse(row.started_at), end: Date.parse(row.completed_at ?? row.started_at) }));
}

const add = (total, usage) => ({
  calls: total.calls + 1,
  inputTokens: total.inputTokens + (usage.inputTokens ?? 0),
  outputTokens: total.outputTokens + (usage.outputTokens ?? 0),
  cacheReadTokens: total.cacheReadTokens + (usage.cacheReadTokens ?? 0),
  cacheWriteTokens: total.cacheWriteTokens + (usage.cacheWriteTokens ?? 0),
  reasoningTokens: total.reasoningTokens + (usage.reasoningTokens ?? 0),
});
const EMPTY = { calls: 0, inputTokens: 0, outputTokens: 0, cacheReadTokens: 0, cacheWriteTokens: 0, reasoningTokens: 0 };

/**
 * Tokens and cost per question. A line outside every question's span (the
 * server warming up) is counted apart, never assigned to a neighbour. A
 * question's cost is null when any of its calls used a model with no checked
 * price.
 */
export function attributeUsage(lines, spans, pricing) {
  const byQuestion = new Map(spans.map((span) => [span.question, { ...EMPTY, costUsd: 0, priced: true }]));
  let outside = { ...EMPTY };
  for (const line of lines) {
    const at = Date.parse(line.at);
    const span = spans.find((item) => at >= item.start && at <= item.end + 1000);
    if (!span) { outside = add(outside, line); continue; }
    const current = byQuestion.get(span.question);
    const cost = priceUsage(line, line.model, pricing);
    byQuestion.set(span.question, { ...add(current, line), costUsd: cost == null || !current.priced ? null : current.costUsd + cost, priced: current.priced && cost != null });
  }
  const questions = [...byQuestion.values()];
  const priced = questions.every((item) => item.priced);
  return {
    byQuestion: Object.fromEntries([...byQuestion].map(([question, item]) => [question, { ...item, costUsd: item.priced ? item.costUsd : null }])),
    outside,
    totalCostUsd: priced ? questions.reduce((sum, item) => sum + item.costUsd, 0) : null,
    pricingAsOf: pricing?.asOf ?? null,
  };
}

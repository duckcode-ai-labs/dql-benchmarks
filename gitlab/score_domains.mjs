// Score ZLens's domain finder against the GitLab truth set (Q0).
//
//   node gitlab/score_domains.mjs <dql-core dist index.js> <dbt project dir> [--json out.json]
//
// <dbt project dir> holds target/manifest.json (a scratch copy of GitLab's
// analytics project; never the owner's checkout). The truth set is
// gitlab/truth.json: one domain and subject area per business table, labelled
// from what each table is about.
//
// A proposed domain is named by ZLens, a true one by the labeller, so names are
// matched by majority: each proposed domain counts as the true domain most of
// its tables carry. A table is right when its proposed domain maps to its own
// true domain. Unplaced tables count as wrong. Tables labelled `unclear` are
// left out of every measure.
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const [distPath, dbtDir] = process.argv.slice(2);
const jsonOut = process.argv.includes('--json') ? process.argv[process.argv.indexOf('--json') + 1] : undefined;
if (!distPath || !dbtDir) {
  console.error('usage: node gitlab/score_domains.mjs <dql-core dist index.js> <dbt project dir> [--json out.json]');
  process.exit(2);
}
const { discoverDbtDomains } = await import(pathToFileURL(distPath).href);
const truth = JSON.parse(readFileSync(join(here, 'truth.json'), 'utf8')).filter((row) => row.domain !== 'unclear');
const started = Date.now();
const report = discoverDbtDomains({ projectRoot: join(dbtDir, 'dql'), dbtManifestPath: join(dbtDir, 'target', 'manifest.json') });
const ms = Date.now() - started;
const membership = new Map(report.memberships.map((item) => [item.dbtUniqueId, item]));

const top = (id) => (id ? id.split('.')[0] : null);
const rows = truth.map((row) => {
  const found = membership.get(row.id);
  const domain = top(found?.proposedDomain ?? null);
  const area = found?.proposedArea ?? found?.proposedDomain ?? null;
  return { ...row, proposedDomain: domain, proposedArea: area, evidence: found?.evidence?.[0]?.kind ?? null };
});

function majorityMap(key, truthKey) {
  const counts = new Map();
  for (const row of rows) {
    if (!row[key]) continue;
    const inner = counts.get(row[key]) ?? new Map();
    inner.set(row[truthKey], (inner.get(row[truthKey]) ?? 0) + 1);
    counts.set(row[key], inner);
  }
  return new Map([...counts].map(([proposed, inner]) => [proposed, [...inner].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0][0]]));
}

// One-to-one: each true domain is matched to at most one proposed domain,
// largest overlap first, so splitting a true domain over many proposals is
// not rewarded. Tables in an unmatched proposal count as wrong.
function oneToOne(key, truthKey) {
  const overlap = new Map();
  for (const row of rows) {
    if (!row[key]) continue;
    const pair = `${row[key]}\u0000${row[truthKey]}`;
    overlap.set(pair, (overlap.get(pair) ?? 0) + 1);
  }
  const usedProposed = new Set();
  const usedTruth = new Set();
  const match = new Map();
  for (const [pair] of [...overlap].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))) {
    const [proposed, truthName] = pair.split('\u0000');
    if (usedProposed.has(proposed) || usedTruth.has(truthName)) continue;
    usedProposed.add(proposed);
    usedTruth.add(truthName);
    match.set(proposed, truthName);
  }
  return rows.filter((row) => row[key] && match.get(row[key]) === row[truthKey]).length;
}

function measure(key, truthKey) {
  const mapping = majorityMap(key, truthKey);
  const right = rows.filter((row) => row[key] && mapping.get(row[key]) === row[truthKey]).length;
  const strict = oneToOne(key, truthKey);
  const placed = rows.filter((row) => row[key]).length;
  const proposedNames = new Set(rows.map((row) => row[key]).filter(Boolean));
  const perTruth = new Map();
  for (const row of rows) {
    if (!row[key]) continue;
    const set = perTruth.get(row[truthKey]) ?? new Set();
    set.add(row[key]);
    perTruth.set(row[truthKey], set);
  }
  return {
    tables: rows.length,
    placed,
    right,
    accuracy: +(right / rows.length).toFixed(3),
    strict,
    strictAccuracy: +(strict / rows.length).toFixed(3),
    proposed: proposedNames.size,
    truth: new Set(rows.map((row) => row[truthKey])).size,
    split: Object.fromEntries([...perTruth].map(([name, set]) => [name, set.size]).sort((a, b) => b[1] - a[1])),
    mapping: Object.fromEntries([...mapping].sort((a, b) => a[0].localeCompare(b[0]))),
  };
}

const domain = measure('proposedDomain', 'domain');
const area = measure('proposedArea', 'area');
const allProposals = report.proposals.map((proposal) => ({ id: proposal.id, models: proposal.matchedDbtUniqueIds.length })).sort((a, b) => b.models - a.models);
const wrong = rows.filter((row) => !row.proposedDomain || domain.mapping[row.proposedDomain] !== row.domain);

console.log(`Domain finder on GitLab (${rows.length} business tables with a clear label; ${ms} ms)`);
console.log(`  domains: ${domain.right}/${domain.tables} right by majority (${(domain.accuracy * 100).toFixed(1)}%), ${domain.strict} one-to-one (${(domain.strictAccuracy * 100).toFixed(1)}%), ${domain.placed} placed, ${domain.proposed} proposed for ${domain.truth} true`);
console.log(`  areas:   ${area.right}/${area.tables} right by majority (${(area.accuracy * 100).toFixed(1)}%), ${area.strict} one-to-one (${(area.strictAccuracy * 100).toFixed(1)}%), ${area.proposed} proposed for ${area.truth} true`);
console.log(`  proposals over the whole project: ${allProposals.length}; top: ${allProposals.slice(0, 12).map((item) => `${item.id} ${item.models}`).join(', ')}`);
console.log(`  true domain → how many proposed domains its tables are split over: ${JSON.stringify(domain.split)}`);
const byCause = new Map();
for (const row of wrong) {
  const cause = row.proposedDomain ? `${row.domain} placed in ${row.proposedDomain} (${row.evidence})` : `${row.domain} unplaced`;
  byCause.set(cause, (byCause.get(cause) ?? 0) + 1);
}
console.log(`  wrong or unplaced, by cause: ${[...byCause].sort((a, b) => b[1] - a[1]).slice(0, 15).map(([cause, count]) => `${cause}: ${count}`).join('; ')}`);
if (jsonOut) writeFileSync(jsonOut, JSON.stringify({ ms, domain, area, allProposals, wrong }, null, 2));

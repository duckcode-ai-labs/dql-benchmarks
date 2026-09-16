// The identity stamped into every report: which code, which DQL, which model,
// which data. A report without a clean identity is not publishable.

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { REPO_ROOT } from './dql.mjs';

function git(args, cwd) {
  try {
    return execFileSync('git', args, { cwd, encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return null;
  }
}

function dqlBuildCommit(entry) {
  const dir = dirname(entry);
  const status = git(['status', '--porcelain', '--untracked-files=no'], dir);
  return {
    commit: git(['rev-parse', 'HEAD'], dir),
    dirty: status === null ? null : status.length > 0,
  };
}

const SKIPPED_DIRS = new Set(['.git', 'node_modules', 'data', 'work', '.venv', '.dql-cli', 'reports', 'submissions']);

/**
 * A hash over the files that decide a result: adapters, scorer, modeling
 * files and gold audits. Reports and downloaded data are excluded, so running
 * a benchmark does not change the fingerprint of the code that ran it.
 */
export function contentFingerprint(roots, repoRoot = REPO_ROOT) {
  const files = [];
  const walk = (dir) => {
    if (!existsSync(dir)) return;
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        if (!SKIPPED_DIRS.has(entry.name)) walk(join(dir, entry.name));
      } else if (entry.isFile() && !/\.(duckdb|duckdb\.wal|log)$/.test(entry.name)) {
        files.push(join(dir, entry.name));
      }
    }
  };
  for (const root of roots) {
    const absolute = join(repoRoot, root);
    if (existsSync(absolute) && statSync(absolute).isFile()) files.push(absolute);
    else walk(absolute);
  }
  const hash = createHash('sha256');
  for (const file of files.sort()) {
    hash.update(relative(repoRoot, file).replace(/\\/g, '/'));
    hash.update('\0');
    hash.update(readFileSync(file));
    hash.update('\0');
  }
  return hash.digest('hex').slice(0, 16);
}

/**
 * @param {object} input
 * @param {{ source: string, entry: string }} input.cli   from resolveDqlCli()
 * @param {string} input.dqlVersion                      from dqlVersion()
 * @param {string} input.benchmark                       e.g. "insurance"
 * @param {string} input.condition                       e.g. "L0" or "L1"
 * @param {string|null} input.provider
 * @param {string|null} input.model
 * @param {'record'|'replay'|'live'} input.cassetteMode
 * @param {string|null} [input.dataHash]                 hash of the downloaded benchmark data
 * @param {Record<string,string|null>} [input.tools]     e.g. { dbt: '1.9.1', duckdb: '1.1.3' }
 */
export function buildIdentity(input, repoRoot = REPO_ROOT) {
  const dqlBuild = input.cli.source === 'npm' ? null : dqlBuildCommit(input.cli.entry);
  const status = git(['status', '--porcelain', '--untracked-files=no'], repoRoot);
  const dirty = status === null ? null : status.length > 0;
  const publishable = dirty === false && input.cli.source === 'npm' && input.cassetteMode !== 'live';
  return {
    benchmark: input.benchmark,
    condition: input.condition,
    repoCommit: git(['rev-parse', 'HEAD'], repoRoot),
    repoDirty: dirty,
    contentFingerprint: contentFingerprint(['lib', 'paired', input.benchmark, 'dql.json', 'pricing.json'], repoRoot),
    dql: {
      version: input.dqlVersion,
      source: input.cli.source,
      // A development build is identified by its commit, since its version
      // number does not say what code ran.
      ...(dqlBuild ?? {}),
    },
    provider: input.provider ?? null,
    model: input.model ?? null,
    cassetteMode: input.cassetteMode,
    dataHash: input.dataHash ?? null,
    tools: input.tools ?? {},
    node: process.version,
    createdAt: new Date().toISOString(),
    // Why a report cannot be published, if it cannot. Checked again by the scorer.
    publishable,
    notPublishableBecause: [
      ...(dirty === true ? ['benchmark repo has uncommitted changes'] : []),
      ...(dirty === null ? ['benchmark repo commit could not be read'] : []),
      ...(input.cli.source === 'local' ? ['DQL came from a local build, not a release'] : []),
      ...(input.cli.source === 'env' ? ['DQL came from the DQL_CLI override, not a release'] : []),
      ...(dqlBuild?.dirty ? ['the DQL build has uncommitted changes'] : []),
      ...(input.cassetteMode === 'live' ? ['AI calls were not recorded'] : []),
    ],
  };
}

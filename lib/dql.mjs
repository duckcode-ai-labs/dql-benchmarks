// Which DQL CLI a run uses, and how to call it.
//
// Published numbers must come from a released npm version so anyone can
// reproduce them. A local build is allowed while developing, and the source is
// always recorded so a local-build report can never be mistaken for a release.

import { existsSync, readFileSync, statSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

export function readDqlPin(repoRoot = REPO_ROOT) {
  const pin = JSON.parse(readFileSync(join(repoRoot, 'dql.json'), 'utf-8'));
  if (pin.source !== 'npm' && pin.source !== 'local') {
    throw new Error(`dql.json: source must be "npm" or "local", got ${JSON.stringify(pin.source)}.`);
  }
  if (pin.source === 'npm' && !pin.version) throw new Error('dql.json: an npm pin needs a version.');
  if (pin.source === 'local' && !pin.path) throw new Error('dql.json: a local pin needs a path to apps/cli/dist/index.js.');
  return pin;
}

/** Where the installed npm release lives inside this repo. */
export function installedCliEntry(repoRoot = REPO_ROOT) {
  return join(repoRoot, '.dql-cli', 'node_modules', '@duckcodeailabs', 'dql-cli', 'dist', 'index.js');
}

/**
 * Resolve the CLI entry file. `DQL_CLI` wins, then `dql.json`. Returns the
 * entry and a `source` label that every report carries.
 */
export function resolveDqlCli({ env = process.env, repoRoot = REPO_ROOT } = {}) {
  if (env.DQL_CLI) {
    const entry = resolve(env.DQL_CLI);
    if (!existsSync(entry)) throw new Error(`DQL_CLI points at ${entry}, which does not exist.`);
    return { entry, source: 'env', pinnedVersion: null };
  }
  const pin = readDqlPin(repoRoot);
  if (pin.source === 'local') {
    const entry = resolve(repoRoot, pin.path);
    if (!existsSync(entry)) throw new Error(`dql.json points at ${entry}, which does not exist. Build DQL first.`);
    return { entry, source: 'local', pinnedVersion: null };
  }
  const entry = installedCliEntry(repoRoot);
  if (!existsSync(entry)) {
    throw new Error(`DQL ${pin.version} is not installed yet. Run: npm run dql:install`);
  }
  return { entry, source: 'npm', pinnedVersion: pin.version };
}

/** Run the CLI synchronously; used for short commands like `init` and `--version`. */
export function runDql(args, { cwd, env = process.env, cli = resolveDqlCli({ env }), timeoutMs = 120_000 } = {}) {
  const result = spawnSync(process.execPath, [cli.entry, ...args], {
    cwd,
    env,
    encoding: 'utf-8',
    timeout: timeoutMs,
  });
  if (result.error) throw result.error;
  return { code: result.status, stdout: result.stdout, stderr: result.stderr };
}

/**
 * The version the CLI reports about itself. For an npm pin it must equal the
 * pin, otherwise the install is stale and the run would be mislabelled.
 */
export function dqlVersion(cli = resolveDqlCli()) {
  const { code, stdout, stderr } = runDql(['--version'], { cli });
  if (code !== 0) throw new Error(`dql --version failed: ${stderr || stdout}`);
  const version = stdout.trim().replace(/^dql\s+/, '');
  if (cli.pinnedVersion && version !== cli.pinnedVersion) {
    throw new Error(`Installed DQL is ${version} but dql.json pins ${cli.pinnedVersion}. Run: npm run dql:install`);
  }
  return version;
}

/**
 * Which source a local CLI was built from: the git commit, whether the tree
 * had uncommitted edits, and a hash of those edits. A run from a dirty tree
 * also saves the edits as a patch next to its results, so the build behind
 * any number can be rebuilt; a score that cannot be traced to code is not
 * evidence. The dist files are the built output of a source tree, so the
 * patch is taken from the tree that holds them.
 *
 * Also records every DQL_* environment switch the run sets, since a switch
 * changes behaviour as much as a code edit does.
 */
export function buildIdentity(cli, { env = process.env } = {}) {
  const switches = Object.fromEntries(Object.entries(env).filter(([key]) => /^DQL_(ASK|SQLITE|EXPLORATION)_/.test(key)).sort(([a], [b]) => a.localeCompare(b)));
  if (cli.source === 'npm') return { kind: 'npm', version: cli.pinnedVersion, switches };
  const git = (args) => spawnSync('git', args, { cwd: dirname(cli.entry), encoding: 'utf-8', maxBuffer: 256 * 1024 * 1024 });
  const top = git(['rev-parse', '--show-toplevel']);
  if (top.status !== 0) return { kind: 'unversioned', entry: cli.entry, switches };
  const root = top.stdout.trim();
  const at = (args) => spawnSync('git', ['-C', root, ...args], { encoding: 'utf-8', maxBuffer: 256 * 1024 * 1024 });
  const head = at(['rev-parse', 'HEAD']).stdout.trim();
  const branch = at(['rev-parse', '--abbrev-ref', 'HEAD']).stdout.trim();
  const tracked = at(['diff', '--binary', 'HEAD']).stdout;
  const untracked = at(['ls-files', '--others', '--exclude-standard']).stdout.split('\n').filter(Boolean);
  // An untracked source file changes the build as surely as an edit does.
  const untrackedBodies = untracked.map((file) => {
    try { return `--- ${file}\n${readFileSync(join(root, file), 'utf-8')}`; } catch { return `--- ${file}\n<unreadable>`; }
  }).join('\n');
  const patch = tracked + (untrackedBodies ? `\n# untracked files\n${untrackedBodies}\n` : '');
  const dirty = patch.trim().length > 0;
  // A dist built before the latest source edit runs older code than the patch
  // describes: the identity would name code that did not run.
  const changed = [...at(['diff', '--name-only', 'HEAD']).stdout.split('\n').filter(Boolean), ...untracked];
  const newestSourceMs = Math.max(0, ...changed.map((file) => { try { return statSync(join(root, file)).mtimeMs; } catch { return 0; } }));
  const distBuiltMs = statSync(cli.entry).mtimeMs;
  const distOlderThanSource = newestSourceMs > distBuiltMs;
  const patchSha256 = dirty ? createHash('sha256').update(patch).digest('hex') : null;
  return { kind: 'git', root, head, branch, dirty, patchSha256, untrackedFiles: untracked, distBuiltAt: new Date(distBuiltMs).toISOString(), distOlderThanSource, switches, patch };
}

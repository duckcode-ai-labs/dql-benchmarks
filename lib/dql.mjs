// Which DQL CLI a run uses, and how to call it.
//
// Published numbers must come from a released npm version so anyone can
// reproduce them. A local build is allowed while developing, and the source is
// always recorded so a local-build report can never be mistaken for a release.

import { existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
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

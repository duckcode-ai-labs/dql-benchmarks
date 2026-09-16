// Install the database drivers DQL loads at runtime, once, into .connectors/.
// Benchmark projects link to this folder instead of installing per project.
// duckdb 1.1.3 is the version DQL's own CI installs.

import { mkdirSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';

const CONNECTORS = ['duckdb@1.1.3'];

const prefix = join(REPO_ROOT, '.connectors');
mkdirSync(prefix, { recursive: true });
writeFileSync(join(prefix, 'package.json'), `${JSON.stringify({ private: true }, null, 2)}\n`);
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const result = spawnSync(npm, ['install', '--no-audit', '--no-fund', '--save-exact', ...CONNECTORS], {
  cwd: prefix,
  stdio: 'inherit',
});
process.exit(result.status ?? 1);

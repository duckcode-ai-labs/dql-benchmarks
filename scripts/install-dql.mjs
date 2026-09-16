// Install the DQL version pinned in dql.json into .dql-cli/, isolated from any
// global `dql` so a stale global install can never run a benchmark.

import { mkdirSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { REPO_ROOT, readDqlPin, resolveDqlCli, dqlVersion } from '../lib/dql.mjs';

const pin = readDqlPin();
if (pin.source !== 'npm') {
  console.log(`dql.json uses a ${pin.source} build (${pin.path}); nothing to install.`);
  process.exit(0);
}

const prefix = join(REPO_ROOT, '.dql-cli');
mkdirSync(prefix, { recursive: true });
writeFileSync(join(prefix, 'package.json'), `${JSON.stringify({ private: true }, null, 2)}\n`);

const spec = `${pin.package}@${pin.version}`;
console.log(`Installing ${spec} into .dql-cli/ ...`);
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const result = spawnSync(npm, ['install', '--no-audit', '--no-fund', '--save-exact', spec], {
  cwd: prefix,
  stdio: 'inherit',
});
if (result.status !== 0) process.exit(result.status ?? 1);

const version = dqlVersion(resolveDqlCli({ env: {} }));
console.log(`DQL ${version} is ready.`);

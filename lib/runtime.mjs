// Start a DQL runtime for one project and stop it afterwards.
//
// The server binds to loopback, so it needs no access token. Recorded AI calls
// are selected with DQL's own cassette variables, so the same command records
// a run once and replays it forever after.

import { spawn } from 'node:child_process';
import { createServer } from 'node:net';
import { resolveDqlCli } from './dql.mjs';

export function freePort() {
  return new Promise((resolvePort, reject) => {
    const server = createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolvePort(port));
    });
  });
}

async function waitForHealth(base, child, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`DQL runtime exited early with code ${child.exitCode}.`);
    try {
      const response = await fetch(`${base}/api/health`);
      if (response.ok) return;
      lastError = new Error(`health returned ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((done) => setTimeout(done, 250));
  }
  throw new Error(`DQL runtime at ${base} did not become healthy: ${lastError?.message ?? 'timeout'}`);
}

/**
 * @param {string} projectRoot
 * @param {object} [options]
 * @param {'record'|'replay'|'live'} [options.cassetteMode]
 * @param {string} [options.cassetteDir]        required unless cassetteMode is 'live'
 * @param {Record<string,string>} [options.env] extra environment (provider keys, ledger path)
 * @param {number} [options.startupTimeoutMs]
 * @returns {Promise<{ base: string, port: number, logs: () => string, close: () => Promise<void> }>}
 */
export async function startRuntime(projectRoot, options = {}) {
  const cli = options.cli ?? resolveDqlCli();
  const cassetteMode = options.cassetteMode ?? 'replay';
  if (cassetteMode !== 'live' && !options.cassetteDir) {
    throw new Error('A recorded or replayed run needs a cassetteDir.');
  }
  const port = await freePort();
  const env = {
    ...process.env,
    ...options.env,
    DQL_TELEMETRY_DISABLED: '1',
    ...(cassetteMode !== 'live'
      ? { DQL_EVAL_CASSETTE_DIR: options.cassetteDir, DQL_EVAL_CASSETTE_MODE: cassetteMode }
      : {}),
  };
  const child = spawn(process.execPath, [
    cli.entry, 'notebook', projectRoot, '--port', String(port), '--no-open',
  ], { env, stdio: ['ignore', 'pipe', 'pipe'] });
  let output = '';
  child.stdout.on('data', (chunk) => { output += chunk; });
  child.stderr.on('data', (chunk) => { output += chunk; });

  const base = `http://127.0.0.1:${port}`;
  try {
    await waitForHealth(base, child, options.startupTimeoutMs ?? 90_000);
  } catch (error) {
    child.kill('SIGTERM');
    throw new Error(`${error.message}\n--- runtime output ---\n${output.slice(-4000)}`);
  }
  return {
    base,
    port,
    logs: () => output,
    close: () => new Promise((done) => {
      if (child.exitCode !== null) return done();
      child.once('exit', () => done());
      child.kill('SIGTERM');
      setTimeout(() => child.kill('SIGKILL'), 5_000).unref();
    }),
  };
}

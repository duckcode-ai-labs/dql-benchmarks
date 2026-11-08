import { test } from 'node:test';
import assert from 'node:assert/strict';
import { forPublic, PRIVATE_PATTERNS } from './public.mjs';

// The examples are built from pieces, so this file itself passes lib/check-public.mjs.
const HOME = ['', 'Users', 'someone'].join('/');
const NOREPLY = ['123+someone@users', 'noreply', 'github', 'com'].join('.');

test('forPublic writes the home folder as ~, the account as <account>, a no-reply email as benchmark-owner', () => {
  const env = { HOME, SNOWFLAKE_ACCOUNT: 'ORG-ACCT1' };
  const text = `{"path":"${HOME}/work/x.json","accountOrWorkspace":"org-acct1","owner":"${NOREPLY}","url":"https://org-acct1.snowflakecomputing.com"}`;
  assert.equal(forPublic(text, env), '{"path":"~/work/x.json","accountOrWorkspace":"<account>","owner":"benchmark-owner","url":"https://<account>.snowflakecomputing.com"}');
});

test('the check patterns find a home folder and a no-reply email, and leave ~ alone', () => {
  const hits = (text) => PRIVATE_PATTERNS.filter(({ pattern }) => pattern.test(text)).map(({ name }) => name);
  assert.deepEqual(hits(`cd ${HOME}/x`), ['a macOS home folder']);
  assert.deepEqual(hits(NOREPLY), ['a GitHub no-reply email']);
  assert.deepEqual(hits('cd ~/x && cd $HOME/y'), []);
});

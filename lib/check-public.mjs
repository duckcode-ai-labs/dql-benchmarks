#!/usr/bin/env node
// Fails when a tracked file names a home folder or a person's email, or (with SNOWFLAKE_ACCOUNT
// set) the Snowflake account: this repository is public. Run before every push.
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { PRIVATE_PATTERNS } from './public.mjs';

const files = execFileSync('git', ['ls-files', '-z'], { encoding: 'utf-8' }).split('\0').filter(Boolean);
const account = process.env.SNOWFLAKE_ACCOUNT?.trim().toLowerCase();
const found = [];
for (const file of files) {
  let text;
  try { text = readFileSync(file); } catch { continue; }
  if (text.includes(0)) continue; // binary
  const content = text.toString('utf-8');
  for (const { name, pattern } of PRIVATE_PATTERNS) if (pattern.test(content)) found.push(`${file}: ${name}`);
  if (account && content.toLowerCase().includes(account)) found.push(`${file}: the Snowflake account`);
}
if (found.length) {
  console.error(`Not for a public repository (${found.length}):\n${found.slice(0, 50).join('\n')}${found.length > 50 ? '\n…' : ''}`);
  process.exit(1);
}
console.log(`public check: ${files.length} tracked files, nothing private`);

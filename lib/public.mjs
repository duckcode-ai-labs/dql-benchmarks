import { homedir } from 'node:os';

/**
 * This repository is public. Text written into it (results, logs, reports) names no
 * local home folder, no Snowflake account and no person's email: the home folder is
 * written as ~, the account as <account>, a GitHub no-reply email as benchmark-owner.
 */
export function forPublic(text, env = process.env) {
  let out = String(text).replace(/("accountOrWorkspace"\s*:\s*)"[^"]*"/g, '$1"<account>"');
  const account = env.SNOWFLAKE_ACCOUNT?.trim();
  if (account) out = out.replace(new RegExp(account.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), '<account>');
  const home = (env.HOME || homedir() || '').trim();
  if (home.length > 1) out = out.split(home).join('~');
  return out.replace(NOREPLY_EMAIL, 'benchmark-owner');
}

const NOREPLY_EMAIL = /\b\d+\+[A-Za-z0-9-]+@users\.noreply\.github\.com\b/g;

/** What must never be committed here: a home folder on macOS or Linux, a GitHub no-reply email. */
export const PRIVATE_PATTERNS = [
  { name: 'a macOS home folder', pattern: /\/Users\/[A-Za-z0-9._-]+\// },
  { name: 'a GitHub no-reply email', pattern: /@users\.noreply\.github\.com/ },
];

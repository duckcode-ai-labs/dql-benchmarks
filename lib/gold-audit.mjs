// The answer-key audit.
//
// Public gold sets contain many wrong answers (a 2026 audit found 52.8% of
// BIRD mini-dev and 62.8% of Spider 2.0-Snow gold annotations wrong). Every
// case we score has one line in gold-audit.jsonl saying whether we accept the
// publisher's answer. Accuracy is reported on the full set and on the accepted
// subset, and a correction never replaces the publisher's gold: it is scored
// as an alternative beside it.

import { existsSync, readFileSync } from 'node:fs';

export const AUDIT_STATUSES = ['accepted', 'disputed', 'corrected'];

/**
 * @typedef {object} AuditEntry
 * @property {string} caseId
 * @property {'accepted'|'disputed'|'corrected'} status
 * @property {string} [reason]       required unless accepted
 * @property {string} [evidenceSql]  required when corrected: the reference we score as an alternative
 * @property {string} reviewer
 * @property {string} reviewedAt     ISO date
 * @property {string} [upstreamIssue] link to a report filed with the publisher
 */

export function parseAudit(text, source = 'gold-audit.jsonl') {
  const entries = new Map();
  const problems = [];
  text.split(/\r?\n/).forEach((line, index) => {
    if (!line.trim()) return;
    const where = `${source}:${index + 1}`;
    let entry;
    try {
      entry = JSON.parse(line);
    } catch (error) {
      problems.push(`${where}: not JSON (${error.message})`);
      return;
    }
    if (typeof entry.caseId !== 'string' || !entry.caseId) problems.push(`${where}: caseId is required`);
    if (!AUDIT_STATUSES.includes(entry.status)) problems.push(`${where}: status must be one of ${AUDIT_STATUSES.join(', ')}`);
    if ((entry.status === 'disputed' || entry.status === 'corrected') && !entry.reason) {
      problems.push(`${where}: a ${entry.status} case needs a reason`);
    }
    if (entry.status === 'corrected' && !entry.evidenceSql) problems.push(`${where}: a corrected case needs evidenceSql`);
    if (!entry.reviewer) problems.push(`${where}: reviewer is required`);
    if (!entry.reviewedAt || Number.isNaN(Date.parse(entry.reviewedAt))) problems.push(`${where}: reviewedAt must be a date`);
    if (entries.has(entry.caseId)) problems.push(`${where}: ${entry.caseId} is audited twice`);
    entries.set(entry.caseId, entry);
  });
  return { entries, problems };
}

export function loadAudit(path) {
  if (!existsSync(path)) return { entries: new Map(), problems: [] };
  return parseAudit(readFileSync(path, 'utf-8'), path);
}

/**
 * Cases without an audit line cannot be scored: an adapter or scorer that
 * meets one stops rather than guessing whether the gold is right.
 */
export function unauditedCases(caseIds, audit) {
  return caseIds.filter((id) => !audit.entries.has(id));
}

export function acceptedCaseIds(audit) {
  return new Set([...audit.entries.values()].filter((entry) => entry.status === 'accepted').map((entry) => entry.caseId));
}

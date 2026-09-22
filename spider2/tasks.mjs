// Spider 2.0-Lite, SQLite subset: the tasks whose database is available here.
//
// Tasks come from the official repository (data/spider2-lite/repo, pinned by
// commit), databases from the authors' Hugging Face dataset
// (xlangai/spider2-localdb, sqlite.zip, sha256 in data/spider2-lite). Correct
// answers stay in the official evaluation suite, outside every DQL project.

import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';

export const DATA = join(REPO_ROOT, 'data', 'spider2-lite');
export const LITE = join(DATA, 'repo', 'spider2-lite');
export const LOCALDB = join(DATA, 'localdb');
export const EVAL_SUITE = join(LITE, 'evaluation_suite');

/** Every SQLite task (`local…`) with its database file, and the ones without. */
export function readTasks() {
  const all = readFileSync(join(LITE, 'spider2-lite.jsonl'), 'utf-8').split('\n').filter(Boolean).map((line) => JSON.parse(line));
  const local = all.filter((task) => task.instance_id.startsWith('local'));
  const available = new Set(readdirSync(LOCALDB).filter((name) => name.endsWith('.sqlite')).map((name) => name.slice(0, -'.sqlite'.length)));
  const tasks = local.filter((task) => available.has(task.db)).map((task) => ({
    id: task.instance_id,
    db: task.db,
    question: task.question,
    externalKnowledge: task.external_knowledge || null,
  }));
  const missing = [...new Set(local.filter((task) => !available.has(task.db)).map((task) => task.db))].sort();
  return { tasks, total: local.length, missingDatabases: missing, skipped: local.length - tasks.length };
}

/**
 * The question as Spider 2.0-Lite poses it: with its reference document, when
 * the task names one (the official setting gives the document to the system).
 */
export function questionText(task) {
  if (!task.externalKnowledge) return task.question;
  const path = join(LITE, 'resource', 'documents', task.externalKnowledge);
  if (!existsSync(path)) throw new Error(`${task.id}: reference document ${task.externalKnowledge} is missing.`);
  return `${task.question}\n\nReference document (${task.externalKnowledge}):\n${readFileSync(path, 'utf-8').trim()}`;
}

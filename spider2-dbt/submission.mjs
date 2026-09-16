// Write a submission in the shape the publisher's evaluate.py reads:
//
//   <submission>/results_metadata.jsonl
//   <submission>/<instance_id>/<database>.duckdb
//
// evaluate.py only scores instances listed in results_metadata.jsonl and
// divides by that count, so a submission that leaves tasks out scores higher
// than it should. Every submission here lists every graded task; a task with
// no output database is listed and scores 0.

import { copyFileSync, existsSync, mkdirSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

export function submissionRecord(instanceId, database) {
  return { instance_id: instanceId, answer_type: 'file', answer_or_path: database };
}

/**
 * @param {string} submissionDir
 * @param {Array<{instanceId: string, database: string|null}>} tasks  every graded task
 * @param {(task) => string|null} outputDatabase   path of the task's resulting DuckDB, or null
 * @param {{ link?: boolean }} [options]   link instead of copy (only for the untouched pipe check)
 */
export function writeSubmission(submissionDir, tasks, outputDatabase, options = {}) {
  rmSync(submissionDir, { recursive: true, force: true });
  mkdirSync(submissionDir, { recursive: true });
  const lines = [];
  const missing = [];
  for (const task of tasks) {
    const database = task.database ?? `${task.instanceId}.duckdb`;
    lines.push(JSON.stringify(submissionRecord(task.instanceId, database)));
    const source = outputDatabase(task);
    if (!source || !existsSync(source)) {
      missing.push(task.instanceId);
      continue;
    }
    const target = join(submissionDir, task.instanceId, database);
    mkdirSync(join(submissionDir, task.instanceId), { recursive: true });
    if (options.link) symlinkSync(source, target);
    else copyFileSync(source, target);
  }
  writeFileSync(join(submissionDir, 'results_metadata.jsonl'), `${lines.join('\n')}\n`);
  return { listed: tasks.length, missing };
}

// The Spider 2.0-DBT task set as published: instructions, grading rules, and
// where each task's database and gold database live.

import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';

export const UPSTREAM_ROOT = join(REPO_ROOT, 'data', 'spider2-dbt', 'Spider2', 'spider2-dbt');
export const EXAMPLES_DIR = join(UPSTREAM_ROOT, 'examples');
export const GOLD_DIR = join(UPSTREAM_ROOT, 'evaluation_suite', 'gold');
export const EVALUATE_PY = join(UPSTREAM_ROOT, 'evaluation_suite', 'evaluate.py');
export const MANIFEST_PATH = join(REPO_ROOT, 'spider2-dbt', 'manifest.json');

function readJsonl(path) {
  return readFileSync(path, 'utf-8').split(/\r?\n/).filter((line) => line.trim()).map((line) => JSON.parse(line));
}

export function upstreamCommit() {
  const file = join(REPO_ROOT, 'data', 'spider2-dbt', 'UPSTREAM_COMMIT');
  return existsSync(file) ? readFileSync(file, 'utf-8').trim() : null;
}

/** The database a task's dbt profile writes to, e.g. "airbnb.duckdb". */
export function profileDatabase(taskDir) {
  const profile = readFileSync(join(taskDir, 'profiles.yml'), 'utf-8');
  const match = profile.match(/^\s*path:\s*["']?(?:\.\/)?([^"'\n]+?\.duckdb)["']?\s*$/m);
  if (!match) throw new Error(`${taskDir}/profiles.yml: no DuckDB path found.`);
  return match[1];
}

/** Build the inventory from the downloaded data. */
export function readUpstreamTasks() {
  if (!existsSync(EXAMPLES_DIR)) throw new Error('Spider 2.0-DBT is not downloaded. Run spider2-dbt/download.sh.');
  const instructions = new Map(readJsonl(join(EXAMPLES_DIR, 'spider2-dbt.jsonl')).map((task) => [task.instance_id, task]));
  const grading = readJsonl(join(GOLD_DIR, 'spider2_eval.jsonl'));
  const taskDirs = new Set(readdirSync(EXAMPLES_DIR, { withFileTypes: true }).filter((entry) => entry.isDirectory()).map((entry) => entry.name));

  const tasks = grading.map((entry) => {
    const id = entry.instance_id;
    const task = instructions.get(id);
    const evaluations = Array.isArray(entry.evaluation) ? entry.evaluation : [entry.evaluation];
    const taskDir = join(EXAMPLES_DIR, id);
    const goldFiles = evaluations.map((evaluation) => evaluation.parameters.gold);
    const goldDir = join(GOLD_DIR, id);
    const goldPresent = goldFiles.every((file) => existsSync(join(goldDir, file)));
    // A gold folder that holds a database under another name is a
    // configuration slip, not a missing answer.
    const goldOnDisk = existsSync(goldDir)
      ? readdirSync(goldDir).filter((file) => file.endsWith('.duckdb')).sort()
      : [];
    const database = taskDirs.has(id) ? profileDatabase(taskDir) : null;
    return {
      instanceId: id,
      instruction: task?.instruction ?? null,
      instructionSha256: task ? createHash('sha256').update(task.instruction).digest('hex') : null,
      hasTaskDir: taskDirs.has(id),
      database,
      startingDatabasePresent: Boolean(database && existsSync(join(taskDir, database))),
      goldFiles,
      goldPresent,
      goldStatus: goldPresent ? 'present' : goldOnDisk.length ? 'misnamed' : 'missing',
      goldOnDisk,
      checks: evaluations.map((evaluation) => ({
        func: evaluation.func,
        tables: evaluation.parameters.condition_tabs ?? null,
        ignoreOrders: evaluation.parameters.ignore_orders ?? null,
      })),
    };
  }).sort((a, b) => a.instanceId.localeCompare(b.instanceId));

  const graded = new Set(tasks.map((task) => task.instanceId));
  return {
    upstreamCommit: upstreamCommit(),
    tasks,
    ungradedTaskDirs: [...taskDirs].filter((dir) => !graded.has(dir)).sort(),
    instructionsWithoutGrading: [...instructions.keys()].filter((id) => !graded.has(id)).sort(),
  };
}

export function readManifest() {
  if (!existsSync(MANIFEST_PATH)) throw new Error('spider2-dbt/manifest.json is missing. Run: node spider2-dbt/inventory.mjs');
  return JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
}

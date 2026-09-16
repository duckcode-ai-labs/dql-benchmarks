#!/usr/bin/env node
// Record the task set we benchmark against in spider2-dbt/manifest.json, so a
// change upstream shows up as a diff instead of silently changing results.

import { writeFileSync } from 'node:fs';
import { MANIFEST_PATH, readUpstreamTasks } from './tasks.mjs';

const inventory = readUpstreamTasks();
const ids = (predicate) => inventory.tasks.filter(predicate).map((task) => task.instanceId);
const goldMissing = ids((task) => task.goldStatus === 'missing');
const goldMisnamed = ids((task) => task.goldStatus === 'misnamed');
const noStartingDatabase = ids((task) => !task.startingDatabasePresent);
const noInstruction = ids((task) => !task.hasTaskDir || !task.instruction);

const manifest = {
  benchmark: 'spider2-dbt',
  upstream: 'https://github.com/xlang-ai/Spider2/tree/main/spider2-dbt',
  upstreamCommit: inventory.upstreamCommit,
  gradedTasks: inventory.tasks.length,
  // Graded tasks the publisher's grader can never pass, for any entrant:
  // the gold database is absent, or present under a name the grader does not
  // look for.
  goldMissing,
  goldMisnamed,
  noStartingDatabase,
  noInstruction,
  bestPossibleScore: {
    passed: inventory.tasks.length - goldMissing.length - goldMisnamed.length,
    of: inventory.tasks.length,
  },
  ungradedTaskDirs: inventory.ungradedTaskDirs,
  tasks: inventory.tasks,
};

writeFileSync(MANIFEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`${manifest.gradedTasks} graded tasks at upstream ${manifest.upstreamCommit?.slice(0, 8) ?? 'unknown'}.`);
if (goldMissing.length) console.log(`Gold database not published: ${goldMissing.join(', ')}.`);
if (goldMisnamed.length) console.log(`Gold database under a name the grader does not read: ${goldMisnamed.join(', ')}.`);
if (noStartingDatabase.length) console.log(`No starting database: ${noStartingDatabase.join(', ')}.`);
if (noInstruction.length) console.log(`No task folder or instruction: ${noInstruction.join(', ')}.`);
if (manifest.ungradedTaskDirs.length) console.log(`Task folders the grader ignores: ${manifest.ungradedTaskDirs.join(', ')}.`);
console.log(`Best possible score with the published grader: ${manifest.bestPossibleScore.passed}/${manifest.bestPossibleScore.of}.`);

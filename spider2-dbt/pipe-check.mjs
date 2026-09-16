#!/usr/bin/env node
// Prove the scoring pipe before trusting any agent's number.
//
// Submits every task's starting database untouched. No work was done, so the
// grader should pass (almost) nothing; any task that passes untouched is a
// task whose check does not test the instruction, and is reported for the
// answer-key audit.

import { join } from 'node:path';
import { REPO_ROOT } from '../lib/dql.mjs';
import { precheck } from './precheck.mjs';
import { writeSubmission } from './submission.mjs';
import { EXAMPLES_DIR, readManifest } from './tasks.mjs';

const manifest = readManifest();
const submissionDir = join(REPO_ROOT, 'work', 'spider2-dbt', 'submissions', 'untouched');
const written = writeSubmission(
  submissionDir,
  manifest.tasks,
  (task) => (task.database ? join(EXAMPLES_DIR, task.instanceId, task.database) : null),
  { link: true },
);
console.log(`Listed ${written.listed} tasks; ${written.missing.length} without a starting database.`);

const result = precheck(submissionDir);
console.log(`Untouched starting databases: ${result.passed}/${result.graded} pass.`);
const passing = result.cases.filter((entry) => entry.passed).map((entry) => entry.caseId);
if (passing.length) console.log(`Pass without any work (audit these): ${passing.join(', ')}`);

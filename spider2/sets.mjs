// Named task sets: `--set quick` runs spider2/quick-set.json instead of all 87.
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));

/** The task ids of a named set, or undefined for the full set. */
export function taskSet(name) {
  if (!name || name === 'full') return undefined;
  const file = join(HERE, `${name}-set.json`);
  return new Set(Object.keys(JSON.parse(readFileSync(file, 'utf-8')).tasks));
}

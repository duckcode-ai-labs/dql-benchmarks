// Does a result match a gold answer, ignoring column names and row order?
//
// Public gold answers name columns differently from any system under test
// ("total" vs "sum_amount"), so matching is by values. Each row becomes a
// tuple of normalized values sorted within the row; the two results match when
// their multisets of tuples are equal. This is the same rule data.world's
// benchmark states: column order and labels are not taken into account.

const DEFAULT_TOLERANCE = 1e-6;

function isDateLike(value) {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$/.test(value);
}

/** Normalize one cell so equal meanings compare equal. */
export function normalizeValue(value, { tolerance = DEFAULT_TOLERANCE } = {}) {
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'bigint') value = Number(value);
  if (typeof value === 'boolean') return value ? 'bool:true' : 'bool:false';
  if (value instanceof Date) value = value.toISOString();
  if (typeof value === 'number' || (typeof value === 'string' && /^-?\d+(\.\d+)?([eE][-+]?\d+)?$/.test(value.trim()))) {
    const number = Number(value);
    if (!Number.isFinite(number)) return `num:${String(number)}`;
    // Round to the tolerance so 0.1 + 0.2 equals 0.3 and 10 equals 10.0.
    const digits = Math.max(0, Math.round(-Math.log10(tolerance)));
    const rounded = Number(number.toFixed(digits));
    return `num:${Object.is(rounded, -0) ? 0 : rounded}`;
  }
  if (isDateLike(value)) {
    // A date and a midnight timestamp of the same day are the same answer.
    const day = value.slice(0, 10);
    const time = value.slice(11, 19);
    return !time || time === '00:00:00' ? `date:${day}` : `ts:${day}T${time}`;
  }
  return `str:${String(value).trim()}`;
}

function rowValues(row) {
  if (Array.isArray(row)) return row;
  if (row && typeof row === 'object') return Object.values(row);
  return [row];
}

function rowKey(row, options) {
  return rowValues(row).map((value) => normalizeValue(value, options)).sort().join('');
}

/**
 * @param {Array<object|Array>} actual
 * @param {Array<object|Array>} gold
 * @param {object} [options]
 * @param {number} [options.tolerance]
 * @param {boolean} [options.ordered]        require the same row order
 * @param {boolean} [options.allowExtraColumns] actual may carry extra columns
 * @returns {{ match: boolean, reason?: string }}
 */
export function rowsMatch(actual, gold, options = {}) {
  if (!Array.isArray(actual) || !Array.isArray(gold)) return { match: false, reason: 'rows must be arrays' };
  if (actual.length !== gold.length) {
    return { match: false, reason: `row count ${actual.length} does not match gold ${gold.length}` };
  }
  if (actual.length === 0) return { match: true };

  if (options.allowExtraColumns) return extraColumnMatch(actual, gold, options);

  const actualKeys = actual.map((row) => rowKey(row, options));
  const goldKeys = gold.map((row) => rowKey(row, options));
  if (options.ordered) {
    const index = goldKeys.findIndex((key, position) => key !== actualKeys[position]);
    return index === -1 ? { match: true } : { match: false, reason: `row ${index + 1} differs from gold` };
  }
  const counts = new Map();
  for (const key of goldKeys) counts.set(key, (counts.get(key) ?? 0) + 1);
  for (const key of actualKeys) {
    const remaining = counts.get(key) ?? 0;
    if (remaining === 0) return { match: false, reason: 'a row has no matching gold row' };
    counts.set(key, remaining - 1);
  }
  return { match: true };
}

/**
 * Gold columns must each be found among the actual columns (by values), but
 * the actual result may carry more, e.g. a name next to an id. Columns are
 * paired greedily by exact value-sequence equality after sorting both results
 * the same way, which is exact for the unordered case when rows are distinct.
 */
function extraColumnMatch(actual, gold, options) {
  const toColumns = (rows) => {
    const width = rowValues(rows[0]).length;
    return Array.from({ length: width }, (_, column) => rows.map((row) => normalizeValue(rowValues(row)[column], options)));
  };
  const goldColumns = toColumns(gold);
  const actualColumns = toColumns(actual);
  if (actualColumns.length < goldColumns.length) {
    return { match: false, reason: `result has ${actualColumns.length} columns, gold needs ${goldColumns.length}` };
  }
  const sortedSignature = (column) => [...column].sort().join('');
  const available = actualColumns.map((column) => sortedSignature(column));
  const chosen = [];
  for (const column of goldColumns) {
    const signature = sortedSignature(column);
    const index = available.findIndex((candidate, position) => candidate === signature && !chosen.includes(position));
    if (index === -1) return { match: false, reason: 'a gold column has no matching result column' };
    chosen.push(index);
  }
  // Column-wise agreement is necessary but not sufficient: the chosen columns
  // must also agree row by row.
  const projected = actual.map((row) => chosen.map((position) => rowValues(row)[position]));
  return rowsMatch(projected, gold, { ...options, allowExtraColumns: false });
}

/**
 * A LENIENT READING OF THE SAME ANSWER. Strict matching asks for the correct
 * answer's columns and rows exactly (ignoring names and order). This asks a
 * weaker question: does the answer carry every value the correct answer has,
 * whatever else it carries? An answer that returns the right total but leaves
 * out the id column the question implies passes here and fails strictly.
 *
 * Published numbers lead with the strict rule; this one is reported beside it
 * so a reader can see how much of the gap is missing labels rather than wrong
 * numbers, and so our numbers can be read next to benchmarks that grade the
 * query rather than the rows.
 */
export function valuesCovered(actual, gold, options = {}) {
  if (!Array.isArray(actual) || !Array.isArray(gold)) return { match: false, reason: 'rows must be arrays' };
  const cells = (rows) => rows.flatMap((row) => rowValues(row).map((value) => normalizeValue(value, options)));
  const have = new Map();
  for (const cell of cells(actual)) have.set(cell, (have.get(cell) ?? 0) + 1);
  const missing = [];
  for (const cell of cells(gold)) {
    const left = have.get(cell) ?? 0;
    if (left === 0) { missing.push(cell); continue; }
    have.set(cell, left - 1);
  }
  return missing.length === 0
    ? { match: true }
    : { match: false, reason: `${missing.length} value(s) of the correct answer are missing` };
}

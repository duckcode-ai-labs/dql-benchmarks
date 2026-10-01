#!/usr/bin/env node
// Re-score finished insurance runs two ways — strict and lenient — and say why
// every strict-wrong answer was wrong.
//
//   node analysis/insurance-2026-09-29/regrade/regrade.mjs
//
// Read-only on runs/, projects/ and the source tree. Each layer's warehouse
// template is copied into this folder and the copy is opened read-only; the
// copies are removed at the end (pass --keep-warehouses to keep them). Nothing
// here calls a model or the network.
//
// Held-out sets (names starting `heldout`) are sealed: no question id or text
// is written for them, only counts per model × level. Development-set (`all`)
// ids may appear.
//
// Grading, per answer (see regrade.md for the method note):
//   strict  — the run's own verdict (executionMatched); the recorded SQL is
//             re-run on a copy of the layer's warehouse and re-matched with the
//             same rule (rows equal as multisets, column names and order
//             ignored, extra answer columns allowed) to check it.
//   lenient — strict, OR the answer has the correct number of rows and, after
//             dropping the correct answer's label/id columns, every remaining
//             (measure) column matches an answer column row by row. Listing
//             questions (no measure column) keep the strict verdict.
// Strict-wrong answers are classed: stopped, grain_or_shape,
// missing_or_extra_columns, wrong_numbers, other.

import { spawnSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { normalizeValue, rowsMatch, valuesCovered } from '../../../lib/row-match.mjs';
import { measureColumnIndexes as regradeMeasureIndexes } from '../../../insurance/regrade.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..', '..');
const WORK = join(REPO, 'work', 'insurance');
const PYTHON = join(REPO, '.venv', 'bin', 'python');
const KEEP = process.argv.includes('--keep-warehouses');

const MODELS = ['fl-opus', 'fl-sonnet', 'fl-qwen', 'fl-luna', 'fl-sol', 'fl-terra'];
const LEVELS = ['baseline-full', 'L0', 'L1', 'L2', 'L3', 'LB', 'W0', 'W1', 'W2', 'WB'];
const SETS = ['heldout-3', 'all'];
const CLASSES = ['wrong_numbers', 'missing_or_extra_columns', 'grain_or_shape', 'stopped', 'other'];
const TRUSTED = new Set(['certified', 'governed']);
const sealed = (set) => set.startsWith('heldout');
// The plain text-to-SQL baseline runs on the L0 warehouse (insurance/baseline-text2sql.mjs).
const warehouseLayer = (level) => (level === 'baseline-full' ? 'L0' : level);

// ---------------------------------------------------------------- warehouses
const WAREHOUSE_DIR = join(HERE, '.warehouses');
function warehouseCopy(layer) {
  const source = join(WORK, 'projects', layer, 'acme_insurance.duckdb');
  // Keep the file name: recorded SQL qualifies tables as "acme_insurance"."main".<t>.
  const target = join(WAREHOUSE_DIR, layer, 'acme_insurance.duckdb');
  if (!existsSync(target)) {
    mkdirSync(dirname(target), { recursive: true });
    copyFileSync(source, target);
    if (existsSync(`${source}.wal`)) copyFileSync(`${source}.wal`, `${target}.wal`);
  }
  return target;
}

function runSql(database, statements) {
  if (statements.length === 0) return {};
  const result = spawnSync(PYTHON, [join(REPO, 'lib', 'duckdb_query.py')], {
    input: JSON.stringify({ database, queries: statements.map((sql, index) => ({ id: String(index), sql })) }),
    encoding: 'utf-8', maxBuffer: 512 * 1024 * 1024,
  });
  if (result.status !== 0) throw new Error(result.stderr);
  const out = JSON.parse(result.stdout);
  return Object.fromEntries(statements.map((sql, index) => [sql, out[String(index)]]));
}

// ------------------------------------------------------------- run stores
// The rows the run actually showed live in the run store
// (project/.dql/local/agent-runs.sqlite → agent_run_artifacts.payload_json →
// { sql, result: { columns, rows } }). They include what DQL computes after the
// query (a governed ratio metric is numerator ÷ denominator in DQL, not in the
// SQL), so they are preferred to a re-run. The store is copied first and the
// copy is read. Stores of resumed attempts (<set>.attempt-N, <set>.aborted-N)
// are read too; answers are matched to a stored result by identical SQL text.
const STORE_DIR = join(HERE, '.tmp-stores');
const STORE_READER = `
import json, sqlite3, sys
out = {}
ambiguous = 0
for path in sys.argv[1:]:
    connection = sqlite3.connect(path)
    for (payload,) in connection.execute("select payload_json from agent_run_artifacts"):
        try:
            artifact = json.loads(payload)
        except Exception:
            continue
        sql = artifact.get("sql")
        result = artifact.get("result")
        if not sql or not isinstance(result, dict) or not isinstance(result.get("rows"), list):
            continue
        columns = result.get("columns") or []
        rows = []
        for row in result["rows"]:
            if isinstance(row, dict):
                keys = columns if columns else list(row.keys())
                rows.append([row.get(key) for key in keys])
            else:
                rows.append(row)
        entry = {"columns": columns, "rows": rows, "rowCount": result.get("rowCount")}
        if sql in out and out[sql]["rows"] != rows:
            ambiguous += 1
            continue
        out.setdefault(sql, entry)
    connection.close()
json.dump({"results": out, "ambiguous": ambiguous}, sys.stdout)
`;
function storeResults(model, level, set) {
  const levelDir = join(WORK, 'runs', model, level);
  const dirs = readdirSync(levelDir).filter((name) => name === set || name.startsWith(`${set}.attempt-`) || name.startsWith(`${set}.aborted-`));
  const copies = [];
  for (const name of dirs) {
    const source = join(levelDir, name, 'project', '.dql', 'local', 'agent-runs.sqlite');
    if (!existsSync(source)) continue;
    const target = join(STORE_DIR, model, level, name, 'agent-runs.sqlite');
    mkdirSync(dirname(target), { recursive: true });
    copyFileSync(source, target);
    if (existsSync(`${source}-wal`)) copyFileSync(`${source}-wal`, `${target}-wal`);
    copies.push(target);
  }
  // The finished set's own store first, so its result wins a tie.
  copies.sort((a, b) => (a.includes(`/${set}/`) ? -1 : 0) - (b.includes(`/${set}/`) ? -1 : 0));
  if (!copies.length) return { results: {}, ambiguous: 0 };
  const run = spawnSync(PYTHON, ['-c', STORE_READER, ...copies], { encoding: 'utf-8', maxBuffer: 512 * 1024 * 1024 });
  if (run.status !== 0) throw new Error(run.stderr);
  return JSON.parse(run.stdout);
}

// --------------------------------------------------------- measure columns
const AGGREGATE = /\b(sum|count|avg|average|min|max|median|stddev\w*|datediff|date_diff)\s*\(/i;
const ARITHMETIC = /[)\w]\s*([+*/]|\s-\s)\s*[(\w]/;
const MEASURE_NAME = /(sum|count|avg|average|total|amount|ratio|size|no_?of|number_of|days|time|loss|premium|rate|pct|percent|share|cost|paid|value)/i;
const IDENTIFIER_NAME = /(identifier|(^|_)id$|_number$|_code$|_name$|_date$|^name$|^(agent|party|policy|policyholder|holder|claim|customer)_?id$)/i;
const isIdentifierName = (column) => IDENTIFIER_NAME.test(column) || /[a-z]ID$/.test(column);

/** The top-level projection of a query, split at top-level commas (skips CTE bodies). */
function topLevelProjection(sql) {
  const text = sql ?? '';
  let depth = 0; let quote = null; let start = -1; let end = -1;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quote) { if (ch === quote) quote = null; continue; }
    if (ch === "'" || ch === '"') { quote = ch; continue; }
    if (ch === '(') depth += 1;
    else if (ch === ')') depth -= 1;
    else if (depth === 0) {
      const rest = text.slice(i, i + 7).toLowerCase();
      const boundary = i === 0 || /\W/.test(text[i - 1]);
      if (start < 0 && boundary && /^select\W/.test(rest)) { start = i + 6; i += 5; continue; }
      if (start >= 0 && boundary && /^from\W/.test(rest.slice(0, 5))) { end = i; break; }
    }
  }
  if (start < 0) return [];
  const projection = text.slice(start, end < 0 ? undefined : end);
  const parts = []; let current = ''; depth = 0; quote = null;
  for (const ch of projection) {
    if (quote) { current += ch; if (ch === quote) quote = null; continue; }
    if (ch === "'" || ch === '"') quote = ch;
    if (ch === '(') depth += 1;
    if (ch === ')') depth -= 1;
    if (ch === ',' && depth === 0) { parts.push(current); current = ''; continue; }
    current += ch;
  }
  parts.push(current);
  return parts.map((part) => part.replace(/^\s*distinct\s+/i, ''));
}

/**
 * The correct answer's measure columns: the numbers the question asks for.
 * A column is a measure when the correct query aggregates or computes it, when
 * its name reads like a number (and not like an id/label), or when its values
 * are non-integer numbers. Everything else (ids, numbers-as-identifiers,
 * names, dates) is a label. This widens insurance/regrade.mjs's rule (which
 * misses CTE queries and names like "Loss"); a wider measure set makes the
 * lenient grade stricter, not looser.
 */
function measureIndexes(goldSql, columns, rows) {
  const expressions = topLevelProjection(goldSql);
  const fromRegrade = new Set(regradeMeasureIndexes(goldSql, columns));
  return columns.map((column, index) => {
    const expression = expressions.length === columns.length ? expressions[index] : undefined;
    const computed = expression ? (AGGREGATE.test(expression) || ARITHMETIC.test(expression.replace(/\bas\s+\w+\s*$/i, ''))) : false;
    const values = rows.map((row) => (Array.isArray(row) ? row[index] : Object.values(row)[index])).filter((v) => v !== null && v !== undefined);
    const fractional = values.length > 0 && values.every((v) => typeof v === 'number') && values.some((v) => !Number.isInteger(v));
    const named = MEASURE_NAME.test(column) && !isIdentifierName(column);
    return computed || named || fractional || fromRegrade.has(index) ? index : -1;
  }).filter((index) => index >= 0);
}

// ------------------------------------------------------------- comparisons
const valuesOf = (row) => (Array.isArray(row) ? row : Object.values(row));
const project = (rows, indexes) => rows.map((row) => indexes.map((index) => valuesOf(row)[index]));
const width = (rows) => (rows.length ? valuesOf(rows[0]).length : 0);

/** Are all gold rows found among the answer's rows (answer may have more rows and columns)? */
function goldRowsContained(actual, gold) {
  if (!gold.length || !actual.length) return false;
  const actualColumns = Array.from({ length: width(actual) }, (_, c) => new Set(actual.map((row) => normalizeValue(valuesOf(row)[c]))));
  const mapping = [];
  for (let c = 0; c < width(gold); c += 1) {
    const wanted = gold.map((row) => normalizeValue(valuesOf(row)[c]));
    const index = actualColumns.findIndex((set, position) => !mapping.includes(position) && wanted.every((value) => set.has(value)));
    if (index < 0) return false;
    mapping.push(index);
  }
  const key = (values) => values.map((value) => normalizeValue(value)).join('\u0001');
  const have = new Map();
  for (const row of project(actual, mapping)) have.set(key(row), (have.get(key(row)) ?? 0) + 1);
  return gold.every((row) => {
    const k = key(valuesOf(row)); const left = have.get(k) ?? 0;
    if (!left) return false; have.set(k, left - 1); return true;
  });
}

const sumColumn = (rows, index) => rows.reduce((total, row) => total + (Number(valuesOf(row)[index]) || 0), 0);
function mergedTotal(actual, gold, measures) {
  // A single-row (or fewer-row) answer whose numbers are the gold measures summed.
  if (!measures.length || !actual.length) return false;
  const cells = new Set(actual.flatMap((row) => valuesOf(row).map((value) => normalizeValue(value, { tolerance: 1e-2 }))));
  return measures.every((index) => cells.has(normalizeValue(sumColumn(gold, index), { tolerance: 1e-2 })));
}

/**
 * Presentation rounding: the answer's measure values equal the correct values
 * rounded to d decimals (d = 1..4, the same d for the whole answer). An answer
 * that shows more digits than that, or whole numbers for fractional values,
 * does not qualify.
 */
function measuresMatchRounded(actual, goldRows, measures) {
  if (!measures.length || actual.length !== goldRows.length) return false;
  const gold = project(goldRows, measures);
  return [1, 2, 3, 4].some((d) => rowsMatch(actual, gold.map((row) => row.map((value) => (typeof value === 'number' && !Number.isInteger(value) ? Number(value.toFixed(d)) : value))), { allowExtraColumns: true }).match);
}

/** Which way a label column the answer gets "wrong" differs, when the numbers are right. */
function labelDifference(actual, goldRows, measures) {
  if (width(actual) < width(goldRows)) return 'label_column_missing';
  const exact = (values) => values.map((value) => normalizeValue(value)).sort().join('\u0001');
  const loose = (values) => values.map((value) => String(value ?? '').trim().toLowerCase()).sort().join('\u0001');
  const answerColumns = Array.from({ length: width(actual) }, (_, c) => actual.map((row) => valuesOf(row)[c]));
  const labels = Array.from({ length: width(goldRows) }, (_, c) => c).filter((c) => !measures.includes(c));
  const kinds = labels.map((c) => {
    const values = goldRows.map((row) => valuesOf(row)[c]);
    if (answerColumns.some((column) => exact(column) === exact(values))) return 'same';
    if (answerColumns.some((column) => loose(column) === loose(values))) return 'format';
    return 'other';
  });
  if (kinds.includes('other')) return 'label_column_substituted';
  if (kinds.includes('format')) return 'label_case_or_format';
  return 'label_column_differs';
}

/** Why a strict-wrong answer was wrong: [class, sub-kind]. */
function classify({ result, executed, goldRows, measures }) {
  const sql = result.answer?.sql;
  if (!sql) return ['stopped', result.route === 'clarify' ? 'asked_to_clarify' : 'no_sql'];
  if (result.kind === 'no_answer') return ['stopped', 'stopped_with_sql'];
  if (!executed || executed.error) return ['other', 'sql_did_not_rerun'];
  const actual = executed.rows;
  if (rowsMatch(actual, goldRows, { allowExtraColumns: true }).match) return ['other', 'rows_match_gold_but_recorded_wrong'];
  if (actual.length !== goldRows.length) {
    if (actual.length === 0) return ['grain_or_shape', 'empty_result'];
    if (goldRows.length === 1 && actual.length > 1) return ['grain_or_shape', 'list_for_a_total'];
    if (actual.length < goldRows.length && mergedTotal(actual, goldRows, measures)) return ['grain_or_shape', 'rows_merged_into_total'];
    if (goldRows.length > 1 && actual.length === 1) return ['grain_or_shape', 'total_for_a_list'];
    if (actual.length > goldRows.length) return ['grain_or_shape', goldRowsContained(actual, goldRows) ? 'extra_rows_gold_rows_inside' : 'more_rows'];
    return ['grain_or_shape', goldRowsContained(goldRows, actual) ? 'missing_rows_subset_of_gold' : 'fewer_rows'];
  }
  if (measures.length) {
    if (rowsMatch(actual, project(goldRows, measures), { allowExtraColumns: true }).match) {
      return ['missing_or_extra_columns', labelDifference(actual, goldRows, measures)];
    }
    if (measuresMatchRounded(actual, goldRows, measures)) return ['wrong_numbers', 'rounding_or_precision'];
    const perColumn = measures.every((index) => rowsMatch(actual, project(goldRows, [index]), { allowExtraColumns: true }).match);
    return ['wrong_numbers', perColumn ? 'numbers_on_wrong_rows' : 'values_differ'];
  }
  // A listing question: no measure; the listed values are what was asked for.
  if (width(actual) < width(goldRows) && rowsMatch(goldRows, actual, { allowExtraColumns: true }).match) {
    return ['missing_or_extra_columns', 'listing_column_missing'];
  }
  return ['wrong_numbers', 'listing_values_differ'];
}

// ------------------------------------------------------------------- gold
const goldFiles = {
  all: JSON.parse(readFileSync(join(WORK, 'gold', 'answers.json'), 'utf-8')),
  'heldout-3': JSON.parse(readFileSync(join(WORK, 'gold', 'heldout-3.json'), 'utf-8')),
};
const goldById = Object.fromEntries(Object.entries(goldFiles).map(([set, file]) => [set, new Map(file.cases.map((c) => [c.id, c]))]));

// ------------------------------------------------------------------- grade
const cells = [];
const skipped = [];
const devCases = [];
const rowsByDatabase = new Map();

for (const model of MODELS) {
  for (const level of LEVELS) {
    for (const set of SETS) {
      const file = join(WORK, 'runs', model, level, set, 'report.json');
      if (!existsSync(file)) {
        if (existsSync(dirname(file))) skipped.push({ model, level, set, why: 'no report.json (in progress)' });
        continue;
      }
      const report = JSON.parse(readFileSync(file, 'utf-8'));
      if (report.invalid) { skipped.push({ model, level, set, why: `invalid: ${report.invalid.reason ?? 'flagged'}` }); continue; }
      const layer = warehouseLayer(level);
      const database = warehouseCopy(layer);
      if (!rowsByDatabase.has(layer)) rowsByDatabase.set(layer, {});
      const cache = rowsByDatabase.get(layer);
      const fresh = [...new Set(report.results.map((r) => r.answer?.sql).filter((sql) => sql && !(sql in cache)))];
      Object.assign(cache, runSql(database, fresh));
      const store = level === 'baseline-full' ? { results: {}, ambiguous: 0 } : storeResults(model, level, set);

      const graded = report.results.map((result) => {
        const gold = goldById[set].get(result.name);
        const goldRows = result.expected?.goldRows ?? gold?.gold.rows ?? [];
        const allowExtra = result.expected?.goldAllowExtraColumns ?? true;
        const ordered = result.expected?.goldOrdered ?? false;
        const columns = gold?.gold.columns ?? [];
        const measures = gold ? measureIndexes(gold.goldSql, columns, goldRows) : [];
        const sql = result.answer?.sql;
        const rerun = sql ? cache[sql] : undefined;
        const stored = sql ? store.results[sql] : undefined;
        // The rows the run showed when they are in the store, else the re-run.
        const executed = stored ?? (rerun && !rerun.error ? rerun : undefined);
        const rowSource = stored ? 'store' : executed ? 'rerun' : 'none';
        const strict = result.executionMatched === true;
        const matches = (rows) => rowsMatch(rows, goldRows, { allowExtraColumns: allowExtra, ordered }).match;
        const rerunStrict = rerun && !rerun.error ? matches(rerun.rows) : false;
        const rowsStrict = executed ? matches(executed.rows) : false;
        let klass = null; let sub = null;
        if (!strict) [klass, sub] = classify({ result, executed, goldRows, measures });
        const lenient = strict || (klass === 'missing_or_extra_columns' && measures.length > 0);
        const lenientRounded = lenient || (klass === 'wrong_numbers' && sub === 'rounding_or_precision');
        const cellCover = strict || (executed?.rows && measures.length ? valuesCovered(executed.rows, project(goldRows, measures)).match : false);
        const trust = result.answer?.trustState ?? 'none';
        return {
          id: result.name, strict, rerunStrict, rowsStrict, rowSource, rerunError: Boolean(sql && (!rerun || rerun.error)), hasSql: Boolean(sql),
          lenient, lenientRounded, cellCover, klass, sub, trust, trusted: TRUSTED.has(trust), measureColumns: measures.length, goldColumns: columns.length,
          goldFound: Boolean(gold),
        };
      });

      const n = graded.length;
      const count = (predicate) => graded.filter(predicate).length;
      const classCounts = Object.fromEntries(CLASSES.map((k) => [k, count((g) => g.klass === k)]));
      const subCounts = {};
      for (const g of graded) if (g.sub) subCounts[`${g.klass}:${g.sub}`] = (subCounts[`${g.klass}:${g.sub}`] ?? 0) + 1;
      const trusted = graded.filter((g) => g.trusted);
      const cell = {
        model, level, set, n,
        strict: count((g) => g.strict),
        // The report's own headline: `passed` for a DQL run (the metrics block's
        // execution_match_rate is over answerable_case_count, which a resumed run
        // leaves partial), passed results for the baseline.
        reportPassed: typeof report.passed === 'number' ? report.passed : count((g) => report.results.find((r) => r.name === g.id)?.passed === true),
        rowsFromStore: count((g) => g.rowSource === 'store'), rowsFromRerun: count((g) => g.rowSource === 'rerun'), rowsNone: count((g) => g.hasSql && g.rowSource === 'none'),
        storeAmbiguous: store.ambiguous,
        rowsStrict: count((g) => g.rowsStrict), rowsDisagree: count((g) => g.rowSource !== 'none' && g.rowsStrict !== g.strict),
        rerunStrict: count((g) => g.rerunStrict), rerunDisagrees: count((g) => g.hasSql && !g.rerunError && g.rerunStrict !== g.strict),
        rerunErrors: count((g) => g.rerunError), rerunErrorsOnStrictRight: count((g) => g.rerunError && g.strict),
        lenient: count((g) => g.lenient), lenientRounded: count((g) => g.lenientRounded), cellCover: count((g) => g.cellCover),
        strictWrong: count((g) => !g.strict), classes: classCounts, subKinds: subCounts,
        trusted: trusted.length,
        trustedWrongStrict: trusted.filter((g) => !g.strict).length,
        trustedWrongLenient: trusted.filter((g) => !g.lenient).length,
        trustedWrongNumbers: trusted.filter((g) => g.klass === 'wrong_numbers').length,
        trustedWrongNumbersExRounding: trusted.filter((g) => g.klass === 'wrong_numbers' && g.sub !== 'rounding_or_precision').length,
        trustedClasses: Object.fromEntries(CLASSES.map((k) => [k, trusted.filter((g) => g.klass === k).length])),
        trustedSubKinds: trusted.filter((g) => g.sub).reduce((out, g) => ({ ...out, [`${g.klass}:${g.sub}`]: (out[`${g.klass}:${g.sub}`] ?? 0) + 1 }), {}),
        goldMissing: count((g) => !g.goldFound),
        dqlVersion: report.identity?.dql?.version ?? null, model_id: report.identity?.model ?? null,
      };
      cells.push(cell);
      if (!sealed(set)) {
        for (const g of graded) {
          if (!g.strict) devCases.push({ model, level, id: g.id, klass: g.klass, sub: g.sub, trust: g.trust, lenient: g.lenient });
        }
      }
    }
  }
}

if (!KEEP) rmSync(WAREHOUSE_DIR, { recursive: true, force: true });
rmSync(STORE_DIR, { recursive: true, force: true });

// ---------------------------------------------------------------- summarise
const pct = (k, n) => (n ? `${((k / n) * 100).toFixed(1)}%` : '—');
const find = (model, level, set) => cells.find((c) => c.model === model && c.level === level && c.set === set);
const modelName = (m) => m.replace(/^fl-/, '');
const presentModels = (set) => MODELS.filter((m) => cells.some((c) => c.model === m && c.set === set));

function pooledClasses(filter) {
  const pool = cells.filter(filter);
  const out = Object.fromEntries(CLASSES.map((k) => [k, pool.reduce((t, c) => t + c.classes[k], 0)]));
  out.total = pool.reduce((t, c) => t + c.strictWrong, 0);
  return out;
}
function pooledSubs(filter) {
  const out = {};
  for (const c of cells.filter(filter)) for (const [k, v] of Object.entries(c.subKinds)) out[k] = (out[k] ?? 0) + v;
  return Object.fromEntries(Object.entries(out).sort((a, b) => b[1] - a[1]));
}

const summary = { heldout3: {}, all: {} };
for (const set of SETS) {
  const key = set === 'all' ? 'all' : 'heldout3';
  summary[key].pooled = pooledClasses((c) => c.set === set);
  summary[key].pooledExBaseline = pooledClasses((c) => c.set === set && c.level !== 'baseline-full');
  summary[key].perModel = Object.fromEntries(presentModels(set).map((m) => [m, pooledClasses((c) => c.set === set && c.model === m)]));
  summary[key].subKinds = pooledSubs((c) => c.set === set);
}

// ------------------------------------------------------------------ markdown
const md = [];
const cellsOf = (set) => cells.filter((c) => c.set === set);
const sum = (list, key) => list.reduce((t, c) => t + c[key], 0);
md.push('# Insurance runs re-graded: strict vs lenient', '');
md.push(`Generated ${new Date().toISOString()} by \`regrade.mjs\` in this folder (\`node analysis/insurance-2026-09-29/regrade/regrade.mjs\`; re-runnable, read-only on runs/, projects/ and the source tree, no model or network calls). Scope: runs ${MODELS.join(', ')}; levels ${LEVELS.join(', ')}; sets heldout-3 and all. Held-out results appear as counts only.`, '');

md.push('## Method', '');
md.push('**Which rows are graded.** For a DQL run, the rows the answer actually showed are read from a copy of the run store (`<run>/<level>/<set>[.attempt-N]/project/.dql/local/agent-runs.sqlite` → `agent_run_artifacts` → `{ sql, result }`), matched to `results[].answer.sql` by identical SQL text. These include what DQL computes after the query (a governed ratio metric such as average loss per claim is numerator ÷ denominator in DQL, not in the SQL). When no stored result exists, the recorded SQL is re-run on a byte copy of the layer\'s warehouse template (`work/insurance/projects/<layer>/acme_insurance.duckdb`, opened read-only, external access off). The text-to-SQL baseline is always re-run, on the L0 warehouse as `insurance/baseline-text2sql.mjs` does. Gold rows are the ones the run was judged against (`results[].expected.goldRows`; the gold file for the baseline).', '');
md.push('**Strict** (the published number) — the run\'s own `executionMatched`: the answer\'s rows equal the correct rows as a multiset; column names and column order are ignored; extra answer columns are allowed; numbers compare after rounding to 1e-6; a date equals a midnight timestamp of the same day. This script recomputes it from the graded rows as a check.', '');
md.push('**Lenient ("measures")** — in the spirit of Cube\'s strict vs OLAP-aware verdicts: strict-right, **or** all of');
md.push('1. the answer has exactly as many rows as the correct answer;');
md.push('2. the correct answer has at least one *measure* column (a listing question — ids, names, dates only — keeps its strict verdict);');
md.push('3. after dropping the correct answer\'s *label* columns, every measure column is matched by some answer column **row by row**, with the strict value rule.', '');
md.push('So lenient accepts an answer whose numbers are right but that leaves out a label/id column, returns a different label for the same rows (a party name where the gold has the party id), or writes the same label in a different case/format. It does **not** accept a different row count (a list answered as a total or vice versa, merged, missing or extra rows), numbers that differ even by rounding, right numbers attached to the wrong rows, or a wrong listing.', '');
md.push('*Measure* columns of the correct answer: those its top-level SELECT aggregates or computes (`sum/count/avg/min/max/datediff/…` or arithmetic), whose name reads like a number and not like an id or label (`total`, `amount`, `loss`, `premium`, `ratio`, `count`, `no_of` …; names ending `_id/_number/_code/_name/_date` or containing `identifier` are labels), or whose values are fractional. Everything else (ids, policy/claim numbers, names, dates) is a label. This widens `insurance/regrade.mjs`\'s rule (which misses CTE queries and bare names like `Loss`); a wider measure set makes lenient stricter.', '');
md.push('Two further columns, reported beside the headline and not part of it: **lenient + rounding** also accepts measure values that equal the correct values rounded to 1–4 decimals (the answer presented a rounded average or ratio); **cellCover** is `insurance/regrade.mjs`\'s own "measures" rule (every gold measure value appears somewhere among the answer\'s cells, no row-count or row-alignment check) — looser than lenient.', '');
md.push('**Why a strict-wrong answer was wrong** (first rule that applies):', '');
md.push('1. **stopped** — no SQL recorded: the run stopped (`no_sql`) or asked to clarify (`asked_to_clarify`).');
md.push('2. **other** — SQL recorded but no stored result and it fails on re-run (`sql_did_not_rerun`; in practice baseline SQL that never ran), or the rows match although the run said wrong (`rows_match_gold_but_recorded_wrong`; none found).');
md.push('3. **grain_or_shape** — the row count differs: `list_for_a_total` (1 gold row, several answer rows), `total_for_a_list`, `rows_merged_into_total` (fewer rows carrying the gold measures summed), `empty_result`, `more_rows`, `extra_rows_gold_rows_inside` (all gold rows plus more, typically a missing filter), `fewer_rows`, `missing_rows_subset_of_gold`.');
md.push('4. **missing_or_extra_columns** — same row count and every measure matches row by row, but a label column is `label_column_missing`, `label_column_substituted` (a different label, e.g. name for id), `label_case_or_format` (same label, different case/format), or `label_column_differs` (label present but paired with the rows differently); for a listing question, `listing_column_missing` (a strict subset of the correct columns; not lenient-right).');
md.push('5. **wrong_numbers** — same row count but measure values differ: `values_differ`, `rounding_or_precision` (equal after rounding the gold to 1–4 decimals), `numbers_on_wrong_rows` (each measure column\'s values are present but paired with the wrong rows); for a listing question, `listing_values_differ` (the listed ids/dates are wrong).', '');
md.push('**Trust.** An answer is *trusted* when `answer.trustState` is `certified` or `governed`. Wrong-trusted is reported as strict-wrong ÷ trusted and "numbers-only" = trusted answers classed `wrong_numbers` ÷ trusted (a trusted answer that is wrong only in shape or label is excluded from numbers-only). The per-cell tables also give lenient-wrong and numbers-only excluding rounding.', '');

if (skipped.length) {
  md.push('**Skipped reports**: ' + skipped.map((s) => `${s.model} ${s.level} ${s.set} (${s.why})`).join('; ') + '.', '');
}

function grid(set, title, render, note) {
  const models = presentModels(set);
  md.push(`### ${title}`, '');
  if (note) md.push(note, '');
  md.push(`| Level | ${models.map(modelName).join(' | ')} |`, `|---|${models.map(() => '---:').join('|')}|`);
  for (const level of LEVELS) {
    if (!models.some((m) => find(m, level, set))) continue;
    md.push(`| ${level} | ${models.map((m) => { const c = find(m, level, set); return c ? render(c) : '—'; }).join(' | ')} |`);
  }
  md.push('');
}
const acc = (k, n) => `${((k / n) * 100).toFixed(1)}`;

for (const set of SETS) {
  const label = set === 'all' ? 'Development set `all` (41 questions)' : 'Held-out set `heldout-3` (40 questions, sealed — counts only)';
  md.push(`## ${label}`, '');
  grid(set, 'Accuracy, strict → lenient (%)', (c) => `${acc(c.strict, c.n)} → **${acc(c.lenient, c.n)}**`, `Cell = strict % → lenient %. Denominator ${set === 'all' ? 41 : 40}.`);
  grid(set, 'Accuracy, lenient + rounding (%)', (c) => `${acc(c.lenientRounded, c.n)}`);
  grid(set, 'Trusted answers that were wrong: strict vs numbers-only', (c) => (c.trusted ? `${c.trustedWrongStrict}/${c.trusted} (${pct(c.trustedWrongStrict, c.trusted)}) · ${c.trustedWrongNumbers}/${c.trusted} (${pct(c.trustedWrongNumbers, c.trusted)})` : '0 trusted'),
    'Cell = strict-wrong/trusted · wrong-numbers/trusted. Levels without certified blocks or governed metrics trust nothing.');
  grid(set, 'Strict-wrong answers by class', (c) => `${c.classes.wrong_numbers} / ${c.classes.missing_or_extra_columns} / ${c.classes.grain_or_shape} / ${c.classes.stopped} / ${c.classes.other}`,
    'Cell = wrong_numbers / missing_or_extra_columns / grain_or_shape / stopped / other.');

  const s = summary[set === 'all' ? 'all' : 'heldout3'];
  md.push('### Why strict-wrong answers were wrong — pooled', '');
  md.push(`| Scope | Strict-wrong | ${CLASSES.join(' | ')} |`, `|---|---:|${CLASSES.map(() => '---:').join('|')}|`);
  const row = (name, p) => md.push(`| ${name} | ${p.total} | ${CLASSES.map((k) => `${p[k]} (${pct(p[k], p.total)})`).join(' | ')} |`);
  row('all models, all levels', s.pooled);
  row('all models, DQL levels only', s.pooledExBaseline);
  row('all models, baseline only', pooledClasses((c) => c.set === set && c.level === 'baseline-full'));
  for (const [m, p] of Object.entries(s.perModel)) row(modelName(m), p);
  md.push('', '| Class:sub-kind (pooled) | Count |', '|---|---:|');
  for (const [k, v] of Object.entries(s.subKinds)) md.push(`| ${k} | ${v} |`);
  md.push('');

  const trustedPool = cellsOf(set).filter((c) => c.trusted > 0);
  if (trustedPool.length) {
    const subs = {};
    for (const c of trustedPool) for (const [k, v] of Object.entries(c.trustedSubKinds)) subs[k] = (subs[k] ?? 0) + v;
    md.push(`Trusted answers, pooled: ${sum(trustedPool, 'trusted')} trusted; strict-wrong ${sum(trustedPool, 'trustedWrongStrict')}, lenient-wrong ${sum(trustedPool, 'trustedWrongLenient')}, wrong numbers ${sum(trustedPool, 'trustedWrongNumbers')} (${sum(trustedPool, 'trustedWrongNumbersExRounding')} excluding rounding). Why: ${Object.entries(subs).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v}`).join(', ') || '—'}.`, '');
  }

  md.push('### Per cell detail', '');
  md.push('| Model | Level | n | Strict | Check | Rows from store / re-run | Re-run disagrees | Lenient | +rounding | cellCover | Trusted | Trusted-wrong strict / lenient / numbers / numbers ex-rounding |', '|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|---|');
  for (const c of cellsOf(set)) {
    const check = c.strict === c.reportPassed && c.rowsDisagree === 0 ? 'ok' : `⚑ passed=${c.reportPassed}, rows disagree ${c.rowsDisagree}`;
    md.push(`| ${modelName(c.model)} | ${c.level} | ${c.n} | ${c.strict} | ${check} | ${c.rowsFromStore} / ${c.rowsFromRerun}${c.rowsNone ? ` (+${c.rowsNone} unrunnable)` : ''} | ${c.rerunDisagrees} | ${c.lenient} | ${c.lenientRounded} | ${c.cellCover} | ${c.trusted} | ${c.trustedWrongStrict} / ${c.trustedWrongLenient} / ${c.trustedWrongNumbers} / ${c.trustedWrongNumbersExRounding} |`);
  }
  md.push('', '"Check" = strict equals the report\'s `passed` and the strict rule re-applied to the graded rows agrees with every recorded verdict.', '');
}

const gained = {};
for (const d of devCases.filter((x) => x.lenient)) gained[d.id] = (gained[d.id] ?? 0) + 1;
const gainedList = Object.entries(gained).sort((a, b) => b[1] - a[1]);
if (gainedList.length) {
  md.push('## Development questions rescued by the lenient rule', '', 'Number of model×level cells in which each `all` question is strict-wrong but lenient-right:', '');
  md.push('| Question id | Cells | Sub-kinds |', '|---|---:|---|');
  for (const [id, k] of gainedList) {
    const subs = [...new Set(devCases.filter((d) => d.id === id && d.lenient).map((d) => d.sub))].join(', ');
    md.push(`| \`${id}\` | ${k} | ${subs} |`);
  }
  md.push('');
}

md.push('## Caveats', '');
md.push(`- Every strict verdict was reproduced: recorded \`executionMatched\` equals the report's \`passed\` in ${cells.filter((c) => c.strict === c.reportPassed).length}/${cells.length} cells, and re-applying the strict rule to the graded rows disagrees with the recording for ${sum(cells, 'rowsDisagree')} answers.`);
md.push(`- Rows came from the run store for ${sum(cells, 'rowsFromStore')} answers and from a re-run for ${sum(cells, 'rowsFromRerun')} (all baseline). ${sum(cells, 'rowsNone')} answers have SQL that has no stored result and fails on re-run (baseline SQL that never ran; classed other:sql_did_not_rerun). Stored results with conflicting rows for the same SQL: ${sum(cells, 'storeAmbiguous')}.`);
md.push(`- Re-running the recorded SQL alone disagrees with the recorded verdict for ${sum(cells, 'rerunDisagrees')} DQL answers, all semantic-tier answers at LB/WB where DQL derives the shown column from the SQL's columns (a governed ratio such as average loss per claim: the SQL returns numerator and denominator, DQL shows the ratio). The stored rows have one column more or fewer than the re-run in every case. Grading the stored rows avoids this; a re-run-only regrade (e.g. \`insurance/regrade.mjs\` as written) would under-count those answers.`);
md.push('- The report\'s `metrics.execution_match_rate` is computed over `metrics.answerable_case_count`, which is partial in resumed runs (e.g. 4 or 5 of 40); use `passed`/`executionMatched`, not that rate.');
md.push('- `grain_or_shape` is decided by row count alone, so a wrong filter that returns more or fewer rows lands there rather than in wrong_numbers (see the `more_rows`/`fewer_rows`/`empty_result` sub-kinds).');
md.push('- The measure/label split is heuristic (names, the correct query\'s projection, fractional values). A label misread as a measure makes lenient stricter; a measure misread as a label would make it looser.');
md.push('- fl-luna, fl-sol and fl-terra were still running; only finished, valid reports are graded, so their rows are partial.');
md.push('');

writeFileSync(join(HERE, 'regrade.md'), `${md.join('\n')}\n`);
writeFileSync(join(HERE, 'regrade.json'), `${JSON.stringify({
  generatedAt: new Date().toISOString(),
  method: {
    rows: 'run-store result for identical SQL (copy of agent-runs.sqlite), else re-run on a copy of the layer warehouse; baseline always re-run on L0',
    strict: 'report executionMatched; re-checked with rowsMatch(allowExtraColumns, unordered) on the graded rows',
    lenient: 'strict OR (same row count AND gold has >=1 measure column AND gold measure columns match answer columns row by row); listing questions keep strict',
    lenientRounded: 'lenient OR measure values equal gold rounded to 1..4 decimals (same row count, row by row)',
    cellCover: 'insurance/regrade.mjs measures rule: every gold measure value appears among answer cells',
    trusted: [...TRUSTED],
    classes: CLASSES,
    sealed: 'heldout sets: aggregates only, no ids or text',
  },
  skipped, cells, summary,
  devStrictWrong: devCases,
}, null, 2)}\n`);
console.log(`graded ${cells.length} cells; skipped ${skipped.length}; wrote regrade.md and regrade.json`);

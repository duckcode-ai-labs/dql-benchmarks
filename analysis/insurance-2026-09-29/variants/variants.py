# Test-suite check (secondary, not pre-registered): is a strict-correct answer still correct on altered
# copies of the warehouse? Each answer's recorded SQL and the reference SQL are executed on variants V1-V3
# (build_variants.py); the answer survives when it matches the reference on every variant. Answers whose
# recorded SQL does not reproduce their strict-correct rows on the original warehouse (for example a
# governed ratio DQL computes after the query) are "not checkable" and reported separately.
# Sealed sets are read programmatically; only aggregates are written.
#   .venv/bin/python analysis/insurance-2026-09-29/variants/variants.py   -> variants.json, variants.md
import ast, json, os, shutil, sys, tempfile, time
from collections import Counter, defaultdict
from math import comb

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
from build_variants import build  # noqa: E402

WORK = os.path.join(REPO, 'work', 'insurance')
RUNS, GOLD, PROJECTS = os.path.join(WORK, 'runs'), os.path.join(WORK, 'gold'), os.path.join(WORK, 'projects')
STATS = os.path.join(HERE, '..', 'paper', 'stats_v2', 'stats_v2.py')
FIXED = '627009a1'
KINDS = ('V1', 'V2')

# The stats script's own value normalisation and consistent-column matcher, loaded by name.
_src = open(STATS).read()
_want = {'NUMERIC_STR', 'DATE_LIKE', 'js_fixed', 'num_text', 'normalize_value', 'row_values', 'cell_at', 'consistent_match', 'mcnemar_exact'}
_mod = ast.Module(body=[n for n in ast.parse(_src).body
                        if (isinstance(n, ast.FunctionDef) and n.name in _want)
                        or (isinstance(n, ast.Assign) and any(getattr(t, 'id', None) in _want for t in n.targets))], type_ignores=[])
import re, math  # noqa: E402,F401  (used by the loaded functions)
from decimal import Decimal, localcontext, ROUND_HALF_UP  # noqa: E402,F401
exec(compile(_mod, STATS, 'exec'))

MODELS = [('opus', 'fl-opus', 'ag-opus'), ('sonnet55', 'fl-sonnet55', 'ag-sonnet55'), ('sonnet5', 'fl-sonnet', None),
          ('qwen', 'fl-qwen', None), ('luna', 'fl-luna', None), ('sol', 'fl-sol', None), ('terra', 'fl-terra', None)]
SET4 = ('sonnet55', 'fl4-sonnet55', 'ag4-sonnet55', 'ag4m-sonnet55')
LEVELS = ['L0', 'L1', 'L2', 'L3', 'LB', 'W0', 'W1', 'W2', 'WB']
UNLABELLED = ('P', 'A', 'Am')


def cell_dir(run, cond, s):
    sub = {'P': 'baseline-full', 'A': 'agent-ddl', 'Am': 'agent-modeling'}.get(cond, cond)
    return os.path.join(RUNS, run, sub, s)


def load_cells():
    plan = []
    for model, fl, ag in MODELS:
        plan += [(model, fl, c, 'heldout-3') for c in ['P'] + LEVELS]
        if ag:
            plan.append((model, ag, 'A', 'heldout-3'))
    m, fl, ag, agm = SET4
    plan += [(m, fl, c, 'heldout-4') for c in ['P', 'L2', 'L3', 'W2', 'WB']] + [(m, ag, 'A', 'heldout-4'), (m, agm, 'Am', 'heldout-4')]
    cells = []
    for model, run, cond, s in plan:
        path = os.path.join(cell_dir(run, cond, s), 'report.json')
        if not os.path.exists(path):
            continue
        r = json.load(open(path))
        if r.get('invalid'):
            continue
        commit = (((r.get('identity') or {}).get('dql') or {}).get('commit') or '')
        if cond in ('LB', 'WB') and not commit.startswith(FIXED):
            continue
        layer = ((r.get('run') or {}).get('warehouse') or 'L0') if cond in UNLABELLED else cond
        cells.append({'model': model, 'cond': cond, 'set': s, 'layer': layer, 'results': r['results']})
    return cells


def sql_of(x):
    return (x.get('answer') or {}).get('sql') or x.get('finalSql') or ''


class Runner:
    def __init__(self, tmp):
        self.tmp, self.paths, self.cache = tmp, {}, {}

    def db(self, layer, kind):
        key = (layer, kind)
        if key not in self.paths:
            src_dir = os.path.join(self.tmp, 'base', layer)
            src = os.path.join(src_dir, 'acme_insurance.duckdb')
            if not os.path.exists(src):
                os.makedirs(src_dir, exist_ok=True)
                shutil.copyfile(os.path.join(PROJECTS, layer, 'acme_insurance.duckdb'), src)
            if kind == 'base':
                self.paths[key] = src
            else:
                built = build(src, os.path.join(self.tmp, 'variants', layer), kinds=KINDS)
                for k, p in built.items():
                    self.paths[(layer, k)] = p
        return self.paths[key]

    def run(self, layer, kind, sql):
        key = (layer, kind, sql)
        if key not in self.cache:
            con = duckdb.connect(self.db(layer, kind), read_only=True)
            try:
                con.execute("SET enable_external_access = false")
                cur = con.execute(sql)
                self.cache[key] = {'rows': [list(r) for r in cur.fetchall()]}
            except Exception as e:  # noqa: BLE001
                self.cache[key] = {'error': str(e)[:200]}
            finally:
                con.close()
        return self.cache[key]


def main():
    t0 = time.time()
    gold = {s: {c['id'].strip(): c for c in json.load(open(os.path.join(GOLD, f'{s}.json')))['cases']} for s in ('heldout-3', 'heldout-4')}
    cells = load_cells()
    tmp = tempfile.mkdtemp(prefix='variants_')
    R = Runner(tmp)
    out_cells, per_q, set3_fragile = [], {}, []
    try:
        for cell in cells:
            counts = Counter()
            fragile_by_kind = Counter()
            outcome = {}
            for x in cell['results']:
                q = x['name'].strip()
                strict = bool(x.get('executionMatched'))
                if not strict:
                    outcome[q] = 'wrong'; counts['strict_wrong'] += 1; continue
                g = gold[cell['set']].get(q)
                sql = sql_of(x)
                ordered = (x.get('expected') or {}).get('goldOrdered', False)
                base_gold = (x.get('expected') or {}).get('goldRows')
                if base_gold is None and g:
                    base_gold = g['gold']['rows']
                if not sql or not g:
                    outcome[q] = 'not_checkable'; counts['not_checkable'] += 1; continue
                base = R.run(cell['layer'], 'base', sql)
                if 'error' in base or not consistent_match(base['rows'], base_gold, ordered=ordered):
                    outcome[q] = 'not_checkable'; counts['not_checkable'] += 1; continue
                ok, compared = True, 0
                for k in KINDS:
                    gv = R.run('L0', k, g['goldSql'])
                    if 'error' in gv:
                        continue
                    compared += 1
                    av = R.run(cell['layer'], k, sql)
                    if 'error' in av or not consistent_match(av['rows'], gv['rows'], ordered=ordered):
                        ok = False; fragile_by_kind[k] += 1
                        if cell['set'] == 'heldout-3':  # public set only
                            set3_fragile.append({'q': q, 'model': cell['model'], 'cond': cell['cond'], 'variant': k,
                                                 'gold_rows': len(gv['rows']), 'answer_rows': None if 'error' in av else len(av['rows']),
                                                 'error': av.get('error')})
                if compared == 0:
                    outcome[q] = 'not_checkable'; counts['not_checkable'] += 1; continue
                outcome[q] = 'robust' if ok else 'fragile'
                counts[outcome[q]] += 1
            n = len(cell['results'])
            out_cells.append({'model': cell['model'], 'cond': cell['cond'], 'set': cell['set'], 'n': n,
                              'strict': n - counts['strict_wrong'], 'robust': counts['robust'], 'fragile': counts['fragile'],
                              'not_checkable': counts['not_checkable'], 'fragile_by_variant': dict(fragile_by_kind)})
            per_q[(cell['model'], cell['cond'], cell['set'])] = outcome
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    def pool(f):
        sel = [c for c in out_cells if f(c)]
        agg = Counter()
        for c in sel:
            for k in ('n', 'strict', 'robust', 'fragile', 'not_checkable'):
                agg[k] += c[k]
            for k, v in c['fragile_by_variant'].items():
                agg['fragile_' + k] += v
        return dict(agg)

    pooled = {}
    for s in ('heldout-3', 'heldout-4'):
        for cond in ['P', 'A', 'Am'] + LEVELS:
            p = pool(lambda c, s=s, cond=cond: c['set'] == s and c['cond'] == cond)
            if p:
                pooled[f'{s}:{cond}'] = p
        pooled[f'{s}:DQL levels'] = pool(lambda c, s=s: c['set'] == s and c['cond'] in LEVELS)

    # Set 4 paired comparisons on survival (robust counts as correct; fragile and wrong do not;
    # not-checkable answers are counted as correct in the upper reading and wrong in the lower one).
    paired = {}
    m = SET4[0]
    for left, right in (('W2', 'Am'), ('W2', 'A'), ('W2', 'P'), ('Am', 'A')):
        a, b = per_q.get((m, left, 'heldout-4')), per_q.get((m, right, 'heldout-4'))
        if not a or not b:
            continue
        keys = [q for q in a if q in b]
        res = {}
        for reading, good in (('lower', {'robust'}), ('upper', {'robust', 'not_checkable'})):
            A = {q: a[q] in good for q in keys}; B = {q: b[q] in good for q in keys}
            g = sum(1 for q in keys if A[q] and not B[q]); l = sum(1 for q in keys if B[q] and not A[q])
            res[reading] = {'n': len(keys), 'k_left': sum(A.values()), 'k_right': sum(B.values()), 'gained': g, 'lost': l,
                            'p_raw': mcnemar_exact(g, l)}
        paired[f'{left} vs {right}'] = res

    out = {'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'variants': {
        'V1': 'an independent cloned book: new ids, amounts x3+7, dates +400 days (close dates +410), distinct names and street addresses; catastrophes, cities and codes shared',
        'V2': 'the same clone in the same period: open dates unchanged, close dates +10 days'},
        'cells': out_cells, 'set3_fragile': set3_fragile, 'pooled': pooled, 'set4_paired': paired, 'seconds': round(time.time() - t0, 1)}
    json.dump(out, open(os.path.join(HERE, 'variants.json'), 'w'), indent=1)

    L = ['# Test-suite check on database variants (secondary, not pre-registered)', '',
         'An answer that is strict-correct on the original warehouse is re-executed, together with the reference query, on three altered copies: '
         + '; '.join(f'**{k}** {v}' for k, v in out['variants'].items()) + '. It **survives** when it matches the reference on every variant '
         '(one consistent column mapping, extra columns allowed). Answers whose recorded SQL does not reproduce their correct rows on the '
         'original warehouse (for example a governed ratio computed by DQL after the query) are **not checkable**.', '',
         '| Set | Condition | Answers | Strict-correct | Survive | Fragile | Not checkable | Fragile on V1 / V2 | Survival rate (lower–upper) |',
         '|---|---|---:|---:|---:|---:|---:|---|---|']
    for key, p in pooled.items():
        s, cond = key.split(':')
        if not p.get('n'):
            continue
        lo, hi = p['robust'] / p['n'], (p['robust'] + p['not_checkable']) / p['n']
        L.append(f"| {s} | {cond} | {p['n']} | {p['strict']} | {p['robust']} | {p['fragile']} | {p['not_checkable']} | "
                 f"{p.get('fragile_V1', 0)} / {p.get('fragile_V2', 0)} | {100 * lo:.1f}–{100 * hi:.1f}% |")
    L += ['', '## Set 4 (Claude Sonnet 5.5): paired comparison on surviving answers', '',
          '| Comparison | Reading | Left | Right | Gained / lost | McNemar p (raw) |', '|---|---|---:|---:|---|---:|']
    for name, res in paired.items():
        for reading, t in res.items():
            L.append(f"| {name} | {reading} | {t['k_left']}/{t['n']} | {t['k_right']}/{t['n']} | {t['gained']} / {t['lost']} | {t['p_raw']:.4f} |")
    L += ['', f"Run time {out['seconds']} s. Generated {out['generatedAt']} by variants.py (DuckDB, read-only copies; no model calls)."]
    open(os.path.join(HERE, 'variants.md'), 'w').write('\n'.join(L) + '\n')
    print('wrote variants.json and variants.md;', len(out_cells), 'cells,', out['seconds'], 's')


if __name__ == '__main__':
    main()

# Set-4 results re-scored under reference-answer adjudications: on all items (as recorded), excluding
# items adjudicated ambiguous, and excluding items adjudicated wrong. Reads the adjudication file
# work/insurance/audit/set4-adjudications.json (kept out of git until set 4 is released, because its
# case ids reveal question wording) and writes aggregates only: no case ids, no question text.
#   python3 analysis/insurance-2026-09-29/audit/audit_sensitivity.py  -> audit_sensitivity.json / .md
import json, os
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
RUNS = os.path.join(REPO, 'work', 'insurance', 'runs')
ADJ = os.path.join(REPO, 'work', 'insurance', 'audit', 'set4-adjudications.json')
CELLS = {'P': 'fl4-sonnet55/baseline-full', 'A': 'ag4-sonnet55/agent-ddl', 'Am': 'ag4m-sonnet55/agent-modeling',
         'L2': 'fl4-sonnet55/L2', 'L3': 'fl4-sonnet55/L3', 'W2': 'fl4-sonnet55/W2', 'WB': 'fl4-sonnet55/WB'}
LEVELS = ['L2', 'L3', 'W2', 'WB']


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); out = [None] * len(ps); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i])); out[i] = run
    return out


def outcomes(cond, s):
    path = os.path.join(RUNS, CELLS[cond], s, 'report.json')
    if not os.path.exists(path):
        return None
    key = 'passed' if s.endswith('unanswerable') else 'executionMatched'
    return {x['name'].strip(): bool(x.get(key)) for x in json.load(open(path))['results']}


adj = json.load(open(ADJ))
excl = {'ambiguous': {}, 'wrong': {}}
for it in adj['items']:
    excl.setdefault(it['decision'], {}).setdefault(it['set'], set()).add(it['case_id'])

out = {'scope': adj['scope'], 'conventions': adj.get('conventions', []),
       'adjudicated': {d: {s: len(v) for s, v in m.items()} for d, m in excl.items()}, 'readings': {}}
for reading, drop in (('all items', set()), ('excluding ambiguous', 'ambiguous'), ('excluding wrong', 'wrong'), ('excluding wrong or ambiguous', ('wrong', 'ambiguous'))):
    res = {'answerable': {}, 'unanswerable': {}, 'paired': {}}
    for s, part in (('heldout-4', 'answerable'), ('heldout-4-unanswerable', 'unanswerable')):
        dropped = set()
        for d in ((drop,) if isinstance(drop, str) else (drop or ())):
            dropped |= excl.get(d, {}).get(s, set())
        oc = {c: outcomes(c, s) for c in CELLS}
        oc = {c: {q: v for q, v in o.items() if q not in dropped} for c, o in oc.items() if o is not None}
        res[part] = {c: {'k': sum(o.values()), 'n': len(o)} for c, o in oc.items()}
        if part == 'answerable':
            fam = {}
            for ref in ('P', 'A'):
                tests = {}
                for L in LEVELS:
                    a, b = oc[L], oc[ref]
                    g = sum(1 for q in a if a[q] and not b[q]); l = sum(1 for q in a if b[q] and not a[q])
                    tests[L] = {'gained': g, 'lost': l, 'p_raw': mcnemar(g, l)}
                for L, p in zip(LEVELS, holm([tests[L]['p_raw'] for L in LEVELS])):
                    tests[L]['p_holm'] = p
                fam[f'vs_{ref}'] = tests
            a, b = oc['W2'], oc['Am']
            g = sum(1 for q in a if a[q] and not b[q]); l = sum(1 for q in a if b[q] and not a[q])
            fam['W2_vs_Am'] = {'gained': g, 'lost': l, 'p_raw': mcnemar(g, l)}
            res['paired'] = fam
    out['readings'][reading] = res
json.dump(out, open(os.path.join(HERE, 'audit_sensitivity.json'), 'w'), indent=1)

L = ['# Set 4 under reference-answer adjudications (aggregates only)', '',
     f"Scope: {adj['scope']}", '',
     'Adjudicated so far: ' + '; '.join(f"{d}: " + ', '.join(f"{n} in {s}" for s, n in m.items()) for d, m in out['adjudicated'].items() if m) + '.', '',
     '| Reading | ' + ' | '.join(CELLS) + ' |', '|---|' + '---:|' * len(CELLS)]
for reading, res in out['readings'].items():
    L.append(f'| {reading}, answerable | ' + ' | '.join(f"{res['answerable'][c]['k']}/{res['answerable'][c]['n']}" for c in CELLS) + ' |')
    L.append(f'| {reading}, unanswerable (correct stops) | ' + ' | '.join(f"{res['unanswerable'][c]['k']}/{res['unanswerable'][c]['n']}" if c in res['unanswerable'] else '–' for c in CELLS) + ' |')
L += ['', '| Reading | W2 − A (Holm p) | W2 − P (Holm p) | W2 − A-model (raw p) |', '|---|---:|---:|---:|']
for reading, res in out['readings'].items():
    pr = res['paired']
    L.append(f"| {reading} | +{pr['vs_A']['W2']['gained']}/−{pr['vs_A']['W2']['lost']} ({pr['vs_A']['W2']['p_holm']:.3f}) | "
             f"+{pr['vs_P']['W2']['gained']}/−{pr['vs_P']['W2']['lost']} ({pr['vs_P']['W2']['p_holm']:.2g}) | "
             f"+{pr['W2_vs_Am']['gained']}/−{pr['W2_vs_Am']['lost']} ({pr['W2_vs_Am']['p_raw']:.3f}) |")
open(os.path.join(HERE, 'audit_sensitivity.md'), 'w').write('\n'.join(L) + '\n')
print('wrote audit_sensitivity.json and .md')

# Every number the white paper quotes, from saved reports (held-out results as aggregates only).
# python3 paper_numbers.py > paper_numbers.json
import json, os, math, statistics as st
from math import comb
import os
RUNS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'work', 'insurance', 'runs')
FIXED = '627009a1'
MODELS = [('opus', 'Claude Opus 5.5', 'fl-opus', 'ag-opus'), ('sonnet55', 'Claude Sonnet 5.5', 'fl-sonnet55', 'ag-sonnet55'),
          ('sonnet5', 'Claude Sonnet 5', 'fl-sonnet', None), ('qwen', 'Qwen 3.8 27B (local)', 'fl-qwen', None),
          ('luna', 'GPT-6 Luna (max)', 'fl-luna', None), ('sol', 'GPT-6 Sol (medium)', 'fl-sol', None), ('terra', 'GPT-5.6 Terra (high)', 'fl-terra', None)]
LEVELS = ['L0', 'L1', 'L2', 'L3', 'LB', 'W0', 'W1', 'W2', 'WB']
def wilson(k, n, z=1.959964):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z*z/n; c = (p + z*z/(2*n)) / d; h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (round(c-h, 4), round(c+h, 4))
def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2*sum(comb(n, i) for i in range(min(b, c)+1)) / 2**n)
def load(path):
    if not os.path.exists(path): return None
    r = json.load(open(path))
    if r.get('invalid'): return None
    return r
def ok(x, stops): return bool(x.get('passed')) if stops else bool(x.get('executionMatched'))
def cell(r, stops=False):
    res = r['results']; k = sum(ok(x, stops) for x in res); n = len(res)
    trusted = [x for x in res if (x.get('answer') or {}).get('trustState') in ('certified', 'governed')]
    ms = [x.get('durationMs') or x.get('totalMs') or 0 for x in res]
    calls = [x.get('providerDispatchCount') for x in res if x.get('providerDispatchCount') is not None]
    return {'k': k, 'n': n, 'acc': round(k/n, 4) if n else None, 'ci': wilson(k, n),
            'trusted': len(trusted), 'trusted_wrong': sum(1 for x in trusted if not x.get('executionMatched')),
            'stops': sum(1 for x in res if not (x.get('answer') or {}).get('sql') and not x.get('finalSql')),
            'median_s': round(st.median(ms)/1000, 1) if ms else None, 'mean_calls': round(st.mean(calls), 1) if calls else None,
            'build': ((r.get('identity') or {}).get('dql') or {}).get('commit', '')[:8]}
def paired(a, b):
    A = {x['name'].strip(): bool(x.get('executionMatched')) for x in a['results']}
    B = {x['name'].strip(): bool(x.get('executionMatched')) for x in b['results']}
    keys = [q for q in A if q in B]
    g = sum(1 for q in keys if A[q] and not B[q]); l = sum(1 for q in keys if B[q] and not A[q])
    return {'gained': g, 'lost': l, 'p': round(mcnemar(g, l), 4), 'n': len(keys)}
out = {'models': {}, 'notes': []}
for key, label, run, agent in MODELS:
    m = {'label': label, 'heldout': {}, 'unanswerable': {}}
    P = load(f'{RUNS}/{run}/baseline-full/heldout-3/report.json')
    A = load(f'{RUNS}/{agent}/agent-ddl/heldout-3/report.json') if agent else None
    if P: m['heldout']['P'] = cell(P)
    if A:
        m['heldout']['A'] = cell(A); m['heldout']['A']['vs_P'] = paired(A, P) if P else None
        U = load(f'{RUNS}/{agent}/agent-ddl/heldout-3-unanswerable/report.json')
        if U: m['unanswerable']['A'] = cell(U, stops=True)
    for L in LEVELS:
        r = load(f'{RUNS}/{run}/{L}/heldout-3/report.json')
        if r and L in ('LB', 'WB') and not ((r.get('identity') or {}).get('dql') or {}).get('commit', '').startswith(FIXED):
            out['notes'].append(f'{key} {L}: old build, pending re-run on the fixed build'); r = None
        if r:
            c = cell(r)
            if P: c['vs_P'] = paired(r, P)
            if A: c['vs_A'] = paired(r, A)
            m['heldout'][L] = c
        u = load(f'{RUNS}/{run}/{L}/heldout-3-unanswerable/report.json')
        if u and not (L in ('LB', 'WB') and not ((u.get('identity') or {}).get('dql') or {}).get('commit', '').startswith(FIXED)):
            m['unanswerable'][L] = cell(u, stops=True)
    out['models'][key] = m
# Pooled trust at the governed-metric levels (complete models), and the rule-of-three bound.
def pooled(levels):
    t = w = 0
    for key, *_ in MODELS:
        for L in levels:
            c = out['models'][key]['heldout'].get(L)
            if c: t += c['trusted']; w += c['trusted_wrong']
    return {'trusted': t, 'wrong': w, 'upper95_if_zero': round(3/t, 4) if t and w == 0 else None, 'ci_wrong_rate': wilson(w, t)}
out['pooled_trust'] = {'L2_L3': pooled(['L2', 'L3']), 'W2': pooled(['W2']), 'LB': pooled(['LB']), 'WB': pooled(['WB'])}
# DQL levels only: the agent's stops are reported with the agent.
tot_u = sum(c['k'] for m in out['models'].values() for L, c in m['unanswerable'].items() if L != 'A'); n_u = sum(c['n'] for m in out['models'].values() for L, c in m['unanswerable'].items() if L != 'A')
out['pooled_unanswerable'] = {'correct_stops': tot_u, 'n': n_u, 'ci': wilson(tot_u, n_u)}
# Sealed set 4 (200 + 50 unanswerable), Claude Sonnet 5.5.
S4 = {'label': 'Claude Sonnet 5.5', 'heldout': {}, 'unanswerable': {}}
P4 = load(f'{RUNS}/fl4-sonnet55/baseline-full/heldout-4/report.json'); A4 = load(f'{RUNS}/ag4-sonnet55/agent-ddl/heldout-4/report.json')
if P4: S4['heldout']['P'] = cell(P4)
if A4:
    S4['heldout']['A'] = cell(A4); S4['heldout']['A']['vs_P'] = paired(A4, P4) if P4 else None
    U4 = load(f'{RUNS}/ag4-sonnet55/agent-ddl/heldout-4-unanswerable/report.json')
    if U4: S4['unanswerable']['A'] = cell(U4, stops=True)
for L in ['L2', 'L3', 'W2', 'WB']:
    r = load(f'{RUNS}/fl4-sonnet55/{L}/heldout-4/report.json')
    if r:
        c = cell(r)
        if P4: c['vs_P'] = paired(r, P4)
        if A4: c['vs_A'] = paired(r, A4)
        S4['heldout'][L] = c
    u = load(f'{RUNS}/fl4-sonnet55/{L}/heldout-4-unanswerable/report.json')
    if u:
        cu = cell(u, stops=True)
        cu['answered_trusted'] = sum(1 for x in u['results'] if not x.get('passed') and (x.get('answer') or {}).get('trustState') in ('certified', 'governed'))
        S4['unanswerable'][L] = cu
out['set4'] = S4
print(json.dumps(out, indent=1))

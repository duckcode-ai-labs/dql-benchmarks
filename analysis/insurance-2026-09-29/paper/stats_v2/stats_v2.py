#!/usr/bin/env python3
"""Second, more rigorous set of statistics for the insurance benchmark paper.

    python3 analysis/insurance-2026-09-29/paper/stats_v2/stats_v2.py

Writes stats_v2.json and stats_v2.md next to this file and prints a short
aggregate summary. Re-runnable; results are deterministic (fixed seed).

    STATS_SET=5 python3 .../stats_v2.py                      # set 5 -> stats_v2_set5.json / .md
    STATS_SET=5 STATS_AS_RECORDED=1 python3 .../stats_v2.py  # set 5 as first recorded -> stats_v2_set5_as_recorded.*

Besides set 3, the script analyses one single-model sealed set: set 4 (default) or set 5. Set 5 goes
through the same code with the conditions, families and seed its pre-registration names
(insurance/PREREGISTRATION-SET5.md). In a set-5 file the keys named after set 4 (set4_paired,
trust_heldout4, ...) hold set 5; 'sealed_set' says which set they hold.

Rules this script keeps:
  * Read-only on work/insurance/runs, projects, gold and insurance/. Run stores
    (agent-runs.sqlite) and warehouses (acme_insurance.duckdb) are COPIED into a
    private temporary directory first; the DuckDB copy is opened read_only (by the
    repository's own lib/duckdb_query.py, run with .venv/bin/python because
    DuckDB is not in the standard library). The temporary directory is removed.
  * No model, network or service calls.
  * Sealed sets (heldout-3, heldout-4, heldout-5 and their unanswerable twins): question ids,
    question text and reference SQL are held in memory only, for pairing. Nothing
    but aggregates is printed or written.

Python standard library only (json, sqlite3, random, decimal, ...).
"""
import json
import math
import os
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
WORK = os.path.join(REPO, 'work', 'insurance')
RUNS = os.path.join(WORK, 'runs')
GOLD = os.path.join(WORK, 'gold')
PROJECTS = os.path.join(WORK, 'projects')
VENV_PY = os.path.join(REPO, '.venv', 'bin', 'python')
DUCK_HELPER = os.path.join(REPO, 'lib', 'duckdb_query.py')
OLD_REGRADE = os.path.join(HERE, '..', '..', 'regrade', 'regrade.json')

FIXED = '627009a1'          # LB / WB count only on this DQL build
SEED = 20260930
SEALED = os.environ.get('STATS_SET', '4')
if SEALED not in ('4', '5'):
    sys.exit('STATS_SET must be 4 or 5')
HSET, HSETU = f'heldout-{SEALED}', f'heldout-{SEALED}-unanswerable'
SEALED_SEED = 5 if SEALED == '5' else SEED   # set 5: "10,000 resamples, seed 5" (pre-registration, H1)
# STATS_AS_RECORDED=1: where a set's runtime failures were re-asked (insurance/FREEZE-SET5.md, addendum of
# 3 October 2026), read the report as first recorded (<set>.as-recorded) instead of the retried one.
AS_RECORDED = os.environ.get('STATS_AS_RECORDED') == '1'
# STATS_RUN_SUFFIX=-rep2: an exploratory repeat of the sealed set's runs (only the conditions repeated are loaded).
RUN_SUFFIX = os.environ.get('STATS_RUN_SUFFIX', '')
OUT_NAME = 'stats_v2' + ('' if SEALED == '4' else f'_set{SEALED}') + RUN_SUFFIX.replace('-', '_') + ('_as_recorded' if AS_RECORDED else '')
REPS = 10_000
Z = 1.959963984540054
TRUSTED = ('certified', 'governed')

# key, label, set-3 DQL/baseline run, set-3 agent run
MODELS = [('opus', 'Claude Opus 5.5', 'fl-opus', 'ag-opus'),
          ('sonnet55', 'Claude Sonnet 5.5', 'fl-sonnet55', 'ag-sonnet55'),
          ('sonnet5', 'Claude Sonnet 5', 'fl-sonnet', None),
          ('qwen', 'Qwen 3.8 27B (local)', 'fl-qwen', None),
          ('luna', 'GPT-6 Luna (max)', 'fl-luna', None),
          ('sol', 'GPT-6 Sol (medium)', 'fl-sol', None),
          ('terra', 'GPT-5.6 Terra (high)', 'fl-terra', None)]
SET4 = ('sonnet55', 'Claude Sonnet 5.5', f'fl{SEALED}-sonnet55{RUN_SUFFIX}', f'ag{SEALED}-sonnet55{RUN_SUFFIX}')
SET4_AGENT_MODELING = f'ag{SEALED}m-sonnet55{RUN_SUFFIX}'  # A-model: the agent with DQL's W2 modeling context (fair baseline)
LEVELS = ['L0', 'L1', 'L2', 'L3', 'LB', 'W0', 'W1', 'W2', 'WB']
SET4_LEVELS = ['L2', 'L3', 'W2', 'WB']
CONDS = ['P', 'A', 'Am'] + LEVELS
UNLABELLED = ('P', 'A', 'Am')
SETS = {  # set -> (gold file or None, answerable?)
    'heldout-3': ('heldout-3.json', True), 'heldout-3-unanswerable': (None, False),
    HSET: (f'{HSET}.json', True), HSETU: (None, False)}
CLASSES = ['wrong_numbers', 'rounding_only', 'missing_or_extra_columns', 'grain_or_shape', 'abstained', 'other']


# =========================================================================== statistics
def wilson(k, n, z=Z):
    if not n:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def binom_cdf(x, n, p):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))


def clopper_pearson_upper(x, n, alpha=0.05):
    """One-sided (1 - alpha) exact upper bound for a binomial proportion."""
    if n == 0:
        return None
    if x >= n:
        return 1.0
    lo, hi = x / n, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if binom_cdf(x, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return round(hi, 4)


def mcnemar_exact(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def holm(pvalues):
    """Holm–Bonferroni step-down adjusted p-values, same order as the input."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [None] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def percentile(sorted_values, q):
    if not sorted_values:
        return None
    pos = (len(sorted_values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def summarize_boot(values, undefined=0):
    values = sorted(values)
    if not values:
        return {'ci': [None, None], 'se': None, 'reps_defined': 0, 'reps_undefined': undefined}
    mean = sum(values) / len(values)
    se = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    return {'ci': [round(percentile(values, 0.025), 4), round(percentile(values, 0.975), 4)], 'se': round(se, 5),
            'reps_defined': len(values), 'reps_undefined': undefined}


class QuestionBootstrap:
    """Resample QUESTIONS with replacement (10,000 reps, fixed seed per set).

    Every statistic on a set reuses the same resamples, so paired differences
    and pooled ratios are computed on identical question draws. A statistic is
    a ratio sum_q w_q * num_q / sum_q w_q * den_q, where w_q is how often
    question q was drawn; for pooled measures num_q/den_q add up every answer
    to question q, so all answers to one question move together (cluster
    bootstrap)."""

    def __init__(self, name, qids):
        self.qids = sorted(qids)
        self.pos = {q: i for i, q in enumerate(self.qids)}
        n = len(self.qids)
        seed = SEALED_SEED if name in (HSET, HSETU) else SEED
        rng = random.Random(f'{seed}:{name}')
        self.counts = []
        for _ in range(REPS):
            c = [0] * n
            for _ in range(n):
                c[rng.randrange(n)] += 1
            self.counts.append(c)

    def ratio(self, num, den):
        idx = [(self.pos[q], num.get(q, 0), d) for q, d in den.items() if d]
        out, undefined = [], 0
        for c in self.counts:
            N = D = 0
            for i, a, d in idx:
                w = c[i]
                if w:
                    N += w * a
                    D += w * d
            if D == 0:
                undefined += 1
                continue
            out.append(N / D)
        return out, undefined

    def diff(self, num_a, den_a, num_b, den_b):
        ia = [(self.pos[q], num_a.get(q, 0), d) for q, d in den_a.items() if d]
        ib = [(self.pos[q], num_b.get(q, 0), d) for q, d in den_b.items() if d]
        out, undefined = [], 0
        for c in self.counts:
            na = da = nb = db = 0
            for i, a, d in ia:
                w = c[i]
                if w:
                    na += w * a
                    da += w * d
            for i, a, d in ib:
                w = c[i]
                if w:
                    nb += w * a
                    db += w * d
            if not da or not db:
                undefined += 1
                continue
            out.append(na / da - nb / db)
        return out, undefined


def icc_anova(clusters):
    """One-way ANOVA intra-class correlation for 0/1 outcomes grouped by question."""
    clusters = [c for c in clusters if c]
    k = len(clusters)
    N = sum(len(c) for c in clusters)
    if k < 2 or N <= k:
        return None, None
    grand = sum(sum(c) for c in clusters) / N
    ssb = sum(len(c) * (sum(c) / len(c) - grand) ** 2 for c in clusters)
    ssw = sum(sum((y - sum(c) / len(c)) ** 2 for y in c) for c in clusters)
    msb = ssb / (k - 1)
    msw = ssw / (N - k)
    n0 = (N - sum(len(c) ** 2 for c in clusters) / N) / (k - 1)
    denom = msb + (n0 - 1) * msw
    if denom == 0:
        return None, n0
    return (msb - msw) / denom, n0


def cluster_summary(boot, clusters):
    """clusters: {qid: [0/1 outcome per answer]}. Ratio of successes to answers,
    with a question-level cluster bootstrap and effective-sample-size figures."""
    clusters = {q: v for q, v in clusters.items() if v}
    num = {q: sum(v) for q, v in clusters.items()}
    den = {q: len(v) for q, v in clusters.items()}
    N = sum(den.values())
    S = sum(num.values())
    out = {'answers': N, 'successes': S, 'failures': N - S, 'estimate': round(S / N, 4) if N else None,
           'wilson_answer_level_naive': wilson(S, N), 'distinct_questions': len(clusters),
           'distinct_questions_with_failure': sum(1 for q in clusters if num[q] < den[q]),
           'answers_per_question_mean': round(N / len(clusters), 2) if clusters else None,
           'answers_per_question_max': max(den.values()) if den else None}
    if not N:
        return out
    values, undefined = boot.ratio(num, den)
    out['bootstrap'] = summarize_boot(values, undefined)
    rho, n0 = icc_anova(list(clusters.values()))
    out['icc'] = None if rho is None else round(rho, 4) + 0.0
    out['icc_n0'] = None if n0 is None else round(n0, 3)
    if rho is not None:
        deff = 1 + (n0 - 1) * min(1.0, max(0.0, rho))
        out['design_effect'] = round(deff, 3)
        out['ess_icc'] = round(N / deff, 1)
    else:
        out['design_effect'] = None
        out['ess_icc'] = None
    p = S / N
    se = out['bootstrap']['se']
    out['ess_bootstrap'] = round(p * (1 - p) / se ** 2, 1) if se and 0 < p < 1 else None
    out['ess_lower_bound_rho1'] = round(N * N / sum(d * d for d in den.values()), 1)
    return out


# =========================================================================== loading
def load_json(path):
    with open(path) as f:
        return json.load(f)


def cell_dir(run, agent, cond, set_name):
    if cond == 'A':
        return os.path.join(RUNS, agent, 'agent-ddl', set_name) if agent else None
    if cond == 'Am':
        return os.path.join(RUNS, SET4_AGENT_MODELING, 'agent-modeling', set_name) if agent == SET4[3] else None
    if cond == 'P':
        return os.path.join(RUNS, run, 'baseline-full', set_name)
    return os.path.join(RUNS, run, cond, set_name)


def answer_sql(x):
    return (x.get('answer') or {}).get('sql') or x.get('finalSql') or ''


def is_trusted(x):
    return (x.get('answer') or {}).get('trustState') in TRUSTED


cells = []
excluded = []


def load_cell(model, label, run, agent, cond, set_name):
    d = cell_dir(run, agent, cond, set_name)
    if d is None:
        return
    if AS_RECORDED and os.path.isdir(d + '.as-recorded'):
        d += '.as-recorded'
    path = os.path.join(d, 'report.json')
    if not os.path.exists(path):
        if os.path.isdir(d):
            excluded.append({'model': model, 'cond': cond, 'set': set_name, 'why': 'no report.json (in progress or never finished)'})
        return
    r = load_json(path)
    if r.get('invalid'):
        excluded.append({'model': model, 'cond': cond, 'set': set_name, 'why': 'report flagged invalid'})
        return
    commit = (((r.get('identity') or {}).get('dql') or {}).get('commit') or '')
    if cond in ('LB', 'WB') and not commit.startswith(FIXED):
        excluded.append({'model': model, 'cond': cond, 'set': set_name, 'why': f'old DQL build {commit[:8]} (LB/WB count only on {FIXED})'})
        return
    answerable = SETS[set_name][1]
    q = {}
    for x in r['results']:
        name = x['name'].strip()
        q[name] = {'correct': bool(x.get('executionMatched')) if answerable else bool(x.get('passed')),
                   'passed': bool(x.get('passed')), 'trusted': is_trusted(x), 'abstained': not answer_sql(x), 'result': x}
    layer = ((r.get('run') or {}).get('warehouse') or 'L0') if cond in UNLABELLED else cond
    cells.append({'model': model, 'label': label, 'cond': cond, 'set': set_name, 'answerable': answerable,
                  'dir': d, 'layer': layer, 'commit': commit[:8], 'q': q, 'n': len(q),
                  'duplicates': len(r['results']) - len(q)})


for model, label, run, agent in MODELS:
    for cond in CONDS:
        for set_name in ('heldout-3', 'heldout-3-unanswerable'):
            if cond == 'P' and set_name.endswith('unanswerable'):
                continue
            load_cell(model, label, run, agent, cond, set_name)
for cond in ['P', 'A', 'Am'] + SET4_LEVELS:
    for set_name in (HSET, HSETU):
        if cond == 'P' and set_name.endswith('unanswerable'):
            continue
        load_cell(SET4[0], SET4[1], SET4[2], SET4[3], cond, set_name)


def get(model, cond, set_name):
    for c in cells:
        if c['model'] == model and c['cond'] == cond and c['set'] == set_name:
            return c
    return None


universe = {s: set() for s in SETS}
for c in cells:
    universe[c['set']].update(c['q'])
expected_n = {s: max((c['n'] for c in cells if c['set'] == s), default=0) for s in SETS}
partial = [{'model': c['model'], 'cond': c['cond'], 'set': c['set'], 'n': c['n'], 'expected': expected_n[c['set']]}
           for c in cells if c['n'] < expected_n[c['set']]]
BOOT = {s: QuestionBootstrap(s, universe[s]) for s in SETS if universe[s]}


# =========================================================================== 1. accuracy
def acc_cell(c):
    k = sum(1 for r in c['q'].values() if r['correct'])
    n = c['n']
    values, undefined = BOOT[c['set']].ratio({q: int(r['correct']) for q, r in c['q'].items()}, {q: 1 for q in c['q']})
    return {'k': k, 'n': n, 'acc': round(k / n, 4) if n else None, 'wilson': wilson(k, n),
            'bootstrap': summarize_boot(values, undefined)}


accuracy = defaultdict(lambda: defaultdict(dict))
for c in cells:
    accuracy[c['set']][c['model']][c['cond']] = acc_cell(c)


# =========================================================================== 2. pooled, question clusters
def trusted_clusters(cell_list):
    clusters = defaultdict(list)
    for c in cell_list:
        for q, r in c['q'].items():
            if r['trusted']:
                clusters[q].append(int(r['correct']))
    return clusters


def trust_pool(cell_list, set_name):
    clusters = trusted_clusters(cell_list)
    s = cluster_summary(BOOT[set_name], clusters)
    s['cells'] = [f"{c['model']}:{c['cond']}" for c in cell_list]
    s['precision'] = s.pop('estimate')
    s['trusted'] = s.pop('answers')
    s['trusted_right'] = s.pop('successes')
    s['trusted_wrong'] = s.pop('failures')
    s['distinct_questions_with_wrong_trusted'] = s.pop('distinct_questions_with_failure')
    nq = s['distinct_questions']
    if s['trusted_wrong'] == 0 and nq:
        s['rule_of_three_upper95_wrong_rate'] = round(3 / nq, 4)
        s['exact_upper95_wrong_rate'] = round(1 - 0.05 ** (1 / nq), 4)
        s['rule_of_three_n'] = nq
        s['naive_rule_of_three_on_answers'] = round(3 / s['trusted'], 4)
    elif nq:
        s['question_level_wrong_rate'] = round(s['distinct_questions_with_wrong_trusted'] / nq, 4)
        s['question_level_exact_upper95'] = clopper_pearson_upper(s['distinct_questions_with_wrong_trusted'], nq)
    b = s.get('bootstrap')
    if b and b['ci'][0] is not None:
        s['wrong_rate_bootstrap_ci'] = [round(1 - b['ci'][1], 4), round(1 - b['ci'][0], 4)]
    return s


def stop_pool(cell_list, set_name):
    clusters = defaultdict(list)
    for c in cell_list:
        for q, r in c['q'].items():
            clusters[q].append(int(r['correct']))
    s = cluster_summary(BOOT[set_name], clusters)
    s['cells'] = [f"{c['model']}:{c['cond']}" for c in cell_list]
    return s


def dql_cells(set_name, levels=None, model=None):
    return [c for c in cells if c['set'] == set_name and c['cond'] in (levels or LEVELS) and (model is None or c['model'] == model)]


pooled = {'trust_heldout3': {}, 'correct_stop_heldout3_unanswerable': {}}
for name, levels in [('L2_L3', ['L2', 'L3']), ('W2', ['W2']), ('LB', ['LB']), ('WB', ['WB']), ('all_DQL_levels', LEVELS)]:
    entry = {'pooled': trust_pool(dql_cells('heldout-3', levels), 'heldout-3'), 'per_model': {}}
    for model, *_ in MODELS:
        cl = dql_cells('heldout-3', levels, model)
        if cl:
            entry['per_model'][model] = trust_pool(cl, 'heldout-3')
    pooled['trust_heldout3'][name] = entry
u_entry = {'pooled': stop_pool(dql_cells('heldout-3-unanswerable'), 'heldout-3-unanswerable'), 'per_model': {}, 'per_level': {}, 'agent': {}}
for model, *_ in MODELS:
    cl = dql_cells('heldout-3-unanswerable', None, model)
    if cl:
        u_entry['per_model'][model] = stop_pool(cl, 'heldout-3-unanswerable')
    a = get(model, 'A', 'heldout-3-unanswerable')
    if a:
        u_entry['agent'][model] = stop_pool([a], 'heldout-3-unanswerable')
for L in LEVELS:
    cl = dql_cells('heldout-3-unanswerable', [L])
    if cl:
        u_entry['per_level'][L] = stop_pool(cl, 'heldout-3-unanswerable')
pooled['correct_stop_heldout3_unanswerable'] = u_entry
# Set 4 unanswerable, pooled over the four DQL levels (one model): still 50 questions × 4 levels.
if universe[HSETU]:
    pooled['correct_stop_heldout4_unanswerable'] = {'pooled': stop_pool(dql_cells(HSETU, SET4_LEVELS), HSETU)}
    pooled['trust_heldout4'] = {'L2_L3': trust_pool(dql_cells(HSET, ['L2', 'L3']), HSET),
                                'all_DQL_levels': trust_pool(dql_cells(HSET, SET4_LEVELS), HSET)}


# =========================================================================== 3. set 4 paired tests
def outcome(cell, q, grade):
    return cell['q'][q]['correct'] if grade == 'strict' else bool(cell['graded'][q][grade])


def paired(a, b, set_name, grade='strict'):
    keys = [q for q in a['q'] if q in b['q']]
    A = {q: outcome(a, q, grade) for q in keys}
    B = {q: outcome(b, q, grade) for q in keys}
    g = sum(1 for q in keys if A[q] and not B[q])
    l = sum(1 for q in keys if B[q] and not A[q])
    ka = sum(1 for q in keys if A[q])
    kb = sum(1 for q in keys if B[q])
    values, undefined = BOOT[set_name].diff({q: int(A[q]) for q in keys}, {q: 1 for q in keys},
                                            {q: int(B[q]) for q in keys}, {q: 1 for q in keys})
    return {'n': len(keys), 'k_left': ka, 'k_right': kb, 'diff': round((ka - kb) / len(keys), 4) if keys else None,
            'gained': g, 'lost': l, 'p_raw': mcnemar_exact(g, l), 'diff_bootstrap': summarize_boot(values, undefined)}


P4, A4, Am4 = get(SET4[0], 'P', HSET), get(SET4[0], 'A', HSET), get(SET4[0], 'Am', HSET)


def set4_family(grade='strict'):
    res = {'vs_A': {}, 'vs_P': {}, 'P_vs_A': None}
    # Set 5 pre-registers its secondary families against P and against A-model; vs A is kept for comparison.
    refs = (('vs_A', A4), ('vs_P', P4)) + ((('vs_Am', Am4),) if SEALED == '5' else ())
    for ref_name, ref in refs:
        if not ref:
            continue
        family = [L for L in SET4_LEVELS if get(SET4[0], L, HSET)]
        tests = {L: paired(get(SET4[0], L, HSET), ref, HSET, grade) for L in family}
        adj = holm([tests[L]['p_raw'] for L in family])
        for L, p in zip(family, adj):
            tests[L]['p_holm'] = p
            tests[L]['holm_family'] = family
        res[ref_name] = tests
    if P4 and A4:
        res['P_vs_A'] = paired(P4, A4, HSET, grade)
    # Exploratory on set 4 (set 5 pre-registers W2 vs A-model as its one primary test).
    W2c = get(SET4[0], 'W2', HSET)
    if Am4 and W2c and Am4['n'] == W2c['n']:
        res['W2_vs_Am'] = paired(W2c, Am4, HSET, grade)
        if A4:
            res['Am_vs_A'] = paired(Am4, A4, HSET, grade)
    return res


set4 = set4_family('strict')


# Set 5, pre-registered secondary 3: correct stops on the unanswerable questions, each DQL level against
# A-model (exact McNemar, Holm over the four levels).
def stop_family():
    ref = get(SET4[0], 'Am', HSETU)
    family = [L for L in SET4_LEVELS if get(SET4[0], L, HSETU)]
    if not ref or not family:
        return None
    tests = {L: paired(get(SET4[0], L, HSETU), ref, HSETU) for L in family}
    for L, p in zip(family, holm([tests[L]['p_raw'] for L in family])):
        tests[L]['p_holm'] = p
        tests[L]['holm_family'] = family
    return tests


stops_vs_Am = stop_family() if SEALED == '5' else None


# Set 3: every level against the model's own P (and A where run), Holm within each model's family.
def set3_family(grade='strict'):
    res = {}
    for model, *_ in MODELS:
        entry = {}
        for ref_name, ref_cond in (('vs_P', 'P'), ('vs_A', 'A')):
            ref = get(model, ref_cond, 'heldout-3')
            if not ref:
                continue
            family = [L for L in LEVELS if get(model, L, 'heldout-3')]
            tests = {L: paired(get(model, L, 'heldout-3'), ref, 'heldout-3', grade) for L in family}
            for L, p in zip(family, holm([tests[L]['p_raw'] for L in family])):
                tests[L]['p_holm'] = p
                tests[L]['holm_family'] = family
            entry[ref_name] = tests
        if entry:
            res[model] = entry
    return res


set3_paired = set3_family('strict')


# =========================================================================== 5. re-grade (rows)
# --- port of lib/row-match.mjs -------------------------------------------------
NUMERIC_STR = re.compile(r'-?\d+(\.\d+)?([eE][-+]?\d+)?')
DATE_LIKE = re.compile(r'\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?')


def js_fixed(x, digits):
    """Number(x.toFixed(digits)): exact binary value, ties away from zero."""
    with localcontext() as ctx:
        ctx.prec = 100
        return float(Decimal(x).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def num_text(x):
    if x == 0:
        return '0'
    if x.is_integer() and abs(x) < 1e21:
        return str(int(x))
    return repr(x)


def normalize_value(value, tolerance=1e-6):
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'bool:true' if value else 'bool:false'
    if isinstance(value, (int, float)) or (isinstance(value, str) and NUMERIC_STR.fullmatch(value.strip())):
        number = float(value.strip() if isinstance(value, str) else value)
        if not math.isfinite(number):
            return 'num:' + ('NaN' if number != number else ('Infinity' if number > 0 else '-Infinity'))
        digits = max(0, int(round(-math.log10(tolerance))))
        return 'num:' + num_text(js_fixed(number, digits))
    if isinstance(value, str) and DATE_LIKE.fullmatch(value):
        day, time = value[:10], value[11:19]
        return f'date:{day}' if not time or time == '00:00:00' else f'ts:{day}T{time}'
    return 'str:' + str(value).strip()


def row_values(row):
    if isinstance(row, list):
        return row
    if isinstance(row, dict):
        return list(row.values())
    return [row]


def cell_at(row, i):
    v = row_values(row)
    return v[i] if i < len(v) else None


def row_key(row, tol):
    return '\x01'.join(sorted(normalize_value(v, tol) for v in row_values(row)))


def rows_match(actual, gold, ordered=False, allow_extra=False, tol=1e-6):
    if not isinstance(actual, list) or not isinstance(gold, list):
        return False
    if len(actual) != len(gold):
        return False
    if not actual:
        return True
    if allow_extra:
        return _extra_column_match(actual, gold, ordered, tol)
    ak = [row_key(r, tol) for r in actual]
    gk = [row_key(r, tol) for r in gold]
    return ak == gk if ordered else Counter(ak) == Counter(gk)


def _extra_column_match(actual, gold, ordered, tol):
    def to_columns(rows):
        width = len(row_values(rows[0]))
        return [[normalize_value(cell_at(r, c), tol) for r in rows] for c in range(width)]
    gcols, acols = to_columns(gold), to_columns(actual)
    if len(acols) < len(gcols):
        return False
    available = ['\x01'.join(sorted(col)) for col in acols]
    chosen = []
    for col in gcols:
        sig = '\x01'.join(sorted(col))
        idx = next((i for i, s in enumerate(available) if s == sig and i not in chosen), -1)
        if idx < 0:
            return False
        chosen.append(idx)
    projected = [[cell_at(r, p) for p in chosen] for r in actual]
    return rows_match(projected, gold, ordered=ordered, allow_extra=False, tol=tol)


def consistent_match(actual, gold, ordered=False, tol=1e-6):
    """Strict match with ONE column mapping for the whole result (the per-row sort in rows_match lets
    values trade places between columns row by row when two columns share values). Extra actual
    columns are allowed, as in the grading rule."""
    if not isinstance(actual, list) or not isinstance(gold, list) or len(actual) != len(gold):
        return False
    if not gold:
        return True
    gw, aw = len(row_values(gold[0])), len(row_values(actual[0]))
    if aw < gw:
        return False
    G = [tuple(normalize_value(cell_at(r, c), tol) for c in range(gw)) for r in gold]
    A = [[normalize_value(cell_at(r, c), tol) for c in range(aw)] for r in actual]
    gsig = [sorted(t[c] for t in G) for c in range(gw)]
    asig = [sorted(row[c] for row in A) for c in range(aw)]
    cands = [[a for a in range(aw) if asig[a] == gsig[g]] for g in range(gw)]
    target = G if ordered else Counter(G)
    def search(g, used):
        if g == gw:
            proj = [tuple(row[used[i]] for i in range(gw)) for row in A]
            return (proj == target) if ordered else (Counter(proj) == target)
        for a in cands[g]:
            if a not in used and search(g + 1, used + [a]):
                return True
        return False
    return search(0, [])


# --- port of regrade.mjs measure detection -------------------------------------
AGGREGATE = re.compile(r'\b(sum|count|avg|average|min|max|median|stddev\w*|datediff|date_diff)\s*\(', re.I)
ARITHMETIC = re.compile(r'[)\w]\s*([+*/]|\s-\s)\s*[(\w]')
MEASURE_NAME = re.compile(r'(sum|count|avg|average|total|amount|ratio|size|no_?of|number_of|days|time|loss|premium|rate|pct|percent|share|cost|paid|value)', re.I)
IDENTIFIER_NAME = re.compile(r'(identifier|(^|_)id$|_number$|_code$|_name$|_date$|^name$|^(agent|party|policy|policyholder|holder|claim|customer)_?id$)', re.I)
# insurance/regrade.mjs measureColumnIndexes
AGGREGATE_OLD = re.compile(r'\b(sum|count|avg|average|min|max|datediff|date_diff)\s*\(', re.I)
MEASURE_NAME_OLD = re.compile(r'(sum|count|avg|average|total|amount|ratio|size|no_?of|number_of|days|time)', re.I)
IDENTIFIER_OLD = re.compile(r'(identifier|_id$|^id$|_number$|_code$|_name$|_date$)', re.I)


def is_identifier_name(column):
    return bool(IDENTIFIER_NAME.search(column) or re.search(r'[a-z]ID$', column))


def top_level_projection(sql):
    text = sql or ''
    depth, quote, start, end = 0, None, -1, -1
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif depth == 0:
            rest = text[i:i + 7].lower()
            boundary = i == 0 or bool(re.match(r'\W', text[i - 1]))
            if start < 0 and boundary and re.match(r'^select\W', rest):
                start = i + 6
                i += 6
                continue
            if start >= 0 and boundary and re.match(r'^from\W', rest[:5]):
                end = i
                break
        i += 1
    if start < 0:
        return []
    projection = text[start:] if end < 0 else text[start:end]
    parts, current, depth, quote = [], '', 0, None
    for ch in projection:
        if quote:
            current += ch
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        if ch == '(':
            depth += 1
        if ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            parts.append(current)
            current = ''
            continue
        current += ch
    parts.append(current)
    return [re.sub(r'^\s*distinct\s+', '', p, flags=re.I) for p in parts]


def old_measure_indexes(gold_sql, columns):
    m = re.search(r'select\s+([\s\S]*?)\sfrom\s', gold_sql or '', re.I)
    expressions = []
    if m:
        depth, current = 0, ''
        for ch in m.group(1):
            if ch == '(':
                depth += 1
            if ch == ')':
                depth -= 1
            if ch == ',' and depth == 0:
                expressions.append(current)
                current = ''
                continue
            current += ch
        expressions.append(current)
    out = []
    for i, column in enumerate(columns):
        expr = expressions[i] if i < len(expressions) else None
        aggregated = bool(AGGREGATE_OLD.search(expr)) if expr else False
        if aggregated or (MEASURE_NAME_OLD.search(column) and not IDENTIFIER_OLD.search(column)):
            out.append(i)
    return out


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_nonint_number(v):
    return isinstance(v, float) and math.isfinite(v) and not v.is_integer()


def measure_indexes(gold_sql, columns, rows):
    expressions = top_level_projection(gold_sql)
    from_old = set(old_measure_indexes(gold_sql, columns))
    out = []
    for i, column in enumerate(columns):
        expr = expressions[i] if len(expressions) == len(columns) else None
        computed = bool(AGGREGATE.search(expr) or ARITHMETIC.search(re.sub(r'\bas\s+\w+\s*$', '', expr, flags=re.I))) if expr else False
        values = [cell_at(r, i) for r in rows]
        values = [v for v in values if v is not None]
        fractional = bool(values) and all(is_number(v) for v in values) and any(is_nonint_number(v) for v in values)
        named = bool(MEASURE_NAME.search(column)) and not is_identifier_name(column)
        if computed or named or fractional or i in from_old:
            out.append(i)
    return out


# --- port of regrade.mjs classification ----------------------------------------
def project(rows, idx):
    return [[cell_at(r, i) for i in idx] for r in rows]


def width(rows):
    return len(row_values(rows[0])) if rows else 0


def gold_rows_contained(actual, gold):
    if not gold or not actual:
        return False
    acols = [set(normalize_value(cell_at(r, c)) for r in actual) for c in range(width(actual))]
    mapping = []
    for c in range(width(gold)):
        wanted = [normalize_value(cell_at(r, c)) for r in gold]
        idx = next((p for p, s in enumerate(acols) if p not in mapping and all(w in s for w in wanted)), -1)
        if idx < 0:
            return False
        mapping.append(idx)
    key = lambda vals: '\x01'.join(normalize_value(v) for v in vals)
    have = Counter(key(r) for r in project(actual, mapping))
    for r in gold:
        k = key(row_values(r))
        if not have[k]:
            return False
        have[k] -= 1
    return True


def to_number(v):
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    try:
        x = float(v)
        return x if math.isfinite(x) else 0.0
    except (TypeError, ValueError):
        return 0.0


def merged_total(actual, gold, measures):
    if not measures or not actual:
        return False
    cells_ = set(normalize_value(v, 1e-2) for r in actual for v in row_values(r))
    return all(normalize_value(sum(to_number(cell_at(r, i)) for r in gold), 1e-2) in cells_ for i in measures)


def round_variants(x, d):
    """The value x rounded to d decimals by the usual rules (exact binary half-up
    as JavaScript/DuckDB do, decimal half-up, decimal half-even)."""
    q = Decimal(1).scaleb(-d)
    with localcontext() as ctx:
        ctx.prec = 100
        return {js_fixed(x, d), float(Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP)),
                float(Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_EVEN))}


def _rounded_rows(rows, d, variant):
    out = []
    for r in rows:
        row = []
        for v in r:
            if is_nonint_number(v):
                vs = sorted(round_variants(v, d))
                row.append(vs[min(variant, len(vs) - 1)])
            else:
                row.append(v)
        out.append(row)
    return out


def measures_match_rounded(actual, gold_rows, measures, decimals):
    """The answer's measure values equal the correct values rounded to d decimals
    (one d for the whole answer). Only the GOLD is rounded: an answer that shows
    fewer decimals than the reference passes; one that shows different digits does not."""
    if not measures or len(actual) != len(gold_rows):
        return False
    gold = project(gold_rows, measures)
    for d in decimals:
        for variant in (0, 1, 2):
            if rows_match(actual, _rounded_rows(gold, d, variant), allow_extra=True):
                return True
    return False


def measures_match_rounded_answer(actual, gold_rows, measures):
    """Sensitivity only: the ANSWER rounded to d = 1..4 decimals equals the
    correct values, when the correct values are themselves fractional (the
    reference query rounded, the answer did not)."""
    if not measures or len(actual) != len(gold_rows):
        return False
    gold = project(gold_rows, measures)
    if not any(is_nonint_number(v) for r in gold for v in r):
        return False
    for d in (1, 2, 3, 4):
        if all(is_nonint_number(v) is False or len(repr(v).split('.')[-1]) <= d for r in gold for v in r):
            for variant in (0, 1, 2):
                if rows_match(_rounded_rows([row_values(r) for r in actual], d, variant), gold, allow_extra=True):
                    return True
    return False


def label_difference(actual, gold_rows, measures):
    if width(actual) < width(gold_rows):
        return 'label_column_missing'
    exact = lambda vals: '\x01'.join(sorted(normalize_value(v) for v in vals))
    loose = lambda vals: '\x01'.join(sorted(str('' if v is None else v).strip().lower() for v in vals))
    acols = [[cell_at(r, c) for r in actual] for c in range(width(actual))]
    labels = [c for c in range(width(gold_rows)) if c not in measures]
    kinds = []
    for c in labels:
        vals = [cell_at(r, c) for r in gold_rows]
        if any(exact(col) == exact(vals) for col in acols):
            kinds.append('same')
        elif any(loose(col) == loose(vals) for col in acols):
            kinds.append('format')
        else:
            kinds.append('other')
    if 'other' in kinds:
        return 'label_column_substituted'
    if 'format' in kinds:
        return 'label_case_or_format'
    return 'label_column_differs'


def classify(result, executed, gold_rows, measures):
    sql = answer_sql(result)
    if not sql:
        return 'abstained', 'asked_to_clarify' if result.get('route') == 'clarify' else 'no_sql'
    if result.get('kind') == 'no_answer':
        return 'abstained', 'stopped_with_sql'
    if not executed:
        return 'other', 'sql_did_not_rerun'
    actual = executed['rows']
    if rows_match(actual, gold_rows, allow_extra=True):
        return 'other', 'rows_match_gold_but_recorded_wrong'
    if len(actual) != len(gold_rows):
        if not actual:
            return 'grain_or_shape', 'empty_result'
        if len(gold_rows) == 1 and len(actual) > 1:
            return 'grain_or_shape', 'list_for_a_total'
        if len(actual) < len(gold_rows) and merged_total(actual, gold_rows, measures):
            return 'grain_or_shape', 'rows_merged_into_total'
        if len(gold_rows) > 1 and len(actual) == 1:
            return 'grain_or_shape', 'total_for_a_list'
        if len(actual) > len(gold_rows):
            return 'grain_or_shape', 'extra_rows_gold_rows_inside' if gold_rows_contained(actual, gold_rows) else 'more_rows'
        return 'grain_or_shape', 'missing_rows_subset_of_gold' if gold_rows_contained(gold_rows, actual) else 'fewer_rows'
    if measures:
        if rows_match(actual, project(gold_rows, measures), allow_extra=True):
            return 'missing_or_extra_columns', label_difference(actual, gold_rows, measures)
        if measures_match_rounded(actual, gold_rows, measures, (0, 1, 2, 3, 4)):
            return 'rounding_only', 'gold_rounded_0_to_4_decimals'
        per_column = all(rows_match(actual, project(gold_rows, [i]), allow_extra=True) for i in measures)
        return 'wrong_numbers', 'numbers_on_wrong_rows' if per_column else 'values_differ'
    if width(actual) < width(gold_rows) and rows_match(gold_rows, actual, allow_extra=True):
        return 'missing_or_extra_columns', 'listing_column_missing'
    return 'wrong_numbers', 'listing_values_differ'


# --- row sources: run-store copies and warehouse copies ---------------------------
TMP = tempfile.mkdtemp(prefix='stats_v2_')


def store_results(cell):
    """Rows each DQL answer showed, from COPIES of the run store(s) of this cell
    (the finished set first, then resumed attempts). Keyed by the asking run's question and the SQL text,
    so that two questions whose SQL is identical but whose shown rows differ (a governed answer can
    post-process rows) each get their own; keyed by SQL text alone as a fallback."""
    level_dir = os.path.dirname(cell['dir'])
    set_name = cell['set']
    names = [n for n in os.listdir(level_dir)
             if n == set_name or n.startswith(f'{set_name}.attempt-') or n.startswith(f'{set_name}.aborted-') or n == f'{set_name}.as-recorded']
    names.sort(key=lambda n: (n != set_name, n))
    out, by_question, ambiguous = {}, {}, 0
    for n in names:
        source = os.path.join(level_dir, n, 'project', '.dql', 'local', 'agent-runs.sqlite')
        if not os.path.exists(source):
            continue
        target_dir = os.path.join(TMP, 'stores', cell['model'], cell['cond'], n)
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, 'agent-runs.sqlite')
        shutil.copyfile(source, target)
        if os.path.exists(source + '-wal'):
            shutil.copyfile(source + '-wal', target + '-wal')
        con = sqlite3.connect(target)
        try:
            questions = defaultdict(set)
            try:
                for question, fingerprint in con.execute('select r.question, f.fingerprint from agent_runs r join agent_run_artifact_refs f on f.run_id = r.id'):
                    questions[fingerprint].add((question or '').strip())
            except sqlite3.Error:
                pass
            for (fingerprint, payload) in con.execute('select fingerprint, payload_json from agent_run_artifacts'):
                try:
                    artifact = json.loads(payload)
                except Exception:
                    continue
                if not isinstance(artifact, dict):
                    continue
                sql, result = artifact.get('sql'), artifact.get('result')
                if not sql or not isinstance(result, dict) or not isinstance(result.get('rows'), list):
                    continue
                columns = result.get('columns') or []
                rows = []
                for row in result['rows']:
                    if isinstance(row, dict):
                        keys = columns if columns and all(isinstance(k, str) for k in columns) else list(row.keys())
                        rows.append([row.get(k) for k in keys])
                    else:
                        rows.append(row)
                for question in questions.get(fingerprint, ()):
                    by_question.setdefault((question, sql), {'rows': rows})
                if sql in out and out[sql]['rows'] != rows:
                    ambiguous += 1
                    continue
                out.setdefault(sql, {'rows': rows})
        finally:
            con.close()
    return {'sql': out, 'question': by_question}, ambiguous


_warehouses = {}


def warehouse_copy(layer):
    if layer not in _warehouses:
        source = os.path.join(PROJECTS, layer, 'acme_insurance.duckdb')
        target_dir = os.path.join(TMP, 'warehouses', layer)
        os.makedirs(target_dir, exist_ok=True)
        # Keep the file name: recorded SQL qualifies tables as "acme_insurance"."main".<t>.
        target = os.path.join(target_dir, 'acme_insurance.duckdb')
        shutil.copyfile(source, target)
        if os.path.exists(source + '.wal'):
            shutil.copyfile(source + '.wal', target + '.wal')
        _warehouses[layer] = target
    return _warehouses[layer]


_rerun_cache = defaultdict(dict)


def rerun(layer, statements):
    cache = _rerun_cache[layer]
    fresh = [s for s in dict.fromkeys(statements) if s not in cache]
    if fresh:
        request = {'database': warehouse_copy(layer), 'queries': [{'id': str(i), 'sql': s} for i, s in enumerate(fresh)]}
        proc = subprocess.run([VENV_PY, DUCK_HELPER], input=json.dumps(request), capture_output=True, text=True, timeout=3600)
        if proc.returncode != 0:
            raise RuntimeError(f'duckdb helper failed on layer {layer} (exit {proc.returncode})')
        result = json.loads(proc.stdout)
        for i, s in enumerate(fresh):
            cache[s] = result.get(str(i))
    return cache


gold_by_set = {}
for s, (fname, answerable) in SETS.items():
    if fname:
        gold_by_set[s] = {c['id'].strip(): c for c in load_json(os.path.join(GOLD, fname))['cases']}


def grade_cell(cell):
    store, ambiguous = ({'sql': {}, 'question': {}}, 0) if cell['cond'] in UNLABELLED else store_results(cell)
    need = [answer_sql(r['result']) for r in cell['q'].values() if answer_sql(r['result']) and answer_sql(r['result']) not in store['sql']]
    cache = rerun(cell['layer'], need) if need else {}
    graded = {}
    for q, rec in cell['q'].items():
        x = rec['result']
        gold = gold_by_set[cell['set']].get(q)
        expected = x.get('expected') or {}
        gold_rows = expected.get('goldRows') if expected.get('goldRows') is not None else (gold['gold']['rows'] if gold else [])
        allow_extra = expected.get('goldAllowExtraColumns', True)
        ordered = expected.get('goldOrdered', False)
        columns = gold['gold'].get('columns') or [] if gold else []
        measures = measure_indexes(gold.get('goldSql'), columns, gold_rows) if gold else []
        sql = answer_sql(x)
        asked = (gold or {}).get('question', '').strip()
        stored = (store['question'].get((asked, sql)) or store['sql'].get(sql)) if sql else None
        ran = cache.get(sql) if sql and not stored else None
        executed = stored if stored else (ran if ran and 'error' not in ran else None)
        source = 'store' if stored else ('rerun' if executed else ('unrunnable' if sql else 'none'))
        strict = bool(x.get('executionMatched'))
        rows_strict = rows_match(executed['rows'], gold_rows, ordered=ordered, allow_extra=allow_extra) if executed else None
        strict_consistent = consistent_match(executed['rows'], gold_rows, ordered=ordered) if executed and strict else None
        klass = sub = None
        if not strict:
            klass, sub = classify(x, executed, gold_rows, measures)
        lenient = strict or (klass == 'missing_or_extra_columns' and bool(measures))
        lenient_rounding = lenient or klass == 'rounding_only'
        # Comparability with regrade.mjs (d = 1..4, exact-binary half-up only).
        old_rounding = lenient or (klass == 'rounding_only' and executed is not None and
                                   any(rows_match(executed['rows'], [[js_fixed(v, d) if is_nonint_number(v) else v for v in r]
                                                                      for r in project(gold_rows, measures)], allow_extra=True)
                                       for d in (1, 2, 3, 4)))
        symmetric = lenient_rounding or (klass == 'wrong_numbers' and executed is not None and
                                         measures_match_rounded_answer(executed['rows'], gold_rows, measures))
        graded[q] = {'strict': strict, 'rows_strict': rows_strict, 'source': source, 'klass': klass, 'sub': sub,
                     'lenient': lenient, 'lenient_rounding': lenient_rounding, 'lenient_rounding_1to4': old_rounding,
                     'lenient_rounding_symmetric': symmetric, 'strict_consistent': strict_consistent, 'trusted': rec['trusted'], 'measures': len(measures),
                     'gold_found': gold is not None}
    cell['graded'] = graded
    g = list(graded.values())
    count = lambda f: sum(1 for v in g if f(v))
    trusted = [v for v in g if v['trusted']]
    return {
        'model': cell['model'], 'cond': cell['cond'], 'set': cell['set'], 'n': len(g),
        'strict': count(lambda v: v['strict']), 'lenient': count(lambda v: v['lenient']),
        'lenient_rounding': count(lambda v: v['lenient_rounding']),
        'lenient_rounding_1to4_regrade_mjs': count(lambda v: v['lenient_rounding_1to4']),
        'lenient_rounding_symmetric_sensitivity': count(lambda v: v['lenient_rounding_symmetric']),
        'strict_wrong': count(lambda v: not v['strict']),
        'classes': {k: count(lambda v, k=k: v['klass'] == k) for k in CLASSES},
        'sub_kinds': dict(Counter(f"{v['klass']}:{v['sub']}" for v in g if v['klass'])),
        'rows_from_store': count(lambda v: v['source'] == 'store'), 'rows_from_rerun': count(lambda v: v['source'] == 'rerun'),
        'sql_unrunnable': count(lambda v: v['source'] == 'unrunnable'), 'store_ambiguous': ambiguous,
        'strict_recheck_disagrees': count(lambda v: v['rows_strict'] is not None and v['rows_strict'] != v['strict']),
        'strict_but_inconsistent_columns': count(lambda v: v['strict_consistent'] is False),
        'strict_unverifiable_rows': count(lambda v: v['strict'] and v['strict_consistent'] is None),
        'gold_missing': count(lambda v: not v['gold_found']),
        'trusted': len(trusted), 'trusted_wrong_strict': sum(1 for v in trusted if not v['strict']),
        'trusted_wrong_lenient_rounding': sum(1 for v in trusted if not v['lenient_rounding']),
    }


regrade_cells = [grade_cell(c) for c in cells if c['answerable']]
shutil.rmtree(TMP, ignore_errors=True)


def pool_regrade(filter_fn):
    pool = [c for c in regrade_cells if filter_fn(c)]
    n = sum(c['n'] for c in pool)
    sw = sum(c['strict_wrong'] for c in pool)
    classes = {k: sum(c['classes'][k] for c in pool) for k in CLASSES}
    subs = Counter()
    for c in pool:
        subs.update(c['sub_kinds'])
    return {'cells': len(pool), 'n': n, 'strict': sum(c['strict'] for c in pool), 'lenient': sum(c['lenient'] for c in pool),
            'lenient_rounding': sum(c['lenient_rounding'] for c in pool),
            'lenient_rounding_symmetric_sensitivity': sum(c['lenient_rounding_symmetric_sensitivity'] for c in pool),
            'strict_wrong': sw, 'classes': classes,
            'class_shares': {k: round(v / sw, 4) if sw else None for k, v in classes.items()},
            'sub_kinds': dict(subs.most_common())}


regrade_pooled = {}
for s in ('heldout-3', HSET):
    entry = {'all_conditions': pool_regrade(lambda c, s=s: c['set'] == s),
             'DQL_levels': pool_regrade(lambda c, s=s: c['set'] == s and c['cond'] in LEVELS),
             'P_one_shot': pool_regrade(lambda c, s=s: c['set'] == s and c['cond'] == 'P'),
             'A_agent': pool_regrade(lambda c, s=s: c['set'] == s and c['cond'] == 'A'),
             'per_model': {}, 'per_condition': {}}
    for m in dict.fromkeys(c['model'] for c in regrade_cells if c['set'] == s):
        entry['per_model'][m] = pool_regrade(lambda c, s=s, m=m: c['set'] == s and c['model'] == m)
    for cond in CONDS:
        if any(c['set'] == s and c['cond'] == cond for c in regrade_cells):
            entry['per_condition'][cond] = pool_regrade(lambda c, s=s, cond=cond: c['set'] == s and c['cond'] == cond)
    regrade_pooled[s] = entry
regrade_pooled['both_sets'] = pool_regrade(lambda c: True)
regrade_pooled['sonnet55_all_conditions_both_sets'] = pool_regrade(lambda c: c['model'] == 'sonnet55')
regrade_pooled['agent_both_sets'] = pool_regrade(lambda c: c['cond'] == 'A')
# Sensitivity: the set-4 paired tests re-run under the lenient grades.
set4['sensitivity'] = {g: set4_family(g) for g in ('lenient', 'lenient_rounding')}


# =========================================================================== 4. trust metrics
def trust_cell(c):
    n = c['n']
    k = sum(1 for r in c['q'].values() if r['correct'])
    T = sum(1 for r in c['q'].values() if r['trusted'])
    W = sum(1 for r in c['q'].values() if r['trusted'] and not r['correct'])
    graded = c.get('graded') or {}
    W_lr = sum(1 for q, r in c['q'].items() if r['trusted'] and not (graded.get(q) or {}).get('lenient_rounding', r['correct']))
    labelled = c['cond'] not in UNLABELLED
    out = {'n': n, 'k': k, 'T': T, 'W_T': W, 'W_T_lenient_rounding': W_lr,
           'precision': round((T - W) / T, 4) if T else None, 'precision_wilson': wilson(T - W, T) if T else [None, None],
           'kappa': round(T / n, 4) if n else None, 'labelled': labelled}
    if not labelled:
        out['sigma'] = round((n - k) / n, 4)
        out['sigma_note'] = 'no labels: every wrong answer is silent, sigma = (n-k)/n'
    elif T == 0:
        out['sigma'] = 0.0
        out['sigma_note'] = 'not informative (no trusted answers)'
    else:
        out['sigma'] = round(W / n, 4)
        out['sigma_note'] = 'sigma = W_T/n'
    unans = get(c['model'], c['cond'], c['set'] + '-unanswerable')
    if unans:
        out['unanswerable_n'] = unans['n']
        out['unanswerable_correct_stops'] = sum(1 for r in unans['q'].values() if r['correct'])
        out['unanswerable_answered_trusted'] = sum(1 for r in unans['q'].values() if not r['correct'] and r['trusted'])
        if labelled:
            # Trust precision over answerable and unanswerable questions together: a trusted answer to an
            # unanswerable question is a wrong trusted answer.
            T_all = T + out['unanswerable_answered_trusted']
            W_all = W + out['unanswerable_answered_trusted']
            out['T_all'], out['W_T_all'] = T_all, W_all
            out['precision_all'] = round((T_all - W_all) / T_all, 4) if T_all else None
            out['precision_all_wilson'] = wilson(T_all - W_all, T_all) if T_all else [None, None]
    return out


trust = {HSET: {}, 'heldout-3': {}, 'heldout-3_pooled_by_level': {}}
for cond in CONDS:
    c = get(SET4[0], cond, HSET)
    if c:
        trust[HSET][cond] = trust_cell(c)
for model, *_ in MODELS:
    for cond in CONDS:
        c = get(model, cond, 'heldout-3')
        if c:
            trust['heldout-3'].setdefault(model, {})[cond] = trust_cell(c)
for L in LEVELS:
    cl = dql_cells('heldout-3', [L])
    if cl:
        p = trust_pool(cl, 'heldout-3')
        n = sum(c['n'] for c in cl)
        p['n_answers_total'] = n
        p['kappa'] = round(p['trusted'] / n, 4)
        p['sigma'] = round(p['trusted_wrong'] / n, 4)
        p['sigma_note'] = 'not informative (no trusted answers)' if p['trusted'] == 0 else 'sigma = W_T/n'
        trust['heldout-3_pooled_by_level'][L] = p


# =========================================================================== 6. the lenient sentence
old = None
if os.path.exists(OLD_REGRADE):
    oc = [x for x in load_json(OLD_REGRADE)['cells'] if x['set'] == 'heldout-3']
    old = {'answers': sum(x['n'] for x in oc), 'cells': len(oc), 'strict': sum(x['strict'] for x in oc),
           'lenient': sum(x['lenient'] for x in oc), 'lenient_rounding_1to4': sum(x['lenientRounded'] for x in oc)}
h3 = regrade_pooled['heldout-3']['all_conditions']
h4 = regrade_pooled[HSET]['all_conditions']
sentence = {'old_scope_from_regrade_json': old, 'set3_all_conditions_now': {k: h3[k] for k in ('n', 'strict', 'lenient', 'lenient_rounding')},
            'set4_all_conditions_now': {k: h4[k] for k in ('n', 'strict', 'lenient', 'lenient_rounding')}}

# =========================================================================== write JSON
out = {
    'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'method': {
        'bootstrap': f'question-level (cluster) percentile bootstrap, {REPS} reps, seed {SEED} (random.Random("{SEED}:<set>")); '
                     f'{HSET} and {HSETU} use seed {SEALED_SEED}; '
                     'same resamples for every statistic on a set; pooled ratios resample questions, not answers',
        'wilson': 'Wilson score 95% interval, z = 1.96',
        'mcnemar': 'exact two-sided binomial McNemar on discordant pairs',
        'holm': 'Holm–Bonferroni step-down within each 4-test family {L2, L3, W2, WB} (vs A; separately vs P)',
        'ess': 'ess_icc = answers / (1 + (n0 - 1) * ICC) with one-way ANOVA ICC (clipped to [0,1]); '
               'ess_bootstrap = p(1-p) / SE_boot^2; ess_lower_bound_rho1 = (sum m_q)^2 / sum m_q^2',
        'rule_of_three': '3 / n with n = distinct questions that received a trusted answer (not answers)',
        'trusted': list(TRUSTED), 'abstained': 'answer.sql (or finalSql) empty',
        'lenient': 'strict OR (same row count AND gold has >= 1 measure column AND every gold measure column matches an answer column row by row)',
        'lenient_rounding': 'lenient OR (same row count AND answer measure values equal the gold measure values rounded to d decimals, d in 0..4, one d per answer; '
                            'only non-integer gold values are rounded; half-up (exact binary), decimal half-up or half-even all accepted)',
        'row_source': 'DQL: rows the answer showed, from a copy of the run store(s); P and A: recorded SQL re-run on a copy of the warehouse (read_only)',
        'LB_WB_build': f'LB and WB count only when identity.dql.commit starts with {FIXED}',
        'sealed': 'aggregates only; no question ids, text or SQL are written',
    },
    'sealed_set': HSET, 'as_recorded': AS_RECORDED,
    'excluded': excluded, 'partial_cells': partial,
    'questions_per_set': {s: len(universe[s]) for s in SETS},
    'accuracy': {s: {m: dict(v) for m, v in d.items()} for s, d in accuracy.items()},
    'pooled': pooled, 'set4_paired': set4, 'set3_paired': set3_paired, 'trust': trust, 'stops_vs_Am': stops_vs_Am,
    'regrade': {'cells': regrade_cells, 'pooled': regrade_pooled}, 'lenient_sentence': sentence,
}
with open(os.path.join(HERE, f'{OUT_NAME}.json'), 'w') as f:
    json.dump(out, f, indent=1)


# =========================================================================== markdown
def pct(x, digits=1):
    return '—' if x is None else f'{100 * x:.{digits}f}%'


def ci(pair, digits=1):
    if not pair or pair[0] is None:
        return '—'
    return f'{100 * pair[0]:.{digits}f}–{100 * pair[1]:.{digits}f}%'


def pfmt(p):
    return '—' if p is None else (f'{p:.4f}' if p >= 0.0001 else f'{p:.1e}')


LABEL = {m: l for m, l, *_ in MODELS}
COND_NAME = {'P': 'P (one-shot SQL)', 'A': 'A (agent)', 'Am': 'A-model (agent + DQL modeling context)'}
md = []
w = md.append
w('# Insurance benchmark — statistics v2' + (f' (sealed set {SEALED}' + (', as first recorded' if AS_RECORDED else '') + ')' if SEALED != '4' or AS_RECORDED else ''))
w('')
w(f"Generated {out['generatedAt']} by `stats_v2.py` in this folder (Python standard library; re-runnable; read-only on runs/, projects/, gold/ and insurance/; "
  'no model or network calls). Sealed sets: aggregates only.')
w('')
w('## Method note')
w('')
w(f'- **Bootstrap.** Question-level (cluster) percentile bootstrap: questions are resampled with replacement, {REPS:,} replicates, fixed seed `{SEED}`' + (f' (`{SEALED_SEED}` for {HSET})' if SEALED_SEED != SEED else '') + ' '
  '(one stream per set, `random.Random("<seed>:<set>")`). Every statistic on a set uses the same resamples, so paired differences are computed on identical question draws. '
  'For pooled measures all answers to a resampled question enter together (a question drawn twice contributes all its answers twice), which removes the pseudo-replication '
  'of counting the same question once per model and level as if it were an independent observation.')
w('- **Wilson.** Score interval, z = 1.96, on the answer counts as before; for pooled measures it is shown only as the naive (pseudo-replicated) comparison.')
w('- **Effective sample size.** `ESS_icc = answers / DEFF`, `DEFF = 1 + (n0 − 1)·ICC` with the one-way ANOVA ICC of the 0/1 outcome within question (clipped to [0, 1]); '
  '`ESS_boot = p(1 − p) / SE²_boot` (undefined when p is 0 or 1); `ESS_min = (Σ m_q)² / Σ m_q²`, the value if all answers to a question always agreed (ICC = 1).')
w('- **Rule of three.** With zero wrong trusted answers, the one-sided 95% upper bound is `3/n` with **n = distinct questions that ever received a trusted answer**; '
  'the exact bound `1 − 0.05^(1/n)` is shown beside it. When some are wrong, the question-level rate (questions with ≥ 1 wrong trusted answer) gets an exact Clopper–Pearson one-sided bound.')
w(f'- **Paired tests (set {SEALED}).** Exact two-sided McNemar on discordant questions; Holm–Bonferroni step-down within the family {{L2, L3, W2, WB}} vs A (4 tests) and separately vs P (4 tests)'
  + (' and vs A-model (4 tests, pre-registered); correct stops vs A-model (4 tests, pre-registered).' if SEALED == '5' else '.'))
w('- **Re-grade.** Strict = the run\'s own `executionMatched`, re-checked on the graded rows. Lenient = strict, or same row count and every gold *measure* (numeric) column '
  'matched by an answer column row by row (label/id columns may be missing or different). Lenient + rounding = lenient, or same row count and the answer\'s measure values '
  'equal the gold values **rounded to d decimals, d ∈ {0,…,4}** (one d per answer; only non-integer gold values are rounded; half-up on the exact binary value, decimal half-up '
  'and half-even are all accepted). The measure/label split and the error classes are a Python port of `regrade/regrade.mjs` (measure = computed in the gold projection, '
  'numeric-sounding name that is not an id/label, or fractional values). DQL rows are those the answer showed (copy of `agent-runs.sqlite`, all attempts); '
  'P and A rows come from re-running the recorded SQL on a read-only copy of the warehouse (L0).')
w('- **Classes of strict-wrong answers** (first that applies): `abstained` (no SQL, asked to clarify, or stopped with SQL); `other` (SQL that fails on re-run, or rows that '
  'match although recorded wrong); `grain_or_shape` (row count differs); `missing_or_extra_columns` (same rows, measures right, a label column missing/substituted/re-formatted); '
  '`rounding_only` (measures equal the gold rounded to 0–4 decimals); `wrong_numbers` (measure values differ, or listing values differ).')
w(f'- **Inclusion.** A report with `invalid` set is missing; LB and WB count only on DQL build `{FIXED}`. Trusted = `trustState` certified or governed; abstained = no recorded SQL.')
w('')
if excluded or partial:
    w('**Excluded / partial cells:** ' + '; '.join(f"{e['model']} {e['cond']} {e['set']} ({e['why']})" for e in excluded)
      + ('' if not partial else '; partial: ' + ', '.join(f"{p['model']} {p['cond']} {p['set']} {p['n']}/{p['expected']}" for p in partial)) + '.')
    w('')

# ---- 1. accuracy
w('## 1. Accuracy per model × condition × set')
w('')
w('Accuracy on answerable sets = strict execution match; on unanswerable sets = correct stops (`passed`). Bootstrap = question-level, 10k reps.')
w('')
for s in SETS:
    if not accuracy.get(s):
        continue
    w(f'### {s} ({len(universe[s])} questions)')
    w('')
    w('| Model | Condition | k/n | Accuracy | Wilson 95% | Bootstrap 95% |')
    w('|---|---|---:|---:|---|---|')
    for model in [m for m, *_ in MODELS]:
        for cond in CONDS:
            a = accuracy[s].get(model, {}).get(cond)
            if a:
                w(f"| {LABEL[model]} | {COND_NAME.get(cond, cond)} | {a['k']}/{a['n']} | {pct(a['acc'])} | {ci(a['wilson'])} | {ci(a['bootstrap']['ci'])} |")
    w('')

# ---- 2. pooled
w('## 2. Pooled measures corrected for pseudo-replication (set 3)')
w('')
w('The same 40 (or 10) questions are answered by every model at every level, so pooled answers are not independent. '
  'The corrected interval resamples questions; the naive Wilson interval treats every answer as independent and is shown only for comparison. '
  'A percentile bootstrap collapses to a point when every pooled answer is right (or wrong); read the upper-bound column (rule of three on distinct questions) there.')
w('')
w('### 2a. Trusted-answer precision, heldout-3')
w('')
w('| Pool | Trusted answers | Wrong | Precision | Naive Wilson (answers) | Question-cluster bootstrap | Distinct questions (with wrong) | Answers/question mean (max) | ICC | ESS_icc | ESS_boot | ESS_min | Upper 95% wrong-rate |')
w('|---|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|---|')


def upper_text(p):
    if 'rule_of_three_upper95_wrong_rate' in p:
        return f"3/{p['rule_of_three_n']} = {pct(p['rule_of_three_upper95_wrong_rate'])} (exact {pct(p['exact_upper95_wrong_rate'])}; naive 3/{p['trusted']} = {pct(p['naive_rule_of_three_on_answers'])})"
    if 'question_level_exact_upper95' in p:
        return f"question-level {p['distinct_questions_with_wrong_trusted']}/{p['distinct_questions']} wrong; exact upper {pct(p['question_level_exact_upper95'])}"
    return '—'


def pool_row(name, p):
    if not p['trusted']:
        w(f'| {name} | 0 | 0 | — | — | — | 0 | — | — | — | — | — | not informative |')
        return
    b = p.get('bootstrap', {})
    w(f"| {name} | {p['trusted']} | {p['trusted_wrong']} | {pct(p['precision'])} | {ci(p['wilson_answer_level_naive'])} | {ci(b.get('ci'))} | "
      f"{p['distinct_questions']} ({p['distinct_questions_with_wrong_trusted']}) | {p['answers_per_question_mean']} ({p['answers_per_question_max']}) | "
      f"{'—' if p.get('icc') is None else p['icc']} | {'—' if p.get('ess_icc') is None else p['ess_icc']} | {'—' if p.get('ess_bootstrap') is None else p['ess_bootstrap']} | "
      f"{p['ess_lower_bound_rho1']} | {upper_text(p)} |")


for name, entry in pooled['trust_heldout3'].items():
    pool_row(f'**{name} pooled** (all models)', entry['pooled'])
    for model, p in entry['per_model'].items():
        pool_row(f'{name} · {LABEL[model]}', p)
w('')
w('### 2b. Correct-stop rate, heldout-3-unanswerable (DQL levels)')
w('')
w('| Pool | Answers | Correct stops | Rate | Naive Wilson (answers) | Question-cluster bootstrap | Distinct questions | Answers/question mean (max) | ICC | ESS_icc | ESS_boot | ESS_min |')
w('|---|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|')


def stop_row(name, p):
    b = p.get('bootstrap', {})
    w(f"| {name} | {p['answers']} | {p['successes']} | {pct(p['estimate'])} | {ci(p['wilson_answer_level_naive'])} | {ci(b.get('ci'))} | {p['distinct_questions']} | "
      f"{p['answers_per_question_mean']} ({p['answers_per_question_max']}) | {'—' if p.get('icc') is None else p['icc']} | {'—' if p.get('ess_icc') is None else p['ess_icc']} | "
      f"{'—' if p.get('ess_bootstrap') is None else p['ess_bootstrap']} | {p['ess_lower_bound_rho1']} |")


stop_row('**All DQL levels × models, pooled**', u_entry['pooled'])
for model, p in u_entry['per_model'].items():
    stop_row(f'{LABEL[model]} (all its DQL levels)', p)
for L, p in u_entry['per_level'].items():
    stop_row(f'Level {L} (all models)', p)
for model, p in u_entry['agent'].items():
    stop_row(f'Agent A · {LABEL[model]}', p)
w('')
if 'correct_stop_heldout4_unanswerable' in pooled:
    w(f'Set {SEALED} (Sonnet 5.5) for reference:')
    w('')
    w('| Pool | Answers | Correct stops | Rate | Naive Wilson (answers) | Question-cluster bootstrap | Distinct questions | Answers/question mean (max) | ICC | ESS_icc | ESS_boot | ESS_min |')
    w('|---|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|')
    stop_row(f'{HSETU}, L2+L3+W2+WB pooled', pooled['correct_stop_heldout4_unanswerable']['pooled'])
    w('')
    w('| Pool | Trusted answers | Wrong | Precision | Naive Wilson (answers) | Question-cluster bootstrap | Distinct questions (with wrong) | Answers/question mean (max) | ICC | ESS_icc | ESS_boot | ESS_min | Upper 95% wrong-rate |')
    w('|---|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|---|')
    for name, p in pooled['trust_heldout4'].items():
        pool_row(f'{HSET} {name}', p)
    w('')

# ---- 3. set 4 paired
w(f'## 3. Set {SEALED} (Claude Sonnet 5.5, 200 questions): paired tests')
w('')
w('Gained = the level right and the reference wrong; lost = the reverse. Holm adjusts within each family of 4 tests.')
w('')
def paired_table(res):
    w('| Comparison | Level k/n | Ref k/n | Δ accuracy | Paired bootstrap 95% (Δ) | Gained / lost | McNemar p (raw) | Holm-adjusted p |')
    w('|---|---:|---:|---:|---|---|---:|---:|')
    for ref_name, ref_label in (('vs_A', 'A (agent)'), ('vs_P', 'P (one-shot SQL)'), ('vs_Am', 'A-model')):
        for L, t in (res.get(ref_name) or {}).items():
            w(f"| {L} − {ref_label} | {t['k_left']}/{t['n']} | {t['k_right']}/{t['n']} | {'+' if t['diff'] >= 0 else ''}{100 * t['diff']:.1f} pts | "
              f"{ci(t['diff_bootstrap']['ci'])} | {t['gained']} / {t['lost']} | {pfmt(t['p_raw'])} | {pfmt(t['p_holm'])} |")
    if res.get('P_vs_A'):
        t = res['P_vs_A']
        w(f"| P − A (not in a family) | {t['k_left']}/{t['n']} | {t['k_right']}/{t['n']} | {'+' if t['diff'] >= 0 else ''}{100 * t['diff']:.1f} pts | "
          f"{ci(t['diff_bootstrap']['ci'])} | {t['gained']} / {t['lost']} | {pfmt(t['p_raw'])} | — |")
    for key, name in (('W2_vs_Am', 'W2 − A-model (H1, pre-registered primary)' if SEALED == '5' else 'W2 − A-model (exploratory)'), ('Am_vs_A', 'A-model − A (exploratory)')):
        t = res.get(key)
        if t:
            w(f"| {name} | {t['k_left']}/{t['n']} | {t['k_right']}/{t['n']} | {'+' if t['diff'] >= 0 else ''}{100 * t['diff']:.1f} pts | "
              f"{ci(t['diff_bootstrap']['ci'])} | {t['gained']} / {t['lost']} | {pfmt(t['p_raw'])} | — |")
    w('')


paired_table(set4)
if stops_vs_Am:
    w('**Correct stops on the 50 unanswerable questions, each level against A-model** (pre-registered secondary 3; Holm over the four levels).')
    w('')
    w('| Comparison | Level k/n | A-model k/n | Δ | Paired bootstrap 95% (Δ) | Gained / lost | McNemar p (raw) | Holm-adjusted p |')
    w('|---|---:|---:|---:|---|---|---:|---:|')
    for L, t in stops_vs_Am.items():
        w(f"| {L} − A-model | {t['k_left']}/{t['n']} | {t['k_right']}/{t['n']} | {'+' if t['diff'] >= 0 else ''}{100 * t['diff']:.1f} pts | "
          f"{ci(t['diff_bootstrap']['ci'])} | {t['gained']} / {t['lost']} | {pfmt(t['p_raw'])} | {pfmt(t['p_holm'])} |")
    w('')
w('**Sensitivity: the same tests under the lenient grades** (section 5). The agent and one-shot SQL lose many more answers to label columns than DQL does, '
  'so the comparison with A depends on the grading rule.')
w('')
for g, label in (('lenient', 'Lenient'), ('lenient_rounding', 'Lenient + rounding')):
    w(f'*{label}*')
    w('')
    paired_table(set4['sensitivity'][g])

# ---- 4. trust
w('## 4. Trust metrics per level')
w('')
w('T = answers labelled certified/governed; W_T = of those, strict-wrong; precision π = (T − W_T)/T with Wilson 95%; trusted coverage κ = T/n; '
  'silent-error rate σ = W_T/n for DQL, (n − k)/n for P and A (no labels, every wrong answer is silent). W_T (lenient+rounding) re-counts W_T under the lenient + rounding grade.')
w('')


def trust_table(rows):
    w('| Condition | n | T | W_T | W_T (lenient+rounding) | Precision π | π Wilson 95% | κ | σ | Unanswerable: correct stops / answered as trusted |')
    w('|---|---:|---:|---:|---:|---:|---|---:|---|---|')
    for cond, t in rows:
        sigma = pct(t['sigma']) if t['sigma_note'] != 'not informative (no trusted answers)' else f"{pct(t['sigma'])} — not informative (no trusted answers)"
        un = f"{t['unanswerable_correct_stops']}/{t['unanswerable_n']} / {t['unanswerable_answered_trusted']}" if 'unanswerable_n' in t else '—'
        w(f"| {COND_NAME.get(cond, cond)} | {t['n']} | {t['T'] if t['labelled'] else '— (no labels)'} | {t['W_T'] if t['labelled'] else '—'} | "
          f"{t['W_T_lenient_rounding'] if t['labelled'] else '—'} | {pct(t['precision'])} | {ci(t['precision_wilson'])} | {pct(t['kappa']) if t['labelled'] else '—'} | {sigma} | {un} |")
    w('')


w(f'### Set {SEALED} (Sonnet 5.5)')
w('')
trust_table(list(trust[HSET].items()))
w('### Set 3, pooled across models per level (precision CI = question-cluster bootstrap)')
w('')
w('| Level | Answers | T | W_T | Precision π | Naive Wilson | Cluster bootstrap | Distinct questions trusted (with wrong) | κ | σ |')
w('|---|---:|---:|---:|---:|---|---|---:|---:|---|')
for L, p in trust['heldout-3_pooled_by_level'].items():
    sig = f"{pct(p['sigma'])}" + (' — not informative (no trusted answers)' if p['trusted'] == 0 else '')
    w(f"| {L} | {p['n_answers_total']} | {p['trusted']} | {p['trusted_wrong']} | {pct(p['precision'])} | {ci(p['wilson_answer_level_naive'])} | "
      f"{ci((p.get('bootstrap') or {}).get('ci'))} | {p['distinct_questions']} ({p['distinct_questions_with_wrong_trusted']}) | {pct(p['kappa'])} | {sig} |")
w('')
w('### Set 3, per model')
w('')
for model, rows in trust['heldout-3'].items():
    w(f'**{LABEL[model]}**')
    w('')
    trust_table(list(rows.items()))

# ---- 5. regrade
w('## 5. Lenient and rounding re-grade (all conditions, both sets)')
w('')


def class_cells(p):
    sw = p['strict_wrong']
    return ' | '.join(f"{p['classes'][k]} ({pct(p['classes'][k] / sw) if sw else '—'})" for k in CLASSES)


w('### Headline')
w('')
w('| Scope | Answers | Strict | Lenient | Lenient + rounding | Strict-wrong | ' + ' | '.join(CLASSES) + ' |')
w('|---|---:|---:|---:|---:|---:|' + '---:|' * len(CLASSES))
scopes = []
for s in ('heldout-3', HSET):
    e = regrade_pooled[s]
    scopes += [(f'{s} · all conditions', e['all_conditions']), (f'{s} · DQL levels', e['DQL_levels']),
               (f'{s} · P (one-shot)', e['P_one_shot']), (f'{s} · A (agent)', e['A_agent'])]
    scopes += [(f'{s} · {LABEL.get(m, m)}', p) for m, p in e['per_model'].items()]
scopes += [('both sets · all conditions', regrade_pooled['both_sets']),
           ('both sets · Sonnet 5.5 (all its conditions)', regrade_pooled['sonnet55_all_conditions_both_sets']),
           ('both sets · agent A (Opus 5.5 + Sonnet 5.5)', regrade_pooled['agent_both_sets'])]
for name, p in scopes:
    if not p['n']:
        continue
    w(f"| {name} | {p['n']} | {p['strict']} ({pct(p['strict'] / p['n'])}) | {p['lenient']} ({pct(p['lenient'] / p['n'])}) | "
      f"{p['lenient_rounding']} ({pct(p['lenient_rounding'] / p['n'])}) | {p['strict_wrong']} | {class_cells(p)} |")
w('')
w('Class cells = count (share of strict-wrong answers).')
w('')
w('### Per condition, pooled over models')
w('')
w('| Set | Condition | Answers | Strict | Lenient | Lenient + rounding | Strict-wrong | ' + ' | '.join(CLASSES) + ' |')
w('|---|---|---:|---:|---:|---:|---:|' + '---:|' * len(CLASSES))
for s in ('heldout-3', HSET):
    for cond, p in regrade_pooled[s]['per_condition'].items():
        w(f"| {s} | {COND_NAME.get(cond, cond)} | {p['n']} | {p['strict']} | {p['lenient']} | {p['lenient_rounding']} | {p['strict_wrong']} | {class_cells(p)} |")
w('')
w('### Per model × condition × set')
w('')
w('| Set | Model | Condition | n | Strict | Lenient | +rounding | Strict-wrong | ' + ' / '.join(CLASSES) + ' | Rows store / re-run / unrunnable | Re-check disagrees |')
w('|---|---|---|---:|---:|---:|---:|---:|---|---|---:|')
for c in regrade_cells:
    w(f"| {c['set']} | {LABEL.get(c['model'], c['model'])} | {COND_NAME.get(c['cond'], c['cond'])} | {c['n']} | {c['strict']} | {c['lenient']} | {c['lenient_rounding']} | "
      f"{c['strict_wrong']} | {' / '.join(str(c['classes'][k]) for k in CLASSES)} | {c['rows_from_store']} / {c['rows_from_rerun']} / {c['sql_unrunnable']} | {c['strict_recheck_disagrees']} |")
w('')
w('### Sub-kinds, pooled (both sets, all conditions)')
w('')
w('| Class:sub-kind | Count |')
w('|---|---:|')
for k, v in regrade_pooled['both_sets']['sub_kinds'].items():
    w(f'| {k} | {v} |')
w('')
tot_dis = sum(c['strict_recheck_disagrees'] for c in regrade_cells)
tot_unr = sum(c['sql_unrunnable'] for c in regrade_cells)
tot_amb = sum(c['store_ambiguous'] for c in regrade_cells)
w(f"Checks: re-applying the strict rule to the graded rows disagrees with the recorded verdict for {tot_dis} of {sum(c['n'] for c in regrade_cells)} answers; "
  f"{tot_unr} answers have SQL with no stored result that fails on re-run (class `other`); {tot_amb} stored results had conflicting rows for the same SQL (first kept). "
  f"For comparability, the regrade.mjs rounding rule (d = 1..4 only) gives {sum(c['lenient_rounding_1to4_regrade_mjs'] for c in regrade_cells)} lenient+rounding answers "
  f"against {sum(c['lenient_rounding'] for c in regrade_cells)} with d = 0..4. Sensitivity (not in the headline): also accepting answers that equal the gold only after "
  f"rounding the *answer* to the gold's 1–4 decimals gives {regrade_pooled['both_sets']['lenient_rounding_symmetric_sensitivity']}.")
w('')

# ---- 6. sentence
w('## 6. The lenient-vs-strict sentence, corrected')
w('')
if old:
    w(f"The earlier re-grade of set 3 ({old['answers']:,} answers: {old['cells']} model×condition cells, Opus 5.5, Sonnet 5, Qwen and the GPT runs available on 29 September, "
      f"before the LB/WB build filter) found **{old['strict']:,} strict-correct and {old['lenient']:,} lenient-correct** answers: lenient exceeded strict by "
      f"{old['lenient'] - old['strict']} answers ({100 * (old['lenient'] - old['strict']) / old['answers']:.1f} points). Correct statement: strict k = {old['strict']:,}, "
      f"lenient k = {old['lenient']:,} (lenient is the larger number).")
    w('')
w(f"With every condition now graded (all seven models, P, A, all DQL levels, LB/WB on build {FIXED} only): set 3 has **strict {h3['strict']:,} and lenient {h3['lenient']:,}** "
  f"of {h3['n']:,} answers (lenient + rounding {h3['lenient_rounding']:,}); set {SEALED} (Sonnet 5.5) has strict {h4['strict']:,}, lenient {h4['lenient']:,}, "
  f"lenient + rounding {h4['lenient_rounding']:,} of {h4['n']:,}.")
w('')
pc = regrade_pooled['heldout-3']['per_condition']
pc4 = regrade_pooled[HSET]['per_condition']
gap = lambda p: 100 * (p['lenient'] - p['strict']) / p['n']
dql3 = regrade_pooled['heldout-3']['DQL_levels']
dql4 = regrade_pooled[HSET]['DQL_levels']
w(f"Suggested wording: *On set 3, {h3['strict']:,} of {h3['n']:,} answers were correct under the strict rule and {h3['lenient']:,} under the lenient rule "
  f"(+{gap(h3):.1f} points). The gap is not uniform: +{gap(dql3):.1f} points for DQL levels, +{gap(pc['P']):.1f} for one-shot SQL and +{gap(pc['A']):.1f} for the agent on set 3; "
  f"on set {SEALED}, +{gap(dql4):.1f} for DQL levels against +{gap(pc4['P']) if 'P' in pc4 else float('nan'):.1f} (one-shot) and +{gap(pc4['A']) if 'A' in pc4 else float('nan'):.1f} (agent), mostly answers that return a different label column "
  "(e.g. a name for an id) with the right numbers.*")
w('')
w('The draft\'s conclusion that "the strict scores do not depend on column naming" holds for the pooled set-3 total but not for comparisons against the baselines: '
  'see the lenient sensitivity of the set-4 paired tests in section 3.')
w('')

with open(os.path.join(HERE, f'{OUT_NAME}.md'), 'w') as f:
    f.write('\n'.join(md) + '\n')

# =========================================================================== stdout (aggregates only)
print(f"cells {len(cells)} (excluded {len(excluded)}, partial {len(partial)}); graded answers {sum(c['n'] for c in regrade_cells)}; "
      f"strict re-check disagreements {tot_dis}; unrunnable {tot_unr}")
print(f'wrote {OUT_NAME}.json and {OUT_NAME}.md')

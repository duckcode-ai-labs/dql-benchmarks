#!/usr/bin/env python3
"""Taxonomy of wrong trusted answers and lenient-grade examples, insurance set 3.

    python3 analysis/insurance-2026-09-29/taxonomy/taxonomy.py          # writes taxonomy.json + taxonomy.md
    python3 analysis/insurance-2026-09-29/taxonomy/taxonomy.py --dump   # also prints every record (inspection)

Scope and rules
  * Set 3 only: heldout-3 (answerable, public) and heldout-3-unanswerable. Every path
    this script opens passes `guard()`, which refuses anything that belongs to a sealed
    set (heldout-4/5, their run ids, audit folders, private/, set5-writer).
  * Read-only on work/ and insurance/. Run stores (agent-runs.sqlite) and the L0
    warehouse are COPIED into a temporary directory first; the DuckDB copy is opened
    read-only by the repository's lib/duckdb_query.py (run with .venv/bin/python).
  * Inclusion is the one stats_v2.py uses: a report with `invalid` set is skipped; LB
    and WB count only on DQL build 627009a1. Trusted = trustState certified|governed.
  * Grading for Task 2 reuses the paper's own code: the "re-grade (rows)" section of
    paper/stats_v2/stats_v2.py (port of lib/row-match.mjs and regrade.mjs) is loaded
    from that file and executed in a private namespace, so strict / lenient here are
    exactly the paper's grades. Its sha256 is recorded in taxonomy.json.
  * No model, network or service calls. Python standard library only.

Everything under JUDGEMENT below is hand-written classification by the analyst, not
computed. Everything else is extracted from the run reports, run stores and gold file.
"""
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
WORK = os.path.join(REPO, 'work', 'insurance')
RUNS = os.path.join(WORK, 'runs')
GOLD_FILE = os.path.join(WORK, 'gold', 'heldout-3.json')
L0_WAREHOUSE = os.path.join(WORK, 'projects', 'L0', 'acme_insurance.duckdb')
STATS_V2 = os.path.join(HERE, '..', 'paper', 'stats_v2', 'stats_v2.py')
VENV_PY = os.path.join(REPO, '.venv', 'bin', 'python')
DUCK_HELPER = os.path.join(REPO, 'lib', 'duckdb_query.py')
DUMP = '--dump' in sys.argv

FIXED = '627009a1'
TRUSTED = ('certified', 'governed')
SETS = ('heldout-3', 'heldout-3-unanswerable')
LEVELS = ['L0', 'L1', 'L2', 'L3', 'LB', 'W0', 'W1', 'W2', 'WB']
# key, label, DQL/baseline run, agent run (set 3)
MODELS = [('opus', 'Claude Opus 5.5', 'fl-opus', 'ag-opus'),
          ('sonnet55', 'Claude Sonnet 5.5', 'fl-sonnet55', 'ag-sonnet55'),
          ('sonnet5', 'Claude Sonnet 5', 'fl-sonnet', None),
          ('qwen', 'Qwen 3.8 27B (local)', 'fl-qwen', None),
          ('luna', 'GPT-6 Luna (max)', 'fl-luna', None),
          ('sol', 'GPT-6 Sol (medium)', 'fl-sol', None),
          ('terra', 'GPT-5.6 Terra (high)', 'fl-terra', None)]
LABEL = {m: l for m, l, *_ in MODELS}
# What answers on each level (insurance/build.mjs LAYERS, insurance/run.mjs):
LEVEL_SEMANTICS = {
    'L2': "dbt Labs' MetricFlow semantic models (data/insurance/semantic-layer-llm-benchmarking/models/omg_semantics), run by MetricFlow",
    'L3': "as L2 + DQL skills",
    'LB': 'business layer B: its dbt metrics run by MetricFlow (insurance/layers/B/dbt/models/business_semantics/*.yml) + 9 certified blocks + skills',
    'W2': "dbt Labs' semantic models converted by `dql semantic import` to DQL native metrics (work/insurance/projects/W2/semantic-layer/), no dbt",
    'WB': "business layer B's metrics as DQL native metrics (imported from LB), no dbt + 9 certified blocks + skills",
}

SEALED = re.compile(r'(heldout-4|heldout-5|questions-4|questions-5|/(fl4|ag4|ag4m|fl5|ag5|ag5m)-|/audit/|/private/|set5-writer)')


def guard(path):
    p = os.path.abspath(path)
    if SEALED.search(p):
        raise RuntimeError(f'refusing to open a sealed path: {p}')
    return p


def load_json(path):
    with open(guard(path)) as f:
        return json.load(f)


# ----------------------------------------------------------------------------- the paper's grader
def load_grader():
    src = open(guard(STATS_V2)).read()
    start = src.index('# --- port of lib/row-match.mjs')
    end = src.index('# --- row sources: run-store copies and warehouse copies')
    segment = src[start:end]
    ns = {'re': re, 'math': math, 'Counter': Counter, 'Decimal': Decimal, 'ROUND_HALF_UP': ROUND_HALF_UP,
          'ROUND_HALF_EVEN': ROUND_HALF_EVEN, 'localcontext': localcontext, 'answer_sql': answer_sql}
    exec(compile(segment, STATS_V2 + ':regrade-section', 'exec'), ns)
    return ns, hashlib.sha256(segment.encode()).hexdigest()


def answer_sql(x):
    return (x.get('answer') or {}).get('sql') or x.get('finalSql') or ''


G, GRADER_SHA = load_grader()

# ----------------------------------------------------------------------------- inputs
gold = {c['id'].strip(): c for c in load_json(GOLD_FILE)['cases']}
TMP = tempfile.mkdtemp(prefix='taxonomy_')


def cell_dir(run, cond, set_name, agent=None):
    if cond == 'P':
        return os.path.join(RUNS, run, 'baseline-full', set_name)
    if cond == 'A':
        return os.path.join(RUNS, agent, 'agent-ddl', set_name)
    return os.path.join(RUNS, run, cond, set_name)


cells, excluded = [], []
for model, label, run, agent in MODELS:
    conds = ['P'] + (['A'] if agent else []) + LEVELS
    for cond in conds:
        for set_name in SETS:
            if cond == 'P' and set_name.endswith('unanswerable'):
                continue
            d = cell_dir(run, cond, set_name, agent)
            path = os.path.join(d, 'report.json')
            if not os.path.exists(guard(path)):
                excluded.append({'model': model, 'cond': cond, 'set': set_name, 'why': 'no report.json'})
                continue
            r = load_json(path)
            commit = (((r.get('identity') or {}).get('dql') or {}).get('commit') or '')
            if r.get('invalid'):
                excluded.append({'model': model, 'cond': cond, 'set': set_name, 'why': 'report flagged invalid'})
                continue
            if cond in ('LB', 'WB') and not commit.startswith(FIXED):
                excluded.append({'model': model, 'cond': cond, 'set': set_name, 'why': f'old DQL build {commit[:8]}'})
                continue
            q = {}
            for x in r['results']:
                q[x['name'].strip()] = x
            cells.append({'model': model, 'label': label, 'run': agent if cond == 'A' else run, 'cond': cond,
                          'set': set_name, 'dir': d, 'commit': commit[:8], 'q': q,
                          'layer': ((r.get('run') or {}).get('warehouse') or 'L0') if cond in ('P', 'A') else cond})


def trust(x):
    return (x.get('answer') or {}).get('trustState')


def correct(cell, x):
    return bool(x.get('executionMatched')) if cell['set'] == 'heldout-3' else bool(x.get('passed'))


def lane(x):
    for t in x.get('trace') or []:
        if t.get('stage') == 'lane':
            return t.get('payload') or {}
    return {}


# ----------------------------------------------------------------------------- run stores (copies)
_stores = {}


def store(cell):
    """Every agent run and artifact of this cell's set, from COPIES of the run store of the
    finished set and of its resumed/aborted attempts."""
    key = (cell['run'], cell['cond'], cell['set'])
    if key in _stores:
        return _stores[key]
    level_dir = os.path.dirname(cell['dir'])
    names = sorted([n for n in os.listdir(guard(level_dir))
                    if n == cell['set'] or n.startswith(cell['set'] + '.attempt-') or n.startswith(cell['set'] + '.aborted-')],
                   key=lambda n: (n != cell['set'], n))
    runs, arts = [], {}
    for n in names:
        src = os.path.join(level_dir, n, 'project', '.dql', 'local', 'agent-runs.sqlite')
        if not os.path.exists(guard(src)):
            continue
        dst_dir = os.path.join(TMP, 'stores', *key[:2], n)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, 'agent-runs.sqlite')
        shutil.copyfile(src, dst)
        if os.path.exists(src + '-wal'):
            shutil.copyfile(src + '-wal', dst + '-wal')
        con = sqlite3.connect(dst)
        try:
            for (p,) in con.execute('select payload_json from agent_runs'):
                try:
                    runs.append(dict(json.loads(p), _store=n))
                except Exception:
                    pass
            for fp, p in con.execute('select fingerprint, payload_json from agent_run_artifacts'):
                try:
                    a = json.loads(p)
                except Exception:
                    continue
                if isinstance(a, dict):
                    arts.setdefault(fp, a)
        finally:
            con.close()
    _stores[key] = (runs, arts)
    return _stores[key]


def rows_of(result):
    if not isinstance(result, dict) or not isinstance(result.get('rows'), list):
        return None, None
    columns = result.get('columns') or []
    out = []
    for row in result['rows']:
        if isinstance(row, dict):
            keys = columns if columns and all(isinstance(k, str) for k in columns) else list(row.keys())
            out.append([row.get(k) for k in keys])
        else:
            out.append(row)
    if out and isinstance(result['rows'][0], dict) and not (columns and all(isinstance(k, str) for k in columns)):
        columns = list(result['rows'][0].keys())
    return columns, out


def shown(cell, x):
    """The run, artifact and rows DQL showed for this answer (artifact SQL == the answer's SQL)."""
    runs, arts = store(cell)
    sql = answer_sql(x)
    art = next((a for a in arts.values() if a.get('sql') == sql and isinstance(a.get('result'), dict)), None)
    question = gold.get(x['name'].strip(), {}).get('question', '').strip()
    run = None
    for p in runs:
        if p.get('question', '').strip() != question:
            continue
        refs = [(a.get('payloadRef') or '') for a in p.get('artifacts') or []]
        hit = [arts.get(r) or arts.get(r.replace('sha256:', '')) for r in refs]
        if art is not None and any(h is art for h in hit):
            run = p
            break
        if run is None and p.get('trustState') == trust(x):
            run = p
    return run, art


# ----------------------------------------------------------------------------- warehouse re-runs
# P and A: their recorded SQL on a copy of the L0 warehouse (the one they ran on).
# DQL levels: only when the run store holds no rows for the answer's SQL (as stats_v2.py does),
# on a copy of that level's warehouse.
_wh = {}
_rerun = defaultdict(dict)


def warehouse(layer='L0'):
    if layer not in _wh:
        source = L0_WAREHOUSE if layer == 'L0' else os.path.join(WORK, 'projects', layer, 'acme_insurance.duckdb')
        d = os.path.join(TMP, 'warehouse', layer)
        os.makedirs(d, exist_ok=True)
        target = os.path.join(d, 'acme_insurance.duckdb')  # keep the name: SQL may say "acme_insurance"."main".t
        shutil.copyfile(guard(source), target)
        if os.path.exists(source + '.wal'):
            shutil.copyfile(source + '.wal', target + '.wal')
        _wh[layer] = target
    return _wh[layer]


def rerun(statements, layer='L0'):
    cache = _rerun[layer]
    fresh = [s for s in dict.fromkeys(statements) if s and s not in cache]
    if fresh:
        req = {'database': warehouse(layer), 'queries': [{'id': str(i), 'sql': s} for i, s in enumerate(fresh)]}
        proc = subprocess.run([VENV_PY, DUCK_HELPER], input=json.dumps(req), capture_output=True, text=True, timeout=3600)
        if proc.returncode != 0:
            raise RuntimeError('duckdb helper failed: ' + proc.stderr[-2000:])
        out = json.loads(proc.stdout)
        for i, s in enumerate(fresh):
            cache[s] = out.get(str(i))
    return cache


# ============================================================================= Task 1: counts
def tier_outcomes(x):
    return tuple((x.get('capture') or {}).get('tiers') or [])


counts = {'by_level': {}, 'by_set': {}}
trusted_records = []
for c in cells:
    if c['cond'] in ('P', 'A'):
        continue
    for name, x in c['q'].items():
        t = trust(x)
        if t not in TRUSTED:
            continue
        trusted_records.append((c, name, x))

for set_name in SETS:
    per_level = {}
    for lv in LEVELS:
        recs = [(c, n, x) for c, n, x in trusted_records if c['set'] == set_name and c['cond'] == lv]
        answers = sum(len(c['q']) for c in cells if c['set'] == set_name and c['cond'] == lv)
        wrong = [(c, n, x) for c, n, x in recs if not correct(c, x)]
        per_level[lv] = {
            'answers': answers,
            'trusted': len(recs),
            'trusted_certified': sum(1 for _, _, x in recs if trust(x) == 'certified'),
            'trusted_governed': sum(1 for _, _, x in recs if trust(x) == 'governed'),
            'wrong_trusted': len(wrong),
            'wrong_certified': sum(1 for _, _, x in wrong if trust(x) == 'certified'),
            'wrong_governed': sum(1 for _, _, x in wrong if trust(x) == 'governed'),
            'distinct_questions_trusted': len({n for _, n, _ in recs}),
            'distinct_questions_wrong': len({n for _, n, _ in wrong}),
            'engine_routes': dict(Counter(lane(x).get('engineRoute') for _, _, x in recs)),
        }
    counts['by_level'][set_name] = per_level
    recs = [(c, n, x) for c, n, x in trusted_records if c['set'] == set_name]
    wrong = [(c, n, x) for c, n, x in recs if not correct(c, x)]
    counts['by_set'][set_name] = {
        'answers': sum(len(c['q']) for c in cells if c['set'] == set_name and c['cond'] in LEVELS),
        'trusted': len(recs), 'wrong_trusted': len(wrong),
        'trusted_certified': sum(1 for _, _, x in recs if trust(x) == 'certified'),
        'trusted_governed': sum(1 for _, _, x in recs if trust(x) == 'governed'),
        'wrong_certified': sum(1 for _, _, x in wrong if trust(x) == 'certified'),
        'wrong_governed': sum(1 for _, _, x in wrong if trust(x) == 'governed'),
        'distinct_questions_trusted': len({n for _, n, _ in recs}),
        'distinct_questions_wrong': len({n for _, n, _ in wrong}),
    }
# Unanswerable answers that did not stop, with their labels (for the record).
counts['unanswerable_not_stopped'] = Counter(
    f"{c['cond']}:{trust(x)}" for c in cells if c['set'] == 'heldout-3-unanswerable' and c['cond'] in LEVELS
    for x in c['q'].values() if not x.get('passed'))
counts['unanswerable_not_stopped'] = dict(counts['unanswerable_not_stopped'])
# Did a certified block ever answer on set 3 (any label)? Tier outcomes of every DQL answer.
tier_counter = Counter()
for c in cells:
    if c['cond'] in LEVELS:
        for x in c['q'].values():
            for t in tier_outcomes(x):
                if t.startswith('certified:'):
                    tier_counter[f"{c['cond']}:{t}"] += 1
counts['certified_tier_outcomes'] = dict(sorted(tier_counter.items()))
counts['certified_tier_answered'] = sum(v for k, v in tier_counter.items() if not k.endswith(':refused'))


# ============================================================================= Task 1: wrong trusted records
def short_rows(rows, k=3):
    return [list(r) if isinstance(r, (list, tuple)) else r for r in (rows or [])[:k]]


def evals(run):
    out = {}
    for e in (run or {}).get('evaluations') or []:
        out.setdefault(e.get('label'), []).append(e.get('message'))
    return out


wrong_records = []
for c, name, x in trusted_records:
    if correct(c, x):
        continue
    g = gold.get(name) if c['set'] == 'heldout-3' else None
    run, art = shown(c, x)
    cols, rows = rows_of((art or {}).get('result'))
    intent = (art or {}).get('askIntentV1') or {}
    ev = evals(run)
    compiled = '; '.join(ev.get('Semantic compilation') or [])
    m = re.search(r'from metrics (.+?)(?: by | \(|$)', compiled)
    metrics = [s.strip() for s in m.group(1).split(',')] if m else []
    engine = re.search(r'on the ([\w-]+) semantic engine', compiled)
    gold_rows = (x.get('expected') or {}).get('goldRows') if (x.get('expected') or {}).get('goldRows') is not None else (g or {}).get('gold', {}).get('rows')
    rec = {
        'set': c['set'], 'model': c['model'], 'model_label': c['label'], 'run': c['run'], 'level': c['cond'],
        'question_id': name, 'question': (g or {}).get('question') or (run or {}).get('question'),
        'trust_state': trust(x), 'eval_route': x.get('route'), 'engine_route': lane(x).get('engineRoute'),
        'tiers': list(tier_outcomes(x)), 'semantic_engine': engine.group(1) if engine else None,
        'governed_metrics': metrics, 'certified_block': None,
        'interpretation': (ev.get('Interpretation') or [None])[0],
        'semantic_compilation': compiled or None,
        'requested_coverage_warnings': ev.get('Requested coverage') or [],
        'intent_unresolved': intent.get('unresolved') or [],
        'intent_group_by': [gb.get('ref') for gb in intent.get('groupBy') or []],
        'intent_measures': [{'ref': mm.get('ref'), 'alias': mm.get('alias'), 'derived': mm.get('derived')} for mm in intent.get('measures') or []],
        'failures': x.get('failures') or [],
        'dql_sql': answer_sql(x),
        'dql_columns': cols, 'dql_row_count': len(rows) if rows is not None else None, 'dql_rows_head': short_rows(rows),
        'gold_sql': (g or {}).get('goldSql'), 'gold_columns': (g or {}).get('gold', {}).get('columns'),
        'gold_row_count': len(gold_rows) if gold_rows is not None else None, 'gold_rows_head': short_rows(gold_rows),
        'run_store': (run or {}).get('_store'), 'agent_run_id': (run or {}).get('id'),
    }
    wrong_records.append(rec)

wrong_records.sort(key=lambda r: (r['question_id'], r['level'], r['model']))

# ----------------------------------------------------------------------------- JUDGEMENT (hand-written)
# =====================================================================================
#  ANALYST JUDGEMENT, NOT COMPUTED. One entry per distinct (question, root cause).
#  Classes: definition | reading | route | compilation | execution | reference | uncertain.
#  Evidence was read from the extracted records (interpretation, compilation receipt,
#  askIntentV1.unresolved, rows shown), the cited definition files and the EVIDENCE_SQL
#  checks below. The script checks that every wrong trusted answer is covered by exactly
#  one entry and that the listed answer counts match the extraction.
# =====================================================================================
B_CLAIMS = 'insurance/layers/B/dbt/models/business_semantics/claims.yml'
B_POLICIES = 'insurance/layers/B/dbt/models/business_semantics/policies.yml'
B_FIRE = 'insurance/layers/B/dbt/models/business_semantics/underwriting_and_fire_risk.yml'
JUDGEMENT = {
    'heldout-across-our-fire-claims-what-is-the-correlation-c-82e631': {
        'label': 'Correlation coefficient (firefighters vs loss ratio)',
        'class': 'route', 'confidence': 'high', 'alternative': None,
        'definition_files': [B_FIRE + ' (metrics fire_sample_avg_loss_ratio, fire_risk_records)'],
        'row_comparison': 'DQL: 7 rows (average loss ratio and record count per firefighter count 4..10). '
                          'Gold: 1 row, corr = -0.291. A correlation over the 7 group means shown is -0.831 (EVIDENCE_SQL corr_over_group_means).',
        'evidence': (
            "The question asks for one Pearson coefficient; layer B has no correlation metric and the semantic tier cannot express one. "
            "DQL's reader recorded exactly this in the structured intent (askIntentV1.unresolved: \"The system cannot compute a Pearson "
            "correlation directly ... A correlation over these groups only approximates the row-level coefficient\", material=false), and the "
            "host still answered on the semantic tier (MetricFlow, fire_sample_avg_loss_ratio and fire_risk_records by number_of_firefighters) "
            "and labelled the 7-row breakdown governed. The metric values are right for what they are (unweighted AVG(Loss_Ratio) and a row "
            f"count, {B_FIRE}), so the definition is not at fault; the route answered a different, easier question. The approximation the "
            "answer invites is badly off: corr over the group means is -0.83 against the row-level -0.29. Of the other 62 DQL answers to this "
            "question, 61 were drafted SQL (review_required) and right, and one was blocked.")},
    'heldout-what-was-the-compound-annual-growth-rate-of-the-53c830': {
        'label': 'CAGR of one policy\'s annual premium',
        'class': 'route', 'confidence': 'high', 'alternative': None,
        'definition_files': [B_POLICIES + ' (metric written_premium)'],
        'row_comparison': 'DQL: 5 rows, written premium 15,000 / 16,000 / 17,000 / 18,000 / 20,000 for 2015-2019. Gold: 1 row, cagr = 0.0746. '
                          'The endpoints shown give (20000/15000)^(1/4) - 1 = 0.0746, i.e. the inputs are right and the rate is missing.',
        'evidence': (
            f"written_premium ({B_POLICIES}: sum of policy_amount.Policy_Amount listed in premium) returns the correct yearly inputs for policy "
            "31003000336, and the CAGR computed from the first and last rows equals the gold. But the answer is the 5-row input series, labelled "
            "governed. Opus's structured intent flags it (\"The intent can't express CAGR directly ...\", material=false); the two Sonnet readings "
            "say it only in prose (\"CAGR itself is not a governed metric\"; \"so the compound annual growth rate ... can be computed from the two "
            "endpoint values\") with an empty unresolved list, so no structured signal existed for those two. A trusted route answered a "
            "sub-question (the inputs) instead of falling back to drafted SQL, which the other four LB models did (Qwen: blocked; Luna, Sol, Terra: "
            "review_required and right).")},
    'heldout-group-our-fire-claims-by-the-distance-to-the-nea-66c568': {
        'label': 'Fire claims by distance band (0-5, 6-10, 11-15, >15 miles)',
        'class': 'route', 'confidence': 'high', 'alternative': None,
        'definition_files': [B_FIRE + ' (metrics fire_risk_records, fire_sample_avg_loss_ratio)'],
        'row_comparison': 'DQL: 20 rows, one per raw distance 1..20 miles (e.g. 1 mile: 83 records, 0.329). Gold: 4 band rows '
                          '(0-5 miles: 335, 0.344; 6-10: 164, 0.862; 11-15: 151, 0.825; >15: 170, 0.858).',
        'evidence': (
            "Layer B has no banding dimension for Nearest_Firestation_miles, and the structured intent has no bucketing construct (the readers' "
            "own notes say so, below), so every governed answer grouped by the raw distance (20 rows instead of 4). The per-mile counts and averages are correct "
            f"({B_FIRE}), so neither definition nor compilation is at fault. In 3 of the 6 answers the reader flagged the banding explicitly as "
            "unresolved (LB Sonnet 5: \"This system has no custom numeric-banding/bucketing capability\"; WB Sonnet 5.5: \"The project has no "
            "distance-band definition; results are grouped by each distance value instead of the requested bands\"; LB Sonnet 5.5 likewise), "
            "always material=false; WB Qwen recorded an unresolved clause on \"distance to the nearest fire station\" without saying why; LB Qwen "
            "and LB Sol carry only the not_modeled substitution note that all six share (\"the answer is broken down by Distance to nearest fire "
            "station (miles) in its place\"). "
            "The label stayed governed in all six. Drafted SQL with a CASE expression got it strictly right in 14 DQL answers, 2 of 7 P and 2 of 2 "
            "A answers, and 33 more (29 DQL, 4 P) were right except for the wording of the last band label (\"More than 15 miles\", "
            "\">15 miles\"; Task 2).")},
    'heldout-what-is-the-average-loss-ratio-on-fire-claims-by-9d6ca0': {
        'label': 'Average loss ratio and claim count by decade built',
        'class': 'route', 'confidence': 'high',
        'alternative': 'reading (secondary): the claim count was mapped to fire_sample_avg_loss_ratio aliased "claims" instead of fire_risk_records',
        'definition_files': [B_FIRE + ' (metric fire_sample_avg_loss_ratio)'],
        'row_comparison': 'DQL: 61 rows, average loss ratio per individual Year_Built (1960..2020), no count column. Gold: 7 decade rows with count and average.',
        'evidence': (
            "No decade dimension exists, so the semantic tier grouped by year_built (61 rows instead of 7). The reader flagged the decade "
            "bucketing as unresolved (material=false), and the host's own coverage check warned \"This answer carries nothing for 'the number of "
            "claims in each decade': no governed metric or dimension of this project is named for it\" - yet the answer was labelled governed. "
            "This is the clearest case of the trust label ignoring the system's own evidence. A secondary reading error is visible in the intent "
            "(the count requested was bound to fire_sample_avg_loss_ratio with alias \"claims\"), but the answer would be wrong even without it.")},
    'heldout-for-each-claim-show-the-claim-number-the-catastr-96ee5a': {
        'label': 'Per claim: total loss, total expense, expense as % of loss',
        'class': 'compilation', 'confidence': 'medium',
        'alternative': 'reading: the structured intent has no way to carry the "as a percentage" scale (derived {kind: ratio} only), '
                       'so the loss can also be placed at the reading-to-intent step; the prose reading and the column alias are right',
        'definition_files': [B_CLAIMS + ' (metrics incurred_losses, incurred_expenses)'],
        'row_comparison': 'DQL: 2 rows, incurred_losses 2,200 / 4,400 and incurred_expenses 2,400 / 4,600 (match gold), '
                          'expense_pct_of_loss = 1.0909 / 1.0455. Gold: 109.09 / 104.55.',
        'evidence': (
            f"incurred_losses and incurred_expenses ({B_CLAIMS}) are correct per claim, and every reading says \"as a percentage\" (aliases "
            "expense_pct_of_loss / expense_as_pct_of_loss). The host's derived-ratio step (\"expense_pct_of_loss = incurred_expenses / "
            "incurred_losses, computed from the executed metrics\") returns the fraction 1.09 under a pct name; the gold is 109.09. The intent "
            "schema's derived measure is {kind: ratio, numerator, denominator} with no scale, so the requested percentage is dropped between the "
            "reading and the computed column: the definition and the reading are right, the generated result is not. The WB Qwen answer also "
            "showed the four components instead of the two totals.")},
    'heldout-for-each-catastrophe-that-has-claims-show-the-nu-e01f4f': {
        'label': 'Per catastrophe: claims, loss paid, loss reserved, paid share as %',
        'class': 'compilation', 'confidence': 'medium',
        'alternative': 'reading (same mechanism as the per-claim expense percentage)',
        'definition_files': [B_CLAIMS + ' (metrics claims_with_amounts, losses_paid, loss_reserves, incurred_losses)'],
        'row_comparison': 'DQL: 1 row Fire, 2 claims, 3,500 paid, 3,100 reserved (match gold), paid_share_of_incurred_loss_pct = 0.5303. Gold: 53.03.',
        'evidence': (
            "Same mechanism: counts and sums are right, the derived column losses_paid / incurred_losses is shown as 0.53 under a _pct name "
            "against the gold 53.03. claims_with_amounts stands in for \"number of claims\"; B documents that every claim carries amounts, so this "
            f"is equivalent here ({B_CLAIMS}). The not_modeled note \"by catastrophe that has\" recorded in the intent is harmless (catastrophes "
            "without claims are excluded either way).")},
    'heldout-what-is-the-total-premium-we-have-charged-across-dbb59f': {
        'label': 'Total premium across all policies and coverage periods (W2)',
        'class': 'definition', 'confidence': 'high',
        'alternative': 'route (secondary): a result that is a single NULL was still labelled governed',
        'definition_files': ['work/insurance/projects/W2/semantic-layer/metrics/uncategorized/premium.yaml (imported metric premium)',
                             'data/insurance/semantic-layer-llm-benchmarking/models/omg_semantics/fire_claim.yaml (dbt Labs measure fire_claim.premium, no create_metric)'],
        'row_comparison': 'DQL: 1 row, premium = NULL. Gold: 98,000. fire_claim.Premium is NULL in all 820 rows (EVIDENCE_SQL fire_claim_premium).',
        'evidence': (
            "W2's governed metric premium is SUM(Premium) over fire_claim, the separate fire-risk sample, described as \"The total premium amount "
            "for the policy.\" It comes from dbt Labs' measure fire_claim.premium, which dbt Labs did not expose as a metric (no create_metric); "
            "`dql semantic import` promoted it to a governed metric, so it exists on W2 but not on L2/L3, where MetricFlow offers no premium "
            "metric and all 14 answers to this question were drafted SQL (13 right, 1 blocked). fire_claim.Premium is NULL in every row, so the "
            "governed answer is a single NULL; the gold is 98,000 (policy_amount joined to premium). The reading is the natural one for a metric "
            "with that name and description (Qwen's reader weighed total_policy_amount, which would also be wrong: 5,698,000 includes "
            "non-premium amounts). The defect is the governed definition as imported, not dbt Labs' authoring of a measure.")},
}

# Task 2 judgement: which kind of lenient-only answer each one is.
#   a = harmless: equivalent label (surrogate id / name / format for the same entity), numbers right
#   b = missing required identity: the question names the identifier or the name, the answer gives a surrogate or NULL
#   c = wrong business meaning: a column means something other than its name or the question, or the numbers
#       coincide only on this data
LENIENT_JUDGEMENT = {
    '66c568': ('a', 'band label differs only in case or wording ("More than 15 miles", ">15 miles")'),
    '89f9d1': ('a', '"for each claim": surrogate Claim_Identifier instead of Company_Claim_Number, same two claims'),
    '8217e1': ('a', '"for each claim": surrogate Claim_Identifier instead of Company_Claim_Number'),
    'e01f4f': ('a', 'Catastrophe_Identifier 4 instead of the name "Fire"'),
    '4dbd49': ('a', 'agent id plus concatenated name "Bob Agent" instead of First_Name / Last_Name'),
    'c1bb8e': ('b', 'asked "which claim number": gives surrogate Claim_Identifier 2, not claim number 12312702'),
    '5390de': ('b', 'policy holder\'s first and last name asked: name column is NULL, only surrogate party id'),
    '96ee5a': ('c', 'surrogate Claim_Identifier aliased as claim_number (claims 1 and 2 shown as claim numbers)'),
    ('2b6c02', 'L1', 'opus'): ('c', 'premium taken as policy amounts with Amount_Type_Code = \'year\' (coincides with the premium table on this data); column policy_number holds the internal Policy_Identifier 1'),
    ('2b6c02', 'L1', 'sonnet5'): ('c', 'column policy_number holds the internal Policy_Identifier 1, not policy number 31003000336'),
    ('2b6c02', 'LB', 'opus'): ('b', 'policy number asked: only internal policy and coverage ids'),
    ('a92504', 'P', 'sonnet55'): ('a', '"for each policy": Policy_Identifier instead of Policy_Number; names and result present'),
    ('a92504', 'L1', 'sonnet55'): ('a', '"for each policy": Policy_Identifier instead of Policy_Number; names and result present'),
    ('a92504', 'P', 'sol'): ('a', '"for each policy": Policy_Identifier instead of Policy_Number; names and result present'),
    ('a92504', 'L2', 'terra'): ('a', 'underwriter name concatenated ("Alice Writer") instead of two columns'),
    ('a92504', 'LB', 'sonnet5'): ('b', '"who was the underwriter (first and last name)": underwriter_name is NULL'),
    ('a92504', 'L2', 'qwen'): ('b', '"who was the underwriter (first and last name)": underwriter_name is NULL'),
    ('a92504', 'L1', 'qwen'): ('c', 'column assessment_result is the party-role code "UW", not the result "OK"; the query never reads assessment_result'),
}
TASK2_PICKS = {
    'a': [(('89f9d1', 'A', 'opus'), 'Harmless. The question says only "for each claim"; the agent returns the warehouse key Claim_Identifier (1, 2) where the reference shows Company_Claim_Number, both identify the same two claims and the ratios are identical.'),
          (('66c568', 'P', 'opus'), 'Harmless. The fourth band is spelled "More than 15 miles" against the reference "more than 15 miles"; counts and averages are identical. The capital M in "More than 15 miles" alone accounts for 32 of the 76 lenient-only answers on set 3.', [1, 2, 3])],
    'b': [(('5390de', 'L3', 'sonnet5'), 'Loses required identity. The question asks per policy holder by first and last name; the name column is NULL (Party_Name is empty for persons) and only the internal party id says whose 98,000 this is.'),
          (('a92504', 'L2', 'qwen'), 'Loses required identity. "Who was the underwriter (first and last name)" is half of the question; underwriter_name is NULL in both rows, so the answer gives the days and the result but not who.')],
    'c': [(('2b6c02', 'L1', 'opus'), 'Wrong meaning, right numbers. Premium is computed as policy amounts typed \'Year\' instead of amounts listed in premium (the six \'Year\' rows happen to be exactly the six premium rows here), and the column named policy_number holds the internal Policy_Identifier 1, not 31003000336.'),
          (('a92504', 'L1', 'qwen'), 'Wrong meaning, right numbers. The column labelled assessment_result is the underwriter\'s party-role code "UW", not the result "OK"; the query never reads assessment_result or underwriting_assessment, and its days match only because both assessments in this data are underwriting assessments with one UW party.')],
}

# Read-only checks on a copy of the L0 warehouse that the evidence above cites.
EVIDENCE_SQL = {
    'fire_claim_premium': 'SELECT COUNT(*) AS fire_claim_rows, COUNT(Premium) AS premium_non_null, SUM(Premium) AS premium_sum FROM main.fire_claim',
    'policy_amount_totals': 'SELECT SUM(pa.Policy_Amount) AS all_policy_amounts, SUM(CASE WHEN pr.Policy_Amount_Identifier IS NOT NULL THEN pa.Policy_Amount END) AS premium_only FROM main.policy_amount pa LEFT JOIN main.premium pr ON pr.Policy_Amount_Identifier = pa.Policy_Amount_Identifier',
    'corr_row_level': 'SELECT corr(Number_of_Firefighters, Loss_Ratio) AS corr_rows FROM main.fire_claim',
    'corr_over_group_means': 'SELECT corr(n, a) AS corr_group_means FROM (SELECT Number_of_Firefighters AS n, AVG(Loss_Ratio) AS a FROM main.fire_claim GROUP BY 1)',
    'year_type_vs_premium': 'SELECT pa.Amount_Type_Code, pr.Policy_Amount_Identifier IS NOT NULL AS listed_in_premium, COUNT(*) AS n FROM main.policy_amount pa LEFT JOIN main.premium pr ON pr.Policy_Amount_Identifier = pa.Policy_Amount_Identifier GROUP BY ALL ORDER BY ALL',
    'assessments': 'SELECT (SELECT COUNT(*) FROM main.assessment) AS assessments, (SELECT COUNT(*) FROM main.underwriting_assessment) AS underwriting_assessments, (SELECT string_agg(DISTINCT Party_Role_Code, \',\') FROM main.assesment_party_role) AS roles, (SELECT string_agg(DISTINCT Assessment_Result_Type_Code, \',\') FROM main.assessment_result) AS results',
    'fire_claim_dimensions': 'SELECT COUNT(DISTINCT Year_Built) AS distinct_year_built, COUNT(DISTINCT Nearest_Firestation_miles) AS distinct_distances, typeof(ANY_VALUE(Nearest_Firestation_miles)) AS distance_type FROM main.fire_claim',
}

# ============================================================================= Task 1: what the trust label ignored
# For every trusted answer: did DQL's own reading record a clause it could not cover
# (askIntentV1.unresolved, all marked material=false here), did the host warn that a
# requested item is not covered ("Requested coverage"), did the answer show only NULLs?
# Cross-tabulated with right/wrong, to size a gate that would demote such answers.
def signals(c, x):
    run, art = shown(c, x)
    intent = (art or {}).get('askIntentV1') or {}
    unresolved = intent.get('unresolved') or []
    substantive = [u for u in unresolved if u.get('kind') != 'not_modeled']
    _, rows = rows_of((art or {}).get('result'))
    all_null = bool(rows) and all(v is None for r in rows for v in (r if isinstance(r, list) else [r]))
    measures = intent.get('measures') or []
    pct_alias_unscaled = any(m.get('derived') and re.search(r'pct|percent', (m.get('alias') or ''), re.I)
                             for m in measures)
    return {'any_unresolved': bool(unresolved), 'substantive_unresolved': bool(substantive),
            'material_unresolved': any(u.get('material') for u in unresolved),
            'coverage_warning': bool(evals(run).get('Requested coverage')), 'all_null_result': all_null,
            'percent_ratio_unscaled': pct_alias_unscaled, 'found_artifact': art is not None}


gate = defaultdict(lambda: {'right': 0, 'wrong': 0})
gate_detail = []
for c, name, x in trusted_records:
    if c['set'] != 'heldout-3':
        continue
    s = signals(c, x)
    ok = correct(c, x)
    for k, v in s.items():
        if v:
            gate[k]['right' if ok else 'wrong'] += 1
    any_flag = s['substantive_unresolved'] or s['coverage_warning'] or s['all_null_result'] or s['percent_ratio_unscaled']
    gate['any_of_four_signals' if any_flag else 'none_of_four_signals']['right' if ok else 'wrong'] += 1
    gate_detail.append({'level': c['cond'], 'model': c['model'], 'question_id': name, 'correct': ok, **s})
gate = {k: dict(v) for k, v in gate.items()}

# ============================================================================= Task 2: lenient grade
regrade_sources = Counter()
grade_rows = []
for c in cells:
    if c['set'] != 'heldout-3':
        continue
    wrong_here = {n: x for n, x in c['q'].items() if not x.get('executionMatched') and answer_sql(x)}
    stored = {}
    if c['cond'] not in ('P', 'A'):
        for n, x in wrong_here.items():
            _, art = shown(c, x)
            acols_, arows_ = rows_of((art or {}).get('result'))
            if arows_ is not None:
                stored[n] = (acols_, arows_)
    need = [answer_sql(x) for n, x in wrong_here.items() if n not in stored]
    cache = rerun(need, c['layer']) if need else {}
    for name, x in c['q'].items():
        if x.get('executionMatched'):
            continue
        g = gold.get(name)
        if not g:
            continue
        expected = x.get('expected') or {}
        gold_rows = expected.get('goldRows') if expected.get('goldRows') is not None else g['gold']['rows']
        columns = g['gold'].get('columns') or []
        measures = G['measure_indexes'](g.get('goldSql'), columns, gold_rows)
        sql = answer_sql(x)
        executed, src, acols = None, 'none', None
        if name in stored:
            acols, arows = stored[name]
            executed, src = {'rows': arows}, 'run_store'
        elif sql:
            res = cache.get(sql)
            src = 'unrunnable'
            if res and 'error' not in res:
                executed, src, acols = {'rows': res['rows']}, f"rerun_{c['layer']}", res['columns']
        regrade_sources[f"{'P/A' if c['cond'] in ('P', 'A') else 'DQL'}:{src}"] += 1
        klass, sub = G['classify'](x, executed, gold_rows, measures)
        lenient = klass == 'missing_or_extra_columns' and bool(measures)
        if not lenient:
            continue
        grade_rows.append({
            'model': c['model'], 'model_label': c['label'], 'condition': c['cond'], 'run': c['run'],
            'question_id': name, 'question': g['question'], 'sub_kind': sub, 'rows_from': src,
            'trust_state': trust(x) if c['cond'] in LEVELS else None,
            'gold_columns': columns, 'gold_measure_columns': [columns[i] for i in measures],
            'gold_row_count': len(gold_rows), 'gold_rows_head': short_rows(gold_rows),
            'answer_columns': acols, 'answer_row_count': len(executed['rows']), 'answer_rows_head': short_rows(executed['rows']),
            'gold_rows_all': short_rows(gold_rows, 50), 'answer_rows_all': short_rows(executed['rows'], 50),
            'answer_sql': sql, 'gold_sql': g.get('goldSql'),
        })


# ============================================================================= evidence checks, then clean up
_ev = rerun(list(EVIDENCE_SQL.values()), 'L0')
evidence_results = {k: _ev.get(q) for k, q in EVIDENCE_SQL.items()}
shutil.rmtree(TMP, ignore_errors=True)

# ============================================================================= assemble Task 1
qids_wrong = {r['question_id'] for r in wrong_records}
missing = qids_wrong - set(JUDGEMENT)
extra = set(JUDGEMENT) - qids_wrong
if missing or extra:
    raise SystemExit(f'JUDGEMENT out of date: missing {sorted(missing)}, extra {sorted(extra)}')


def outcomes_for(qid):
    """How every DQL answer (all levels, all models) and every P / A answer to this question came out."""
    per_label = Counter()
    by_level = defaultdict(list)
    p_right = p_n = a_right = a_n = 0
    for c in cells:
        if c['set'] != 'heldout-3' or qid not in c['q']:
            continue
        x = c['q'][qid]
        ok = bool(x.get('executionMatched'))
        if c['cond'] == 'P':
            p_n += 1
            p_right += ok
        elif c['cond'] == 'A':
            a_n += 1
            a_right += ok
        else:
            per_label[f"{trust(x)}:{'right' if ok else 'wrong'}"] += 1
            by_level[c['cond']].append(f"{c['model']}={(trust(x) or '-')[:3]}/{'R' if ok else 'W'}")
    return {'dql_by_label': dict(sorted(per_label.items())), 'dql_by_level': {k: by_level[k] for k in LEVELS if k in by_level},
            'P_right': f'{p_right}/{p_n}', 'A_right': f'{a_right}/{a_n}'}


groups = []
for qid, j in JUDGEMENT.items():
    answers = [r for r in wrong_records if r['question_id'] == qid]
    distinct_sql = list(dict.fromkeys(r['dql_sql'] for r in answers))
    groups.append({
        'question_id': qid, 'question': answers[0]['question'], 'label': j['label'],
        'root_cause': j['class'], 'confidence': j['confidence'], 'alternative': j['alternative'],
        'answers': len(answers), 'by_level': dict(Counter(r['level'] for r in answers)),
        'models': [f"{r['model_label']} ({r['level']})" for r in answers],
        'trust_states': dict(Counter(r['trust_state'] for r in answers)),
        'route_kind': 'governed metric (semantic tier)' if all(r['engine_route'] == 'semantic_answer' for r in answers) else 'mixed',
        'certified_block': None,
        'governed_metrics': sorted({m for r in answers for m in r['governed_metrics']}),
        'semantic_engines': sorted({r['semantic_engine'] for r in answers if r['semantic_engine']}),
        'definition_files': j['definition_files'], 'row_comparison': j['row_comparison'], 'evidence': j['evidence'],
        'gold_sql': answers[0]['gold_sql'], 'dql_sql_distinct': distinct_sql,
        'other_answers_to_this_question': outcomes_for(qid),
    })
CLASS_ORDER = ['definition', 'reading', 'route', 'compilation', 'execution', 'reference', 'uncertain']
groups.sort(key=lambda g: (CLASS_ORDER.index(g['root_cause']), -g['answers'], g['question_id']))
root_cause_table = []
for cl in CLASS_ORDER:
    gs = [g for g in groups if g['root_cause'] == cl]
    recs = [r for r in wrong_records if JUDGEMENT[r['question_id']]['class'] == cl]
    root_cause_table.append({
        'class': cl, 'distinct_questions': len(gs), 'wrong_trusted_answers': len(recs),
        'by_level': {lv: sum(1 for r in recs if r['level'] == lv) for lv in ('L2', 'L3', 'LB', 'W2', 'WB')},
        'certified_block_answers': sum(1 for r in recs if r['trust_state'] == 'certified'),
        'governed_metric_answers': sum(1 for r in recs if r['trust_state'] == 'governed'),
    })
assert sum(r['wrong_trusted_answers'] for r in root_cause_table) == len(wrong_records)
for r in wrong_records:
    r['root_cause'] = JUDGEMENT[r['question_id']]['class']  # hand-written, see JUDGEMENT

model_level = {}
for m, label, *_ in MODELS:
    row = {}
    for lv in ('L2', 'L3', 'LB', 'W2', 'WB'):
        recs = [(c, n, x) for c, n, x in trusted_records if c['set'] == 'heldout-3' and c['cond'] == lv and c['model'] == m]
        row[lv] = {'trusted': len(recs), 'wrong': sum(1 for c, n, x in recs if not correct(c, x))}
    model_level[label] = row


# ============================================================================= assemble Task 2
def lenient_kind(r):
    q = r['question_id'][-6:]
    j = LENIENT_JUDGEMENT.get((q, r['condition'], r['model'])) or LENIENT_JUDGEMENT.get(q)
    if not j:
        raise SystemExit(f"LENIENT_JUDGEMENT has no entry for {q} {r['condition']} {r['model']}")
    return j


for r in grade_rows:
    r['kind'], r['kind_reason'] = lenient_kind(r)
lenient_counts = {}
for grp, test in (('DQL levels', lambda r: r['condition'] in LEVELS), ('P (one-shot SQL)', lambda r: r['condition'] == 'P'),
                  ('A (agent)', lambda r: r['condition'] == 'A'), ('all', lambda r: True)):
    rs = [r for r in grade_rows if test(r)]
    lenient_counts[grp] = {'lenient_only': len(rs), **{k: sum(1 for r in rs if r['kind'] == k) for k in 'abc'},
                           'trusted': sum(1 for r in rs if r['trust_state'] in TRUSTED)}
picks = {}
for kind, chosen in TASK2_PICKS.items():
    picks[kind] = []
    for (q, cond, model), why, *show in chosen:
        hit = [r for r in grade_rows if r['question_id'].endswith(q) and r['condition'] == cond and r['model'] == model]
        if len(hit) != 1 or hit[0]['kind'] != kind:
            raise SystemExit(f'TASK2_PICKS entry {q} {cond} {model} not found as kind {kind}')
        pick = {**hit[0], 'judgement': why}
        if show:  # display the rows that carry the difference (row indices, same for reference and answer)
            pick['gold_rows_head'] = [pick['gold_rows_all'][i] for i in show[0]]
            pick['answer_rows_head'] = [pick['answer_rows_all'][i] for i in show[0]]
            pick['rows_shown'] = f'rows {", ".join(str(i + 1) for i in show[0])}'
        picks[kind].append(pick)

# ============================================================================= JSON
COND_NAME = {'P': 'P (one-shot SQL)', 'A': 'A (agent)'}
out = {
    'generated_by': 'analysis/insurance-2026-09-29/taxonomy/taxonomy.py',
    'scope': 'insurance set 3 only: heldout-3 (40 answerable) and heldout-3-unanswerable (10)',
    'inclusion': {'invalid_reports_skipped': True, 'LB_WB_build': FIXED, 'trusted': list(TRUSTED), 'excluded_cells': excluded,
                  'cells_loaded': len(cells)},
    'grader': {'source': 'paper/stats_v2/stats_v2.py, section "re-grade (rows)" executed verbatim', 'sha256': GRADER_SHA},
    'level_semantics': LEVEL_SEMANTICS,
    'task1': {
        'counts': counts, 'model_by_level': model_level,
        'root_cause_table': root_cause_table, 'groups': groups,
        'wrong_trusted_answers': wrong_records,
        'trust_signals_on_trusted_answers': {
            'note': 'In-sample and post hoc (signals chosen after reading the failures); a sizing aid, not a validated rule. '
                    'percent_ratio_unscaled = a derived ratio whose alias says pct/percent (on set 3 the derived-ratio step never multiplies by 100).',
            'table': gate, 'per_answer': gate_detail},
        'judgement_is_hand_written': True,
    },
    'task2': {
        'definition': "lenient-only = strict-wrong and lenient-right under the paper's grader (missing_or_extra_columns with gold measure columns matched)",
        'row_sources': dict(regrade_sources), 'counts_by_kind': lenient_counts, 'picks': picks,
        'all_lenient_only_answers': grade_rows, 'judgement_is_hand_written': True,
    },
    'evidence_sql': {k: {'sql': EVIDENCE_SQL[k], 'result': evidence_results[k]} for k in EVIDENCE_SQL},
}
with open(os.path.join(HERE, 'taxonomy.json'), 'w') as f:
    json.dump(out, f, indent=1, default=str)


# ============================================================================= Markdown
def esc(v):
    return str(v).replace('|', '\\|').replace('\n', ' ')


def fmt_val(v):
    if isinstance(v, float):
        return f'{v:.6g}'
    if isinstance(v, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T00:00:00(\.000)?Z?', v):
        return v[:10]
    return 'NULL' if v is None else str(v)


def mini_table(columns, rows):
    cols = columns or [f'c{i + 1}' for i in range(len(rows[0]) if rows else 0)]
    lines = ['| ' + ' | '.join(esc(c) for c in cols) + ' |', '|' + '---|' * len(cols)]
    for r in rows:
        lines.append('| ' + ' | '.join(esc(fmt_val(v)) for v in r) + ' |')
    return '\n'.join(lines)


def def_file(d):
    path, _, rest = d.partition(' (')
    return f'`{path}`' + (f' ({rest}' if rest else '')


bs3 = counts['by_set']['heldout-3']
bsu = counts['by_set']['heldout-3-unanswerable']
lvl = counts['by_level']['heldout-3']
md = []
w = md.append
w('# Wrong trusted answers and lenient-grade examples — insurance set 3\n')
w('Generated by `taxonomy.py` in this folder (Python standard library; re-runnable; read-only on `work/` and `insurance/`; '
  'run stores and warehouses are copied to a temporary directory first; no model or network calls). '
  'Machine-readable version: `taxonomy.json`. Sealed sets are never opened: every path the script opens passes a guard.\n')
w('## Summary\n')
w(f"- **{bs3['wrong_trusted']} wrong trusted answers out of {bs3['trusted']}** on heldout-3, on **{bs3['distinct_questions_wrong']} distinct questions** "
  f"(LB {lvl['LB']['wrong_trusted']}/{lvl['LB']['trusted']}, WB {lvl['WB']['wrong_trusted']}/{lvl['WB']['trusted']}, W2 {lvl['W2']['wrong_trusted']}/{lvl['W2']['trusted']}, "
  f"L2+L3 0/{lvl['L2']['trusted'] + lvl['L3']['trusted']}); none on heldout-3-unanswerable, where no answer was trusted.")
w(f"- **All are governed-metric answers; no set-3 answer is certified at all** (the certified tier refused all {counts['certified_tier_outcomes'].get('LB:certified:refused', 0) + counts['certified_tier_outcomes'].get('WB:certified:refused', 0)} LB/WB consultations). Certified-block failures: 0 of 0.")
w('- **Root causes:** ' + '; '.join(f"{r['class']} {r['distinct_questions']} question{'s' if r['distinct_questions'] != 1 else ''} / {r['wrong_trusted_answers']} answers"
                                    for r in root_cause_table if r['wrong_trusted_answers']) +
  '. Route: a governed answer to part of the question (inputs of a CAGR, a breakdown instead of a correlation, raw values instead of requested bands or decades). '
  'Compilation: a requested percentage returned as an unscaled fraction (1.09 for 109%). Definition: a W2 metric `premium`, created by `dql semantic import` from a dbt Labs measure, sums an all-NULL column.')
told = sum(1 for d in gate_detail if not d['correct'] and (d['substantive_unresolved'] or d['coverage_warning']))
w(f"- **The trust label overrode DQL's own records.** For {told} of the {bs3['wrong_trusted']} wrong trusted answers DQL's reader wrote down the clause it could not cover "
  "(always marked not material) or the host warned that a requested item was missing, and the answer was still labelled governed. Adding two mechanical checks "
  f"(all-NULL result; a ratio named as a percentage but not multiplied by 100) flags {gate.get('any_of_four_signals', {}).get('wrong', 0)} of {bs3['wrong_trusted']}, against "
  f"{gate.get('any_of_four_signals', {}).get('right', 0)} of the {bs3['trusted'] - bs3['wrong_trusted']} right trusted answers (in-sample and post hoc: a sizing aid, not a validated rule).")
w(f"- **Lenient grade:** {lenient_counts['all']['lenient_only']} set-3 answers are strict-wrong but lenient-right; by hand, {lenient_counts['all']['a']} are harmless label differences, "
  f"{lenient_counts['all']['b']} lose a required identity (NULL name or surrogate key where the question names the identifier) and {lenient_counts['all']['c']} change the meaning of a column. None is trusted.\n")
w('## Method\n')
w('- **Cells.** Seven models (`fl-opus`, `fl-sonnet55`, `fl-sonnet` = Claude Sonnet 5, `fl-qwen`, `fl-luna`, `fl-sol`, `fl-terra`) × nine DQL levels × '
  '{heldout-3, heldout-3-unanswerable}; P = `<fl-run>/baseline-full/heldout-3`, A = `ag-opus|ag-sonnet55/agent-ddl/heldout-3`. '
  f'Reports with `invalid` set are skipped; LB and WB count only on DQL build `{FIXED}`. Excluded cells: {len(excluded)}.')
w('- **Trusted** = `answer.trustState` certified or governed. **Wrong** = `executionMatched` false (answerable) or `passed` false (unanswerable: answered instead of stopping).')
w("- **Per answer** the script extracts the route (engine route, tiers, semantic engine and governed metric names from the run's compilation receipt), "
  "the structured reading (`askIntentV1`: measures, group-by, `unresolved` clauses), the host's coverage warnings, DQL's SQL and the rows DQL showed "
  '(artifact in a copy of `agent-runs.sqlite`, matched on identical SQL, all attempts of the cell), and the gold SQL and rows.')
w('- **Root cause** is a hand-written judgement per distinct (question, root cause), in the `JUDGEMENT` dict of the script; the script refuses to run if a wrong trusted answer is not covered. '
  'Facts the evidence cites are re-checked by read-only SQL on a copy of the L0 warehouse (`EVIDENCE_SQL`, results in `taxonomy.json`).')
w(f"- **Lenient grade** reuses the paper's grader: the \"re-grade (rows)\" section of `paper/stats_v2/stats_v2.py` is executed verbatim (sha256 `{GRADER_SHA[:12]}…`). "
  "DQL rows come from the run store; P and A rows from re-running the recorded SQL on a copy of the L0 warehouse. "
  f"The {lenient_counts['all']['lenient_only']} lenient-only answers found here equal stats_v2's set-3 count (44 label substituted + 32 label case/format).\n")

w('## 1. Counts (set 3)\n')
w('| Set | DQL answers | Trusted | of which certified | of which governed | Wrong trusted | Distinct questions trusted | Distinct questions wrong |')
w('|---|---:|---:|---:|---:|---:|---:|---:|')
for sname, b in (('heldout-3', bs3), ('heldout-3-unanswerable', bsu)):
    w(f"| {sname} | {b['answers']} | {b['trusted']} | {b['trusted_certified']} | {b['trusted_governed']} | {b['wrong_trusted']} | {b['distinct_questions_trusted']} | {b['distinct_questions_wrong']} |")
w('')
w('**By level, heldout-3** (L0, L1, W0, W1 have no trusted answer and are omitted):\n')
w('| Level | What answers | Trusted | Wrong | Precision | Distinct q. trusted | Distinct q. wrong | Certified (wrong) | Governed (wrong) |')
w('|---|---|---:|---:|---:|---:|---:|---:|---:|')
for lv in ('L2', 'L3', 'LB', 'W2', 'WB'):
    b = lvl[lv]
    prec = f"{(b['trusted'] - b['wrong_trusted']) / b['trusted']:.1%}" if b['trusted'] else '—'
    w(f"| {lv} | {esc(LEVEL_SEMANTICS[lv])} | {b['trusted']} | {b['wrong_trusted']} | {prec} | {b['distinct_questions_trusted']} | {b['distinct_questions_wrong']} | "
      f"{b['trusted_certified']} ({b['wrong_certified']}) | {b['trusted_governed']} ({b['wrong_governed']}) |")
l23_q = len({n for c, n, x in trusted_records if c['set'] == 'heldout-3' and c['cond'] in ('L2', 'L3')})
w(f"| L2+L3 pooled | dbt Labs' metrics via MetricFlow | {lvl['L2']['trusted'] + lvl['L3']['trusted']} | {lvl['L2']['wrong_trusted'] + lvl['L3']['wrong_trusted']} | | {l23_q} | 0 | 0 (0) | {lvl['L2']['trusted'] + lvl['L3']['trusted']} (0) |")
w('')
w('**Wrong / trusted per model and level, heldout-3:**\n')
w('| Model | L2 | L3 | LB | W2 | WB |')
w('|---|---|---|---|---|---|')
for label, row in model_level.items():
    w(f"| {label} | " + ' | '.join(f"{row[lv]['wrong']}/{row[lv]['trusted']}" for lv in ('L2', 'L3', 'LB', 'W2', 'WB')) + ' |')
w('')
w('**Certified vs governed.** Not one set-3 answer, at any level or model, carries trustState `certified`: all '
  f"{bs3['trusted']} trusted answers are `governed` answers from the semantic tier (engine route `semantic_answer`). "
  "The certified tier was `skipped` where no blocks exist (L2, L3, W2) and `refused` every time it was consulted on LB and WB "
  f"({counts['certified_tier_outcomes'].get('LB:certified:refused', 0)} LB and {counts['certified_tier_outcomes'].get('WB:certified:refused', 0)} WB answers). "
  f"So **all {len(wrong_records)} wrong trusted answers are governed-metric failures; certified-block failures: 0 of 0**. "
  '"Zero wrong certified answers" on set 3 is vacuous and must not be reported as evidence that certified blocks are safe.\n')
nstop = counts['unanswerable_not_stopped']
stop_text = ', '.join(f"{k.split(':')[0]} {v}" for k, v in sorted(nstop.items()))
w(f"**Unanswerable set.** 0 trusted answers among {bsu['answers']} DQL answers; the {sum(nstop.values())} answers that did not stop were all "
  f"`review_required` ({stop_text}). No wrong trusted answer comes from heldout-3-unanswerable.\n")

w('## 2. Root causes\n')
w('| Root cause | Distinct questions | Wrong trusted answers | L2 | L3 | LB | W2 | WB | Certified-block | Governed-metric |')
w('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for r in root_cause_table:
    b = r['by_level']
    w(f"| {r['class']} | {r['distinct_questions']} | {r['wrong_trusted_answers']} | {b['L2']} | {b['L3']} | {b['LB']} | {b['W2']} | {b['WB']} | {r['certified_block_answers']} | {r['governed_metric_answers']} |")
w(f"| **total** | **{len(groups)}** | **{len(wrong_records)}** | 0 | 0 | {lvl['LB']['wrong_trusted']} | {lvl['W2']['wrong_trusted']} | {lvl['WB']['wrong_trusted']} | **0** | **{len(wrong_records)}** |")
w('')
w('Classes: *definition* — the governed metric itself computes the wrong thing; *reading* — DQL read the question wrong while the definition was fine; '
  '*route* — a trusted route answered although it did not cover the whole question; *compilation* — definition and reading right, generated result wrong; '
  '*execution* — right SQL, wrong rows at run time; *reference* — gold wrong or question ambiguous. Certified-block failures: none (no certified answers exist on set 3).\n')
w('| Question | Root cause (confidence) | Wrong trusted answers (model, level) | Governed metrics used (engine) | Row comparison |')
w('|---|---|---|---|---|')
for g in groups:
    w(f"| {esc(g['label'])} (`…{g['question_id'][-6:]}`) | **{g['root_cause']}** ({g['confidence']}) | {esc(', '.join(g['models']))} | "
      f"{esc(', '.join(g['governed_metrics']))} ({esc(', '.join(g['semantic_engines']))}) | {esc(g['row_comparison'])} |")
w('')

w('### What the trust label ignored\n')
w('In all but the W2 case the governed metrics computed correctly what they define; the failure is that a partial or rescaled result kept the `governed` label. '
  f"In most cases DQL had already written down why the answer was incomplete. Signals present on the {bs3['trusted']} trusted answers "
  '(in-sample and chosen after reading the failures, so a sizing aid, not a validated rule):\n')
w('| Signal on a trusted answer | Right | Wrong |')
w('|---|---:|---:|')
names = {'substantive_unresolved': '`askIntentV1.unresolved` holds a clause other than a `not_modeled` substitution note (every one was `material: false`)',
         'any_unresolved': 'any `unresolved` clause, including `not_modeled` notes',
         'coverage_warning': 'host warning "Requested coverage: this answer carries nothing for …"',
         'all_null_result': 'every value shown is NULL',
         'percent_ratio_unscaled': 'a derived ratio whose alias says pct/percent (on set 3 the derived-ratio step never multiplies by 100)',
         'any_of_four_signals': 'any of: substantive unresolved clause, coverage warning, all-NULL result, pct-named ratio',
         'none_of_four_signals': 'none of the four'}
for k in ('substantive_unresolved', 'any_unresolved', 'coverage_warning', 'all_null_result', 'percent_ratio_unscaled', 'any_of_four_signals', 'none_of_four_signals'):
    v = gate.get(k, {})
    w(f"| {names[k]} | {v.get('right', 0)} | {v.get('wrong', 0)} |")
w('')
no_signal = [d for d in gate_detail if not d['correct'] and not (d['substantive_unresolved'] or d['coverage_warning'] or d['all_null_result'] or d['percent_ratio_unscaled'])]
right_flag = [d for d in gate_detail if d['correct'] and d['substantive_unresolved']]
w('Wrong answers with none of the four signals: ' + '; '.join(f"{LABEL[d['model']]} {d['level']} `…{d['question_id'][-6:]}`" for d in no_signal) +
  ' (the two CAGR answers say "CAGR itself is not a governed metric" in prose only; the two band answers carry only a `not_modeled` note). '
  'Right answers with a substantive unresolved clause: ' + ('; '.join(f"{LABEL[d['model']]} {d['level']} `…{d['question_id'][-6:]}`" for d in right_flag) or 'none') + '.\n')

w('### Evidence per group\n')
for g in groups:
    o = g['other_answers_to_this_question']
    w(f"#### {g['label']} — {g['root_cause']} ({g['confidence']} confidence)\n")
    w(f"*Question* (`{g['question_id']}`): {g['question']}\n")
    w(f"*Wrong trusted answers*: {g['answers']} — {', '.join(g['models'])}. *Definition files*: {'; '.join(def_file(d) for d in g['definition_files'])}.\n")
    w(g['evidence'] + '\n')
    if g['alternative']:
        w(f"*Alternative or secondary cause*: {g['alternative']}.\n")
    w(f"*Rows*: {g['row_comparison']}\n")
    w(f"*All answers to this question*: DQL levels (63) — {', '.join(f'{k} {v}' for k, v in o['dql_by_label'].items())}; P right {o['P_right']}; A right {o['A_right']}.\n")
    w('<details><summary>Gold SQL and DQL SQL (' + str(len(g['dql_sql_distinct'])) + ' distinct)</summary>\n')
    w('Gold:\n\n```sql\n' + (g['gold_sql'] or '') + '\n```\n')
    for sql in g['dql_sql_distinct']:
        who = ', '.join(f"{r['model_label']} {r['level']}" for r in wrong_records if r['question_id'] == g['question_id'] and r['dql_sql'] == sql)
        w(f'DQL ({who}):\n\n```sql\n{sql}\n```\n')
    w('</details>\n')

w('## 3. Lenient-grade examples (set 3)\n')
w("Lenient-only = strict-wrong but lenient-right under the paper's grader. Every one was classified by hand (`LENIENT_JUDGEMENT`): "
  '**a** harmless equivalent label; **b** missing required identity (the question names the identifier or the person, the answer gives a surrogate key or NULL); '
  '**c** wrong business meaning (a column means something other than its name or the question, or the numbers coincide only on this data).\n')
w('| Condition | Lenient-only | a harmless | b missing identity | c wrong meaning | of which trusted |')
w('|---|---:|---:|---:|---:|---:|')
for grp, v in lenient_counts.items():
    w(f"| {grp} | {v['lenient_only']} | {v['a']} | {v['b']} | {v['c']} | {v['trusted']} |")
w('')
w("No set-3 lenient-only answer drops a grouping or identity column outright (sub-kind `label_column_missing` does not occur); identity is lost through NULL names or surrogate keys. "
  f"None of the {lenient_counts['all']['lenient_only']} is a trusted answer, so the lenient grade does not change trusted precision on set 3, and none of the {len(wrong_records)} wrong trusted answers is lenient-right.\n")
TITLES = {'a': '(a) Harmless: equivalent label', 'b': '(b) Missing required identity', 'c': '(c) Wrong business meaning despite matching numbers'}
for kind in 'abc':
    w(f'### {TITLES[kind]}\n')
    chosen = {(p['question_id'], p['condition'], p['model']) for p in picks[kind]}
    for i, r in enumerate(picks[kind], 1):
        cond = COND_NAME.get(r['condition'], f"DQL {r['condition']}, {r['trust_state']}")
        w(f"**{kind}{i}. {r['model_label']} — {cond}** (`…{r['question_id'][-6:]}`; rows from {r['rows_from'].replace('_', ' ')})\n")
        w(f"*Question*: {r['question']}\n")
        shown_note = f"; {r['rows_shown']} shown" if r.get('rows_shown') else ''
        w(f"Reference ({r['gold_row_count']} row{'s' if r['gold_row_count'] != 1 else ''}{shown_note}):\n")
        w(mini_table(r['gold_columns'], r['gold_rows_head']) + '\n')
        w(f"Answer ({r['answer_row_count']} row{'s' if r['answer_row_count'] != 1 else ''}{shown_note}):\n")
        w(mini_table(r['answer_columns'], r['answer_rows_head']) + '\n')
        w(f"*Judgement*: {r['judgement']}\n")
    others = [r for r in grade_rows if r['kind'] == kind and (r['question_id'], r['condition'], r['model']) not in chosen]
    if kind == 'a':
        w(f"Other answers of this kind: {len(others)} (listed in `taxonomy.json`, task2.all_lenient_only_answers).\n")
    elif others:
        w('Other answers of this kind: ' + '; '.join(f"{LABEL[r['model']]} {r['condition']} `…{r['question_id'][-6:]}` — {r['kind_reason']}" for r in others) + '.\n')

w('## 4. Notes and data problems\n')
w('- The pooled numbers in the task brief (LB 50 trusted / 15 wrong; WB 24 / 4) predate the GPT runs. Current set-3 counts: '
  f"L2+L3 {lvl['L2']['trusted'] + lvl['L3']['trusted']} / 0 ({l23_q} questions), "
  f"LB {lvl['LB']['trusted']} / {lvl['LB']['wrong_trusted']} ({lvl['LB']['distinct_questions_wrong']} questions with a wrong one), "
  f"WB {lvl['WB']['trusted']} / {lvl['WB']['wrong_trusted']} ({lvl['WB']['distinct_questions_wrong']}), "
  f"W2 {lvl['W2']['trusted']} / {lvl['W2']['wrong_trusted']} ({lvl['W2']['distinct_questions_wrong']}) — identical to stats_v2 section 2a.")
w('- `results[].route` in the run reports reads `certified` for every governed semantic answer (trace: "Persisted engine route semantic_answer evaluated as certified"). '
  f"Counting certified answers from that field would report {bs3['trusted']} certified answers where there are none; use `answer.trustState` or the engine route.")
w('- The GPT-6 Luna W2 answer to the total-premium question is recorded in the resumed store `fl-luna/W2/heldout-3.attempt-1`, not in the final set directory; the script reads all attempts of a cell.')
w('- Derived ratios are stored as decimal strings (e.g. `"1.090909090909090909"`); the grader normalises numeric strings, so grading is unaffected.')
w(f"- Row sources for the re-grade (strict-wrong answers only): {', '.join(f'{k} {v}' for k, v in sorted(regrade_sources.items()))}. `unrunnable` = the recorded SQL fails on the warehouse copy; DQL `none` = no SQL (stopped or blocked).")
w(f"- Each failure repeats on every model that took the governed route for that question, so {len(wrong_records)} answers collapse to {len(groups)} questions; "
  'answer counts overstate the independent evidence (stats_v2 section 2 on pseudo-replication).')
with open(os.path.join(HERE, 'taxonomy.md'), 'w') as f:
    f.write('\n'.join(md) + '\n')

summary_rc = ', '.join(f"{r['class']} {r['distinct_questions']}q/{r['wrong_trusted_answers']}a" for r in root_cause_table if r['wrong_trusted_answers'])
print(f"trusted {bs3['trusted']} (certified {bs3['trusted_certified']}), wrong {bs3['wrong_trusted']} on {bs3['distinct_questions_wrong']} questions; "
      f"root causes: {summary_rc}; lenient-only {lenient_counts['all']['lenient_only']} "
      f"(a {lenient_counts['all']['a']}, b {lenient_counts['all']['b']}, c {lenient_counts['all']['c']})")
if DUMP:
    print(json.dumps(evidence_results, indent=1))

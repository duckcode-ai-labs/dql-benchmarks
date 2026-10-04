# Blind review sheet for the set-5 primary comparison (post-hoc, owner decision of 3 October 2026): every
# answerable question where exactly one of W2 and A-model (Claude Sonnet 5.5, pre-registered runs) was
# strict-correct. Each row shows the question, the reference result and the two answers' results as
# "Answer 1" and "Answer 2" in a seeded random order; which one is DQL's is written only to a separate key
# file, to be opened after the verdicts are in. Prints counts only.
#   .venv/bin/python insurance/audit/make_discordant_sheet.py
#   -> work/insurance/audit/set5-discordant-review.csv, set5-discordant-key.json
import csv, json, os, random, shutil, sqlite3, tempfile

import duckdb

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WORK = os.path.join(REPO, 'work', 'insurance')
RUNS, OUT = os.path.join(WORK, 'runs'), os.path.join(WORK, 'audit')
W2_DIR = os.path.join(RUNS, 'fl5-sonnet55', 'W2', 'heldout-5')
AM_DIR = os.path.join(RUNS, 'ag5m-sonnet55', 'agent-modeling', 'heldout-5')
SEED, MAX_ROWS = 20261003, 10
TMP = tempfile.mkdtemp(prefix='discordant_')


def report(d):
    return {x['name'].strip(): x for x in json.load(open(os.path.join(d, 'report.json')))['results']}


def answer_sql(x):
    return (x.get('answer') or {}).get('sql') or x.get('finalSql') or ''


def store_rows(level_dir, set_name):
    """Rows DQL showed for each SQL text, from copies of the run store(s) of this set (all attempts)."""
    out = {}
    names = sorted((n for n in os.listdir(level_dir) if n == set_name or n.startswith(set_name + '.')), key=lambda n: (n != set_name, n))
    for n in names:
        src = os.path.join(level_dir, n, 'project', '.dql', 'local', 'agent-runs.sqlite')
        if not os.path.exists(src):
            continue
        dst = os.path.join(TMP, n + '.sqlite')
        shutil.copyfile(src, dst)
        if os.path.exists(src + '-wal'):
            shutil.copyfile(src + '-wal', dst + '-wal')
        con = sqlite3.connect(dst)
        for (payload,) in con.execute('select payload_json from agent_run_artifacts'):
            try:
                a = json.loads(payload)
            except Exception:
                continue
            if not isinstance(a, dict) or not a.get('sql') or not isinstance(a.get('result'), dict):
                continue
            res = a['result']
            cols = res.get('columns') or []
            cols = [c if isinstance(c, str) else (c.get('name') if isinstance(c, dict) else str(c)) for c in cols]
            rows = []
            for r in res.get('rows') or []:
                rows.append([r.get(k) for k in (cols or list(r.keys()))] if isinstance(r, dict) else list(r))
                if not cols and isinstance(r, dict):
                    cols = list(r.keys())
            out.setdefault(a['sql'], (cols, rows))
        con.close()
    return out


def warehouse(layer):
    d = os.path.join(TMP, 'wh-' + layer)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, 'acme_insurance.duckdb')  # the views name their catalog after the file
    if not os.path.exists(dst):
        shutil.copyfile(os.path.join(WORK, 'projects', layer, 'acme_insurance.duckdb'), dst)
    return duckdb.connect(dst, read_only=True)


def run_sql(con, sql):
    try:
        cur = con.execute(sql)
        return [d[0] for d in cur.description], [list(r) for r in cur.fetchall()]
    except Exception as e:
        return ['(the SQL failed when re-run)'], [[type(e).__name__]]


def fmt(cols, rows):
    if cols is None:
        return '(no answer: the system stopped without SQL)'
    v = lambda x: (f'{x:.6g}' if isinstance(x, float) else str(x))
    shown = rows[:MAX_ROWS]
    more = len(rows) - len(shown)
    return ' | '.join(map(str, cols)) + '\n' + '\n'.join(' | '.join(v(x) for x in r) for r in shown) + (f'\n... {more} more rows' if more > 0 else '') + f'\n({len(rows)} rows)'


w2, am = report(W2_DIR), report(AM_DIR)
gold = {c['id'].strip(): c for c in json.load(open(os.path.join(WORK, 'gold', 'heldout-5.json')))['cases']}
disc = sorted(q for q in w2 if q in am and bool(w2[q].get('executionMatched')) != bool(am[q].get('executionMatched')))
store = store_rows(os.path.dirname(W2_DIR), 'heldout-5')
con_w2 = warehouse('W2')
rng = random.Random(SEED)
order = disc[:]
rng.shuffle(order)
rows_out, key, src = [], {}, {'store': 0, 'rerun': 0, 'none': 0}
for i, q in enumerate(order, 1):
    g = gold[q]
    ref = fmt(g['gold'].get('columns') or [], g['gold'].get('rows') or [])
    a_sql = {'W2': answer_sql(w2[q]), 'A-model': answer_sql(am[q])}
    res = {}
    for name, sql in a_sql.items():
        if not sql:
            res[name] = fmt(None, None); src['none'] += 1
        elif name == 'W2' and sql in store:
            res[name] = fmt(*store[sql]); src['store'] += 1
        else:
            res[name] = fmt(*run_sql(con_w2, sql)); src['rerun'] += 1
    first = rng.choice(['W2', 'A-model'])
    second = 'A-model' if first == 'W2' else 'W2'
    key[str(i)] = {'answer_1': first, 'answer_2': second, 'strict_correct': 'W2' if w2[q].get('executionMatched') else 'A-model'}
    rows_out.append([i, g['question'], ref, res[first], res[second], '', '', '', '', '', '', a_sql[first], a_sql[second], g['goldSql']])
con_w2.close()
shutil.rmtree(TMP, ignore_errors=True)

with open(os.path.join(OUT, 'set5-discordant-review.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['item', 'question', 'reference result', 'Answer 1 result', 'Answer 2 result',
                'ANSWER 1 (acceptable / not acceptable / unsure)', 'ANSWER 2 (acceptable / not acceptable / unsure)',
                'better answer (1 / 2 / same)', 'reason', 'reviewer', 'date',
                'Answer 1 SQL (optional; its style may reveal the system)', 'Answer 2 SQL (optional)', 'reference SQL'])
    w.writerows(rows_out)
json.dump({'note': 'Open only after the verdicts are recorded.', 'seed': SEED, 'items': key},
          open(os.path.join(OUT, 'set5-discordant-key.json'), 'w'), indent=1)
print(f"wrote {len(rows_out)} items (W2 alone strict-correct: {sum(1 for k in key.values() if k['strict_correct'] == 'W2')}, "
      f"A-model alone: {sum(1 for k in key.values() if k['strict_correct'] == 'A-model')}); result sources {src}")

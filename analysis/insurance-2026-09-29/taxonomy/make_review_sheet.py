# Review sheet for a person to confirm or correct the AI-made classifications in paper Section 6.8
# (public set 3 only). Rows: the 7 root-cause groups of wrong trusted answers (one representative answer
# each), every lenient-only answer the AI judged NOT harmless, and a seeded random sample of 10 it
# judged harmless.   python3 analysis/insurance-2026-09-29/taxonomy/make_review_sheet.py
import csv, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, 'taxonomy.json')))
fmt = lambda cols, rows: (' | '.join(map(str, cols or [])) + '\n' + '\n'.join(' | '.join(map(str, r)) for r in (rows or [])[:5])).strip()
KIND = {'a': 'harmless (equivalent label)', 'b': 'identity lost', 'c': 'different meaning despite matching numbers'}
CLASS = {'route': 'route: a governed answer covered only part of the question', 'compilation': 'compilation: "as a percentage" returned as a fraction',
         'definition': 'definition: the metric itself computes the wrong thing', 'reading': 'reading', 'execution': 'execution', 'reference': 'reference error'}

rows = []
wrong = {}
for w in d['task1']['wrong_trusted_answers']:
    wrong.setdefault(w['question_id'], w)
for g in d['task1']['groups']:
    w = wrong.get(g['question_id'], {})
    rows.append(['6.8 root cause', g['question'], CLASS.get(g['root_cause'], g['root_cause']) + f" (AI confidence {g.get('confidence')})",
                 f"{g.get('answers')} wrong trusted answers; levels {', '.join(f'{k} {v}' for k, v in (g.get('by_level') or {}).items() if v)}. {g.get('evidence', '')}"
                 + (f" Alternative: {g['alternative']}" if g.get('alternative') else ''),
                 g.get('gold_sql', ''), (g.get('dql_sql_distinct') or [''])[0], fmt(w.get('gold_columns'), w.get('gold_rows_head')),
                 fmt(w.get('dql_columns'), w.get('dql_rows_head'))])
lo = d['task2']['all_lenient_only_answers']
harmless = [x for x in lo if x['kind'] == 'a']
pick = [x for x in lo if x['kind'] != 'a'] + random.Random(20261002).sample(harmless, min(10, len(harmless)))
for x in pick:
    rows.append([f"6.8 lenient-only ({x['model_label']}, {x['condition']})", x['question'], KIND[x['kind']], x.get('kind_reason', ''),
                 x.get('gold_sql', ''), x.get('answer_sql', ''), fmt(x.get('gold_columns'), x.get('gold_rows_head')), fmt(x.get('answer_columns'), x.get('answer_rows_head'))])

out = os.path.join(HERE, 'taxonomy-review-sheet.csv')
with open(out, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['item', 'part', 'question (set 3, public)', 'AI classification', 'AI evidence', 'reference SQL', 'answer SQL', 'reference rows (first 5)', 'answer rows (first 5)',
                'VERDICT (agree / disagree / unsure)', 'your classification if different', 'notes', 'reviewer', 'date'])
    for i, r in enumerate(rows, 1):
        w.writerow([i] + r + ['', '', '', '', ''])
print(f'wrote {out}: {len(rows)} rows ({len(d["task1"]["groups"])} root-cause groups, {len(pick)} lenient-only answers)')

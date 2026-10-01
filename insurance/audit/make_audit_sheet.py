# Build a human audit sheet for a sealed set without printing any question: a random sample of
# answerable items (stratified by complexity quadrant, fixed seed) and unanswerable items, with the
# reference SQL and the first rows of its result, and empty columns for the reviewer's verdict.
#   python3 insurance/audit/make_audit_sheet.py                      # set 4: 25 per quadrant + 20, seed 20260930
#   python3 insurance/audit/make_audit_sheet.py --set 5 --answerable 50 --unanswerable 13 --seed 20261001
import argparse, csv, json, os, random

ap = argparse.ArgumentParser()
ap.add_argument('--set', type=int, default=4)
ap.add_argument('--answerable', type=int, default=100, help='total answerable items, split evenly over quadrants')
ap.add_argument('--unanswerable', type=int, default=20)
ap.add_argument('--seed', type=int, default=20260930)
a = ap.parse_args()

g = json.load(open(f'work/insurance/gold/heldout-{a.set}.json'))
q = json.load(open(f'insurance/heldout/questions-{a.set}.json'))
rng = random.Random(a.seed)
by_quad = {}
for c in g['cases']:
    by_quad.setdefault(c['quadrant'], []).append(c)
quads = sorted(by_quad)
# Even split; any remainder goes to the first quadrants in a seeded order (50 over 4 -> 13, 13, 12, 12).
base, extra = divmod(a.answerable, len(quads))
bonus = set(rng.sample(quads, extra))
sample = [c for quad in quads for c in rng.sample(by_quad[quad], min(base + (quad in bonus), len(by_quad[quad])))]
rng.shuffle(sample)

def preview(gold):
    cols = gold.get('columns') or []
    rows = (gold.get('rows') or [])[:5]
    more = len(gold.get('rows') or []) - len(rows)
    return ' | '.join(map(str, cols)) + '\n' + '\n'.join(' | '.join(map(str, r)) for r in rows) + (f'\n… {more} more rows' if more > 0 else '')

os.makedirs('work/insurance/audit', exist_ok=True)
out = f'work/insurance/audit/set{a.set}-audit-sample.csv'
with open(out, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['item', 'kind', 'quadrant', 'question', 'reference_sql', 'reference_result_first_rows',
                'VERDICT (correct / wrong / ambiguous)', 'what is wrong or ambiguous', 'corrected_sql (optional)', 'reviewer', 'date'])
    for i, c in enumerate(sample, 1):
        w.writerow([i, 'answerable', c['quadrant'], c['question'], c['goldSql'], preview(c.get('gold') or {}), '', '', '', '', ''])
    unans = rng.sample(q['unanswerable'], min(a.unanswerable, len(q['unanswerable'])))
    for j, u in enumerate(unans, len(sample) + 1):
        w.writerow([j, 'unanswerable', '', u['question'], '(none: the data should not answer this)', 'why: ' + u['why'], '', '', '', '', ''])
print(f'wrote {out}: {len(sample)} answerable + {len(unans)} unanswerable rows (seed {a.seed})')

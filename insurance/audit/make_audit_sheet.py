# Build the human audit sheet for sealed set 4 without printing any question: a random sample of
# 100 answerable items (25 per complexity quadrant, fixed seed) and 20 unanswerable items, with the
# reference SQL and the first rows of its result, and empty columns for the reviewer's verdict.
import csv, json, random
g = json.load(open('work/insurance/gold/heldout-4.json'))
q = json.load(open('insurance/heldout/questions-4.json'))
rng = random.Random(20260930)
by_quad = {}
for c in g['cases']:
    by_quad.setdefault(c['quadrant'], []).append(c)
sample = [c for quad in sorted(by_quad) for c in rng.sample(by_quad[quad], min(25, len(by_quad[quad])))]
rng.shuffle(sample)
def preview(gold):
    cols = gold.get('columns') or []
    rows = (gold.get('rows') or [])[:5]
    more = len(gold.get('rows') or []) - len(rows)
    return ' | '.join(map(str, cols)) + '\n' + '\n'.join(' | '.join(map(str, r)) for r in rows) + (f'\n… {more} more rows' if more > 0 else '')
with open('work/insurance/audit/set4-audit-sample.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['item', 'kind', 'quadrant', 'question', 'reference_sql', 'reference_result_first_rows',
                'VERDICT (correct / wrong / ambiguous)', 'what is wrong or ambiguous', 'corrected_sql (optional)', 'reviewer', 'date'])
    for i, c in enumerate(sample, 1):
        w.writerow([i, 'answerable', c['quadrant'], c['question'], c['goldSql'], preview(c.get('gold') or {}), '', '', '', '', ''])
    for j, u in enumerate(rng.sample(q['unanswerable'], min(20, len(q['unanswerable']))), len(sample) + 1):
        w.writerow([j, 'unanswerable', '', u['question'], '(none: the data should not answer this)', 'why: ' + u['why'], '', '', '', '', ''])
print('wrote', len(sample), 'answerable +', min(20, len(q['unanswerable'])), 'unanswerable rows')

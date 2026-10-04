# Where added context lost answers (exploratory): for sets 4 and 5 (Claude Sonnet 5.5), the questions W2
# answered correctly and another DQL level did not, and the reverse, split by how that level answered
# (a trusted label, drafted SQL for review, or no answer). Strict grading. Aggregates only.
#   python3 analysis/insurance-2026-09-29/routes/routes.py  -> routes.json / routes.md
import json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, '..', '..', '..', 'work', 'insurance', 'runs')
SETS = {'heldout-4': 'fl4-sonnet55', 'heldout-5': 'fl5-sonnet55'}
OTHERS = ['L2', 'L3', 'WB']


def report(run, level, s):
    return {x['name'].strip(): x for x in json.load(open(os.path.join(RUNS, run, level, s, 'report.json')))['results']}


def route(x):
    a = x.get('answer') or {}
    if not a.get('sql'):
        return 'no_answer'
    return 'trusted' if a.get('trustState') in ('certified', 'governed') else 'drafted'


out = {}
for s, run in SETS.items():
    w2 = report(run, 'W2', s)
    entry = {'W2_routes': dict(Counter(route(x) for x in w2.values())), 'levels': {}}
    for L in OTHERS:
        o = report(run, L, s)
        lost = [q for q in w2 if w2[q].get('executionMatched') and not o[q].get('executionMatched')]
        won = [q for q in w2 if o[q].get('executionMatched') and not w2[q].get('executionMatched')]
        entry['levels'][L] = {'routes': dict(Counter(route(x) for x in o.values())),
                              'W2_right_level_wrong': len(lost), 'lost_by_route': dict(Counter(route(o[q]) for q in lost)),
                              'level_right_W2_wrong': len(won), 'won_by_route': dict(Counter(route(o[q]) for q in won))}
    out[s] = entry
json.dump(out, open(os.path.join(HERE, 'routes.json'), 'w'), indent=1)
L = ['# Where added context lost answers (aggregates only)', '',
     '| Set | Level | W2 right, level wrong | ...level trusted | ...level drafted | ...level no answer | Level right, W2 wrong |', '|---|---|---:|---:|---:|---:|---:|']
for s, e in out.items():
    for lv, v in e['levels'].items():
        b = v['lost_by_route']
        L.append(f"| {s} | {lv} | {v['W2_right_level_wrong']} | {b.get('trusted', 0)} | {b.get('drafted', 0)} | {b.get('no_answer', 0)} | {v['level_right_W2_wrong']} |")
open(os.path.join(HERE, 'routes.md'), 'w').write('\n'.join(L) + '\n')
print('wrote routes.json and routes.md')

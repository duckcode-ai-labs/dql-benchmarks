# Results of the person's audit of the reference answers (sets 4 and 5), from the completed audit sheets
# work/insurance/audit/set{4,5}-audit-sample.csv (kept out of git until each set is released, because they
# hold the questions). Writes counts and Wilson 95% intervals only: no item text.
#   python3 analysis/insurance-2026-09-29/audit/audit_results.py  -> audit_results.json / .md
import csv, json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
AUDIT = os.path.join(REPO, 'work', 'insurance', 'audit')
SAMPLES = {'4': {'seed': 20260930, 'answerable': 100, 'unanswerable': 20, 'set_size': (200, 50)},
           '5': {'seed': 20261001, 'answerable': 50, 'unanswerable': 13, 'set_size': (200, 50)}}
VERDICTS = ('correct', 'wrong', 'ambiguous')
# AI models also looked over both samples as a second check after the author's own reading; the author
# re-examined every item where one of them disagreed and kept the verdict. Counted on 3 October 2026 from
# the reviewers' files (kept with the sealed material, outside the repository).
SECOND_LOOK = {'models': ['Claude Fable 5.1', 'GPT-6.1 Sol at low reasoning effort'],
               'items_with_disagreement': {'4': 1, '5': 1}, 'verdicts_changed': 0}


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


out = {'second_look': SECOND_LOOK, 'sets': {}}
for s, spec in SAMPLES.items():
    rows = list(csv.reader(open(os.path.join(AUDIT, f'set{s}-audit-sample.csv'), encoding='utf-8-sig')))
    head, rows = rows[0], rows[1:]
    assert head[6].startswith('VERDICT'), head
    entry = {'seed': spec['seed'], 'set_size': {'answerable': spec['set_size'][0], 'unanswerable': spec['set_size'][1]},
             # The reviewer is named only with consent (docs/RELEASE-CHECKLIST.md): count them, do not name them.
             'reviewers': len({r[9].strip() for r in rows if r[9].strip()}), 'reviewer_role': 'an author (a person)',
             'unsigned_rows': sum(1 for r in rows if not r[9].strip() or not r[10].strip()),
             'dates': sorted({r[10].strip() for r in rows})}
    for kind in ('answerable', 'unanswerable'):
        part = [r for r in rows if r[1] == kind]
        assert len(part) == spec[kind], (s, kind, len(part))
        v = [r[6].strip().lower() for r in part]
        assert all(x in VERDICTS for x in v), (s, kind, set(v))
        n = len(v)
        entry[kind] = {'n': n, **{x: v.count(x) for x in VERDICTS},
                       'wrong_rate_wilson': wilson(v.count('wrong'), n),
                       'wrong_or_ambiguous_rate_wilson': wilson(v.count('wrong') + v.count('ambiguous'), n)}
    out['sets'][s] = entry
json.dump(out, open(os.path.join(HERE, 'audit_results.json'), 'w'), indent=1)

pc = lambda x: f'{100 * x:.1f}%'
L = ['# Audit of the reference answers (aggregates only)', '',
     '| Set | Part | Items | Correct | Wrong | Ambiguous | Wrong rate, Wilson 95% |', '|---|---|---:|---:|---:|---:|---|']
for s, e in out['sets'].items():
    for kind in ('answerable', 'unanswerable'):
        k = e[kind]; lo, hi = k['wrong_rate_wilson']
        L.append(f"| {s} | {kind} | {k['n']} | {k['correct']} | {k['wrong']} | {k['ambiguous']} | {pc(lo)}–{pc(hi)} |")
L += ['', f"Second look: {', '.join(SECOND_LOOK['models'])}; items where a model disagreed with the author: "
      + ', '.join(f'set {s}: {n}' for s, n in SECOND_LOOK['items_with_disagreement'].items())
      + f"; verdicts changed after re-examination: {SECOND_LOOK['verdicts_changed']}."]
open(os.path.join(HERE, 'audit_results.md'), 'w').write('\n'.join(L) + '\n')
print('wrote audit_results.json and .md')

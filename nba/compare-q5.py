"""Q5: compare P7's DA (the NBA model shown whole) with DX (NBA inside a 95-table
model) with Ask's area routing on and off, on the same 40 fresh questions.

    work/nba/.venv/bin/python -I nba/compare-q5.py
"""
import json
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = {
    'DA whole model (P7)': ROOT / 'results/nba/P7/DA/pass-1/graded.json',
    'DX routing on': ROOT / 'results/nba/Q5-on/DX/pass-1/graded.json',
    'DX routing off': ROOT / 'results/nba/Q5-off/DX/pass-1/graded.json',
}
graded = {name: {str(row['question_id']): row for row in json.load(open(path))} for name, path in RUNS.items() if path.exists()}

def right(row, measure):
    return bool(row.get(measure))

def mcnemar(a, b):
    n = a + b
    if n == 0:
        return 1.0
    k = min(a, b)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)

print('| Arm | Right in substance | Right with any name | Refused |')
print('|---|---|---|---|')
for name, rows in graded.items():
    shape = sum(right(r, 'shape') for r in rows.values())
    anyname = sum(right(r, 'entities') or right(r, 'shape') for r in rows.values())
    refused = sum(1 for r in rows.values() if (r.get('failure_reason') or '') in ('refused', 'no_sql') or not r.get('sql'))
    print(f'| {name} | {shape} | {anyname} | {refused} |')

on, off = graded.get('DX routing on'), graded.get('DX routing off')
if on and off:
    for measure in ('shape', 'entities'):
        a = sum(1 for q in on if (right(on[q], measure) or (measure == 'entities' and right(on[q], 'shape'))) and not (right(off[q], measure) or (measure == 'entities' and right(off[q], 'shape'))))
        b = sum(1 for q in on if not (right(on[q], measure) or (measure == 'entities' and right(on[q], 'shape'))) and (right(off[q], measure) or (measure == 'entities' and right(off[q], 'shape'))))
        print(f'on vs off, {measure}: only on right {a}, only off right {b}, McNemar p = {mcnemar(a, b):.3f}')

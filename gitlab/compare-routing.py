"""Simplification plan Z4: routing on vs off on the 40 blind GitLab questions.

    python3 -I gitlab/compare-routing.py <run id> [<fill run id> ...]

Reads results/gitlab/<run>/{on,off}/shown.jsonl (gitlab/run-routing.mjs) and prints how often
the first gold table, and all gold tables, reached the SQL writer in each arm, overall and for
the questions written to share words across areas; then an exact McNemar test on the pairs.
A fill run re-asks the questions that stored no run; its rows replace the earlier run's.
Decision Z-D6: routing stays on if it beats search by 5 or more of 40 on the first gold table.
"""
import json
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(run, arm):
    path = ROOT / 'results' / 'gitlab' / run / arm / 'shown.jsonl'
    return {row['id']: row for row in map(json.loads, path.read_text().splitlines())}


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def main():
    on, off = {}, {}
    for run in sys.argv[1:]:
        on.update(load(run, 'on'))
        off.update(load(run, 'off'))
    ids = sorted(set(on) & set(off))
    print(f'| | Routing on | Routing off |')
    print('|---|---|---|')
    for key, label in (('primaryShown', 'First gold table shown'), ('allShown', 'All gold tables shown')):
        for subset, name in ((ids, 'all 40'), ([i for i in ids if on[i]['overlap']], 'shared words')):
            print(f"| {label}, {name} ({len(subset)}) | {sum(on[i][key] for i in subset)} | {sum(off[i][key] for i in subset)} |")
    print(f"| Tables shown, median | {sorted(on[i]['shown'] for i in ids)[len(ids) // 2]} | {sorted(off[i]['shown'] for i in ids)[len(ids) // 2]} |")
    for key in ('primaryShown', 'allShown'):
        only_on = sum(1 for i in ids if on[i][key] and not off[i][key])
        only_off = sum(1 for i in ids if off[i][key] and not on[i][key])
        print(f'{key}: only on {only_on}, only off {only_off}, McNemar p = {mcnemar(only_on, only_off):.3f}')
    gain = sum(on[i]['primaryShown'] for i in ids) - sum(off[i]['primaryShown'] for i in ids)
    print(f"Z-D6: routing {'stays on' if gain >= 5 else 'goes off by default'} (first gold table: {gain:+d} of {len(ids)})")
    misses = [i for i in ids if not on[i]['primaryShown']]
    for i in misses:
        print(f"  on missed q{i} ({on[i]['subject']}): {on[i]['title']}")


if __name__ == '__main__':
    main()

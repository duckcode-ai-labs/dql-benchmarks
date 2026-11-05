"""Compare two GitLab routing runs question by question (ask-area-ranking design, A3).

    python3 -I gitlab/rank/compare-runs.py <run[,fill...]>:<arm> <run[,fill...]>:<arm>

Prints how often the first gold table, and all gold tables, reached the SQL writer in each,
the exact McNemar test on the pairs, and, for the first run, whether each routed step's own
count of tables equals the tables it lists (R1: the step counts what reached the SQL writer).
"""
import json
import re
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(spec):
    runs, arm = spec.split(':')
    rows = {}
    for run in runs.split(','):
        for line in (ROOT / 'results' / 'gitlab' / run / arm / 'shown.jsonl').read_text().splitlines():
            row = json.loads(line)
            rows[row['id']] = row
    return rows


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def counted(title):
    """The tables a routed step says it showed: '29 of the 30 tables …, and 2 Shared …, and 3 more …'."""
    if not title or not title.startswith('Showed the') or ' area' not in title:
        return None
    head = re.search(r': (?:the (\d+) tables?|(\d+) of the \d+ tables)', title)
    if not head:
        return None
    total = int(head.group(1) or head.group(2))
    for extra in re.findall(r'and (\d+) (?:Shared tables?|more)', title):
        total += int(extra)
    return total


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    ids = sorted(set(a) & set(b))
    print(f'| | {sys.argv[1]} | {sys.argv[2]} |')
    print('|---|---|---|')
    for key, label in (('primaryShown', 'First gold table shown'), ('allShown', 'All gold tables shown')):
        print(f'| {label} ({len(ids)}) | {sum(a[i][key] for i in ids)} | {sum(b[i][key] for i in ids)} |')
    print(f"| Tables shown, median | {sorted(a[i]['shown'] for i in ids)[len(ids) // 2]} | {sorted(b[i]['shown'] for i in ids)[len(ids) // 2]} |")
    print(f"| Stopped before tables | {sum(1 for i in ids if not a[i]['title'])} | {sum(1 for i in ids if not b[i]['title'])} |")
    only_a = [i for i in ids if a[i]['primaryShown'] and not b[i]['primaryShown']]
    only_b = [i for i in ids if b[i]['primaryShown'] and not a[i]['primaryShown']]
    print(f'first gold table: only first {len(only_a)} {only_a}, only second {len(only_b)} {only_b}, McNemar p = {mcnemar(len(only_a), len(only_b)):.3f}')
    mismatched = [(i, counted(a[i]['title']), a[i]['shown']) for i in ids if counted(a[i]['title']) is not None and counted(a[i]['title']) != a[i]['shown']]
    print(f"routed steps whose count differs from the tables listed: {len(mismatched)} {mismatched[:8]}")


if __name__ == '__main__':
    main()

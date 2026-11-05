"""Ranking alone, with the area given: for each Z4 question whose gold table sits in an area of
more than 30 tables, where does the word score put it, and what would an AI pick from the area's
one-line index choose? (Design study, ask-area-ranking-design-2026-11-05.)

    python3 -I gitlab/rank/oracle.py <dql project dir> prepare <out dir>
        writes ai-input-original.md and ai-input-reworded.md: each area's index once, then its questions
    python3 -I gitlab/rank/oracle.py <dql project dir> score <out dir>
        reads ai-picks-original.json and ai-picks-reworded.json ({"picks": {"<id>": ["table", ...]}})

The index lines follow apps/cli/src/ask-pipeline-host/table-index.ts (tableIndexLine, width 140):
the table's description when it has one, else its columns.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rank import COLUMNS, DESCRIPTION, NAME, ROOT, bm25_order, load, tail  # noqa: E402

SYSTEM = ('You choose which database tables a question needs. You are given one line per table: its name, then what it holds, '
          'or its columns when nothing says what it holds. Choose every table needed to answer the question, including tables '
          'needed only to join others or to name what the answer groups by. Prefer the table that holds the live data over '
          'archives, copies, backups, snapshots and per-department duplicates, unless the question asks for one of those. '
          'Respond with ONLY a JSON object: {"tables":["schema.table"]}, most important first, at most 8 tables.')


def index_line(relation, table, width=140):
    words = ' '.join((table['description'] or '').split()) or f"columns: {', '.join(table['columns'])}"
    return f"- {relation}: {words[:width - 1] + '…' if len(words) > width else words}"


def cases(project):
    groups, tables, joins, dbt = load(project)
    questions = json.loads((ROOT / 'gitlab' / 'routing-questions.json').read_text())['questions']
    reworded = {q['id']: q['question'] for q in json.loads((ROOT / 'gitlab' / 'rank' / 'reworded-questions.json').read_text())['questions']}
    out = []
    for q in questions:
        gold = tail(dbt.get(q['gold'][0], {}).get('relation_name') or '')
        group = next((g for g in groups if gold in g['relations'] and not g['shared']), None)
        if group and len(group['relations']) > 30:
            out.append({'id': q['id'], 'gold': gold, 'group': group, 'original': q['question'], 'reworded': reworded[q['id']]})
    return out, tables, joins


def main():
    project, mode, out_dir = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)
    items, tables, joins = cases(project)
    if mode == 'prepare':
        for wording in ('original', 'reworded'):
            parts = [f'SYSTEM INSTRUCTION FOR EVERY QUESTION: {SYSTEM}\n']
            for key in dict.fromkeys(item['group']['key'] for item in items):
                group = next(item['group'] for item in items if item['group']['key'] == key)
                parts.append(f"## Area {group['name']} ({len(group['relations'])} tables)\n\nTABLES:\n" + '\n'.join(index_line(r, tables[r]) for r in group['relations']))
                for item in (i for i in items if i['group']['key'] == key):
                    parts.append(f"QUESTION {item['id']}: {item[wording]}")
            (out_dir / f'ai-input-{wording}.md').write_text('\n\n'.join(parts) + '\n')
        print(f'{len(items)} questions in areas over 30 tables; inputs in {out_dir}')
        return
    print('| Wording | Questions | Word score top 8 | top 10 | top 30 | AI pick (8 tables) has it |')
    print('|---|---|---|---|---|---|')
    for wording in ('original', 'reworded'):
        picks = json.loads((out_dir / f'ai-picks-{wording}.json').read_text())['picks']
        ranks, ai = [], 0
        for item in items:
            order = bm25_order(item['group']['relations'], item[wording], tables, set(), joins, [NAME, COLUMNS, DESCRIPTION], False)
            ranks.append(order.index(item['gold']) + 1)
            ai += item['gold'] in {tail(p) for p in picks.get(str(item['id']), [])[:8]}
        print(f"| {wording} | {len(items)} | {sum(r <= 8 for r in ranks)} | {sum(r <= 10 for r in ranks)} | {sum(r <= 30 for r in ranks)} | {ai} |")


if __name__ == '__main__':
    main()

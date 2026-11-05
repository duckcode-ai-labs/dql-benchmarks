"""Design study: how should Ask rank the tables inside a large subject area?

    python3 -I gitlab/rank/rank.py <dql project dir> [--json out.json] [--questions reworded.json] [--no-anchors]

--questions swaps in reworded question text (same ids and gold tables); --no-anchors ranks by
the words alone, as when search found nothing, so the original and reworded sets compare fairly.

Rebuilds Ask's area routing (apps/cli/src/ask-pipeline-host/model-routing.ts at zlens
main ffc48804) from the project's drafted model and the dbt manifest, takes the tables each
Z4 question's search had already chosen from the stored runs (gitlab/rank/steps.py), and
reports where each question's first gold table lands in the chosen area under the order Ask
uses today and under candidate orders. No AI calls: everything is read from files.
"""
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUDGET = 30
STOP = set('''the and for with per each all any how many much what which who whom when where why
are was were has have had did does from into over that this these those than then
show list give top most least total number count average sum by of in on to a an
table tables one row rows model data last first between during their its'''.split())


def words(text):
    out = []
    for word in re.split(r'[^a-z0-9]+', (text or '').lower()):
        if len(word) < 3 or word in STOP or word.isdigit():
            continue
        if len(word) > 4 and word.endswith('ies'):
            word = word[:-3] + 'y'
        elif len(word) > 3 and word.endswith('s') and not word.endswith('ss'):
            word = word[:-1]
        out.append(word)
    return out


def tail(relation):
    parts = [p.strip('"`').lower() for p in (relation or '').split('.') if p]
    return '.'.join(parts[-2:])


LAYER = [('mart_', 0), ('rpt_', 0), ('fct_', 1), ('dim_', 1), ('bdg_', 2), ('map_', 2)]


def layer(name):
    table = name.split('.')[-1]
    return next((rank for prefix, rank in LAYER if table.startswith(prefix)), 3)


def load(project):
    project = Path(project)
    model = json.loads((project / 'dql-manifest.json').read_text())['modeling']
    dbt = json.loads((project.parent / 'target' / 'manifest.json').read_text())['nodes']
    tables = {}
    groups = {}
    for entity in model['entities'].values():
        if entity.get('status') == 'deprecated':
            continue
        node = dbt.get(entity.get('dbtUniqueId'), {})
        relation = tail(node.get('relation_name') or entity.get('relation') or '')
        if not relation:
            continue
        area = model['areas'].get(entity.get('areaId') or '')
        in_area = bool(area) and area.get('localId') != 'core'
        domain = entity.get('domain') or ''
        key = f"area:{area['qualifiedId']}" if in_area else f'domain:{domain}'
        pkg = (model.get('packages', {}).get(domain) or {}).get('name')
        group = groups.setdefault(key, {
            'key': key,
            'name': area['name'] if in_area else (pkg or domain.replace('_', ' ')),
            'shared': bool(area.get('shared')) if in_area else domain == 'shared',
            'words': set(words(f"{area['name']} {area.get('description', '')} {' '.join(area.get('intentExamples', []))}" if in_area else '') + words(f"{domain} {pkg or ''}")),
            'relations': [], 'lookAlikes': [],
        })
        if entity.get('useInstead'):
            group['lookAlikes'].append(relation)
            continue
        columns = node.get('columns', {})
        group['words'].update(words(f"{entity.get('localId') or entity['id']} {entity.get('businessName', '')} {relation.split('.')[-1]} {' '.join(columns)}"))
        if relation not in group['relations']:
            group['relations'].append(relation)
        tables[relation] = {
            'name': relation.split('.')[-1],
            'business': entity.get('businessName', ''),
            'description': node.get('description', ''),
            'columns': list(columns),
            'column_text': ' '.join(f"{name} {col.get('description', '')}" for name, col in columns.items()),
            'grain': entity.get('grain') or '',
        }
    by_ref = {}
    for key, entity in model['entities'].items():
        by_ref[key] = entity
        by_ref[entity.get('qualifiedId') or key] = entity
        by_ref.setdefault(entity.get('localId') or entity['id'], entity)
    joins = []
    for rel in model.get('relationships', {}).values():
        a, b = by_ref.get(rel['from']), by_ref.get(rel['to'])
        if a and b:
            ra = tail(dbt.get(a.get('dbtUniqueId'), {}).get('relation_name') or '')
            rb = tail(dbt.get(b.get('dbtUniqueId'), {}).get('relation_name') or '')
            if ra and rb:
                joins.append((ra, rb))
    groups = [g for g in groups.values() if g['relations']]
    return groups, tables, joins, dbt


def route(groups, question, anchors, joins):
    if len([g for g in groups if not g['shared']]) < 2:
        return None
    asked = set(words(question))
    anchored = lambda r: r in anchors
    ranked = []
    for g in groups:
        score = 3 * sum(1 for r in g['relations'] + g['lookAlikes'] if anchored(r)) + len(asked & g['words'])
        if score > 0:
            ranked.append((g, score))
    ranked.sort(key=lambda item: (item[0]['shared'], -item[1], len(item[0]['relations'])))
    if not ranked:
        return None
    best, best_score = ranked[0]
    chosen = [best]
    for g, score in ranked[1:]:
        if g['shared'] or score * 2 < best_score:
            continue
        if sum(len(c['relations']) for c in chosen) + len(g['relations']) > BUDGET:
            continue
        chosen.append(g)
    pool = list(dict.fromkeys(r for g in chosen for r in g['relations']))
    return {'groups': chosen, 'pool': pool}


def joined(relation, targets, joins):
    return any((a == relation and b in targets) or (b == relation and a in targets) for a, b in joins)


def order_today(pool, anchors, joins):
    a = [r for r in pool if r in anchors]
    return a + [r for r in pool if r not in anchors and joined(r, a, joins)] + [r for r in pool if r not in anchors and not joined(r, a, joins)]


def bm25_order(pool, question, tables, anchors, joins, fields, use_layer):
    """Score each table in the area by the question's words (BM25 inside the area)."""
    asked = list(dict.fromkeys(words(question)))
    docs = {r: Counter(sum((words(field(tables[r])) for field in fields), [])) for r in pool}
    n = len(pool)
    avg = sum(sum(d.values()) for d in docs.values()) / max(n, 1)
    df = Counter(w for d in docs.values() for w in set(d))
    def score(r):
        d = docs[r]
        length = sum(d.values())
        s = 0.0
        for w in asked:
            if d[w]:
                idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * d[w] * 2.2 / (d[w] + 1.2 * (0.25 + 0.75 * length / max(avg, 1)))
        return s
    scores = {r: score(r) for r in pool}
    anchor_list = [r for r in pool if r in anchors]
    def key(r):
        return (-(r in anchors), -scores[r] - (0.5 if joined(r, anchor_list, joins) else 0), layer(r) if use_layer else 0, pool.index(r))
    return sorted(pool, key=key)


NAME = lambda t: f"{t['name']} {t['business']}"
COLUMNS = lambda t: ' '.join(t['columns'])
DESCRIPTION = lambda t: t['description']
COLUMN_TEXT = lambda t: t['column_text']


def main():
    project = sys.argv[1]
    out_json = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
    groups, tables, joins, dbt = load(project)
    questions = json.loads((ROOT / 'gitlab' / 'routing-questions.json').read_text())['questions']
    if '--questions' in sys.argv:
        reworded = {q['id']: q['question'] for q in json.loads(Path(sys.argv[sys.argv.index('--questions') + 1]).read_text())['questions']}
        questions = [{**q, 'question': reworded[q['id']]} for q in questions]
    steps = json.loads((ROOT / 'work' / 'gitlab' / 'rank-steps.json').read_text())['on']
    orders = {
        'today': None,
        'name+columns': ([NAME, COLUMNS], False),
        'name+columns+desc': ([NAME, COLUMNS, DESCRIPTION], False),
        'all text': ([NAME, COLUMNS, DESCRIPTION, COLUMN_TEXT], False),
        'all text+layer': ([NAME, COLUMNS, DESCRIPTION, COLUMN_TEXT], True),
    }
    rows = []
    for q in questions:
        step = steps[str(q['id'])] or {}
        # What search had chosen before routing: the catalog search's picks and the tables the
        # reading named (not what was finally shown, which already holds routed tables).
        anchors = set() if '--no-anchors' in sys.argv else {tail(r) for r in step.get('catalog', []) + step.get('read', [])}
        gold = tail(dbt.get(q['gold'][0], {}).get('relation_name') or '')
        r = route(groups, q['question'], anchors, joins)
        row = {'id': q['id'], 'gold': gold, 'title': step.get('title'), 'groups': [g['name'] for g in r['groups']] if r else [],
               'pool': len(r['pool']) if r else 0, 'inPool': bool(r) and gold in r['pool'],
               'shownToday': gold in {tail(x) for x in step.get('shown', [])}, 'searchFound': gold in anchors, 'rank': {}}
        if r and gold in r['pool']:
            for label, spec in orders.items():
                ordered = order_today(r['pool'], anchors, joins) if spec is None else bm25_order(r['pool'], q['question'], tables, anchors, joins, *spec)
                row['rank'][label] = ordered.index(gold) + 1
        rows.append(row)
    in_pool = [row for row in rows if row['inPool']]
    print(f"Questions: {len(rows)}; routed: {sum(1 for row in rows if row['groups'])}; gold table in the chosen area(s): {len(in_pool)}; search had already found it: {sum(row['searchFound'] for row in rows)}; shown to the SQL writer today: {sum(row['shownToday'] for row in rows)}")
    print('| Order inside the area | in top 5 | top 10 | top 15 | top 30 | median rank |')
    print('|---|---|---|---|---|---|')
    for label in orders:
        ranks = sorted(row['rank'][label] for row in in_pool)
        print(f"| {label} | {sum(x <= 5 for x in ranks)} | {sum(x <= 10 for x in ranks)} | {sum(x <= 15 for x in ranks)} | {sum(x <= 30 for x in ranks)} | {ranks[len(ranks) // 2] if ranks else '-'} |")
    print()
    for row in rows:
        print(f"q{row['id']:>2} {','.join(row['groups']) or '-':<22} pool {row['pool']:>3} gold {row['gold'].split('.')[-1]:<45} inArea {str(row['inPool'])[0]} found {str(row['searchFound'])[0]} shown {str(row['shownToday'])[0]} {row['rank']}")
    if out_json:
        Path(out_json).write_text(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()

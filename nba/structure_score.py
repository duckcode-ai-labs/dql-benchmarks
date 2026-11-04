"""Structure score: a drafted model (`zlens model discover --validate --format json`)
against the hand-built NBA business model (nba/dm-model/model.dql.yaml).

Design "ZLens drafts the whole business model" (2026-11-04), "How we'll know it works" 1:
  - tables picked right, of 8 (a table in use in the hand model, kept by the draft);
  - legacy tables flagged, of 7 (the draft says use another table, or leaves it out as a staging copy);
  - row identities right, of 15 (the drafted identity is the hand grain's columns, or a unique subset of them);
  - joins found, of 17 (same two tables, same key columns, either direction);
  - wrong joins drafted (any drafted join the hand model does not have).

Usage: python3 nba/structure_score.py <discover.json> [--model nba/dm-model/model.dql.yaml] [--json]
"""
import json
import re
import sys
from pathlib import Path

import yaml


def table_of(dbt_model: str) -> str:
    return dbt_model.split('.')[-1].lower()


def grain_columns(grain: str) -> set[str]:
    match = re.search(r'\(([^)]*)\)', grain or '')
    return {part.strip().lower() for part in match.group(1).split(',')} if match else set()


def main() -> None:
    args = sys.argv[1:]
    report_path = Path(args[0])
    model_path = Path(args[args.index('--model') + 1]) if '--model' in args else Path(__file__).parent / 'dm-model' / 'model.dql.yaml'
    report = json.loads(report_path.read_text())
    model = yaml.safe_load(model_path.read_text())

    entities = {entity['id']: entity for entity in model['entities']}
    table_by_entity = {entity_id: table_of(entity['dbt_model']) for entity_id, entity in entities.items()}
    in_use = {table_by_entity[e['id']] for e in model['entities'] if e.get('status') != 'deprecated'}
    legacy = {table_by_entity[e['id']] for e in model['entities'] if e.get('status') == 'deprecated'}

    drafted = {entity['relation'].split('.')[-1].lower(): entity for entity in report['entities']}
    hidden = {item['relation'].split('.')[-1].lower(): item['finalRelation'].split('.')[-1].lower() for item in report.get('stagingHidden', [])}

    picks = []
    for table in sorted(in_use):
        entity = drafted.get(table)
        ok = entity is not None and not entity.get('useInstead')
        picks.append({'table': table, 'ok': ok, 'why': 'kept' if ok else ('not drafted' if entity is None else f"use {entity['useInstead']['relation'].split('.')[-1]}: {entity['useInstead']['reason']}")})

    flags = []
    for table in sorted(legacy):
        entity = drafted.get(table)
        if entity and entity.get('useInstead'):
            flags.append({'table': table, 'ok': True, 'how': 'use_instead', 'why': entity['useInstead']['reason']})
        elif table in hidden:
            flags.append({'table': table, 'ok': True, 'how': 'staging_hidden', 'why': f'left out as a staging copy of {hidden[table]}'})
        else:
            flags.append({'table': table, 'ok': False, 'how': None, 'why': 'kept' if entity else 'not drafted'})

    identities = []
    for entity in model['entities']:
        table = table_by_entity[entity['id']]
        wanted = grain_columns(entity.get('grain', ''))
        found = drafted.get(table, {}).get('identity')
        columns = {column.lower() for column in found['columns']} if found else set()
        ok = bool(columns) and columns <= wanted
        identities.append({'table': table, 'ok': ok, 'hand': sorted(wanted), 'drafted': sorted(columns), 'duplicates': found.get('duplicates') if found else None})

    def signature(from_table: str, to_table: str, keys: list[tuple[str, str]]) -> frozenset:
        return frozenset({(from_table, to_table, frozenset(keys)), (to_table, from_table, frozenset((b, a) for a, b in keys))})

    hand_joins = []
    for relationship in model['relationships']:
        from_table = table_by_entity[relationship['from']]
        to_table = table_by_entity[relationship['to']]
        keys = [(pair['from'].lower(), pair['to'].lower()) for pair in relationship['keys']]
        hand_joins.append({'id': relationship['id'], 'sig': signature(from_table, to_table, keys), 'text': f"{from_table} → {to_table} on {', '.join(f'{a}={b}' for a, b in keys)}"})
    drafted_joins = []
    for relationship in report.get('relationships', []):
        from_table = relationship['fromRelation'].split('.')[-1].lower()
        to_table = relationship['toRelation'].split('.')[-1].lower()
        keys = [(pair['from'].lower(), pair['to'].lower()) for pair in relationship['keys']]
        drafted_joins.append({'sig': signature(from_table, to_table, keys), 'text': f"{from_table} → {to_table} on {', '.join(f'{a}={b}' for a, b in keys)}", 'status': (relationship.get('validation') or {}).get('status')})
    drafted_sigs = [item['sig'] for item in drafted_joins]
    found = [{'id': join['id'], 'ok': any(join['sig'] & sig for sig in drafted_sigs), 'text': join['text']} for join in hand_joins]
    hand_sigs = [join['sig'] for join in hand_joins]
    wrong = [item for item in drafted_joins if not any(item['sig'] & sig for sig in hand_sigs)]

    score = {
        'tables_picked': [sum(item['ok'] for item in picks), len(picks)],
        'legacy_flagged': [sum(item['ok'] for item in flags), len(flags)],
        'legacy_flagged_by_picks': [sum(item['how'] == 'use_instead' for item in flags), len(flags)],
        'identities': [sum(item['ok'] for item in identities), len(identities)],
        'joins_found': [sum(item['ok'] for item in found), len(found)],
        'wrong_joins': len(wrong),
        'picks': picks, 'flags': flags, 'identity_detail': identities, 'joins': found, 'wrong': [item['text'] for item in wrong],
    }
    if '--json' in args:
        print(json.dumps(score, indent=2))
        return
    print(f"tables picked right   {score['tables_picked'][0]}/{score['tables_picked'][1]}")
    print(f"legacy flagged        {score['legacy_flagged'][0]}/{score['legacy_flagged'][1]} ({score['legacy_flagged_by_picks'][0]} by table picks, the rest left out as staging copies)")
    print(f"row identities right  {score['identities'][0]}/{score['identities'][1]}")
    print(f"joins found           {score['joins_found'][0]}/{score['joins_found'][1]}")
    print(f"wrong joins drafted   {score['wrong_joins']}")
    for item in picks + flags:
        if not item['ok']:
            print(f"  miss {item['table']}: {item['why']}")
    for item in identities:
        if not item['ok']:
            print(f"  identity {item['table']}: hand {item['hand']} drafted {item['drafted']}")


if __name__ == '__main__':
    main()

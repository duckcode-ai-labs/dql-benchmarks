"""Pull each Z4 question's schema and search steps out of the stored runs.

    python3 -I gitlab/rank/steps.py > work/gitlab/rank-steps.json

For every question and arm (later fill runs replace earlier ones): the schema step's title,
the tables it finally showed, the tables the catalog search found, the tables whose columns
were read from the warehouse, and the request vocabulary's size line.
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ('Z4', 'Z4-fill', 'Z4-fill2')


def steps(run, arm):
    store = ROOT / 'work' / 'gitlab' / 'runs' / run / arm / 'dbt' / 'dql' / '.dql' / 'local' / 'agent-runs.sqlite'
    if not store.exists():
        return {}
    db = sqlite3.connect(f'file:{store}?mode=ro', uri=True)
    out = {}
    for question, payload in db.execute('select question, payload_json from agent_runs order by rowid'):
        if question in out:
            continue
        story = json.loads(payload).get('diagnosticReceiptV9', {}).get('story', [])
        context = next((s for s in story if s.get('phase') == 'context'), {})
        schema = next((s for s in story if s.get('phase') == 'schema' and isinstance(s.get('relations'), list)), None)
        detail = (schema or {}).get('detail') or ''
        catalog = re.search(r'found by the catalog search: (.*?)(?:; [a-z]|$)', detail)
        read = re.search(r'columns of (.*?) read from the warehouse', detail)
        split = lambda text: [item.strip() for item in text.split(', ')] if text else []
        out[question] = {
            'context': context.get('title'),
            'title': (schema or {}).get('title'),
            'shown': (schema or {}).get('relations', []),
            'catalog': split(catalog.group(1) if catalog else ''),
            'read': split(read.group(1) if read else ''),
            'detail': detail,
        }
    return out


def main():
    questions = json.loads((ROOT / 'gitlab' / 'routing-questions.json').read_text())['questions']
    result = {}
    for arm in ('on', 'off'):
        merged = {}
        for run in RUNS:
            merged.update(steps(run, arm))
        result[arm] = {q['id']: merged.get(q['question']) for q in questions}
    json.dump(result, sys.stdout, indent=1)


if __name__ == '__main__':
    main()

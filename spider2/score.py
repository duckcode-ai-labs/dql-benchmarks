#!/usr/bin/env python3
"""Grade a Spider 2.0-Lite SQLite run with the official evaluator.

    .venv/bin/python spider2/score.py work/spider2/runs/<run>/<condition> [more run dirs]
        [--baseline work/spider2/runs/<run>/baseline]

Every prediction is executed and compared by the official evaluation suite
(`evaluate_spider2sql`, sql mode, its gold results and per-task comparison
rules). A task with no SQL counts as wrong over every task the run asked, so
a stop is never dropped from the denominator. Writes score.json in each run
directory and prints one line per run, plus a paired table when given two.
"""
import argparse, collections, contextlib, io, json, math, re, sqlite3, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / 'data' / 'spider2-lite' / 'repo' / 'spider2-lite' / 'evaluation_suite'
sys.path.insert(0, str(SUITE))
import evaluate as official  # noqa: E402


def wilson(correct, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = correct / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


TIERS = ('certified', 'governed', 'review_required', 'blocked')

# Why a question ended without SQL, from the words of the check that stopped
# it. The receipt's refusal code says which stage; the message says which
# check, and the checks are what we fix.
STOP_CLASSES = [
    ('fanout_both_sides', r'repeats the key on both sides'),
    ('fanout_one_side', r'across its join to|counted once per matching'),
    ('unused_join', r'uses none of its columns|which both only reference'),
    ('catalog_validator', r'inspected|outside the inspected metadata|references .* but this request'),
    ('stated_value', r'leaves out|does not (?:apply|mention)|stated'),
    ('time_budget', r'did not respond|budget|elapsed|deadline|timed out'),
    ('empty_result', r'no rows|found nothing|No matching data'),
    ('declined_missing', r'missing|does not hold|do not hold|not in the'),
]


def stop_class(code, message):
    for name, pattern in STOP_CLASSES:
        if message and re.search(pattern, message, re.I):
            return name
    return code or 'unknown'


def receipts(run_dir: Path):
    """Per task: the pipeline receipt DQL stored for it (refusals, dispatches)."""
    out = {}
    for db_dir in sorted(p for p in run_dir.iterdir() if p.is_dir() and (p / 'evals.yml').exists()):
        questions = {}
        for block in re.split(r'\n  - name: ', (db_dir / 'evals.yml').read_text()):
            name = re.match(r'(?:cases:\n  - name: )?"([^"]+)"', block)
            question = re.search(r'question: ("(?:[^"\\]|\\.)*")', block)
            if name and question:
                questions[json.loads(question.group(1))] = name.group(1)
        store = db_dir / 'project' / '.dql' / 'local' / 'agent-runs.sqlite'
        if not store.exists():
            continue
        con = sqlite3.connect(f'file:{store}?mode=ro', uri=True)
        try:
            rows = con.execute('select question, payload_json from agent_runs').fetchall()
        finally:
            con.close()
        for question, payload in rows:
            task = questions.get(question)
            if not task or not payload:
                continue
            try:
                data = json.loads(payload)
            except ValueError:
                continue
            receipt = data.get('diagnosticReceiptV9') or {}
            refusal = (receipt.get('refusals') or [{}])[0]
            terminal = receipt.get('terminal') or {}
            message = refusal.get('message') or (data.get('answer') if isinstance(data.get('answer'), str) else '') or ''
            out[task] = {
                'dispatches': len(receipt.get('dispatches') or []),
                'purposes': [d.get('purpose') for d in receipt.get('dispatches') or []],
                'refusalCode': refusal.get('code'),
                'terminal': terminal.get('code'),
                'stop': stop_class(refusal.get('code') or terminal.get('code'), message),
                'stopMessage': message[:300],
            }
    return out


def pct(values, q):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))]


def grade(run_dir: Path):
    summary = json.loads((run_dir / 'summary.json').read_text())
    asked = sorted(task for db in summary['databases'].values() for task in db['tasks'])
    predictions = run_dir / 'predictions'
    args = argparse.Namespace(mode='sql', result_dir=str(predictions), gold_dir=str(SUITE / 'gold'), is_sql_debug=False, max_workers=8, timeout=60)
    with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
        results = official.evaluate_spider2sql(args, Path(temp)) if any(predictions.glob('*.sql')) else []
    scored = {item['instance_id']: item for item in results}
    stored = receipts(run_dir) if summary.get('dql') else {}
    per_task = {}
    for task in asked:
        item = scored.get(task)
        outcome = next((db['outcomes'].get(task) for db in summary['databases'].values() if task in db['outcomes']), {}) or {}
        per_task[task] = {
            'correct': bool(item and item['score'] == 1),
            'answered': item is not None,
            'error': (item or {}).get('error_info'),
            'trust': outcome.get('trust'),
            'durationMs': outcome.get('durationMs'),
            **({k: v for k, v in stored[task].items() if k != 'purposes'} if task in stored else {}),
        }
    correct = sum(1 for value in per_task.values() if value['correct'])
    answered = sum(1 for value in per_task.values() if value['answered'])
    trusted_wrong = sum(1 for value in per_task.values() if value['answered'] and not value['correct'] and value['trust'] in ('certified', 'governed'))
    durations = sorted(value['durationMs'] for value in per_task.values() if isinstance(value['durationMs'], (int, float)))
    low, high = wilson(correct, len(asked))
    # Every trust rate is printed beside how many answers were issued at that
    # tier: zero wrong out of zero issued is not a trust result.
    matrix = {tier: {'issued': 0, 'correct': 0, 'wrong': 0} for tier in TIERS}
    for value in per_task.values():
        tier = value['trust'] if value['trust'] in matrix else None
        if not tier:
            continue
        if tier == 'blocked' or not value['answered']:
            matrix['blocked']['issued'] += 1
            continue
        matrix[tier]['issued'] += 1
        matrix[tier]['correct' if value['correct'] else 'wrong'] += 1
    stops = collections.Counter(value.get('stop', 'no_receipt') for value in per_task.values() if not value['answered'])
    dispatch_counts = [value['dispatches'] for value in per_task.values() if isinstance(value.get('dispatches'), int)]
    result = {
        'run': summary['run'], 'condition': summary['condition'], 'provider': summary['provider'], 'model': summary['model'], 'dql': summary.get('dql'),
        'asked': len(asked), 'answered': answered, 'correct': correct, 'accuracy': correct / len(asked) if asked else 0,
        'ci95': [low, high], 'wrongShownAsTrustworthy': trusted_wrong,
        'trustedIssued': matrix['certified']['issued'] + matrix['governed']['issued'],
        'trustMatrix': matrix,
        'stopRate': (len(asked) - answered) / len(asked) if asked else 0,
        'stops': dict(stops.most_common()),
        'medianSeconds': durations[len(durations) // 2] / 1000 if durations else None,
        'p90Seconds': pct(durations, 0.9) / 1000 if durations else None,
        'dispatchesPerQuestion': (sum(dispatch_counts) / len(dispatch_counts)) if dispatch_counts else None,
        'missingDatabases': summary.get('missingDatabases', []), 'invalid': summary.get('invalid', []),
        'evaluator': 'Spider2 official evaluate_spider2sql (sql mode)', 'tasks': per_task,
    }
    (run_dir / 'score.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def bucket(task):
    return 'correct' if task['correct'] else 'wrong' if task['answered'] else 'no SQL'


def transitions(base, run):
    """The 3x3 table baseline -> run, and the ids that moved, on shared tasks."""
    if not set(run['tasks']) <= set(base['tasks']):
        raise SystemExit(f"refusing a transition table over different task sets: {base['run']}/{base['condition']} vs {run['run']}/{run['condition']}")
    # A quick run is compared with the same tasks of a full baseline.
    base = {**base, 'tasks': {task: base['tasks'][task] for task in run['tasks']}}
    table = collections.Counter((bucket(base['tasks'][t]), bucket(run['tasks'][t])) for t in base['tasks'])
    lost_stop = sorted(t for t in base['tasks'] if base['tasks'][t]['correct'] and not run['tasks'][t]['answered'])
    turned_wrong = sorted(t for t in base['tasks'] if base['tasks'][t]['correct'] and run['tasks'][t]['answered'] and not run['tasks'][t]['correct'])
    won = sorted(t for t in base['tasks'] if not base['tasks'][t]['correct'] and run['tasks'][t]['correct'])
    return table, lost_stop, turned_wrong, won


def describe_build(item):
    build = (item.get('dql') or {}).get('build')
    if not build:
        return 'build: not recorded'
    if build.get('kind') != 'git':
        return f"build: {build.get('kind')} {build.get('version') or ''}".strip()
    flags = ' '.join(f'{k}={v}' for k, v in (build.get('switches') or {}).items())
    return f"build: {build['branch']} @ {build['head'][:8]}{' + UNCOMMITTED patch ' + build['patchSha256'][:8] if build.get('dirty') else ' (clean)'}{' STALE DIST' if build.get('distOlderThanSource') else ''}{' · ' + flags if flags else ''}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('runs', nargs='+', type=Path)
    parser.add_argument('--baseline', type=Path, help='a scored or scorable baseline run to compare every run against')
    options = parser.parse_args()
    graded = [grade(run) for run in options.runs]
    base = grade(options.baseline) if options.baseline else None
    for item in graded:
        low, high = item['ci95']
        median = f"{item['medianSeconds']:.0f} s" if item['medianSeconds'] is not None else 'n/a'
        p90 = f"{item['p90Seconds']:.0f} s" if item.get('p90Seconds') is not None else 'n/a'
        calls = f"{item['dispatchesPerQuestion']:.1f}" if item.get('dispatchesPerQuestion') is not None else 'n/a'
        print(f"{item['run']}/{item['condition']} ({item['model']}): {item['correct']}/{item['asked']} ({item['accuracy']:.1%}, 95% CI {low:.1%}–{high:.1%}) · SQL returned {item['answered']} · stop rate {item['stopRate']:.0%} · median {median}, p90 {p90} · calls/question {calls}{' · INVALID' if item['invalid'] else ''}")
        print(f"  {describe_build(item)}")
        matrix = item['trustMatrix']
        print('  trust:  ' + ' · '.join(f"{tier} {cell['issued']} issued ({cell['correct']} right, {cell['wrong']} wrong)" if tier != 'blocked' else f"blocked {cell['issued']}" for tier, cell in matrix.items()))
        print(f"  wrong shown as trustworthy: {item['wrongShownAsTrustworthy']} of {item['trustedIssued']} governed/certified answers issued")
        if item['stops']:
            print('  stops:  ' + ', '.join(f'{name} {count}' for name, count in item['stops'].items()))
        if base:
            table, lost_stop, turned_wrong, won = transitions(base, item)
            cols = ('correct', 'wrong', 'no SQL')
            print(f"  vs {base['run']}/{base['condition']} (rows) → this run (cols):")
            for row in cols:
                print(f"    {row:>8}: " + '  '.join(f"{col} {table[(row, col)]:>2}" for col in cols))
            print(f"    baseline-right → no SQL ({len(lost_stop)}): {', '.join(lost_stop)}")
            print(f"    baseline-right → wrong  ({len(turned_wrong)}): {', '.join(turned_wrong)}")
            print(f"    baseline-wrong → right  ({len(won)}): {', '.join(won)}")
    if len(graded) == 2:
        a, b = graded
        common = sorted(set(a['tasks']) & set(b['tasks']))
        only_a = sum(1 for task in common if a['tasks'][task]['correct'] and not b['tasks'][task]['correct'])
        only_b = sum(1 for task in common if b['tasks'][task]['correct'] and not a['tasks'][task]['correct'])
        print(f"paired on {len(common)}: {a['run']}/{a['condition']} only {only_a}, {b['run']}/{b['condition']} only {only_b}, exact McNemar p = {mcnemar(only_a, only_b):.3f}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Grade a Spider 2.0-Lite SQLite run with the official evaluator.

    .venv/bin/python spider2/score.py work/spider2/runs/<run>/<condition> [more run dirs]

Every prediction is executed and compared by the official evaluation suite
(`evaluate_spider2sql`, sql mode, its gold results and per-task comparison
rules). A task with no SQL counts as wrong over every task the run asked, so
a stop is never dropped from the denominator. Writes score.json in each run
directory and prints one line per run, plus a paired table when given two.
"""
import argparse, contextlib, io, json, math, sys, tempfile
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


def grade(run_dir: Path):
    summary = json.loads((run_dir / 'summary.json').read_text())
    asked = sorted(task for db in summary['databases'].values() for task in db['tasks'])
    predictions = run_dir / 'predictions'
    args = argparse.Namespace(mode='sql', result_dir=str(predictions), gold_dir=str(SUITE / 'gold'), is_sql_debug=False, max_workers=8, timeout=60)
    with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
        results = official.evaluate_spider2sql(args, Path(temp)) if any(predictions.glob('*.sql')) else []
    scored = {item['instance_id']: item for item in results}
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
        }
    correct = sum(1 for value in per_task.values() if value['correct'])
    answered = sum(1 for value in per_task.values() if value['answered'])
    trusted_wrong = sum(1 for value in per_task.values() if value['answered'] and not value['correct'] and value['trust'] in ('certified', 'governed'))
    durations = sorted(value['durationMs'] for value in per_task.values() if isinstance(value['durationMs'], (int, float)))
    low, high = wilson(correct, len(asked))
    result = {
        'run': summary['run'], 'condition': summary['condition'], 'provider': summary['provider'], 'model': summary['model'], 'dql': summary.get('dql'),
        'asked': len(asked), 'answered': answered, 'correct': correct, 'accuracy': correct / len(asked) if asked else 0,
        'ci95': [low, high], 'wrongShownAsTrustworthy': trusted_wrong,
        'medianSeconds': durations[len(durations) // 2] / 1000 if durations else None,
        'missingDatabases': summary.get('missingDatabases', []), 'invalid': summary.get('invalid', []),
        'evaluator': 'Spider2 official evaluate_spider2sql (sql mode)', 'tasks': per_task,
    }
    (run_dir / 'score.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    runs = [Path(arg) for arg in sys.argv[1:]]
    if not runs:
        sys.exit(__doc__)
    graded = [grade(run) for run in runs]
    for item in graded:
        low, high = item['ci95']
        median = f"{item['medianSeconds']:.0f} s" if item['medianSeconds'] is not None else 'n/a'
        print(f"{item['run']}/{item['condition']} ({item['model']}): {item['correct']}/{item['asked']} ({item['accuracy']:.1%}, 95% CI {low:.1%}–{high:.1%}) · SQL returned {item['answered']} · wrong shown as trustworthy {item['wrongShownAsTrustworthy']} · median {median}{' · INVALID' if item['invalid'] else ''}")
    if len(graded) == 2:
        a, b = graded
        common = sorted(set(a['tasks']) & set(b['tasks']))
        only_a = sum(1 for task in common if a['tasks'][task]['correct'] and not b['tasks'][task]['correct'])
        only_b = sum(1 for task in common if b['tasks'][task]['correct'] and not a['tasks'][task]['correct'])
        print(f"paired on {len(common)}: {a['condition']} only {only_a}, {b['condition']} only {only_b}, exact McNemar p = {mcnemar(only_a, only_b):.3f}")


if __name__ == '__main__':
    main()

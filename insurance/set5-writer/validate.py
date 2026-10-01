# Checks questions-5.json: counts, fields, and that every goldSql runs and returns rows. Prints counts only.
import json, subprocess, sys, collections
d = json.load(open('questions-5.json'))
qs, un = d.get('questions', []), d.get('unanswerable', [])
problems = []
quad = collections.Counter(q.get('quadrant') for q in qs)
if len(qs) != 200: problems.append(f'{len(qs)} answerable questions, need 200')
for k in ('LQLS', 'LQHS', 'HQLS', 'HQHS'):
    if quad.get(k, 0) != 50: problems.append(f'quadrant {k}: {quad.get(k, 0)}, need 50')
if len(un) != 50: problems.append(f'{len(un)} unanswerable, need 50')
if len({q.get("question", "").strip().lower() for q in qs + un}) != len(qs) + len(un): problems.append('duplicate questions')
bad = 0
for i, q in enumerate(qs):
    sql = q.get('goldSql', '')
    if not sql.strip().lower().startswith(('select', 'with')): problems.append(f'questions[{i}]: goldSql must be one SELECT'); continue
    r = subprocess.run(['/opt/homebrew/bin/duckdb', '-readonly', '-json', 'acme_insurance.duckdb', '-c', sql], capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not r.stdout.strip() or r.stdout.strip() in ('[]', '[{}]'):
        bad += 1; problems.append(f'questions[{i}]: goldSql failed or returned no rows')
for u in un:
    if not u.get('why'): problems.append('an unanswerable question has no why')
print(f'{len(qs)} answerable ({dict(quad)}), {len(un)} unanswerable, {bad} gold queries failed or empty')
print('\n'.join(problems) if problems else 'VALID')
sys.exit(1 if problems else 0)

# Build the run archive deposited with the paper (docs/RELEASE-CHECKLIST.md): for every run reported in the
# paper, each set's report, eval file, agent transcripts, provider cassettes, usage log and DQL run store
# (agent-runs.sqlite), including resumed, aborted and as-recorded attempts. Warehouses and project copies
# are left out (they are rebuilt by insurance/build.mjs). Contains the sealed sets: build it on release day.
#   python3 scripts/build-run-archive.py --dry-run     # list sizes only
#   python3 scripts/build-run-archive.py               # -> work/release/dql-insurance-runs-<date>.tar.zst
import os, subprocess, sys, tarfile, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(REPO, 'work', 'insurance', 'runs')
src = open(os.path.join(REPO, 'scripts', 'export-results.py')).read()
RUN_IDS = eval(src.split('RUN_IDS = ', 1)[1].split(']', 1)[0] + ']')   # one list of reported runs, kept in export-results.py
KEEP_FILES = {'report.json', 'evals.yml', 'transcripts.json', 'usage.jsonl', 'refused-attempts.jsonl', 'eval.stderr.log', 'server.log'}
KEEP_DIRS = {'cassettes'}
STORE = os.path.join('project', '.dql', 'local')

files = []
for run in RUN_IDS:
    for root, dirs, names in os.walk(os.path.join(RUNS, run)):
        rel = os.path.relpath(root, RUNS)
        parts = rel.split(os.sep)
        if len(parts) >= 3 and parts[3:4] == ['project']:
            if rel.endswith(STORE):
                files += [os.path.join(root, n) for n in names if n.startswith('agent-runs.sqlite')]
            if not STORE.startswith(os.sep.join(parts[3:])):
                dirs[:] = []
            continue
        if len(parts) >= 4 and parts[3] in KEEP_DIRS:
            files += [os.path.join(root, n) for n in names]
            continue
        files += [os.path.join(root, n) for n in names if n in KEEP_FILES]
size = sum(os.path.getsize(f) for f in files)
print(f'{len(RUN_IDS)} runs, {len(files)} files, {size / 1e6:.0f} MB before compression')
if '--dry-run' in sys.argv:
    sys.exit(0)
out_dir = os.path.join(REPO, 'work', 'release'); os.makedirs(out_dir, exist_ok=True)
tar_path = os.path.join(out_dir, f'dql-insurance-runs-{datetime.date.today().isoformat()}.tar')
with tarfile.open(tar_path, 'w') as tf:
    for f in sorted(files):
        tf.add(f, arcname=os.path.join('runs', os.path.relpath(f, RUNS)))
subprocess.run(['zstd', '-19', '-T0', '--rm', '-f', tar_path], check=True)
print(f'wrote {os.path.relpath(tar_path, REPO)}.zst')

# Copy the evidence behind the paper from work/ (ignored, 35 GB of projects and databases) into
# results/ (committed): each run's report.json, evals.yml and, for agents, transcripts.json.
# Sealed question sets (set 4 until the paper is posted, set 5 until its pre-registered run is
# reported) are refused unless --release is given, because their reports contain question text.
#   python3 scripts/export-results.py            # public sets only
#   python3 scripts/export-results.py --release  # also set 4 (release day)
import os, shutil, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(REPO, 'work', 'insurance', 'runs')
OUT = os.path.join(REPO, 'results', 'insurance')
RELEASE = '--release' in sys.argv

# Runs reported in the paper (analysis/insurance-2026-09-29): DQL ladders, then agents.
RUN_IDS = ['fl-opus', 'fl-sonnet55', 'fl-sonnet', 'fl-qwen', 'fl-luna', 'fl-sol', 'fl-terra',
           'ag-opus', 'ag-sonnet55', 'fl4-sonnet55', 'ag4-sonnet55', 'ag4m-sonnet55']
PUBLIC_SETS = {'all', 'heldout-3', 'heldout-3-unanswerable'}   # dev set; set 3 is spent
RELEASE_SETS = {'heldout-4', 'heldout-4-unanswerable'}          # sealed until the paper is posted
FILES = ('report.json', 'evals.yml', 'transcripts.json')

copied, refused = 0, set()
for run in RUN_IDS:
    base = os.path.join(RUNS, run)
    if not os.path.isdir(base):
        continue
    for cond in sorted(os.listdir(base)):
        cdir = os.path.join(base, cond)
        if not os.path.isdir(cdir):
            continue
        for set_name in sorted(os.listdir(cdir)):
            sdir = os.path.join(cdir, set_name)
            if not os.path.isdir(sdir) or not os.path.exists(os.path.join(sdir, 'report.json')) and not os.path.exists(os.path.join(sdir, 'transcripts.json')):
                continue
            if set_name in RELEASE_SETS and not RELEASE:
                refused.add(set_name); continue
            if set_name not in PUBLIC_SETS | RELEASE_SETS:
                continue   # attempts, smoke sets and anything else stay in the archive
            dest = os.path.join(OUT, run, cond, set_name)
            os.makedirs(dest, exist_ok=True)
            for f in FILES:
                src = os.path.join(sdir, f)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(dest, f)); copied += 1
print(f'copied {copied} files into results/insurance' + (f'; refused sealed sets {sorted(refused)} (use --release on release day)' if refused else ''))

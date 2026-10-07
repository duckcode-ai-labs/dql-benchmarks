# Copy the evidence behind the paper from work/ (ignored, 35 GB of projects and databases) into
# results/ (committed): each run's report.json, evals.yml and, for agents, transcripts.json.
# Sealed question sets (sets 4 and 5, released with the paper) are refused unless --release is given,
# because their reports contain question text. With --release it also copies the reference rows and
# the audit files; the reviewer column of the audit sheets is replaced by "author" unless
# --reviewer-consent is given (docs/RELEASE-CHECKLIST.md).
#   python3 scripts/export-results.py                                # public sets only
#   python3 scripts/export-results.py --release [--reviewer-consent]  # release day
import csv, os, shutil, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(REPO, 'work', 'insurance', 'runs')
OUT = os.path.join(REPO, 'results', 'insurance')
RELEASE = '--release' in sys.argv
CONSENT = '--reviewer-consent' in sys.argv

# Runs reported in the paper (analysis/insurance-2026-09-29): DQL ladders, then agents.
RUN_IDS = ['fl-opus', 'fl-sonnet55', 'fl-sonnet', 'fl-qwen', 'fl-luna', 'fl-sol', 'fl-terra',
           'ag-opus', 'ag-sonnet55', 'fl4-sonnet55', 'ag4-sonnet55', 'ag4m-sonnet55',
           'fl5-sonnet55', 'ag5-sonnet55', 'ag5m-sonnet55', 'fl5-qwen', 'ag5-qwen', 'ag5m-qwen',
           'fl5-sonnet55-rep2', 'fl5-sonnet55-rep3', 'ag5m-sonnet55-rep2', 'ag5m-sonnet55-rep3']
PUBLIC_SETS = {'all', 'heldout-3', 'heldout-3-unanswerable'}   # dev set; set 3 is spent
RELEASE_SETS = {'heldout-4', 'heldout-4-unanswerable', 'heldout-5', 'heldout-5-unanswerable'}  # sealed until the paper is posted
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
            base_set = set_name[:-len('.as-recorded')] if set_name.endswith('.as-recorded') else set_name   # first recording of a re-asked set
            if base_set in RELEASE_SETS and not RELEASE:
                refused.add(base_set); continue
            if base_set not in PUBLIC_SETS | RELEASE_SETS:
                continue   # attempts, smoke sets and anything else stay in the archive
            dest = os.path.join(OUT, run, cond, set_name)
            os.makedirs(dest, exist_ok=True)
            for f in FILES:
                src = os.path.join(sdir, f)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(dest, f)); copied += 1
if RELEASE:
    # Reference rows from executing the writers' reference SQL, and the audit evidence.
    for s in ('heldout-4', 'heldout-5'):
        src = os.path.join(REPO, 'work', 'insurance', 'gold', f'{s}.json')
        os.makedirs(os.path.join(OUT, 'gold'), exist_ok=True)
        shutil.copy2(src, os.path.join(OUT, 'gold', f'{s}.json')); copied += 1
    AUD_SRC, AUD_DST = os.path.join(REPO, 'work', 'insurance', 'audit'), os.path.join(REPO, 'insurance', 'audit')
    for src_name, dst_name in (('set4-audit-sample.csv', 'set4-audit-completed.csv'), ('set5-audit-sample.csv', 'set5-audit-completed.csv'),
                               ('set5-discordant-review.csv', 'set5-discordant-review.csv'), ('set5-discordant-check12.csv', 'set5-discordant-check12.csv')):
        src = os.path.join(AUD_SRC, src_name)
        if not os.path.exists(src):
            continue
        rows = list(csv.reader(open(src, encoding='utf-8-sig')))
        col = next((i for i, h in enumerate(rows[0]) if h.strip().lower() == 'reviewer'), None)
        if col is not None and not CONSENT:
            for r in rows[1:]:
                if r[col].strip():
                    r[col] = 'author'
        with open(os.path.join(AUD_DST, dst_name), 'w', newline='') as f:
            csv.writer(f).writerows(rows)
        copied += 1
    # The AI model's blind judgement of the set-5 disagreements and the prompt it was given.
    src_dir = os.path.join(AUD_SRC, 'second-opinion')
    if os.path.isdir(src_dir):
        os.makedirs(os.path.join(AUD_DST, 'second-opinion'), exist_ok=True)
        for name in sorted(os.listdir(src_dir)):
            shutil.copy2(os.path.join(src_dir, name), os.path.join(AUD_DST, 'second-opinion', name)); copied += 1
    for name in ('set4-adjudications.json', 'set5-discordant-key.json'):
        src = os.path.join(AUD_SRC, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(AUD_DST, name)); copied += 1
print(f'copied {copied} files into results/insurance' + (f'; refused sealed sets {sorted(refused)} (use --release on release day)' if refused else ''))

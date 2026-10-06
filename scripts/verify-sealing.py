# Check sealed files against the SHA-256 hashes published in docs/SEALING.md before any system was run.
# Looks for each listed file in the places it lives before and after release; prints names and verdicts only.
#   python3 scripts/verify-sealing.py
import glob, hashlib, os, re, tarfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACES = ['insurance/heldout', 'work/insurance/gold', 'results/insurance/gold', 'private/sealed', 'insurance/audit', '']
row = re.compile(r'^\|\s*`([^`]+)`[^|]*\|\s*(\d*)\s*\|\s*`([0-9a-f]{64})`\s*\|')

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

counts = {'ok': 0, 'mismatch': 0, 'not found': 0}
for line in open(os.path.join(REPO, 'docs', 'SEALING.md')):
    m = row.match(line.strip())
    if not m:
        continue
    name, size, digest = m.groups()
    candidates = [os.path.join(REPO, name)] + [os.path.join(REPO, p, os.path.basename(name)) for p in PLACES]
    found = [c for c in dict.fromkeys(candidates) if os.path.isfile(c)]
    if not found:
        # Writer transcripts and logs live inside the sealed writer archives (private/sealed/*.tar).
        inside = []
        for tar in sorted(glob.glob(os.path.join(REPO, 'private', 'sealed', '*.tar'))):
            with tarfile.open(tar) as tf:
                for member in tf.getmembers():
                    if member.isfile() and os.path.basename(member.name) == os.path.basename(name):
                        inside.append((os.path.relpath(tar, REPO) + ':' + member.name, hashlib.sha256(tf.extractfile(member).read()).hexdigest()))
        if not inside:
            counts['not found'] += 1; print(f'not found  {name}'); continue
        hits = [where for where, d in inside if d == digest]
        verdict = 'ok' if hits else 'mismatch'
        counts[verdict] += 1
        print(f"{verdict:<10} {name}  ({hits[0] if hits else 'checked ' + ', '.join(w for w, _ in inside)})")
        continue
    hits = [c for c in found if sha(c) == digest]
    verdict = 'ok' if hits else 'mismatch'
    counts[verdict] += 1
    print(f"{verdict:<10} {name}" + (f"  ({os.path.relpath(hits[0], REPO)})" if hits else f"  (checked {', '.join(os.path.relpath(c, REPO) for c in found)})"))
print(counts)

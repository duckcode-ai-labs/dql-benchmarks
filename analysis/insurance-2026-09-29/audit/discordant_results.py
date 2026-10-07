# Blind review of the set-5 disagreements between W2 and A-model (Claude Sonnet 5.5, pre-registered runs):
# the 34 answerable questions on which exactly one of the two was strict-correct. An AI model judged all 34;
# the author judged a random 12 (seed 20261007). Both were blind to which system gave which answer
# (insurance/audit/AUDIT-INSTRUCTIONS.md). Reads the sealed sheets and the key in work/; writes counts only.
#   python3 analysis/insurance-2026-09-29/audit/discordant_results.py  -> discordant_results.json / .md
import collections, csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, '..', '..', '..', 'work', 'insurance', 'audit')
NORM = {'acceptable': 'acceptable', 'not acceptable': 'not acceptable', 'unsure': 'unsure'}
key = json.load(open(os.path.join(AUD, 'set5-discordant-key.json')))['items']


def read(path, cols):
    out = {}
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        a1, a2, b = (r[c].strip().lower() for c in cols)
        out[int(r['item'])] = (NORM.get(a1, a1), NORM.get(a2, a2), b)
    return out


def tally(verdicts):
    c = collections.Counter()
    for i, (a1, a2, b) in verdicts.items():
        k = key[str(i)]
        side = {k['answer_1']: a1, k['answer_2']: a2}
        right, wrong = k['strict_correct'], ('A-model' if k['strict_correct'] == 'W2' else 'W2')
        c[f'W2: {side["W2"]}'] += 1
        c[f'A-model: {side["A-model"]}'] += 1
        c[f'strict-correct answer: {side[right]}'] += 1
        c[f'strict-wrong answer: {side[wrong]}'] += 1
        c[f'strict-wrong {wrong} answer: {side[wrong]}'] += 1
        c[f'only {right} strict-correct'] += 1
        c['better: ' + {'1': k['answer_1'], '2': k['answer_2']}.get(b, b)] += 1
    return {'n': len(verdicts), **dict(sorted(c.items()))}


author_cols = ('ANSWER 1 (acceptable / not acceptable / unsure)', 'ANSWER 2 (acceptable / not acceptable / unsure)', 'better answer (1 / 2 / same)')
author = read(os.path.join(AUD, 'set5-discordant-check12.csv'), author_cols)
model = read(os.path.join(AUD, 'second-opinion', 'set5-blind-codex-review.csv'), ('answer_1_verdict', 'answer_2_verdict', 'better'))
both = sorted(set(author) & set(model))
out = {'questions': len(key), 'model': {'name': 'GPT-6.1 Sol at low reasoning effort', **tally(model)},
       'author': {'sample_seed': 20261007, **tally(author)},
       'agreement_on_author_sample': {'answer_verdicts': sum(1 for i in both for j in (0, 1) if author[i][j] == model[i][j]),
                                      'answer_verdicts_n': 2 * len(both),
                                      'better': sum(1 for i in both if author[i][2] == model[i][2]), 'better_n': len(both)}}
json.dump(out, open(os.path.join(HERE, 'discordant_results.json'), 'w'), indent=1)
L = ['# Blind review of the set-5 W2 / A-model disagreements (counts only)', '']
for who in ('model', 'author'):
    L.append(f"**{who}** ({out[who]['n']} questions): " + '; '.join(f'{k} {v}' for k, v in out[who].items() if k not in ('n', 'name', 'sample_seed')))
    L.append('')
a = out['agreement_on_author_sample']
L.append(f"Agreement on the author's sample: answer verdicts {a['answer_verdicts']}/{a['answer_verdicts_n']}, better answer {a['better']}/{a['better_n']}.")
open(os.path.join(HERE, 'discordant_results.md'), 'w').write('\n'.join(L) + '\n')
print('wrote discordant_results.json and .md')

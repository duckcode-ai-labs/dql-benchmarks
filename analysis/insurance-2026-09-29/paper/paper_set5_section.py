# Section 6.1, the pre-registered set-5 results, generated from stats_v2/stats_v2_set5.json (S5; the
# set-4-named keys there hold set 5) and stats_v2_set5_as_recorded.json (S5R); exec'd by paper_docx.py.
_C5 = ['P', 'A', 'Am', 'L2', 'L3', 'W2', 'WB']
_lev = ['L2', 'L3', 'W2', 'WB']
_hp = lambda t: f"{dpt(t)} points, Holm {pstr(t['p_holm'])}"
_word = lambda n, cap=False: (['no', 'one', 'two', 'three', 'four', 'five'][n] if n < 6 else str(n)).capitalize() if cap else (['no', 'one', 'two', 'three', 'four', 'five'][n] if n < 6 else str(n))
_aud5 = AUDR['sets']['5']
_wrong5 = _aud5['answerable']['wrong'] + _aud5['unanswerable']['wrong']
add(H2('6.1  Pre-registered test on set 5'))
add(P(f'Claude Sonnet 5.5 ran every condition once on the frozen build. '
      + ('The audit found no wrong item in the set-5 sample (Section 4.5), so the scoring without wrong items is the scoring on all items. ' if not _wrong5 else f'The audit found {_wrong5} wrong items in the set-5 sample (Section 4.5); results without them are in audit/. ')
      + 'Table 4 gives accuracy and abstention, Table 5 the trusted labels.'))
_MODELS5 = [('Sonnet 5.5', S5, 'sonnet55')] + ([('Qwen 3.8 27B', S5Q, 'qwen')] if S5Q else [])
def _m5(d, key):
    return (d['accuracy']['heldout-5'][key], d['accuracy']['heldout-5-unanswerable'].get(key, {}),
            {c['cond']: c for c in d['regrade']['cells'] if c['set'] == 'heldout-5' and c['model'] == key}, d['trust']['heldout-5'])
rows = []
for mlabel, d, key in _MODELS5:
    acc, un, rcs, _ = _m5(d, key)
    for k in _C5:
        if k not in acc: continue
        c, rc, uu = acc[k], rcs[k], un.get(k)
        rows.append([mlabel if k == _C5[0] else '', NAME[k], f"{c['k']} ({pct(c['acc'])})", ci(c['bootstrap']['ci']), str(rc['lenient']), str(rc['lenient_rounding']), f"{uu['k']}/50" if uu else '–'])
add(TABLE(['Model', 'Condition', 'Strict correct', 'Bootstrap 95% CI', 'Lenient', 'Lenient + rounding', 'Correct abstentions'], rows, [1300, 2500, 1300, 1300, 900, 1100, 960]))
_l3r = S5R['accuracy']['heldout-5']['sonnet55']['L3']['k']
add(CAP(f'**Table 4.** Set 5 (200 answerable and 50 unanswerable questions written by GPT-6 Sol), build 627009a1: correct answers of 200 under each grading rule and correct abstentions of 50. Claude Sonnet 5.5 is the pre-registered primary model' + (', Qwen 3.8 27B a pre-registered secondary model' if S5Q else '') + f'. Bootstrap: question-level, seed 5. DQL counts include answers re-asked after runtime connection failures (Section 8); as recorded, Sonnet\'s L3 answered {_l3r}.'))
rows = []
for mlabel, d, key in _MODELS5:
    tr = _m5(d, key)[3]
    for k in _lev:
        t = tr[k]
        rows.append([mlabel if k == _lev[0] else '', NAME[k], str(t['T']), str(t['W_T']), f"{pct(t['precision'])} ({ci(t['precision_wilson'], 0)})" if t['T'] else 'none', str(t['W_T_lenient_rounding']),
                     f"{pct(t['precision_all'])} ({ci(t['precision_all_wilson'], 0)})" if t.get('T_all') else 'none', pct(t['kappa']), pct(t['sigma']), str(t.get('unanswerable_answered_trusted', 0))])
add(TABLE(['Model', 'Level', 'T', 'W_T', 'π (Wilson)', 'W_T, lenient + rounding', 'π all (Wilson)', 'κ', 'ω', 'Unanswerable labelled trusted'], rows, [1200, 2000, 450, 550, 1300, 1050, 1300, 550, 550, 1050]))
add(CAP('**Table 5.** Trusted answers on set 5. *T* trusted answers on the answerable set, *W*_{T} of them strict-wrong; π all counts trusted answers to unanswerable questions as wrong. One-shot SQL and the agents assign no labels.'))

_h, _hl = PR5['W2_vs_Am'], PR5['sensitivity']['lenient']['W2_vs_Am']
_tax = ''
if globals().get('TAX'):
    _lk = TAX['task2']['counts_by_kind']['all']
    _tax = f' On the public set 3, {_lk["b"] + _lk["c"]} of the {_lk["lenient_only"]} answers that only the lenient rule accepts lost an identity the question asked for or changed its meaning, as classified by an AI assistant (Appendix D).'
_gA, _gW = RC5['Am']['lenient'] - RC5['Am']['strict'], RC5['W2']['lenient'] - RC5['W2']['strict']
add(P((f'**H1 (primary).** W2 answered {AC5["W2"]["k"]} of 200 questions correctly and A-model {AC5["Am"]["k"]}: a difference of {dpt(_h)} points (question-level bootstrap 95% interval {dci(_h)}). W2 alone was right on {_h["gained"]} questions and A-model alone on {_h["lost"]}; the exact two-sided McNemar test gives {pstr(_h["p_raw"])}, below the pre-registered α = 0.05. H1 is supported: under the strict rule, DQL at W2 answered more of these questions correctly than an agent given the same modeling knowledge as text. The difference depends on the grading rule. Under the lenient rule both answered {RC5["W2"]["lenient"]} ({_hl["gained"]} questions each way, {pstr(_hl["p_raw"])})' if _hl['gained'] == _hl['lost'] else
      f'**H1 (primary).** W2 answered {AC5["W2"]["k"]} of 200 questions correctly and A-model {AC5["Am"]["k"]}: a difference of {dpt(_h)} points (question-level bootstrap 95% interval {dci(_h)}). W2 alone was right on {_h["gained"]} questions and A-model alone on {_h["lost"]}; the exact two-sided McNemar test gives {pstr(_h["p_raw"])}. Under the lenient rule the difference is {dpt(_hl)} points ({pstr(_hl["p_raw"])})')
  + f': the lenient rule accepts {_gA} more of A-model\'s answers and {_gW} more of W2\'s. The strict advantage disappears under the lenient sensitivity rule and is associated with differences in the columns the answers returned. That is consistent with DQL\'s instructions to show an entity\'s identifier beside its name, which the agent did not receive (Section 4.3), and with a strict rule that accepts extra columns.' + _tax))
if DR:
    _m, _a, _ag = DR['model'], DR['author'], DR['agreement_on_author_sample']
    _nq = DR['questions']; _nW, _nA = _m.get('only W2 strict-correct', 0), _m.get('only A-model strict-correct', 0)
    _mAw, _mWw = _m.get('strict-wrong A-model answer: acceptable', 0), _m.get('strict-wrong W2 answer: acceptable', 0)
    _allpass = _m.get('strict-correct answer: acceptable', 0) == _nq
    add(P(f'**Do the differences matter?** (post-hoc, not pre-registered). The {_nq} questions on which only one of the two answers passed the strict rule were judged blind to which system gave which answer, as the person who asked would judge them: is each answer acceptable, and which is better (insurance/audit/AUDIT-INSTRUCTIONS.md). An AI model ({_m["name"]}) judged all {_nq}. '
          + ('It found every answer that passed the strict rule acceptable, and ' if _allpass else 'It found ')
          + f'{_mAw} of A-model\'s {_nW} strict failures and {_mWw} of W2\'s {_nA} acceptable as well, and it judged the two answers equally good on {_m.get("better: same", 0)} questions, A-model\'s better on {_m.get("better: A-model", 0)} and W2\'s on {_m.get("better: W2", 0)}. '
          + f'Counted that way, A-model would have {AC5["Am"]["k"] + _mAw} acceptable answers and W2 {AC5["W2"]["k"] + _mWw}, the same picture as the lenient rule. '
          + f'The author judged a random {_a["n"]} of the {_nq} questions (seed {_a["sample_seed"]}), also blind, by a stricter standard (for example, an internal key in place of the policy or claim number was not accepted): {_a.get("strict-wrong answer: not acceptable", 0)} of the {_a["n"]} answers that failed the strict rule were not acceptable, and {_a.get("strict-correct answer: acceptable", 0)} of the {_a["n"]} that passed were acceptable. '
          + f'The two reviews agreed on {_ag["answer_verdicts"]} of {_ag["answer_verdicts_n"]} answer verdicts. Whether W2\'s strict advantage matters therefore depends on whether the reader expects business identifiers such as policy and claim numbers. The {_nq} cases and both reviews are released with set 5.'))

if REPS:
    _runs = [S5] + REPS
    def _wa(d, grade):
        acc = d['accuracy']['heldout-5']['sonnet55']
        cells = {c['cond']: c for c in d['regrade']['cells'] if c['set'] == 'heldout-5'}
        t = d['set4_paired']['W2_vs_Am'] if grade == 'strict' else d['set4_paired']['sensitivity'][grade]['W2_vs_Am']
        k = (lambda c: acc[c]['k']) if grade == 'strict' else (lambda c: cells[c][grade])
        return k('W2'), k('Am'), t['p_raw']
    _s = [_wa(d, 'strict') for d in _runs]; _l = [_wa(d, 'lenient') for d in _runs]
    _ord = ['pre-registered run', 'second run', 'third run']
    _pn = lambda ps: ', '.join(pstr(p).replace('p = ', '').replace('p ', '') for p in ps[:-1]) + ' and ' + pstr(ps[-1]).replace('p = ', '').replace('p ', '')
    _times = {1: 'once', 2: 'twice'}.get(len(REPS), f'{len(REPS)} times')
    add(P(f'**Repeat runs** (exploratory, not pre-registered). Earlier repeated runs had moved single levels by up to 4 of 40 questions (10 points), more than the H1 effect, so after the pre-registered result was known we ran W2 and A-model {_times} more on set 5 with the same build, model and settings. Under the strict rule W2 led in every run: '
          + ', '.join(f'{w} against {a} in the {_ord[i]}' for i, (w, a, _) in enumerate(_s)) + f'; exact McNemar p = {_pn([p for *_, p in _s])}. '
          + f'Under the lenient rule {"no" if all(p >= 0.05 for *_, p in _l) else "not every"} run showed a significant difference: ' + ', '.join(f'{w} against {a}' for w, a, _ in _l) + f'; p = {_pn([p for *_, p in _l])}. '
          + 'The strict advantage is stable across runs, and so is its dependence on the columns returned. One runtime failure in the second W2 run was re-asked under the same rule as the main runs (Section 8).'))

_f5, _w5, _hh5 = fig5()
add(FIG(_f5, _w5, _hh5))
_fr = ['the pre-registered run'] + ([f'{_word(len(REPS))} repeat run' + ('s' if len(REPS) != 1 else '')] if REPS else [])
_frt = (', '.join(_fr) + ' and with the secondary model') if S5Q else ' and '.join(_fr)
add(CAP(f'**Figure 1.** Set 5: DQL W2 against the agent given the same modeling knowledge (A-model), under strict and lenient grading, in {_frt}. Lines: question-level bootstrap 95% intervals (strict grading only).'))

_vp, _vm, _va = PR5['vs_P'], PR5['vs_Am'], PR5['vs_A']
_vaL = PR5['sensitivity']['lenient']['vs_A']
_rng = lambda fam: f"{min(fam[L]['diff'] for L in _lev) * 100:+.1f} to {max(fam[L]['diff'] for L in _lev) * 100:+.1f}".replace('-', '−')
_allP = all(_vp[L]['p_holm'] < 0.05 for L in _lev)
_sigm = [L for L in _lev if _vm[L]['p_holm'] < 0.05]
_sigA, _sigAL = [L for L in _lev if _va[L]['p_holm'] < 0.05], [L for L in _lev if _vaL[L]['p_holm'] < 0.05]
add(P(f'**Accuracy against P and A-model** (secondary; Holm within each family of four). '
      + (f'Every level was significantly more accurate than one-shot SQL ({_rng(_vp)} points; largest Holm {pstr(max(_vp[L]["p_holm"] for L in _lev))}). ' if _allP else 'Not every level was significantly more accurate than one-shot SQL. ')
      + ('Against A-model no level differed significantly after correction: ' if not _sigm else f'Against A-model {", ".join(_sigm)} differed significantly after correction: ')
      + '; '.join(f'{L} {_hp(_vm[L])}' for L in _lev)
      + '. W2 against A-model is significant as the single primary test and not within this secondary family; both readings are as pre-registered. '
      + f'Against the agent without the modeling knowledge (not pre-registered; for comparison with set 4), {"every level was" if len(_sigA) == 4 else ", ".join(_sigA) + (" was" if len(_sigA) == 1 else " were")} significantly more accurate under the strict rule (W2 {_hp(_va["W2"])}) and {"none" if not _sigAL else ", ".join(_sigAL)} under the lenient rule (W2 {_hp(_vaL["W2"])}).'))

_p = P5L23
_tl = {L: T5[L] for L in _lev}
_lr23 = _tl['L2']['W_T_lenient_rounding'] + _tl['L3']['W_T_lenient_rounding']
add(P(f'**Trusted labels** (secondary). At L2 and L3, {_tl["L2"]["T"]} and {_tl["L3"]["T"]} answers carried a governed label ({pct(_tl["L2"]["kappa"])} and {pct(_tl["L3"]["kappa"])} of answers), and {_tl["L2"]["T"] - _tl["L2"]["W_T"]} and {_tl["L3"]["T"] - _tl["L3"]["W_T"]} of them were right: π = {pct(_tl["L2"]["precision"])} (Wilson {ci(_tl["L2"]["precision_wilson"])}) and {pct(_tl["L3"]["precision"])} ({ci(_tl["L3"]["precision_wilson"])}). Pooled, {_p["trusted_right"]} of {_p["trusted"]} trusted answers were right; they came from {_p["distinct_questions"]} distinct questions, {_p["distinct_questions_with_wrong_trusted"]} of which received a wrong trusted answer. '
      + f'The pre-registered hypothesis that precision is at least 0.95 is not supported: the lower confidence limits are {pct(_tl["L2"]["precision_wilson"][0], 0)} and {pct(_tl["L3"]["precision_wilson"][0], 0)}. '
      + f'Under lenient + rounding only {_word(_lr23)} of the {_p["trusted"]} remain{"s" if _lr23 == 1 else ""} wrong, so most of these errors are in the columns returned rather than the numbers; under the pre-registered strict rule they count as wrong. '
      + f'At WB, {_tl["WB"]["W_T"]} of {_tl["WB"]["T"]} trusted answers were wrong ({_tl["WB"]["W_T_lenient_rounding"]} under lenient + rounding), and W2 labelled {_tl["W2"]["T"]} answers trusted, {_tl["W2"]["W_T"]} of them wrong. '
      + f'Counting trusted answers to unanswerable questions as wrong, π all was {pct(_tl["L2"]["precision_all"])} at L2 and {pct(_tl["L3"]["precision_all"])} at L3 (Table 5).'))

_st = STOP5
_le = [L for L in _lev if U5[L]['k'] <= U5['Am']['k']]
_sigs = [L for L in _lev if _st[L]['p_holm'] < 0.05]
_minL = min(_lev, key=lambda L: _st[L]['p_raw'])
add(P(f'**Abstention** (secondary). On the 50 unanswerable questions A-model abstained correctly {U5["Am"]["k"]} times and the agent without modeling {U5["A"]["k"]}; DQL abstained correctly {", ".join(str(U5[L]["k"]) for L in _lev[:3])} and {U5["WB"]["k"]} times at L2, L3, W2 and WB. '
      + ('No level differed significantly from A-model after Holm correction' if not _sigs else f'{", ".join(_sigs)} differed significantly from A-model after Holm correction')
      + f' (largest difference {_minL}, {dpt(_st[_minL])} points, raw {pstr(_st[_minL]["p_raw"])}, Holm {pstr(_st[_minL]["p_holm"])})'
      + (', but no level abstained correctly more often than A-model' if len(_le) == 4 else '')
      + f', and {", ".join(str(T5[L].get("unanswerable_answered_trusted", 0)) for L in _lev[:3])} and {T5["WB"].get("unanswerable_answered_trusted", 0)} answers to unanswerable questions carried a trusted label.'))

if S5Q:
    _qa, _qu, _qrc, _qt = _m5(S5Q, 'qwen')
    _qp = S5Q['set4_paired']; _qh, _qhl = _qp['W2_vs_Am'], _qp['sensitivity']['lenient']['W2_vs_Am']
    _qsigP = [L for L in _lev if _qp['vs_P'][L]['p_holm'] < 0.05]; _qsigM = [L for L in _lev if _qp['vs_Am'][L]['p_holm'] < 0.05]
    _qst = S5Q.get('stops_vs_Am') or {}
    _qsigS = [L for L in _lev if _qst.get(L, {}).get('p_holm', 1) < 0.05]
    _qpool = S5Q['pooled']['trust_heldout4']['L2_L3']
    _rec = (S5QR or {}).get('accuracy', {}).get('heldout-5', {}).get('qwen', {})
    _chg = [L for L in _lev if L in _rec and _rec[L]['k'] != _qa[L]['k']]
    _lst = lambda Ls: ', '.join(Ls[:-1]) + (' and ' if len(Ls) > 1 else '') + Ls[-1] if Ls else 'none'
    add(P(f'**Secondary model.** Qwen 3.8 27B, run locally, is the pre-registered secondary model reported here (GPT-6 Sol, the other, was not run; Section 8). It answered fewer questions in every condition (Table 4). W2 answered {_qa["W2"]["k"]} of 200 correctly and A-model {_qa["Am"]["k"]}: {dpt(_qh)} points (exact McNemar {pstr(_qh["p_raw"])}; {_qh["gained"]} questions only W2 answered correctly and {_qh["lost"]} only A-model), and {dpt(_qhl)} points under the lenient rule ({pstr(_qhl["p_raw"])}). '
          + f'Against one-shot SQL ({_qa["P"]["k"]} correct), {_lst(_qsigP)} {"was" if len(_qsigP) == 1 else "were"} significantly more accurate after Holm correction; against A-model, {_lst(_qsigM)}. '
          + f'At L2 and L3, {_qpool["trusted_right"]} of {_qpool["trusted"]} trusted answers were right' + (f' ({pct(_qpool["precision"])})' if _qpool['trusted'] else '') + f'; at WB, {_qt["WB"]["T"] - _qt["WB"]["W_T"]} of {_qt["WB"]["T"]}. '
          + f'On the 50 unanswerable questions DQL abstained correctly {", ".join(str(_qu[L]["k"]) for L in _lev[:3])} and {_qu["WB"]["k"]} times at L2, L3, W2 and WB, against {_qu["Am"]["k"]} for A-model and {_qu["A"]["k"]} for the agent without modeling; '
          + (f'{_lst(_qsigS)} abstained correctly significantly more often than A-model after Holm correction. ' if _qsigS else 'no level differed significantly from A-model after Holm correction. ')
          + (f'Re-asking Qwen\'s runtime connection failures changed {_lst(_chg)} (as recorded: ' + ', '.join(f'{L} {_rec[L]["k"]}' for L in _chg) + '). ' if _chg else '')
          + 'With this model, then, the pre-registered comparison of W2 with A-model ' + ('also favoured W2.' if _qh['p_raw'] < 0.05 and _qh['diff'] > 0 else 'showed no significant difference.')))

_inc = sum(c.get('strict_but_inconsistent_columns', 0) for c in RC5.values())
add(P(f'**Checks.** Read as first recorded, without the re-asked runtime failures, Sonnet\'s results change only at L3 ({_l3r} of 200), and no conclusion above changes. {_word(_inc, True)} strict-correct answer{"" if _inc == 1 else "s"} failed the consistent-column check of Section 5. The database variants and the root-cause taxonomy have not yet been applied to set 5. ' + ('' if S5Q else '**Secondary models.** GPT-6 Sol was not run on set 5, and Qwen 3.8 27B is still running at the time of writing.')))

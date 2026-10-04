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
rows = []
for k in _C5:
    c, rc, u = AC5[k], RC5[k], U5.get(k)
    rows.append([NAME[k], f"{c['k']} ({pct(c['acc'])})", ci(c['bootstrap']['ci']), str(rc['lenient']), str(rc['lenient_rounding']), f"{u['k']}/50" if u else '–'])
add(TABLE(['Condition', 'Strict correct', 'Bootstrap 95% CI', 'Lenient', 'Lenient + rounding', 'Correct abstentions'], rows, [2700, 1500, 1500, 1100, 1300, 1260]))
_l3r = S5R['accuracy']['heldout-5']['sonnet55']['L3']['k']
add(CAP(f'**Table 4.** Set 5 (200 answerable and 50 unanswerable questions written by GPT-6 Sol), Claude Sonnet 5.5, build 627009a1: correct answers of 200 under each grading rule and correct abstentions of 50. Bootstrap: question-level, seed 5. L3 includes the two re-asked runtime failures (Section 8); as recorded it answered {_l3r}.'))
rows = []
for k in _lev:
    t = T5[k]
    rows.append([NAME[k], str(t['T']), str(t['W_T']), f"{pct(t['precision'])} ({ci(t['precision_wilson'], 0)})" if t['T'] else 'none', str(t['W_T_lenient_rounding']),
                 f"{pct(t['precision_all'])} ({ci(t['precision_all_wilson'], 0)})" if t.get('T_all') else 'none', pct(t['kappa']), pct(t['sigma']), str(t.get('unanswerable_answered_trusted', 0))])
add(TABLE(['Level', 'T', 'W_T', 'π (Wilson)', 'W_T, lenient + rounding', 'π all (Wilson)', 'κ', 'ω', 'Unanswerable labelled trusted'], rows, [2300, 500, 600, 1500, 1200, 1500, 650, 650, 1300]))
add(CAP('**Table 5.** Trusted answers on set 5, Claude Sonnet 5.5. *T* trusted answers on the answerable set, *W*_{T} of them strict-wrong; π all counts trusted answers to unanswerable questions as wrong. One-shot SQL and the agents assign no labels.'))

_h, _hl = PR5['W2_vs_Am'], PR5['sensitivity']['lenient']['W2_vs_Am']
_tax = ''
if 'TAX' in globals():
    _lk = TAX['task2']['counts_by_kind']['all']
    _tax = f' On the public set 3, {_lk["b"] + _lk["c"]} of the {_lk["lenient_only"]} answers that only the lenient rule accepts lost an identity the question asked for or changed its meaning, as classified by an AI assistant (Section 6.9).'
_gA, _gW = RC5['Am']['lenient'] - RC5['Am']['strict'], RC5['W2']['lenient'] - RC5['W2']['strict']
add(P((f'**H1 (primary).** W2 answered {AC5["W2"]["k"]} of 200 questions correctly and A-model {AC5["Am"]["k"]}: a difference of {dpt(_h)} points (question-level bootstrap 95% interval {dci(_h)}). W2 alone was right on {_h["gained"]} questions and A-model alone on {_h["lost"]}; the exact two-sided McNemar test gives {pstr(_h["p_raw"])}, below the pre-registered α = 0.05. H1 is supported: under the strict rule, DQL at W2 answered more of these questions correctly than an agent given the same modeling knowledge as text. The difference depends on the grading rule. Under the lenient rule both answered {RC5["W2"]["lenient"]} ({_hl["gained"]} questions each way, {pstr(_hl["p_raw"])})' if _hl['gained'] == _hl['lost'] else
      f'**H1 (primary).** W2 answered {AC5["W2"]["k"]} of 200 questions correctly and A-model {AC5["Am"]["k"]}: a difference of {dpt(_h)} points (question-level bootstrap 95% interval {dci(_h)}). W2 alone was right on {_h["gained"]} questions and A-model alone on {_h["lost"]}; the exact two-sided McNemar test gives {pstr(_h["p_raw"])}. Under the lenient rule the difference is {dpt(_hl)} points ({pstr(_hl["p_raw"])})')
  + f': the lenient rule accepts {_gA} more of A-model\'s answers and {_gW} more of W2\'s. The strict advantage disappears under the lenient sensitivity rule and is associated with differences in the columns the answers returned. That is consistent with DQL\'s instructions to show an entity\'s identifier beside its name, which the agent did not receive (Section 4.3), and with a strict rule that accepts extra columns. Whether those differences are harmless substitutions or lose the identity the question asked for needs case-level review; an author is reviewing the {_h["gained"] + _h["lost"]} questions on which the two disagree, blind to which system gave which answer.' + _tax))

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

_inc = sum(c.get('strict_but_inconsistent_columns', 0) for c in RC5.values())
add(P(f'**Checks.** Read as first recorded, without the re-asked runtime failures, only L3 changes ({_l3r} of 200), and no conclusion above changes. {_word(_inc, True)} strict-correct answer{"" if _inc == 1 else "s"} failed the consistent-column check of Section 5. The database variants and the root-cause taxonomy have not yet been applied to set 5. **Secondary models.** GPT-6 Sol was not run on set 5, and Qwen 3.8 27B is still running at the time of writing.'))

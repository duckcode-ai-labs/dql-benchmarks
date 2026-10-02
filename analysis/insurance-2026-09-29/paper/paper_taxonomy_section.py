# Section 6.8, generated from ../taxonomy/taxonomy.json (exec'd by paper_docx.py with TAX loaded).
T1, T2 = TAX['task1'], TAX['task2']
_bl = T1['counts']['by_level']['heldout-3']
_tr = sum(v['trusted'] for v in _bl.values()); _wr = sum(v['wrong_trusted'] for v in _bl.values())
_cert = sum(v['trusted_certified'] for v in _bl.values())
_qw = len({a['question_id'] for a in T1['wrong_trusted_answers']})
_cto = T1['counts']['certified_tier_outcomes']
_refused = sum(v for k, v in _cto.items() if k.endswith(':refused'))
_rc = {r['class']: r for r in T1['root_cause_table']}
_sig = T1['trust_signals_on_trusted_answers']['table']['any_of_four_signals']
_ok = T1['trust_signals_on_trusted_answers']['table']['found_artifact']
_lk = T2['counts_by_kind']['all']
def _only_case(x):
    g, a = x.get('gold_rows_all'), x.get('answer_rows_all')
    if not g or not a or len(g) != len(a): return False
    low = lambda rows: sorted(tuple(str(v).lower() for v in r) for r in rows)
    exact = lambda rows: sorted(tuple(str(v) for v in r) for r in rows)
    return low(g) == low(a) and exact(g) != exact(a)
_case = sum(1 for x in T2['all_lenient_only_answers'] if _only_case(x))

add(H2('6.8  Why trusted answers were wrong, and what the lenient grade forgives (set 3)'))
add(P(f'We classified every wrong trusted answer on the public set 3 by root cause (set 4 will follow once its audit is complete and it is released). Of {_tr} trusted answers across seven models, {_wr} were wrong, on {_qw} distinct questions. None was certified: no set-3 question matched a certified block, the certified tier declined each of the {_refused} times it was consulted at LB and WB, and every trusted answer came from governed metrics. On set 3, therefore, the absence of wrong certified answers is an empty statement. The run reports\' route field names the certified tier for these governed answers; we classify by the trust label instead.'))
_lbl = {'route': 'Route: a governed answer covered only part of the question', 'compilation': 'Compilation: "as a percentage" returned as a fraction',
        'definition': 'Definition: the metric sums a column that is empty in every row', 'reading': 'Reading', 'execution': 'Execution', 'reference': 'Reference error'}
rows = []
for cls in ('route', 'compilation', 'definition', 'reading', 'execution', 'reference'):
    r = _rc.get(cls)
    if not r: continue
    lv = ', '.join(f'{k} {v}' for k, v in r['by_level'].items() if v) or '–'
    rows.append([_lbl[cls], str(r['distinct_questions']), str(r['wrong_trusted_answers']), lv])
add(TABLE(['Root cause', 'Questions', 'Wrong trusted answers', 'Levels'], rows, [5400, 1100, 1500, 1360], ['left', 'right', 'right', 'left']))
add(CAP('**Table 11.** Root causes of wrong trusted answers on set 3, all models. The two compilation cases could also be classed as reading, since the structured reading has no field for "as a percentage"; we rate that judgement medium-confidence. No wrong trusted answer was a reference error.'))
add(P(f'The metric definitions were almost always right; the label was the problem. In the route cases the governed metric answered part of the question (the yearly inputs of a growth rate, a per-group breakdown instead of a correlation, raw distances or years instead of bands and decades) and kept its governed label. In the compilation cases a ratio named as a percentage was returned unscaled. The one definition failure came from W2: importing dbt Labs\' semantic models turned a measure that was never published as a metric into a governed metric over a column that is NULL in all 820 rows, and DQL labelled the resulting single NULL as governed. DQL\'s own reading often recorded the part it could not cover, or warned that a requested item was missing, and still labelled the answer governed. Four simple signals (an unresolved part of the reading, a coverage warning, an all-NULL result, a ratio named as a percentage but not multiplied by 100) would have flagged {_sig["wrong"]} of the {_wr} wrong trusted answers and {_sig["right"]} of the {_ok["right"]} right ones. We chose these signals after reading the failures, on the same data, so this sizes the opportunity; it is not a validated rule.'))
add(P(f'**What the lenient grade forgives.** On set 3, {_lk["lenient_only"]} answers are wrong under the strict rule but right under the lenient one. Judged by hand, {_lk["a"]} are harmless (an equivalent label, such as an internal claim key where the reference shows the claim number), {_lk["b"]} lose an identity the question asked for (a name column that is NULL, so the numbers cannot be attributed), and {_lk["c"]} carry a different meaning despite matching numbers (for example a premium computed from amounts typed "Year" that happen to equal the premium rows, or a column labelled as an assessment result that holds a role code). None of the {_lk["lenient_only"]} is a trusted answer, so the lenient grade does not change trust precision. In {_case} of them the answer differs from the reference only in letter case (one band label written "More than 15 miles"); the strict rule compares text case-sensitively. Table 12 gives one example of each kind.'))
_ex = []
_kind = {'a': 'Harmless label', 'b': 'Identity lost', 'c': 'Different meaning'}
for k in 'abc':
    p = T2['picks'][k][0]
    j = p.get('judgement', '')
    j = j.split('. ', 1)[1] if '. ' in j else j
    _ex.append([_kind[k], f"{p.get('model_label', '')}, {p.get('condition', '')}", (p.get('question', '')[:150] + ('…' if len(p.get('question', '')) > 150 else '')), j[:230] + ('…' if len(j) > 230 else '')])
add(TABLE(['Kind', 'Model, condition', 'Question (set 3)', 'Judgement'], _ex, [1400, 1700, 3200, 3060], ['left', 'left', 'left', 'left']))
add(CAP('**Table 12.** Strict-wrong, lenient-right answers on the public set 3, one per kind; the full list with rows is in the benchmark repository (analysis/insurance-2026-09-29/taxonomy).'))

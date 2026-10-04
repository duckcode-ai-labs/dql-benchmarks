# Section 4.5, generated from ../audit/audit_results.json (AUDR) and ../audit/audit_sensitivity.json (AUD);
# exec'd by paper_docx.py.
_a4, _a5 = AUDR['sets']['4'], AUDR['sets']['5']
_sl = AUDR['second_look']
_up = lambda e: pct(e['wrong_rate_wilson'][1])
_ndis = sum(_sl['items_with_disagreement'].values())
_amb = sum(e[k]['ambiguous'] for e in (_a4, _a5) for k in ('answerable', 'unanswerable'))
_w4u = _a4['unanswerable']['wrong']
add(P('We audited the development-set reference answers and marked three as disputed: a loss ratio the question does not define, a column the question does not request, and a list where one total per policy is a fair reading.'))
add(P(f'For the sealed sets, an author (a person, not an AI system) audited a random sample against written criteria (insurance/audit/AUDIT-INSTRUCTIONS.md) after the systems had been run and DQL frozen: for set 4, {_a4["answerable"]["n"]} answerable items (25 per grid cell, seed {_a4["seed"]}) and {_a4["unanswerable"]["n"]} unanswerable; for set 5, the pre-registered 25% ({_a5["answerable"]["n"]} answerable and {_a5["unanswerable"]["n"]} unanswerable, seed {_a5["seed"]}). All {_a4["answerable"]["correct"]} sampled answerable set-4 references and all {_a5["answerable"]["correct"]} set-5 references were judged correct, which bounds the share of wrong answerable references at {_up(_a4["answerable"])} for set 4 and {_up(_a5["answerable"])} for set 5 (upper 95% Wilson limits). '
      + (f'One of the {_a4["unanswerable"]["n"]} sampled set-4 unanswerable items was judged wrong, because the data can answer it (Wilson {ci(_a4["unanswerable"]["wrong_rate_wilson"])}); ' if _w4u == 1 else f'{_w4u} of the {_a4["unanswerable"]["n"]} sampled set-4 unanswerable items were judged wrong (Wilson {ci(_a4["unanswerable"]["wrong_rate_wilson"])}); ')
      + f'{"none" if not _a5["unanswerable"]["wrong"] else _a5["unanswerable"]["wrong"]} of the {_a5["unanswerable"]["n"]} set-5 unanswerable items {"was" if not _a5["unanswerable"]["wrong"] else "were"}. '
      + ('No sampled item was judged ambiguous. ' if not _amb else f'{_amb} sampled items were judged ambiguous. ')
      + f'Two AI models ({" and ".join(_sl["models"])}) also looked over the samples as a second check; on the {_ndis} items where one of them disagreed, the author re-examined the item and kept the verdict. The audit bounds the error rate of the references; it does not check every item.'))
_ew, _ewa, _aa = AUD['readings']['excluding wrong'], AUD['readings']['excluding wrong or ambiguous'], AUD['readings']['all items']
_same = all(_ew['paired'][f] == _aa['paired'][f] and _ewa['paired'][f] == _aa['paired'][f] for f in ('vs_A', 'vs_P', 'W2_vs_Am'))
_ans_same = all(_ew['answerable'][c] == _aa['answerable'][c] and _ewa['answerable'][c] == _aa['answerable'][c] for c in _aa['answerable'])
_ag = lambda r: (f'{r["unanswerable"]["A"]["k"]} for each agent' if r['unanswerable']['A']['k'] == r['unanswerable']['Am']['k']
                 else f'{r["unanswerable"]["Am"]["k"]} for A-model and {r["unanswerable"]["A"]["k"]} for the agent')
add(P(f'Before the audit, an author had adjudicated two set-4 items in a preliminary review with an AI assistant. The first asks which policy earns more premium per day of its term; it was marked ambiguous because "earns" can mean actuarial earned premium, which the data cannot give. It fell in the audit sample, and in the full audit, against the written criterion (the reference answers the question as a reasonable insurance analyst would read it), the author judged its reference correct, revising that decision; the actuarial reading remains possible. The second, an unanswerable question about the average payout for an accident year with no claims, is outside the sample and stays ambiguous: an answer explaining that the average is undefined is as defensible as the refusal the key requires. As pre-registered for set 5, and likewise for set 4, we report results on all items and without items found wrong. '
      + ('On set 4 the wrong item is unanswerable, so no answerable result changes' if _ans_same else 'On set 4 some answerable results change')
      + f'; without it, W2 abstains correctly on {_ew["unanswerable"]["W2"]["k"]} of {_ew["unanswerable"]["W2"]["n"]} unanswerable questions against {_ag(_ew)}, and without the ambiguous item as well, on {_ewa["unanswerable"]["W2"]["k"]} of {_ewa["unanswerable"]["W2"]["n"]} against {_ag(_ewa)}. '
      + ('No paired comparison in Section 6 changes. ' if _same else 'Some paired comparisons change (audit/audit_sensitivity.md). ')
      + 'The author also confirmed the elapsed-days convention the references use (1 January to 2 January is one day). '
      + ('On set 5 no sampled item was found wrong, so its two scorings coincide (Section 6.1).' if not (_a5['answerable']['wrong'] + _a5['unanswerable']['wrong']) else 'Set 5 is reported both ways (Section 6.1).')))

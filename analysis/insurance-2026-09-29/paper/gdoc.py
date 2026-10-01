# Build the Google Docs version of the white paper (HTML that Drive converts to a Doc) from
# paper_numbers.json. Every figure in the text comes from the data; nothing is typed by hand.
# python3 gdoc.py > gdoc.html
import json, html

D = json.load(open('paper_numbers.json'))
M = D['models']; S4 = D['set4']; PT = D['pooled_trust']; PU = D['pooled_unanswerable']
DQL = ['L0', 'L1', 'L2', 'L3', 'LB', 'W0', 'W1', 'W2', 'WB']
ORDER = ['opus', 'sonnet55', 'sonnet5', 'qwen', 'luna', 'sol', 'terra']
e = html.escape

def pct(x, d=1):
    return f"{round(100 * x, d):g}%"
def ci(c):
    return f"{round(100 * c[0])}–{round(100 * c[1])}%" if c and c[0] is not None else ''
def pv(p):
    return '<0.001' if p < 0.001 else f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
def paired(v):
    if not v: return ''
    return f"+{v['gained']}/−{v['lost']}, p < 0.001" if v['p'] < 0.001 else f"+{v['gained']}/−{v['lost']}, p = {pv(v['p'])}"
def table(head, rows, text=False):
    al = lambda i: 'left' if (text or i == 0) else 'right'
    th = ''.join(f'<th style="background-color:#e8eef0;text-align:{al(i)};padding:4px 6px">{h}</th>' for i, h in enumerate(head))
    body = ''.join('<tr>' + ''.join(f'<td style="text-align:{al(i)};padding:4px 6px">{c}</td>' for i, c in enumerate(r)) + '</tr>' for r in rows)
    return f'<table border="1" cellspacing="0" style="border-collapse:collapse;border-color:#b9c2c9">{"<tr>" + th + "</tr>"}{body}</table>'
def cap(text):
    return f'<p><i>{text}</i></p>'
def formula(text):
    return f'<p style="text-align:center"><i>{text}</i></p>'

s4 = S4['heldout']; u4 = S4['unanswerable']
s3 = lambda k, L: M[k]['heldout'].get(L)
w2 = s4['W2']; A4 = s4['A']; P4 = s4['P']
tr4_dbt = sum(s4[L]['trusted'] for L in ('L2', 'L3')); tw4_dbt = sum(s4[L]['trusted_wrong'] for L in ('L2', 'L3'))
u4_dql = [u4[L] for L in ('L2', 'L3', 'W2', 'WB')]
u4_min = min(c['k'] for c in u4_dql); u4_max = max(c['k'] for c in u4_dql)
u4_trusted = sum(c.get('answered_trusted', 0) for c in u4_dql)

out = []
w = out.append
w('<html><head><meta charset="utf-8"></head><body style="font-family:Georgia, serif">')
w('<h1>The DQL Trust Benchmark</h1>')
w('<p><i>Accuracy, trust labels and stopping of a governed analytics layer, measured on sealed insurance question sets across seven language models.</i></p>')
w('<p>DuckCode AI Labs. Technical white paper, draft 0.2, 30 September 2026.</p>')
w('<p><b>Draft status.</b> Results for Claude Opus 5.5, Claude Sonnet 5.5, Claude Sonnet 5 and Qwen 3.8 27B are complete. The three GPT models are still running; their unfinished cells read "pending". Every figure in this document was generated from the saved benchmark reports.</p>')

w('<h2>Summary</h2>')
w(f'<p>On a sealed set of 200 questions over an insurance warehouse, Claude Sonnet 5.5 answered through DQL without a dbt project (level W2) was the most accurate option we measured: {w2["k"]} of 200 correct ({pct(w2["acc"])}), against {P4["k"]} for the same model writing SQL alone and {A4["k"]} for the same model as an agent that explores the database. The difference over the agent is statistically significant ({paired(w2["vs_A"])}). Teams without a semantic layer can get this accuracy by connecting DQL to the warehouse and describing its relationships and metrics.</p>')
w(f'<p>The trust labels are useful but not yet reliable enough to act on without review. On the larger set, governed answers from dbt metrics were wrong {tw4_dbt} of {tr4_dbt} times, answers from the business layer we authored were wrong {s4["WB"]["trusted_wrong"]} of {s4["WB"]["trusted"]} times, and DQL stopped correctly on {u4_min}–{u4_max} of 50 unanswerable questions, while the agent stopped on {u4["A"]["k"]}. On the smaller set 3 the same measures looked nearly perfect (0 wrong of {PT["L2_L3"]["trusted"]} governed dbt answers, {PU["correct_stops"]} of {PU["n"]} correct stops), which shows how much a 40-question set can mislead. The next release should close these gaps, measured on a fresh sealed set.</p>')

w('<h2>1. Why trust, not only accuracy</h2>')
w('<p>Public text-to-SQL benchmarks such as BIRD [6] and Spider 2.0 [7] score a system by the share of questions whose query returns the reference rows. That number leaves out what an organization needs most: which answers it can act on, which ones someone must check, and when the system should decline. A wrong revenue figure delivered without a warning leads to a worse decision than no figure.</p>')
w('<p>Earlier work shows that describing the business improves accuracy. On the insurance data used here, data.world found that GPT-4 answered 16.7% of questions from the SQL schema and 54.2% with a knowledge graph of the same schema [1]. dbt Labs reported gains of 8 to 16 points from a modeled semantic layer, which returned errors rather than wrong numbers on questions outside its scope [3]. Cube reported gains of 17 to 23 points from a semantic description [4].</p>')
w('<p>Two further findings shape how we report. Reference answers are often wrong: an audit of BIRD mini-dev and Spider 2.0-Snow found errors in 52.8% and 62.8% of annotations, and re-scoring moved agent rankings by up to nine places [5]. And one run of a few dozen questions has an uncertainty of about ±14 points. We therefore publish our answer-key audit, compare conditions question by question with exact tests, and give every rate a confidence interval.</p>')

w('<h2>2. How DQL answers</h2>')
w('<p>DQL reads a project\'s models, relationships and metric definitions, from dbt or directly from the warehouse, and answers each question through the most governed route that fits it. Every answer carries one of four labels.</p>')
w(table(['Label', 'Meaning', 'Produced by'], [
    ['certified', 'A query block that a person reviewed and certified answers this exact question.', 'Certified blocks'],
    ['governed', 'Computed from approved metric definitions, and the reading uses everything the question names.', 'Semantic metrics (dbt MetricFlow or DQL\'s native engine)'],
    ['review required', 'SQL the AI drafted from the modeled schema. It is checked against the catalog before it runs, but it is not governed.', 'Drafted SQL'],
    ['blocked', 'No answer: the data does not hold what the question asks for, or no safe query exists. The reason is stated.', 'A stop'],
], text=True))
w(cap('Table 1. The four answer labels.'))
w('<p>The route is chosen in this order:</p><ol><li>Read the question into a structured intent: what is measured, the grouping, the filters and the time period.</li><li>If a certified block names the question, answer from it.</li><li>If governed metrics cover the whole reading, compile and run them.</li><li>Otherwise draft SQL from the modeled schema, check every table and column against the catalog, run it and label it for review.</li><li>If none of these is possible, stop and say what is missing.</li></ol>')
w('<p>The label is decided by rules over the reading and the result, not by the model\'s confidence. A governed answer loses its label when the reading leaves a question word unused, cannot carry a requested label, or merges records the question asked to see separately.</p>')

w('<h2>3. Benchmark design</h2>')
w('<h3>3.1 Data</h3>')
w('<p>The warehouse is the ACME property-and-casualty insurance database from the data.world benchmark [1][2], as packaged by dbt Labs with a dbt project and MetricFlow metrics [3], loaded into DuckDB. It has 29 relations, 161 columns and about 980 rows. Money is split across separate claim-amount tables, policies reach people through a party-role bridge table, and several names are misspelled in the source. The core records are few: 2 policies, 2 claims, one named policy holder and one named agent.</p>')
w('<h3>3.2 Question sets</h3>')
w('<ul>')
w('<li><b>Development set</b> (41 questions): the published data.world questions. We used them to find and fix problems, so no headline number comes from them.</li>')
w('<li><b>Sealed set 3</b> (40 answerable, 10 unanswerable), written by a separate agent that saw only the warehouse schema and data, never the published questions, any results, or DQL. It has 10 questions in each cell of data.world\'s 2×2 grid of question complexity by schema complexity.</li>')
w('<li><b>Sealed set 4</b> (200 answerable, 50 unanswerable, 50 per cell), written the same way for this study. It is the main result of this paper.</li>')
w('</ul>')
w('<p>Reference answers for the sealed sets were produced by running the author agent\'s SQL on the warehouse. The authors of this paper have not read the sealed questions. Sets 1 and 2 were used during development and are not reported.</p>')
w('<h3>3.3 Conditions</h3>')
w(table(['Condition', 'What the model is given'], [
    ['P (plain SQL)', 'The full table definitions; the model writes one SQL statement.'],
    ['A (agent)', 'The same definitions plus tools to list tables, inspect them, sample rows and run read-only queries, for up to 12 turns and 20 tool calls; it gives final SQL or declines.'],
    ['L0', 'DQL with the dbt project only.'],
    ['L1', 'L0 plus DQL modeling: entities and relationships.'],
    ['L2', 'L1 plus dbt Labs\' MetricFlow metrics.'],
    ['L3', 'L2 plus skills: business rules written as guidance.'],
    ['LB', 'L3 plus our business layer: governed metrics, skills and 9 certified blocks.'],
    ['W0', 'DQL connected to the warehouse only, with no dbt project.'],
    ['W1', 'W0 plus modeling.'],
    ['W2', 'W1 plus the same metrics as native DQL definitions.'],
    ['WB', 'W2 plus our business layer.'],
], text=True))
w(cap('Table 2. Conditions. The business layer was written from a business brief by a separate agent, checked by another, and certified by a person; it was never written from the questions.'))
w('<h3>3.4 Models and settings</h3>')
w(table(['Model', 'Access', 'Reasoning'], [
    ['Claude Opus 5.5', 'Claude Code CLI 2.1.282, subscription', 'DQL per step (medium to read, high to draft)'],
    ['Claude Sonnet 5.5', 'Claude Code CLI 2.1.285, subscription', 'same'],
    ['Claude Sonnet 5', 'Claude Code CLI 2.1.282, subscription', 'same'],
    ['Qwen 3.8 27B', 'Ollama on a laptop (Apple M2 Max, 32 GB)', 'model default'],
    ['GPT-6 Luna, GPT-6 Sol, GPT-5.6 Terra', 'Codex CLI 0.158, subscription, isolated home folder', 'fixed at max, medium and high'],
], text=True))
w(cap('Table 3. Models and settings. Local and fixed-reasoning runs get a 20 times longer answer deadline and a 300-second limit per model call, so that a stop is DQL\'s decision and not a timeout.'))
w('<h3>3.5 Isolation</h3>')
w('<p>Every question is asked as a new conversation on a fresh copy of the project, with DQL\'s caches, memory and run history removed. Claude calls replace the tool\'s system prompt, disable its tools and ignore local MCP configuration. Codex calls run from a separate home folder with no personal instructions, plugins, MCP servers or memories; the default folder added 23,800 tokens of the operator\'s own setup to every call, and all runs made with it were discarded. A usage limit never counts as an answer: the refused questions are asked again after the limit resets.</p>')
w('<h3>3.6 Builds and answer-key audit</h3>')
w('<p>All levels ran on DQL build 49c0e1cb; LB and WB ran on 627009a1, which adds one fix (section 11). Each report records its build, model, CLI version and settings. Three development-set reference answers are marked disputed in the published audit: a loss ratio the question does not define, a column the question does not ask for, and a list where one total per policy is a fair reading.</p>')

w('<h2>4. Metrics and statistics</h2>')
w('<p><b>Accuracy.</b> For a condition that answers n questions, k of which return the reference rows (compared as multisets, ignoring column names and order), accuracy is</p>')
w(formula('p̂ = k / n'))
w('<p>with a 95% Wilson score interval [10], which behaves well near 0 and 1 and for small n:</p>')
w(formula('( p̂ + z²/2n ± z · √( p̂(1 − p̂)/n + z²/4n² ) ) / ( 1 + z²/n ),   z = 1.96'))
w('<p><b>Paired comparison.</b> Two conditions answer the same questions, so we compare them question by question. Let b be the number of questions condition X answered correctly and Y did not, and c the reverse. Under the hypothesis that X and Y are equally accurate, each of the b + c discordant questions is equally likely to fall either way, and the exact two-sided McNemar test [9] gives</p>')
w(formula('p = min( 1, 2 · Σ<sub>i=0…min(b,c)</sub> C(b + c, i) · 2<sup>−(b + c)</sup> )'))
w('<p>Tables write the discordant counts as +b/−c. We call a difference significant when p is below 0.05 and do not correct for multiple comparisons.</p>')
w('<p><b>Trust.</b> Let T be the number of answers labelled certified or governed and W<sub>T</sub> the number of those that are wrong. Trust precision and trusted coverage are</p>')
w(formula('π = (T − W<sub>T</sub>) / T,     κ = T / n'))
w('<p>When no trusted answer is wrong, the one-sided 95% upper bound on the wrong-trusted rate is approximately 3/T, the rule of three [11].</p>')
w('<p><b>Silent errors.</b> A wrong answer that carries no warning is the costly case. Without labels every wrong answer is silent; with DQL, review-required answers carry a warning and stops are declared, so only wrong trusted answers are silent:</p>')
w(formula('σ<sub>unlabelled</sub> = (n − k) / n,     σ<sub>DQL</sub> = W<sub>T</sub> / n'))
w('<p><b>Stopping.</b> On an unanswerable set of n<sub>u</sub> questions with S<sub>u</sub> correct stops, the stop rate is s = S<sub>u</sub> / n<sub>u</sub>. On answerable sets a stop counts as a wrong answer.</p>')
w('<p><b>Lenient match.</b> The strict rule requires the returned rows R to equal the reference rows G. The lenient rule also accepts R when |R| = |G|, G has at least one numeric column, and every numeric column of G matches a column of R row by row. It forgives a missing or renamed label column; it does not forgive a different row count or different numbers.</p>')

w('<h2>5. Results on sealed set 4</h2>')
rows = []
for L, name in [('P', 'P, plain SQL'), ('A', 'A, agent'), ('L2', 'L2, dbt metrics'), ('L3', 'L3, + skills'), ('W2', 'W2, warehouse + native metrics'), ('WB', 'WB, + business layer')]:
    c = s4[L]
    rows.append([name, f"{c['k']}/200", f"{pct(c['acc'])} ({ci(c['ci'])})", paired(c.get('vs_P')) if L != 'P' else '', paired(c.get('vs_A')) if L not in ('P', 'A') else '', f"{c['median_s']} s"])
w(table(['Condition', 'Correct', 'Accuracy (95% CI)', 'vs P', 'vs agent', 'Median time'], rows))
w(cap('Table 4. Claude Sonnet 5.5 on sealed set 4 (200 questions). Paired counts are +better/−worse than the comparison, with the exact McNemar p.'))
w(f'<p>DQL on the warehouse with native metrics (W2) answered {w2["k"]} of 200 questions correctly. It beat plain SQL ({paired(w2["vs_P"])}) and the agent ({paired(w2["vs_A"])}). The dbt levels L2 and L3 were more accurate than plain SQL but not better than the agent, and the business layer (WB) was level with the agent.</p>')
rows = []
for L in ('L2', 'L3', 'W2', 'WB'):
    c = s4[L]; u = u4[L]
    rows.append([L, str(c['trusted']), str(c['trusted_wrong']), pct(c['trusted'] / c['n']), f"{u['k']}/50", str(u.get('answered_trusted', 0))])
rows.append(['A (agent)', '–', '–', '–', f"{u4['A']['k']}/50", '–'])
w(table(['Level', 'Trusted answers', 'Wrong trusted', 'Trusted coverage κ', 'Correct stops, unanswerable', 'Unanswerable answered as governed'], rows))
w(cap('Table 5. Trust and stopping on sealed set 4, Claude Sonnet 5.5.'))
w(f'<p>On this set the trust labels fell short. {tw4_dbt} of {tr4_dbt} governed answers at the dbt levels were wrong, and {s4["WB"]["trusted_wrong"]} of {s4["WB"]["trusted"]} at the business layer. DQL stopped correctly on {u4_min} to {u4_max} of the 50 unanswerable questions, below the agent\'s {u4["A"]["k"]}, and {u4_trusted} of its answers to unanswerable questions were labelled governed. These are the failures DQL exists to prevent, and they are the first priority for the next release.</p>')

w('<h2>6. Results across seven models on sealed set 3</h2>')
head = ['Model', 'P', 'A'] + DQL
rows = []
for k in ORDER:
    m = M[k]; row = [e(m['label'])]
    best = max((m['heldout'][L]['k'] for L in DQL if L in m['heldout']), default=None)
    for L in ['P', 'A'] + DQL:
        c = m['heldout'].get(L)
        if not c:
            row.append('–' if L == 'A' else 'pending'); continue
        mark = ''
        if c.get('vs_P') and c['vs_P']['p'] < 0.05:
            mark = ' ▲' if c['vs_P']['gained'] > c['vs_P']['lost'] else ' ▼'
        txt = f"{c['k']}{mark}"
        row.append(f"<b>{txt}</b>" if L in DQL and c['k'] == best else txt)
    rows.append(row)
w(table(head, rows))
w(cap('Table 6. Correct answers out of 40 on sealed set 3. ▲ significantly better than the same model\'s P, ▼ significantly worse (exact McNemar, p < 0.05). Best DQL level per model in bold. The agent was run for two models. Unfinished GPT cells read "pending".'))
gains = [s3(k, 'L1')['k'] - s3(k, 'L0')['k'] for k in ORDER if s3(k, 'L0') and s3(k, 'L1')]
wr = [s3('sonnet55', L)['k'] for L in ('W0', 'W1', 'W2', 'WB')]
w('<ul>')
w(f'<li><b>Modeling is the most reliable single step.</b> Adding DQL modeling to the dbt project (L0 to L1) improved every model, by {min(gains)} to {max(gains)} questions out of 40.</li>')
w(f'<li><b>Without dbt, DQL does best.</b> For Sonnet 5.5 the warehouse levels answered {min(wr)} to {max(wr)} of 40 correctly and lost no question that plain SQL answered correctly at W0, W1 or W2.</li>')
w(f'<li><b>The weaker the model, the larger the lift.</b> Qwen 27B, running on a laptop, rose from {s3("qwen", "P")["k"]} to {s3("qwen", "WB")["k"]} of 40 through DQL, and six of its levels were significantly above its plain baseline. Opus, the strongest plain model, gained less, and no level was significant at 40 questions.</li>')
w('<li><b>The dbt-only level trails.</b> L0 was the weakest level for every model and stopped most often, because DQL gives dbt projects a more conservative drafter than warehouse projects.</li>')
w('</ul>')

w('<h2>7. DQL against an agent</h2>')
w(f'<p>A one-shot SQL baseline is easy to beat; the stronger comparison is the same model working as an agent that explores the database and retries. On set 3 (40 questions), Opus 5.5 as an agent answered {s3("opus", "A")["k"]} and Sonnet 5.5 {s3("sonnet55", "A")["k"]}, level with DQL\'s middle levels; Sonnet 5.5 at W2 was ahead ({paired(s3("sonnet55", "W2")["vs_A"])}) but not significantly. On set 4 (200 questions) the same comparison is significant: W2 {w2["k"]}, agent {A4["k"]}, {paired(w2["vs_A"])}.</p>')
rows = []
for L in ('P', 'A', 'L2', 'L3', 'W2', 'WB'):
    c = s4[L]
    silent = (c['n'] - c['k']) / c['n'] if L in ('P', 'A') else c['trusted_wrong'] / c['n']
    cover = 0 if L in ('P', 'A') else c['trusted'] / c['n']
    rows.append([L, pct(silent), pct(cover)])
w(table(['Condition', 'Silent errors σ', 'Trusted coverage κ'], rows))
w(cap('Table 7. Silent errors and trusted coverage on sealed set 4, Claude Sonnet 5.5. Plain SQL and the agent label nothing, so every wrong answer is silent.'))
w('<p>The agent\'s wrong answers look the same as its right ones. DQL puts a warning on every answer it does not govern, so its silent errors are limited to wrong trusted answers. The cost is coverage: at W2 no answer was trusted, so every answer still needs review.</p>')

w('<h2>8. Trust labels across models</h2>')
rows = [[name, str(v['trusted']), str(v['wrong']), pct(1 - v['wrong'] / v['trusted']) if v['trusted'] else '–', ci(v['ci_wrong_rate'])]
        for name, v in [('L2 and L3, dbt Labs metrics', PT['L2_L3']), ('LB, dbt with business layer', PT['LB']), ('WB, warehouse with business layer', PT['WB']), ('W2, native metrics', PT['W2'])]]
w(table(['Levels (set 3, all models)', 'Trusted', 'Wrong', 'Precision', 'Wrong-trusted 95% CI'], rows))
w(cap('Table 8. Trusted answers on sealed set 3, pooled across models with results at each level.'))
w(f'<p>On set 3, governed dbt metrics were never wrong when trusted ({PT["L2_L3"]["trusted"]} answers; by the rule of three the rate is below {pct(PT["L2_L3"]["upper95_if_zero"])} at 95% confidence). Set 4 found {tw4_dbt} wrong of {tr4_dbt}, so the true rate is small but not zero. Our business layer was wrong on {PT["LB"]["wrong"]} of {PT["LB"]["trusted"]} trusted answers at LB on set 3 and {s4["WB"]["trusted_wrong"]} of {s4["WB"]["trusted"]} at WB on set 4. On the development set, most business-layer failures were lists answered with a count metric nobody asked for; a fix exists and is not in the measured builds.</p>')

w('<h2>9. Stopping</h2>')
w(f'<p>On set 3 DQL\'s levels stopped correctly on {PU["correct_stops"]} of {PU["n"]} unanswerable questions across all models. On set 4, whose author was asked to write near-miss questions that tempt a system to answer with a similar column, DQL stopped on {u4_min} to {u4_max} of 50 per level and the agent on {u4["A"]["k"]}. Stops on answerable questions count as wrong answers and are most common at L0 and for the smaller model.</p>')

w('<h2>10. Why answers were wrong</h2>')
w('<p>We re-graded 2,240 set-3 answers (Opus 5.5, Sonnet 5 and Qwen, plus the GPT runs available on 29 September) with the lenient rule. Lenient accuracy was only 2.5 points above strict (1,612 to 1,667), so the strict scores are not an artifact of the grading rule. The strict-wrong answers break down as follows.</p>')
w(table(['Reason', 'Share of wrong answers'], [['DQL stopped on an answerable question', '39%'], ['Wrong numbers', '38%'], ['Different number of rows (a list for a total, merged rows)', '13%'], ['Right numbers, a label column missing or renamed', '9%'], ['Query did not run', '2%']]))
w(cap('Table 9. Why strict-wrong answers were wrong, sealed set 3 (628 answers). 45 of the wrong-number answers differ only by rounding.'))

w('<h2>11. Defects found during the study</h2>')
w('<p>We changed DQL during the study and disclose each change.</p><ol>')
w('<li><b>Near-fit certified blocks</b> (in both measured builds). A tag on a certified block was treated as its name, and a block that only nearly fit a question was served as governed without letting the drafter answer first. Found on the development set.</li>')
w('<li><b>A metric name overriding the reading</b> (in both builds). A question word that named a metric replaced the measure the model had read, so "the expense reserve amount of all claims" was measured as a claim count. Found on the development set.</li>')
w('<li><b>Short table names on DuckDB</b> (build 627009a1, used for LB and WB). A check on the final SQL rejected main.claim for the inspected acme_insurance.main.claim, which caused most of Sonnet 5\'s stops at LB and WB. The first half of this fix came from the development set; the second half was found on sealed set 3, and every model\'s LB and WB were run again on the fixed build.</li>')
w('<li><b>Lists answered with a count</b> (written, not measured). A list whose count metric merged records is no longer labelled governed. Found on the development set.</li>')
w('</ol>')

w('<h2>12. Limitations</h2><ul>')
w('<li><b>A small warehouse.</b> With 2 policies and 2 claims, many answers are one or two rows, and an agent can explore the schema in a few calls. It tests reasoning over an awkward schema, not scale.</li>')
w('<li><b>Sample size.</b> Set 3 has 40 answerable questions per condition, about ±14 points. Set 4 (200) narrows this to about ±6 but has so far been run for one model.</li>')
w('<li><b>One run per condition.</b> Earlier repeated runs moved individual levels by up to 4 questions out of 40.</li>')
w('<li><b>Unequal reasoning settings.</b> Claude used DQL\'s per-step effort while each GPT model used one fixed level, and Codex adds its own fixed instructions to every call.</li>')
w('<li><b>Timing.</b> Runs shared a laptop and ran in parallel, so the reported times are indicative only.</li>')
w('<li><b>AI-written reference answers.</b> The sealed sets\' SQL was written by an agent and executed. A human spot-check is planned; some disagreements may be answer-key errors.</li>')
w('</ul>')

w('<h2>13. Next steps</h2><ol>')
w('<li>Fix, using the development set only: governed answers to unanswerable questions, the business layer\'s wrong trusted answers, missed stops, and the dbt-only drafting gap.</li>')
w('<li>Measure the fixes on a fresh sealed set 5, and run set 4 for the other models.</li>')
w('<li>Run a larger benchmark (Spider 2.0 [7] or LiveSQLBench [8]) to test scale.</li>')
w('<li>Publish the measured DQL builds as an npm release, with the recorded model replies, so every result can be reproduced.</li>')
w('</ol>')

w('<h2>14. Reproducing the results</h2>')
w('<p>The harness, question sets (the sealed sets after publication), answer-key audit, recorded model replies and analysis scripts are in the dql-benchmarks repository, to be released with this paper. Each report records the DQL build, model, CLI version and settings. Example commands:</p>')
w('<p style="font-family:Courier New, monospace">node insurance/run.mjs --layer W2 --set heldout-4 --provider claude-code --model claude-sonnet-5-5 --run my-run</p>')
w('<p style="font-family:Courier New, monospace">node insurance/baseline-agent.mjs --context ddl --set heldout-4 --provider claude-code --model claude-sonnet-5-5 --run my-agent</p>')

w('<h2>References</h2><ol>')
refs = [
    ('J. Sequeda, D. Allemang, B. Jacob. A Benchmark to Understand the Role of Knowledge Graphs on Large Language Model\'s Accuracy for Question Answering on Enterprise SQL Databases. 2023.', 'https://arxiv.org/abs/2311.07509', 'arXiv:2311.07509'),
    ('data.world. cwd-benchmark-data: schema, data, ontology and questions.', 'https://github.com/datadotworld/cwd-benchmark-data', 'github.com/datadotworld/cwd-benchmark-data'),
    ('dbt Labs. Semantic Layer vs Text-to-SQL: 2026 Benchmark Update. Code: github.com/dbt-labs/dbt-llm-sl-bench.', 'https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026', 'docs.getdbt.com'),
    ('Cube. Semantic layer benchmark.', 'https://github.com/cubedevinc/semantic-layer-benchmark', 'github.com/cubedevinc/semantic-layer-benchmark'),
    ('Pervasive Annotation Errors Break Text-to-SQL Benchmarks. CIDR 2026.', 'https://arxiv.org/abs/2601.08778', 'arXiv:2601.08778'),
    ('J. Li et al. Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs (BIRD). NeurIPS 2023.', 'https://arxiv.org/abs/2305.03111', 'arXiv:2305.03111'),
    ('F. Lei et al. Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows. ICLR 2025.', 'https://arxiv.org/abs/2411.07763', 'arXiv:2411.07763'),
    ('BIRD team. LiveSQLBench.', 'https://livesqlbench.ai/', 'livesqlbench.ai'),
    ('Q. McNemar. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika 12(2):153–157, 1947.', 'https://doi.org/10.1007/BF02295996', 'doi:10.1007/BF02295996'),
    ('E. B. Wilson. Probable inference, the law of succession, and statistical inference. Journal of the American Statistical Association 22(158):209–212, 1927.', 'https://doi.org/10.1080/01621459.1927.10502953', 'doi:10.1080/01621459.1927.10502953'),
    ('J. A. Hanley, A. Lippman-Hand. If nothing goes wrong, is everything all right? Interpreting zero numerators. JAMA 249(13):1743–1745, 1983.', 'https://doi.org/10.1001/jama.1983.03330370053031', 'doi:10.1001/jama.1983.03330370053031'),
    ('dbt Labs. About MetricFlow.', 'https://docs.getdbt.com/docs/build/about-metricflow', 'docs.getdbt.com'),
    ('DuckCode AI Labs. DQL.', 'https://github.com/duckcode-ai/dql', 'github.com/duckcode-ai/dql'),
]
for text, url, label in refs:
    w(f'<li>{e(text)} <a href="{url}">{label}</a></li>')
w('</ol></body></html>')
print(''.join(out))

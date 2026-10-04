# Build the research paper as a .docx (standard library only) for upload to Google Drive and
# conversion to Google Docs, then export to PDF for arXiv. Every number comes from
# stats_v2/stats_v2.json (question-level bootstrap, Holm, lenient re-grade); median times and model
# labels come from paper_numbers.json. Equations are OMML, figures SVG -> PNG via Quick Look.
#   python3 paper_docx.py   -> paper.docx (+ fig*.svg / fig*.png)
import json, math, os, subprocess, zipfile, html
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, 'stats_v2', 'stats_v2.json')))
D = json.load(open(os.path.join(HERE, 'paper_numbers.json')))
LAB = {k: v['label'] for k, v in D['models'].items()}
MED4 = {k: v.get('median_s') for k, v in D['set4']['heldout'].items()}
DQL = ['L0', 'L1', 'L2', 'L3', 'LB', 'W0', 'W1', 'W2', 'WB']
ORDER = ['opus', 'sonnet55', 'sonnet5', 'qwen', 'luna', 'sol', 'terra']
AC3, U3 = S['accuracy']['heldout-3'], S['accuracy']['heldout-3-unanswerable']
AC4, U4 = S['accuracy']['heldout-4']['sonnet55'], S['accuracy']['heldout-4-unanswerable']['sonnet55']
T4, PR4, PR3, PO, RG = S['trust']['heldout-4'], S['set4_paired'], S['set3_paired'], S['pooled'], S['regrade']['pooled']
HAS_AM = 'Am' in AC4
C4 = ['P', 'A'] + (['Am'] if HAS_AM else []) + ['L2', 'L3', 'W2', 'WB']
NAME = {'P': 'P, one-shot SQL', 'A': 'A, agent', 'Am': 'A-model, agent + modeling', 'L2': 'L2, dbt metrics', 'L3': 'L3, + skills',
        'W2': 'W2, warehouse + native metrics', 'WB': 'WB, + business layer'}
a3 = lambda m, c: AC3.get(m, {}).get(c)

def pct(x, d=1): return f"{round(100 * x, d):g}%"
def ci(c, d=1): return f"{round(100 * c[0], d):g}–{round(100 * c[1], d):g}%" if c and c[0] is not None else '–'
def pstr(p):
    if p < 0.001: return 'p < 0.001'
    return f"p = {min(p, 1):.3f}" if p < 0.01 else f"p = {min(p, 1):.2f}"
def dpt(t): return f"{'+' if t['diff'] >= 0 else '−'}{abs(100 * t['diff']):.1f}"
def dci(t):
    lo, hi = t['diff_bootstrap']['ci']
    f = lambda v: f"{'+' if v >= 0 else '−'}{abs(100 * v):.1f}"
    return f"{f(lo)} to {f(hi)}"
def ptest(t, holm=True): return f"{dpt(t)} pts ({pstr(t['p_holm'] if holm else t['p_raw'])})"

W2, A4, P4 = AC4['W2'], AC4['A'], AC4['P']
tW2A, tW2P = PR4['vs_A']['W2'], PR4['vs_P']['W2']
LEN = PR4['sensitivity']['lenient']
dbt4 = PO['trust_heldout4']['L2_L3']
u4k = {L: U4[L]['k'] for L in ('L2', 'L3', 'W2', 'WB')}
u4gov = sum(T4[L].get('unanswerable_answered_trusted', 0) for L in ('L2', 'L3', 'W2', 'WB'))
pt3 = PO['trust_heldout3']
st3 = PO['correct_stop_heldout3_unanswerable']['pooled']
st4 = PO['correct_stop_heldout4_unanswerable']['pooled']
VAR = json.load(open(os.path.join(HERE, '..', 'variants', 'variants.json')))
VP = VAR['pooled']
N_GRADED = sum(c['n'] for c in S['regrade']['cells'])
N_INCONS = sum(c.get('strict_but_inconsistent_columns', 0) for c in S['regrade']['cells'])
N_STRICT = sum(c['strict'] for c in S['regrade']['cells'])
N_UNVER = sum(c.get('strict_unverifiable_rows', 0) for c in S['regrade']['cells'])
AUD = json.load(open(os.path.join(HERE, '..', 'audit', 'audit_sensitivity.json')))
AUDR = json.load(open(os.path.join(HERE, '..', 'audit', 'audit_results.json')))
# Set 5 (pre-registered): the set-4-named keys of stats_v2_set5.json hold set 5.
S5 = json.load(open(os.path.join(HERE, 'stats_v2', 'stats_v2_set5.json')))
S5R = json.load(open(os.path.join(HERE, 'stats_v2', 'stats_v2_set5_as_recorded.json')))
AC5, U5 = S5['accuracy']['heldout-5']['sonnet55'], S5['accuracy']['heldout-5-unanswerable']['sonnet55']
T5, PR5, STOP5 = S5['trust']['heldout-5'], S5['set4_paired'], S5['stops_vs_Am']
RC5 = {c['cond']: c for c in S5['regrade']['cells'] if c['set'] == 'heldout-5'}
P5L23 = S5['pooled']['trust_heldout4']['L2_L3']
H1T, H1L = PR5['W2_vs_Am'], PR5['sensitivity']['lenient']['W2_vs_Am']
RT = json.load(open(os.path.join(HERE, '..', 'routes', 'routes.json')))

# ---------------------------------------------------------------- WordprocessingML helpers
def x(t): return html.escape(str(t), quote=False)
def run(t, b=False, i=False, sz=None, font=None, color=None, va=None):
    pr = ''
    if font: pr += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>'
    if b: pr += '<w:b/>'
    if i: pr += '<w:i/>'
    if color: pr += f'<w:color w:val="{color}"/>'
    if sz: pr += f'<w:sz w:val="{int(sz * 2)}"/><w:szCs w:val="{int(sz * 2)}"/>'
    if va: pr += f'<w:vertAlign w:val="{va}"/>'
    return f'<w:r>{"<w:rPr>" + pr + "</w:rPr>" if pr else ""}<w:t xml:space="preserve">{x(t)}</w:t></w:r>'
def rich(s):
    # **bold**, *italic*, _{sub}, ^{sup} in running text
    out, i, bold, ital = [], 0, False, False
    buf = ''
    def flush():
        nonlocal buf
        if buf: out.append(run(buf, b=bold, i=ital)); buf = ''
    while i < len(s):
        if s.startswith('**', i): flush(); bold = not bold; i += 2; continue
        if s[i] == '*' and not s.startswith('**', i): flush(); ital = not ital; i += 1; continue
        if s.startswith('_{', i) or s.startswith('^{', i):
            flush(); j = s.index('}', i); out.append(run(s[i + 2:j], b=bold, i=ital, va='subscript' if s[i] == '_' else 'superscript')); i = j + 1; continue
        buf += s[i]; i += 1
    flush(); return ''.join(out)
def para(content, style=None, align=None, keep=False, extra=''):
    pr = (f'<w:pStyle w:val="{style}"/>' if style else '') + ('<w:keepNext/>' if keep else '') + (f'<w:jc w:val="{align}"/>' if align else '') + extra
    return f'<w:p>{"<w:pPr>" + pr + "</w:pPr>" if pr else ""}{content}</w:p>'
def P(s, **k): return para(rich(s), **k)
def H1(s): return para(run(s), style='Heading1')
def H2(s): return para(run(s), style='Heading2')
def CAP(s): return para(rich(s), style='Caption')
NUMS = []  # numbering instances: ('bullet'|'decimal')
def LIST(items, kind='bullet'):
    NUMS.append(kind); nid = len(NUMS)
    return ''.join(para(rich(it), style='ListParagraph', extra=f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{nid}"/></w:numPr>') for it in items)
def TABLE(head, rows, widths, align=None):
    total = sum(widths); align = align or (['left'] + ['right'] * (len(head) - 1))
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    def cell(t, w, a, hdr=False):
        shade = '<w:shd w:val="clear" w:color="auto" w:fill="E7EDEF"/>' if hdr else ''
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}<w:vAlign w:val="center"/></w:tcPr>'
                f'{para(rich(t) if not hdr else run(t, b=True), style="TableText", align=a)}</w:tc>')
    hrow = '<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' + ''.join(cell(h, w, a, True) for h, w, a in zip(head, widths, align)) + '</w:tr>'
    body = ''.join('<w:tr><w:trPr><w:cantSplit/></w:trPr>' + ''.join(cell(c, w, a) for c, w, a in zip(r, widths, align)) + '</w:tr>' for r in rows)
    b = '<w:top w:val="single" w:sz="8" w:color="3A4A55"/><w:bottom w:val="single" w:sz="8" w:color="3A4A55"/><w:insideH w:val="single" w:sz="4" w:color="C9D2D8"/>'
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{b}</w:tblBorders>'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>{hrow}{body}</w:tbl>')

# ---------------------------------------------------------------- OMML equations
def mr(t, plain=False):
    return f'<m:r>{"<m:rPr><m:sty m:val=\"p\"/></m:rPr>" if plain else ""}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">{x(t)}</m:t></m:r>'
def mf(n, d): return f'<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>'
def msub(b, s): return f'<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>'
def msup(b, s): return f'<m:sSup><m:e>{b}</m:e><m:sup>{s}</m:sup></m:sSup>'
def mrad(e): return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{e}</m:e></m:rad>'
def mdel(e): return f'<m:d><m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr><m:e>{e}</m:e></m:d>'
def msum(lo, hi, e): return f'<m:nary><m:naryPr><m:chr m:val="∑"/></m:naryPr><m:sub>{lo}</m:sub><m:sup>{hi}</m:sup><m:e>{e}</m:e></m:nary>'
def mbinom(n, k): return f'<m:d><m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr><m:e><m:f><m:fPr><m:type m:val="noBar"/></m:fPr><m:num>{n}</m:num><m:den>{k}</m:den></m:f></m:e></m:d>'
def EQ(inner, num):
    # Equation centred, its number at the right margin.
    return (f'<w:p><w:pPr><w:pStyle w:val="Equation"/><w:tabs><w:tab w:val="center" w:pos="4680"/><w:tab w:val="right" w:pos="9360"/></w:tabs></w:pPr>'
            f'{run(chr(9))}<m:oMath>{inner}</m:oMath>{run(chr(9) + f"({num})")}</w:p>')
# ---------------------------------------------------------------- figures (SVG -> PNG via Quick Look)
FIGS = []
def svg_png(name, svg, w, h):
    path = os.path.join(HERE, name)
    # Quick Look fits a size-less SVG (viewBox only) into a square thumbnail, centred; crop the band back out.
    svg = svg.replace(f' width="{w}" height="{h}" viewBox', ' viewBox', 1)
    open(path + '.svg', 'w').write(svg)
    S = 2 * w
    subprocess.run(['qlmanage', '-t', '-s', str(S), '-o', HERE, path + '.svg'], capture_output=True)
    png = path + '.svg.png'
    subprocess.run(['sips', '--cropToHeightWidth', str(round(S * h / w)), str(S), png, '--out', path + '.png'], capture_output=True)
    os.remove(png); return path + '.png'
IMG = []
def FIG(png, w, h, width_in=6.3):
    IMG.append(png); rid = f'rIdImg{len(IMG)}'; cx = int(width_in * 914400); cy = int(cx * h / w)
    n = len(IMG)
    d = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{n}" name="Figure {n}"/>'
         f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
         f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{n}" name="fig{n}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
         f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
         f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
    return para(d, align='center', keep=True)
LINKS = []
def LINK(text, url):
    LINKS.append(url); return f'<w:hyperlink r:id="rIdL{len(LINKS)}"><w:r><w:rPr><w:color w:val="0B5E7A"/><w:u w:val="single"/></w:rPr><w:t xml:space="preserve">{x(text)}</w:t></w:r></w:hyperlink>'


# ---------------------------------------------------------------- equations
phat = '<m:acc><m:accPr><m:chr m:val="̂"/></m:accPr><m:e>' + mr('p') + '</m:e></m:acc>'
EQS = {
    'acc': phat + mr('=') + mf(mr('k'), mr('n')),
    'wilson': mf(phat + mr('+') + mf(msup(mr('z'), mr('2')), mr('2n')) + mr('±') + mr('z') + mrad(mf(phat + mdel(mr('1−') + phat), mr('n')) + mr('+') + mf(msup(mr('z'), mr('2')), msup(mr('4n'), mr('2')))),
                 mr('1+') + mf(msup(mr('z'), mr('2')), mr('n'))) + mr(',  z=1.96'),
    'boot': msup(msub(mr('θ'), mr('b')), mr('*')) + mr('=θ') + mdel(msup(msub(mr('Q'), mr('b')), mr('*'))) + mr(',  b=1,…,B;     CI = ') + mr('[') + msub(mr('q'), mr('0.025')) + mr(', ') + msub(mr('q'), mr('0.975')) + mr(']'),
    'mcnemar': mr('p=min') + mdel(mr('1, 2') + msum(mr('i=0'), mr('min(b,c)'), mbinom(mr('b+c'), mr('i')) + msup(mr('2'), mr('−(b+c)')))),
    'holm': msub(mr('p̃'), mr('(i)')) + mr('=') + msub(mr('max'), mr('j≤i')) + mr(' min') + mdel(mr('1, ') + mdel(mr('m−j+1')) + msub(mr('p'), mr('(j)'))),
    'trust': mr('π=') + mf(mr('T−') + msub(mr('W'), mr('T')), mr('T')) + mr(',     κ=') + mf(mr('T'), mr('n')),
    'rule3': msub(mr('W'), mr('T')) + mr('=0  ⇒  Pr(wrong | trusted) ≲ ') + mf(mr('3'), msub(mr('n'), mr('q'))),
    'silent': mr('ω=') + mf(msub(mr('W'), mr('T')), mr('n')) + mr(',     ') + msub(mr('π'), mr('all', True)) + mr('=') + mf(mr('T+') + msub(mr('T'), mr('u')) + mr('−') + msub(mr('W'), mr('T')) + mr('−') + msub(mr('T'), mr('u')), mr('T+') + msub(mr('T'), mr('u'))),
    'stop': mr('s=') + mf(msub(mr('S'), mr('u')), msub(mr('n'), mr('u'))),
}

# ---------------------------------------------------------------- figures
COL = {'P': '#8a939d', 'A': '#6d4fa0', 'Am': '#b0569a'}
def fig1():
    W, H, L, R, T = 900, 60 + 44 * len(C4), 300, 70, 30
    lo_ax, hi_ax = 0.5, 0.95
    X = lambda v: L + (v - lo_ax) / (hi_ax - lo_ax) * (W - L - R)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#ffffff"/>']
    for g in (0.5, 0.6, 0.7, 0.8, 0.9):
        s.append(f'<line x1="{X(g)}" x2="{X(g)}" y1="{T}" y2="{H - 40}" stroke="#d5dde2" stroke-width="1"/><text x="{X(g)}" y="{H - 16}" text-anchor="middle" font-family="Times New Roman" font-size="16" fill="#44525c">{int(round(g * 100))}%</text>')
    for i, k in enumerate(C4):
        c = AC4[k]; y = T + 20 + i * 44; col = COL.get(k, '#0d6b66'); b = c['bootstrap']['ci']
        s.append(f'<text x="{L - 14}" y="{y + 6}" text-anchor="end" font-family="Times New Roman" font-size="17" fill="#1b2630">{NAME[k]}</text>')
        s.append(f'<line x1="{X(b[0])}" x2="{X(b[1])}" y1="{y}" y2="{y}" stroke="{col}" stroke-width="3"/>')
        s.append(f'<circle cx="{X(c["acc"])}" cy="{y}" r="7" fill="{col}"/><text x="{X(b[1]) + 10}" y="{y + 6}" font-family="Times New Roman" font-size="16" fill="#1b2630">{c["k"]}/200</text>')
    s.append('</svg>'); return svg_png('fig1', ''.join(s), W, H), W, H
def fig2():
    ks = [k for k in ORDER if a3(k, 'P') and a3(k, 'W2')]
    W, H, L, R, T = 900, 100 + 58 * len(ks), 230, 40, 70
    lo_ax, hi_ax = 0.3, 1.0
    X = lambda v: L + (v - lo_ax) / (hi_ax - lo_ax) * (W - L - R)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#ffffff"/>']
    for g in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        s.append(f'<line x1="{X(g)}" x2="{X(g)}" y1="{T - 20}" y2="{H - 40}" stroke="#d5dde2"/><text x="{X(g)}" y="{H - 16}" text-anchor="middle" font-family="Times New Roman" font-size="16" fill="#44525c">{int(round(g * 100))}%</text>')
    for i, k in enumerate(ks):
        y = T + i * 58
        s.append(f'<text x="{L - 14}" y="{y + 6}" text-anchor="end" font-family="Times New Roman" font-size="17" fill="#1b2630">{LAB[k]}</text>')
        for off, cond, col in ((-14, 'P', '#8a939d'), (0, 'W2', '#0d6b66'), (14, 'A', '#6d4fa0')):
            c = a3(k, cond)
            if not c: continue
            b = c['bootstrap']['ci']; yy = y + off
            s.append(f'<line x1="{X(b[0])}" x2="{X(b[1])}" y1="{yy}" y2="{yy}" stroke="{col}" stroke-width="2.5"/>')
            if cond == 'A':
                s.append(f'<rect x="{X(c["acc"]) - 5}" y="{yy - 5}" width="10" height="10" fill="{col}" transform="rotate(45 {X(c["acc"])} {yy})"/>')
            else:
                s.append(f'<circle cx="{X(c["acc"])}" cy="{yy}" r="6" fill="{col}"/>')
    lx = L
    for lab_, col, shape in (('one-shot SQL (P)', '#8a939d', 'c'), ('DQL W2', '#0d6b66', 'c'), ('agent (A)', '#6d4fa0', 'd')):
        s.append(f'<circle cx="{lx + 6}" cy="20" r="6" fill="{col}"/>' if shape == 'c' else f'<rect x="{lx + 1}" y="15" width="10" height="10" fill="{col}" transform="rotate(45 {lx + 6} 20)"/>')
        s.append(f'<text x="{lx + 18}" y="25" font-family="Times New Roman" font-size="15" fill="#44525c">{lab_}</text>'); lx += 40 + 8 * len(lab_)
    s.append(f'<text x="{lx}" y="25" font-family="Times New Roman" font-size="15" fill="#44525c">lines: bootstrap 95% CI</text>')
    s.append('</svg>'); return svg_png('fig2', ''.join(s), W, H), W, H

# ---------------------------------------------------------------- the paper
B = []; add = B.append
add(para(run('Context, Trust Labels and Abstention in a Governed Text-to-SQL Layer: An Exploratory Case Study on an Insurance Warehouse'), style='Title'))
add(para(run('[Author names]'), style='Authors'))
add(para(run('DuckCode AI Labs', i=True), style='Authors'))
add(para(run(f'Preprint, {date(2026, 10, 4).strftime("%-d %B %Y")}. Intended categories: cs.DB (primary), cs.CL, cs.AI.', sz=9.5, color='55636C'), align='center'))

add(para(run('Abstract'), style='AbstractHeading'))
_am = (f' An agent given DQL\'s modeling knowledge as text answered {pct(AC4["Am"]["acc"])} ({dpt(PR4["W2_vs_Am"])} points for DQL, p = {PR4["W2_vs_Am"]["p_raw"]:.2f}), consistent with modeled context explaining much of the gain; an additional advantage from DQL\'s answering pipeline was not established.') if HAS_AM else ''
_amu = (f'{U4["A"]["k"]} for each agent' if U4['Am']['k'] == U4['A']['k'] else f'{U4["A"]["k"]} and {U4["Am"]["k"]} for the agents') if HAS_AM else f'{U4["A"]["k"]} for the agent'
_lr23 = T5['L2']['W_T_lenient_rounding'] + T5['L3']['W_T_lenient_rounding']
_u5 = [U5[L]['k'] for L in ('L2', 'L3', 'W2', 'WB')]
add(P(f'Text-to-SQL systems are usually judged by execution accuracy alone. For business use, two further properties matter: whether a label marking an answer as computed from approved definitions can be trusted, and whether the system declines questions the data cannot answer. We evaluate DQL, an open-source analytics layer that labels each answer by how it was produced, on a small insurance warehouse with held-out question sets written by AI agents. In a pre-registered test on 200 answerable questions written by a GPT model, DQL with modeled context (level W2) answered {pct(AC5["W2"]["acc"])} correctly with Claude Sonnet 5.5, against {pct(AC5["P"]["acc"])} for one-shot SQL and {pct(AC5["Am"]["acc"])} for an agent given the same modeling knowledge as text ({dpt(H1T)} points, 95% CI {dci(H1T)}, exact McNemar {pstr(H1T["p_raw"])}); the difference from that agent vanishes under a grade that forgives label columns. Answers labelled governed at DQL\'s dbt-metric levels were right in {P5L23["trusted_right"]} of {P5L23["trusted"]} cases ({P5L23["trusted"] - _lr23} when label columns are forgiven), short of the pre-registered 95%, and DQL declined {min(_u5)} to {max(_u5)} of 50 unanswerable questions against {U5["Am"]["k"]} for the agent. Exploratory results on a second set of 250 questions written by a Claude model agree on the gain over one-shot SQL and did not establish an advantage over the same-context agent; there, {T4["WB"]["W_T"]} of {T4["WB"]["T"]} answers labelled governed by an authored business layer were wrong.', style='Abstract'))
add(para(run('Keywords: ', b=True, sz=10) + run('text-to-SQL; semantic layer; selective prediction; abstention; benchmark methodology; data governance', sz=10), style='Abstract'))

# ---- 1
add(H1('1  Introduction'))
add(P('Benchmarks such as BIRD [9] and Spider 2.0 [10] score text-to-SQL systems by the share of questions whose query returns the reference rows. That measure leaves out two properties an organization needs before it acts on an answer. The first is whether the system can say which of its answers rest on approved definitions, so that those can be used without checking. The second is whether it declines a question the data cannot answer instead of returning a plausible number from a nearby column.'))
add(P('Describing a warehouse to the model is known to raise accuracy. On the insurance data used here, querying a knowledge-graph representation raised GPT-4 from 16.7% to 54.2% [1]. dbt Labs reported that, once three models were added so that its semantic layer covered all 11 test questions, the layer answered 98.2% and 100% of 20 runs per question correctly against 90.0% and 84.1% for text-to-SQL [3]. On a retail warehouse, prepending a hand-written description of the data to the prompt raised three models by 17 to 23 points [6]. These studies measure accuracy. We add the reliability of answer labels and the rate of correct abstention, and we try to report all three with the statistical care that a small warehouse requires.'))
add(P('We study DQL [16], an open-source layer that answers through certified queries, governed metrics or drafted SQL and labels each answer (Section 3). Our contributions are:'))
add(LIST([
    'Metrics for labelled text-to-SQL answers framed as selective prediction (trust precision, trusted coverage, wrong trusted answers, correct abstention), with question-level bootstrap intervals that account for the same question being answered by many models and levels (Sections 5 and 6.6).',
    'A context ladder that separates a dbt project, entity and relationship modeling, metric definitions, written business rules and an authored business layer, with and without dbt (Section 4.3).',
    'Results for seven models, a one-shot baseline and two agentic baselines, one of them given the same modeling knowledge as DQL, separating context-assisted accuracy from the reliability of governance labels, with negative results on both labels and abstention (Section 6).',
    'A test-suite check on altered copies of the warehouse, and a root-cause taxonomy of wrong trusted answers (Sections 6.8 and 6.9).',
    'An account of where the study departed from a clean held-out protocol, and a pre-registered confirmatory test of the central comparison (Sections 4.2, 4.6, 6.1, 7 and 8).',
], 'decimal'))
add(P('Our central finding is narrower than a system comparison. On a small insurance warehouse, modeled context improved accuracy relative to one-shot SQL. Against an agent given the same knowledge, the pre-registered test found an advantage for DQL under the strict rule that disappears when label columns are forgiven, and an earlier, exploratory set did not establish one. Governance labels required separate validation and fell short of the precision we pre-registered. We do not claim that DQL is more accurate than, or equivalent to, an agentic text-to-SQL system given the same knowledge beyond this warehouse, model and grading rule (no equivalence margin was set); that its trusted labels reach a particular precision; that results on a warehouse with two policies carry over to production scale; or that our figures can be compared with BIRD or Spider 2.0 leaderboard scores, which use different data, scale, tasks and protocols.'))

# ---- 2
add(H1('2  Related work'))
add(P('**Text-to-SQL benchmarks.** BIRD [9] and Spider 2.0 [10] measure execution accuracy on large and enterprise-style databases; LiveSQLBench [11] refreshes its tasks to limit contamination. Jin et al. [7] found errors in 52.8% of BIRD Mini-Dev and 62.8% of Spider 2.0-Snow reference annotations; re-scoring 16 agents changed their performance by −7% to +31% (relative) and their ranks by up to nine positions. A shorter peer-reviewed version analyses five agents and reports different figures [8]. We therefore audit our reference answers and report lenient scores next to strict ones. Zhong et al. [26] evaluate a query on a distilled suite of databases so that a query correct only by coincidence on one database is caught; we apply a small version of this idea (Section 6.8).'))
add(P('**Semantic layers and knowledge graphs.** Sequeda et al. [1] released the insurance warehouse with 43 questions in a 2×2 grid of question and schema complexity [2]; GPT-4 answered 16.7% correctly over SQL and 54.2% over a knowledge graph, and 0% over SQL in both high-schema-complexity quadrants. Ganz and Perigaud [3] used the same data with 11 questions run 20 times each [4]. Before three models were added, the semantic layer scored 0% on questions that needed too many joins and failed with an error, where text-to-SQL returned a plausible wrong answer; they report no significance tests. Rumiantsau and Fokeev [5][6] used a retail warehouse on ClickHouse with 99 scored questions. Their "semantic layer" is a markdown document of about 2,200 tokens prepended to the prompt, so the model still writes SQL. They report Wilson intervals and paired exact McNemar tests, and gains of 17.2 to 23.2 points across three models. MetricFlow [15] is the dbt metric engine used at two of our levels. The dbt study notes that the layer fails visibly out of scope; we measure this directly, as correct abstention on unanswerable questions, and we also measure how often labelled answers are wrong.'))
add(P('**Abstention and selective prediction.** A system that may abstain is characterized by its coverage and by its risk on the answers it gives [17][18]. Wang et al. [21] classify ambiguous and unanswerable text-to-SQL questions into six types and train a model to detect and explain them. Chen et al. [20] apply conformal prediction to a model\'s hidden states at schema linking and abstain or ask the user when an error is likely. TrustSQL [24] scores systems on answering feasible questions and abstaining on infeasible ones, with a penalty for wrong answers, and PRACTIQ [25] separates ambiguous questions from four kinds of unanswerable ones in conversation and studies clarification. Richardson [19] measures which signals predict SQL correctness: a two-provider ensemble of LLM judges reaches an AUROC of 0.82, and, for example, answers 27% of questions at 24% selective risk. DQL\'s trusted label is a selective predictor of a different kind: it is assigned by rules over the route an answer took and the reading of the question, not by a confidence score. That makes it auditable, but not calibrated, and, as Section 6 shows, not error-free.'))

# ---- 3
add(H1('3  The system under test'))
add(P('DQL reads a project\'s models, relationships and metric definitions, from a dbt project or directly from the warehouse catalog, and answers a question through the most governed route that fits it. Every answer carries one of four labels (Table 1).'))
add(TABLE(['Label', 'Meaning', 'Produced by'], [
    ['certified', 'A query block reviewed and certified by a person answers this exact question.', 'Certified blocks'],
    ['governed', 'Computed from approved metric definitions, and the reading uses every term the question names.', 'Semantic metrics (MetricFlow or DQL\'s native engine)'],
    ['review required', 'SQL drafted by the model from the modeled schema and checked against the catalog before it runs.', 'Drafted SQL'],
    ['blocked', 'No answer: the data does not hold what is asked, or no safe query exists; the reason is stated.', 'Abstention'],
], [1500, 4860, 3000], ['left', 'left', 'left']))
add(CAP('**Table 1.** Answer labels. We call certified and governed answers *trusted*.'))
add(P('A question is first read into a structured intent (measure, grouping, filters and period). If a certified block names the question, it answers. Otherwise, if governed metrics cover the whole reading, DQL compiles and runs them. Otherwise it drafts SQL from the modeled schema, with the modeling and metric definitions as context, checks every referenced table and column against the catalog, runs it and labels it for review. If none of these applies, it abstains and names what is missing. A governed answer loses its label when the reading leaves a question term unused, cannot carry a requested label column, or merges records the question asked to see separately. The accuracy of a level therefore mixes two things: governed answers, and drafted SQL written with the context that level provides.'))

# ---- 4
add(H1('4  Benchmark'))
add(H2('4.1  Data'))
add(P('The warehouse is the ACME property-and-casualty insurance database [1][2] as packaged by dbt Labs with a dbt project and MetricFlow metrics [3][4], loaded into DuckDB: 29 relations, 161 columns and about 980 rows. Monetary amounts are split across separate claim-amount tables, policies reach people through a party-role bridge table, and several identifiers are misspelled in the source. The core records are few (2 policies, 2 claims, one named policy holder and one named agent), a limitation we return to in Section 9.'))
add(H2('4.2  Question sets, and what "held out" meant here'))
add(LIST([
    '**Development set** (41 questions): the published data.world questions. We used it to diagnose and fix defects and report no headline number on it.',
    '**Set 3** (40 answerable, 10 unanswerable), 10 answerable questions in each cell of the question-complexity by schema-complexity grid.',
    '**Set 4** (200 answerable, 50 unanswerable), 50 per cell; the writer was asked to include near-miss unanswerable questions that invite an answer from a similar column.',
    '**Set 5** (200 answerable, 50 unanswerable), 50 per cell, written by GPT-6 Sol under a pre-registration and run once on a frozen build (Section 4.6).',
]))
add(P('Sets 3 and 4 were written by a Claude agent (Claude Opus 5.5 for set 4) that was given only the warehouse schema and data, not the published questions, DQL or any results. Its reference SQL was executed to produce the reference rows. Until the reference-answer audit (Section 4.5), which an author carried out after the systems had been run and DQL frozen, neither the authors nor the AI coding assistant used to run the study read the question text or reference SQL of these sets. The protocol of sets 3 and 4 was nonetheless not clean, in five ways:'))
add(LIST([
    '**Set 3 is spent.** Its run logs showed set-3 table names in DQL\'s stop codes, which led to the second half of a fix for short table names (Section 7). Levels LB and WB were rerun for every model on the fixed build, so their set-3 results reflect a change prompted by set 3.',
    '**Two set-4 identifiers were seen.** Two question identifiers (hash strings, not question text) from set 4 appeared in a log shown by the assistant. No change was made to DQL after set 4 was run.',
    '**Writer transcripts exist.** The writing agent\'s own transcripts, which contain question text, remain unread on the machine used to run the study. Their SHA-256 hashes, and those of the set-4 files, are published in the benchmark repository (docs/SEALING.md), so they can be checked when set 4 is released.',
    '**Overlap between sets.** Two set-4 reference queries are textually identical to set-3 reference queries; their question wording differs.',
    '**Same model family.** The question writer and three of the seven evaluated models are Claude models, and set 4 was run only with a Claude model. Shared phrasing could favour Claude models or DQL\'s Claude-tuned prompts. Set 5 (Section 4.6) is written by a GPT model.',
]))
add(H2('4.3  Conditions'))
add(TABLE(['Condition', 'What the model is given'], [
    ['P', 'Full table definitions; the model writes one SQL statement.'],
    ['A', 'The same definitions and tools to list tables, describe them, sample rows and run read-only queries (at most 12 turns and 20 tool calls); it returns final SQL or declines.'],
    ['A-model', 'A, plus a text rendering of DQL\'s W2 knowledge: entities, keys, certified relationships, measures, computed dimensions and metrics with their filters (about 23 KB). Run on set 4 only, after its other results were known.'],
    ['L0', 'DQL with the dbt project only.'],
    ['L1', 'L0 plus DQL modeling: entities, relationships and their cardinality.'],
    ['L2', 'L1 plus dbt Labs\' MetricFlow metrics.'],
    ['L3', 'L2 plus skills: business rules written as guidance.'],
    ['LB', 'L3 plus an authored business layer: governed metrics, skills and 9 certified blocks.'],
    ['W0', 'DQL connected to the warehouse catalog only; no dbt project.'],
    ['W1', 'W0 plus modeling.'],
    ['W2', 'W1 plus the same metrics as native DQL definitions.'],
    ['WB', 'W2 plus the business layer.'],
], [1500, 7860], ['left', 'left']))
add(CAP('**Table 2.** Conditions. The business layer was written from a business brief by one agent, checked by a second and certified by a person; it was not written from any question set.'))
add(P('**Same knowledge, different instructions.** A-model receives the same modeling knowledge as W2, but not DQL\'s instructions about the shape of an answer. DQL\'s question reader is told to group a breakdown or ranking by the entity\'s key and show its name beside it ("Never group by a name"). Its SQL writer is told, when an answer lists people or things, to "select and group by their id column beside the name", to show a table\'s business number (such as the policy number) beside its internal key, and to "aggregate at the grain the question asks for". A review step checks each drafted result once for a missing name column, repeated rows or a total at the wrong level, and may revise it. The agents are told only to "return the columns and rows the question asks for, not a preview", and that the answer is checked by its values. These instructions are part of the system under test, so the comparison with A-model is between DQL\'s pipeline and an agent with the same knowledge, not the same instructions. The prompts are in the public repositories (insurance/baseline-agent.mjs in the benchmark repository; apps/cli/src/ask-pipeline-host/host.ts and join-relationships.ts, and packages/dql-agent/src/ask-pipeline/resolve-intent.ts, in DQL at build 627009a1).'))
add(H2('4.4  Models and run settings'))
add(TABLE(['Model', 'Identifier', 'Access', 'Reasoning setting'], [
    ['Claude Opus 5.5', 'claude-opus-5-5', 'Claude Code CLI 2.1.282', 'DQL per step: medium to read, high to draft; agents high'],
    ['Claude Sonnet 5.5', 'claude-sonnet-5-5', 'Claude Code CLI 2.1.285', 'same'],
    ['Claude Sonnet 5', 'claude-sonnet-5', 'Claude Code CLI 2.1.282', 'same'],
    ['Qwen 3.8 27B', 'qwen3.8:27b', 'Ollama, Apple M2 Max, 32 GB', 'model default'],
    ['GPT-6 Luna', 'gpt-6-luna', 'Codex CLI 0.158.0-alpha.2.1 / 0.159.2', 'max'],
    ['GPT-6 Sol', 'gpt-6-sol', 'same', 'medium'],
    ['GPT-5.6 Terra', 'gpt-5.6-terra', 'same', 'high'],
], [2100, 1900, 2860, 2500], ['left', 'left', 'left', 'left']))
add(CAP('**Table 3.** Models. Local and fixed-reasoning runs get a 20-fold answer deadline and a 300-second limit per model call, so that a stop reflects the system\'s decision rather than a timeout. The Codex CLI was updated during the GPT runs.'))
add(P('Every question is asked in a new conversation on a fresh copy of the project, with DQL\'s caches, memory and run history removed. Claude calls replace the tool\'s system prompt, disable its tools and ignore local MCP configuration. Codex calls run from a separate home directory with no personal instructions, plugins, MCP servers or memories. The default directory had added about 23,800 tokens of the operator\'s configuration to each call, and every run made with it was discarded. Provider usage limits are never scored; refused questions are asked again after the limit resets. All DQL levels ran on development build 49c0e1cb of DQL 1.17.3, except LB and WB, which ran on 627009a1 (49c0e1cb plus the fix in Section 7). Both are public as branches of github.com/duckcode-ai-labs/dql (claude/dql-benchmark-final and claude/dql-benchmark-final-2); neither is a tagged release.'))
add(H2('4.5  Reference-answer audit'))
exec(open(os.path.join(HERE, 'paper_audit_section.py')).read())
add(H2('4.6  Pre-registration of set 5'))
add(P('To address the post-hoc choice of comparison and the question writer\'s model family, we committed a pre-registration (insurance/PREREGISTRATION-SET5.md, commit 6f60a71 in github.com/duckcode-ai-labs/dql-benchmarks, then at github.com/duckcode-ai/dql-benchmarks, which now redirects) at 18:19 CDT on 30 September 2026 and pushed it to the public repository at 20:50:22 CDT. GPT-6 Sol, started automatically when its provider limit lifted, began writing set 5 at 20:50:33 and finished at 20:59 (both times from the same machine\'s clock; GitHub\'s push record shows the first). Its validator reported 200 answerable and 50 unanswerable questions, and the audit of its command log found no access outside its folder. SHA-256 hashes of the set-5 files and the writer\'s log are published in docs/SEALING.md, and the DQL build frozen for set 5 (627009a1) in insurance/FREEZE-SET5.md, both before any system was run on set 5. One exposure occurred during the runs: the operator\'s AI assistant printed the truncated identifiers (about 60 characters of question text each) of 31 set-5 answerable questions while checking a report invalidated by a provider usage limit; no reference SQL or answers were shown, and DQL was not changed. Its main points:'))
add(LIST([
    '**Questions.** 200 answerable (50 per grid cell) and 50 unanswerable questions, including near-miss ones, written by GPT-6 Sol through the Codex CLI with an isolated home directory. The writer saw only a copy of the warehouse and a format specification.',
    '**Audit.** Before scoring, a person audits a random 25% of items; results are reported on all items and without items found wrong.',
    '**System.** DQL is frozen before set 5 is run (commit 627009a1, recorded in insurance/FREEZE-SET5.md), and each condition runs once on it. No DQL change is made because of set 5.',
    '**Primary hypothesis (H1).** With Claude Sonnet 5.5, W2 and A-model answer a different share of the 200 questions correctly: one exact two-sided McNemar test at α = 0.05, reported with the paired difference and its question-level bootstrap interval.',
    '**Secondary analyses** (Holm within each family): each of L2, L3, W2 and WB against P and against A-model; trust precision at L2 and L3 with the number of distinct questions; correct abstention against A-model; wrong trusted answers and κ per condition. Secondary models: GPT-6 Sol and Qwen 3.8 27B.',
    '**Scoring.** Strict rule primary; lenient and lenient + rounding reported as secondary.',
]))
add(P('**What set 5 could and could not show,** as we wrote before the run. H1 is a test of difference: a non-significant result would not be read as equivalence, since no equivalence margin was pre-registered and 200 paired questions could not support a tight one. The precision hypothesis for trusted labels is underpowered: at the coverage seen on set 4 (about 7% at L2 and L3), a level would yield roughly 14 trusted answers, and even if none were wrong the one-sided 95% lower bound on precision would be about 81%; placing that bound above 95% needs about 59 error-free trusted questions. It is reported descriptively, with distinct questions. The primary interval uses seed 5, as pre-registered.'))

# ---- 5
add(H1('5  Metrics and statistical method'))
add(P('**Accuracy.** A condition answers *n* questions, *k* of which return the reference rows, compared as multisets and ignoring column names and order:'))
add(EQ(EQS['acc'], 1))
add(P('For a single condition we report the 95% Wilson score interval [13]:'))
add(EQ(EQS['wilson'], 2))
add(P('**Question-level bootstrap.** Every model and level answers the same questions, so answers pooled across models or levels are not independent: a question that one condition gets wrong tends to be got wrong by others. Pooled figures, and all intervals we show in figures, therefore resample questions rather than answers [23]. Each replicate *b* draws the question set with replacement, and every answer to a drawn question enters together. The statistic θ is recomputed on the replicate, and the interval is the 2.5% and 97.5% quantiles of B = 10,000 replicates (seed 20260930, the same draws for every statistic on a set; set 5\'s primary interval uses seed 5, as pre-registered):'))
add(EQ(EQS['boot'], 3))
add(P('**Paired comparison.** Two conditions answer the same questions. Let *b* count questions X answers correctly and Y does not, and *c* the reverse. The exact two-sided McNemar test [12] gives'))
add(EQ(EQS['mcnemar'], 4))
add(P('**Multiple comparisons.** Tests are grouped in families that were fixed before these tests were computed, though after the set-3 and set-4 results had been seen: on set 4, the four DQL levels against P and, separately, against A; on set 3, each model\'s nine levels against that model\'s P, and against A where A was run; on set 5, as pre-registered, H1 (W2 against A-model) is one test without correction, and the secondary families are the four levels against P, against A-model, and, for correct abstention, against A-model. Within a family of *m* tests with ordered raw p-values, Holm\'s step-down adjustment [22] is'))
add(EQ(EQS['holm'], 5))
add(P('We call a difference significant when the Holm-adjusted *p* < 0.05. On set 4, comparisons involving A-model, and the W2-against-A comparison as a headline, were chosen after results were seen; we label them exploratory. On set 5 they are pre-registered.'))
add(P('**Trust.** Let *T* be the number of answers labelled certified or governed and *W*_{T} the number of those that are wrong. Trust precision π and trusted coverage κ are'))
add(EQ(EQS['trust'], 6))
add(P('In selective-prediction terms κ is coverage and 1 − π the selective risk [17][18]. When no trusted answer is wrong, the one-sided 95% upper bound on the wrong-trusted rate follows the rule of three [14], with *n*_{q} the number of **distinct questions** that received a trusted answer, not the number of answers:'))
add(EQ(EQS['rule3'], 7))
add(P('**Wrong trusted answers.** ω is the share of questions that received a wrong trusted answer, and π_{all} is trust precision over answerable and unanswerable questions together, where *T*_{u} counts trusted answers to unanswerable questions, all of which are wrong. ω describes DQL\'s labelling policy only. We do not compare it with the baselines: they label nothing, and a system that marked every answer for review would have ω = 0 without being more accurate. Comparing harm across systems would need a common acceptance policy at matched coverage, which this study does not have. When κ = 0, ω = 0 carries no information about label quality:'))
add(EQ(EQS['silent'], 8))
add(P('**Abstention.** On an unanswerable set of *n*_{u} questions with *S*_{u} correct abstentions, the rate is'))
add(EQ(EQS['stop'], 9))
add(P(f'On answerable sets an abstention counts as a wrong answer. **Grading rules.** The strict rule above is primary. The *lenient* rule also accepts an answer with the reference row count whose numeric reference columns each match a returned column row by row, which forgives a missing or substituted label column. *Lenient + rounding* further accepts numbers that equal the reference rounded to 0–4 decimals. When an answer has one numeric column and a substituted label, the lenient rule cannot check that each number is attached to the right entity, so it is a sensitivity analysis, not a replacement. Both rules compare values without column names. The strict matcher normalises the values within each row before comparing rows, which in principle lets values trade places between columns that share values; among the {N_STRICT - N_UNVER:,} originally strict-correct answers whose rows could be reconstructed ({N_UNVER} could not), {N_INCONS} failed an independent check that requires one column mapping for the whole result. The check was applied to strict-correct answers only, since it can only remove credit.'))
add(P('**Database variants (secondary, not pre-registered).** On a warehouse with two policies a wrong filter, join or aggregation can return the right rows by coincidence. Following the test-suite idea [26], each strict-correct answer\'s SQL and the reference SQL are re-run on two altered copies of the warehouse: V1 adds an independent second book of business (new identifiers, amounts ×3 + 7, distinct names, street addresses and coordinates, dates moved 400 days with closing dates moved 410), and V2 adds the same book in the same period. Catastrophes, cities and codes are shared, so that every question keeps its meaning; we checked this on the public set 3 only, so it is unverified for the fragile set-4 answers (Section 6.8). An answer *survives* when it matches the re-run reference on both. Answers whose recorded SQL does not reproduce their correct rows on the original (for example a ratio DQL computes after the query) are *not checkable*. A first design that also duplicated names, addresses, catastrophes and coordinates broke the presuppositions of some questions (a named property no longer identified one property); it was replaced after inspecting public set-3 cases only.'))

# ---- 6
add(H1('6  Results'))
add(P('We report the pre-registered test on set 5 first (Section 6.1). The results on sets 3 and 4 that follow (Sections 6.2 to 6.9) are exploratory: their headline comparisons, and the A-model baseline, were chosen after results were seen.'))
exec(open(os.path.join(HERE, 'paper_set5_section.py')).read())
add(H2('6.2  Accuracy on set 4 (exploratory)'))
f1, w1, hh1 = fig1()
rows = []
for k in C4:
    c = AC4[k]
    vp = PR4['vs_P'].get(k); va = PR4['vs_A'].get(k)
    if k == 'Am': vp, va = None, PR4.get('Am_vs_A')
    rows.append([NAME[k], f"{c['k']}/200", pct(c['acc']), ci(c['bootstrap']['ci']),
                 ptest(vp) if vp else ('–' if k != 'A' else ptest(dict(PR4['P_vs_A'], diff=-PR4['P_vs_A']['diff']), holm=False) + '^{a}'),
                 (ptest(va, holm=k != 'Am') + ('^{b}' if k == 'Am' else '')) if va else '–',
                 f"{MED4[k]} s" if MED4.get(k) else '–'])
add(TABLE(['Condition', 'Correct', 'Accuracy', 'Bootstrap 95% CI', 'Δ vs P (Holm p)', 'Δ vs A (Holm p)', 'Median'], rows, [2500, 900, 950, 1250, 1500, 1500, 760]))
add(CAP('**Table 6.** Claude Sonnet 5.5 on set 4 (200 answerable questions), strict grading. Δ in percentage points. ^{a} A against P, raw *p* (not in a family). ^{b} Exploratory, raw *p*. Times are indicative (Section 9).'))
add(FIG(f1, w1, hh1))
add(CAP('**Figure 1.** Accuracy on set 4 with question-level bootstrap 95% intervals, Claude Sonnet 5.5.'))
sigP = [L for L in ('L2', 'L3', 'W2', 'WB') if PR4['vs_P'][L]['p_holm'] < 0.05]
nsP = [L for L in ('L2', 'L3', 'W2', 'WB') if L not in sigP]
add(P(f'Every DQL level was more accurate than one-shot SQL; after Holm correction the difference is significant for {", ".join(sigP)}' + (f' ({", ".join(f"{L}: Holm {pstr(PR4["vs_P"][L]["p_holm"])}" for L in nsP)})' if nsP else '') + f'. No DQL level differed significantly from the agent. The most accurate level, W2, answered {W2["k"]} of 200 questions. Its advantage over the agent ({dpt(tW2A)} points, CI {dci(tW2A)}; {tW2A["gained"]} questions gained and {tW2A["lost"]} lost; raw {pstr(tW2A["p_raw"])}) does not survive the correction (Holm {pstr(tW2A["p_holm"])}). Three further caveats apply to W2. It was chosen as the headline level after set 3 had been seen. It ran on a different build from WB. And none of its answers carried a trusted label (Section 6.4), so its accuracy measures drafted SQL written with DQL\'s context, not governed answers.'))
if HAS_AM:
    t = PR4['W2_vs_Am']; ta = PR4.get('Am_vs_A')
    add(P(f'**A fairer agent.** The agent above had only table definitions, while W2 also had DQL\'s modeling and metric definitions. Given that context as text (A-model), the agent answered {AC4["Am"]["k"]} of 200 ({pct(AC4["Am"]["acc"])}, CI {ci(AC4["Am"]["bootstrap"]["ci"])}). W2 against A-model: {dpt(t)} points (CI {dci(t)}; +{t["gained"]}/−{t["lost"]}; exploratory {pstr(t["p_raw"])}).' + (f' A-model against A: {dpt(ta)} points ({pstr(ta["p_raw"])}).' if ta else '') + ' Set 5 tests this comparison as its one pre-registered primary hypothesis (Section 6.1).'))
else:
    add(P('**A fairer agent.** The agent above had only table definitions, while W2 also had DQL\'s modeling and metric definitions. An agent given the same context as text (A-model, Table 2) is running on set 4 at the time of this draft; its result will be added in the next revision. Set 5 tests W2 against A-model as its one pre-registered primary hypothesis (Section 6.1).'))

add(H2('6.3  Sensitivity to the grading rule'))
LR = PR4['sensitivity']['lenient_rounding']
rows = []
for k in C4:
    cell = next((c for c in S['regrade']['cells'] if c['set'] == 'heldout-4' and c['cond'] == k), None)
    if not cell: continue
    rows.append([NAME[k], str(cell['strict']), str(cell['lenient']), str(cell['lenient_rounding']), str(cell['lenient'] - cell['strict'])])
add(TABLE(['Condition', 'Strict', 'Lenient', 'Lenient + rounding', 'Lenient gain'], rows, [3000, 1300, 1300, 1900, 1500]))
add(CAP('**Table 7.** Correct answers of 200 on set 4 under the three grading rules.'))
sub = RG['heldout-4']['A_agent']['sub_kinds']
lp = [L for L in ('L2', 'L3', 'WB') if LEN['vs_A'][L]['p_holm'] < 0.05]
add(P(f'Under the lenient rule the agent gains {RG["heldout-4"]["A_agent"]["lenient"] - RG["heldout-4"]["A_agent"]["strict"]} answers, most of them ({sub.get("missing_or_extra_columns:label_column_substituted", 0)}) answers that return a different label column, such as a name where the reference has an identifier, with the right numbers. DQL levels gain {RG["heldout-4"]["DQL_levels"]["lenient"] - RG["heldout-4"]["DQL_levels"]["strict"]} answers across all four levels. The comparison with the agent reverses: W2 − A becomes {ptest(LEN["vs_A"]["W2"])}, and {", ".join(lp)} fall significantly below the agent. Against one-shot SQL only W2 stays significant under the lenient rule ({ptest(LEN["vs_P"]["W2"])}). The lenient + rounding results are nearly identical (W2 − A {ptest(LR["vs_A"]["W2"])}).{(' The agent given DQL\'s modeling knowledge also leads W2 under the lenient rule (W2 − A-model ' + dpt(LEN['W2_vs_Am']) + ' points, exploratory ' + pstr(LEN['W2_vs_Am']['p_raw']) + ').') if HAS_AM else ''} Whether DQL is more or less accurate than the agent on this set therefore depends on whether a substituted label column counts as an error; a business user reading a report would usually see it as one, a numeric check would not. Neither grade is the business metric in general: returning a name instead of an identifier is often acceptable, while losing which entity a number belongs to is not. Section 6.9 gives classified examples of each kind from the public set 3.'))

add(H2('6.4  Trust labels and abstention on set 4'))
rows = []
for L in C4:
    t = T4.get(L)
    if not t: continue
    lab = t['labelled']
    un = U4.get(L)
    rows.append([NAME[L], str(t['T']) if lab else '–', str(t['W_T']) if lab else '–',
                 (f"{pct(t['precision'])} ({ci(t['precision_wilson'], 0)})" if t['T'] else ('none' if lab else '–')),
                 (f"{pct(t['precision_all'])} ({ci(t['precision_all_wilson'], 0)})" if lab and t.get('T_all') else ('none' if lab else '–')),
                 pct(t['kappa']) if lab else '–',
                 (pct(t['sigma']) + ('‡' if t['T'] == 0 else '')) if lab else '–',
                 f"{un['k']}/50" if un else '–', str(t.get('unanswerable_answered_trusted', 0)) if lab and un else '–'])
add(TABLE(['Condition', 'T', 'W_T', 'π answerable (Wilson)', 'π all (Wilson)', 'κ', 'ω', 'Correct abstentions', 'Unanswerable labelled trusted'], rows, [2150, 450, 550, 1450, 1450, 650, 700, 1000, 1110]))
add(CAP('**Table 8.** Trusted answers and abstention on set 4, Claude Sonnet 5.5. At each level every question is answered once, so *T* also counts distinct questions. π all counts trusted answers to unanswerable questions as wrong. One-shot SQL and the agents assign no labels, so π, κ and ω do not apply to them. ‡ not informative: no trusted answers (κ = 0).'))
add(P(f'Trusted coverage was small: {pct(T4["L2"]["kappa"])} of answers at L2 and L3, {pct(T4["WB"]["kappa"])} at WB and none at W2. The dbt-metric governed answers were wrong {dbt4["trusted_wrong"]} times out of {dbt4["trusted"]}, on {dbt4["distinct_questions_with_wrong_trusted"]} of {dbt4["distinct_questions"]} distinct questions (question-level upper 95% bound on the wrong rate {pct(dbt4["question_level_exact_upper95"])}); under the lenient + rounding rule {T4["L2"]["W_T_lenient_rounding"] + T4["L3"]["W_T_lenient_rounding"]} of them {'remains' if T4['L2']['W_T_lenient_rounding'] + T4['L3']['W_T_lenient_rounding'] == 1 else 'remain'} wrong. The authored business layer did not deliver reliable labels: {T4["WB"]["W_T"]} of its {T4["WB"]["T"]} trusted answers were wrong ({T4["WB"]["W_T_lenient_rounding"]} under lenient + rounding). On the 50 unanswerable questions DQL abstained correctly {min(u4k.values())} to {max(u4k.values())} times, against {U4["A"]["k"]} for the agent{(' and ' + str(U4['Am']['k']) + ' for A-model') if HAS_AM else ''}, and {u4gov} of its answers to unanswerable questions across the four levels carried a trusted label; counted together with the answerable set, trust precision was {pct(T4['L2']['precision_all'])} at L2, {pct(T4['L3']['precision_all'])} at L3 and {pct(T4['WB']['precision_all'])} at WB. Pooled over the four levels, DQL abstained correctly on {st4["successes"]} of {st4["answers"]} answers ({pct(st4["estimate"])}, question-level CI {ci(st4["bootstrap"]["ci"])}, {st4["distinct_questions"]} questions).'))

add(H2('6.5  Seven models on set 3'))
rows = []
for k in ORDER:
    r = [LAB[k]]; best = max((a3(k, L)['k'] for L in DQL if a3(k, L)), default=None)
    fam = PR3.get(k, {}).get('vs_P', {})
    for L in ['P', 'A'] + DQL:
        c = a3(k, L)
        if not c: r.append('–' if L == 'A' else '·'); continue
        t = fam.get(L); mk = ''
        if t and t['p_holm'] < 0.05: mk = '▲' if t['diff'] > 0 else '▼'
        v = f"{c['k']}{mk}"
        r.append(f"**{v}**" if L in DQL and c['k'] == best else v)
    rows.append(r)
_miss3 = any(not a3(k, L) for k in ORDER for L in ['P'] + DQL)
add(TABLE(['Model', 'P', 'A'] + DQL, rows, [2260] + [645] * 11, ['left'] + ['center'] * 11))
add(CAP('**Table 9.** Correct answers of 40 on set 3. ▲/▼ significantly above/below the model\'s own P after Holm correction over its nine levels. Bold: best DQL level.' + (' · not run on the final build.' if _miss3 else '') + ' –: agent not run.'))
f2, w2_, hh2 = fig2()
add(FIG(f2, w2_, hh2))
add(CAP('**Figure 2.** Set 3: one-shot SQL (P), DQL W2 and, where run, the agent (A) for each model, with question-level bootstrap 95% intervals.'))
sig3 = {k: [L for L, t in PR3.get(k, {}).get('vs_P', {}).items() if t['p_holm'] < 0.05] for k in ORDER}
sig3txt = '; '.join(f"{LAB[k]} at {', '.join(v)}" for k, v in sig3.items() if v) or 'none'
gains = [a3(k, 'L1')['k'] - a3(k, 'L0')['k'] for k in ORDER if a3(k, 'L0') and a3(k, 'L1')]
l0rg = RG['heldout-3']['per_condition']['L0']
anyA = [k for k in ORDER if PR3.get(k, {}).get('vs_A') and any(t['p_holm'] < 0.05 for t in PR3[k]['vs_A'].values())]
add(P(f'With 40 questions a 95% interval spans about ±14 points, so set 3 separates conditions only when differences are large. After Holm correction within each model, levels significantly above the model\'s own one-shot baseline were: {sig3txt}. No level was significantly below it, and for the two models run with the agent no level differed significantly from it{"" if not anyA else " (except " + ", ".join(anyA) + ")"}. L0 was the weakest level for every model, mostly because it abstained on answerable questions ({l0rg["classes"]["abstained"]} of its {l0rg["strict_wrong"]} wrong answers); adding modeling (L1) raised every model by {min(gains)} to {max(gains)} questions of 40.'))

add(H2('6.6  What set 3 showed about labels and abstention'))
rows = []
for key, name in (('L2_L3', 'L2 + L3 (dbt metrics)'), ('LB', 'LB (business layer, dbt)'), ('WB', 'WB (business layer, warehouse)'), ('W2', 'W2'), ('all_DQL_levels', 'All DQL levels')):
    p = pt3[key]['pooled']
    if p.get('rule_of_three_n'):
        ub = f"{pct(p['rule_of_three_upper95_wrong_rate'], 0)} (exact {pct(p['exact_upper95_wrong_rate'])})"
    else:
        ub = pct(p['question_level_exact_upper95'], 0)
    rows.append([name, str(p['trusted']), str(p['trusted_wrong']), f"{p['distinct_questions']} ({p['distinct_questions_with_wrong_trusted']})",
                 pct(p['precision']), ci(p['wilson_answer_level_naive'], 0), ci(p['bootstrap']['ci'], 0) if p['trusted_wrong'] else '–', ub])
add(TABLE(['Pool (all models)', 'Trusted answers', 'Wrong', 'Distinct questions (with wrong)', 'Precision', 'Naive Wilson', 'Question bootstrap', 'Upper 95% wrong rate (questions)'],
          rows, [2150, 900, 700, 1250, 950, 1050, 1100, 1260]))
add(CAP('**Table 10.** Trusted answers on set 3 pooled over models. The naive interval treats every answer as independent; the question bootstrap and the upper bound use distinct questions. The bootstrap is degenerate when no answer is wrong.'))
p23 = pt3['L2_L3']['pooled']
add(P(f'On set 3 the dbt-metric governed answers and abstention looked nearly perfect, but both rest on few distinct questions. The {p23["trusted"]} governed answers at L2 and L3 came from {p23["distinct_questions"]} questions, so the upper 95% bound on their wrong rate is {pct(p23["rule_of_three_upper95_wrong_rate"], 0)} (exact {pct(p23["exact_upper95_wrong_rate"])}), not the {pct(p23["naive_rule_of_three_on_answers"])} that counting answers suggests. Set 3 already showed the business-layer labels to be unreliable: {pt3["LB"]["pooled"]["trusted_wrong"]} of {pt3["LB"]["pooled"]["trusted"]} trusted answers at LB were wrong ({pt3["LB"]["pooled"]["distinct_questions_with_wrong_trusted"]} of {pt3["LB"]["pooled"]["distinct_questions"]} questions) and {pt3["WB"]["pooled"]["trusted_wrong"]} of {pt3["WB"]["pooled"]["trusted"]} at WB, and W2\'s only {pt3["W2"]["pooled"]["trusted"]} trusted answers, all on one question, were wrong. DQL\'s levels abstained correctly on {st3["successes"]} of {st3["answers"]} answers to unanswerable questions, but they come from only {st3["distinct_questions"]} questions. Resampling those questions gives {ci(st3["bootstrap"]["ci"])}, an interval that describes these {st3["distinct_questions"]} questions and cannot represent the variety of unanswerable questions a user may ask; on the 50 questions of set 4 the rate was {pct(st4["estimate"], 0)}. Set 4 did not so much contradict set 3 as show what its small numbers could not establish.'))

add(H2('6.7  Error analysis'))
groups = [('Set 3, DQL levels', RG['heldout-3']['DQL_levels']), ('Set 3, P', RG['heldout-3']['P_one_shot']), ('Set 3, A', RG['heldout-3']['A_agent']),
          ('Set 4, DQL levels', RG['heldout-4']['DQL_levels']), ('Set 4, P', RG['heldout-4']['P_one_shot']), ('Set 4, A', RG['heldout-4']['A_agent'])]
if HAS_AM: groups.append(('Set 4, A-model', RG['heldout-4']['per_condition']['Am']))
CL = [('wrong_numbers', 'Wrong numbers'), ('abstained', 'Abstained'), ('missing_or_extra_columns', 'Label column'), ('grain_or_shape', 'Grain or shape'), ('rounding_only', 'Rounding only'), ('other', 'Other')]
rows = [[g, str(v['strict_wrong'])] + [f"{v['classes'][c]} ({round(100 * v['classes'][c] / v['strict_wrong']) if v['strict_wrong'] else 0}%)" for c, _ in CL] for g, v in groups]
add(TABLE(['Group', 'Wrong'] + [n for _, n in CL], rows, [1900, 800, 1150, 1100, 1150, 1150, 1150, 900], ['left'] + ['right'] * 7))
add(CAP('**Table 11.** Strict-wrong answers by class (first class that applies). *Label column*: right rows and numbers, a label column missing, substituted or formatted differently. *Grain or shape*: a different number of rows, such as a list for a total.'))
h3a, h4a = RG['heldout-3']['all_conditions'], RG['heldout-4']['all_conditions']
gap = lambda v: 100 * (v['lenient'] - v['strict']) / v['n']
s55 = RG['sonnet55_all_conditions_both_sets']
add(P(f'On set 3, {h3a["strict"]:,} of {h3a["n"]:,} answers were correct under the strict rule and {h3a["lenient"]:,} under the lenient rule (+{gap(h3a):.1f} points; {h3a["lenient_rounding"]:,} when rounding differences are also forgiven). The gap is not uniform: +{gap(RG["heldout-3"]["DQL_levels"]):.1f} points for DQL levels, +{gap(RG["heldout-3"]["P_one_shot"]):.1f} for one-shot SQL and +{gap(RG["heldout-3"]["A_agent"]):.1f} for the agent on set 3; on set 4, +{gap(RG["heldout-4"]["DQL_levels"]):.1f} for DQL levels against +{gap(RG["heldout-4"]["P_one_shot"]):.1f} for one-shot SQL and +{gap(RG["heldout-4"]["A_agent"]):.1f} for the agent. The kinds of error differ. DQL\'s errors are mostly wrong numbers and abstentions on answerable questions; the agent never abstained on an answerable question, and most of its errors on set 4 were label columns. Across both sets, Claude Sonnet 5.5\'s {s55["strict_wrong"]} wrong answers in all conditions were {round(100 * s55["class_shares"]["wrong_numbers"])}% wrong numbers, {round(100 * s55["class_shares"]["missing_or_extra_columns"])}% label columns, {round(100 * s55["class_shares"]["abstained"])}% abstentions and {round(100 * s55["class_shares"]["grain_or_shape"])}% grain or shape.'))

_r4, _r5 = RT['heldout-4']['levels'], RT['heldout-5']['levels']
add(P(f'**Where added context lost answers.** More context did not always help. W2 answered {AC4["W2"]["k"]} questions of set 4 correctly against {AC4["L2"]["k"]} at L2, {AC4["L3"]["k"]} at L3 and {AC4["WB"]["k"]} at WB, and {AC5["W2"]["k"]} of set 5 against {AC5["L2"]["k"]}, {AC5["L3"]["k"]} and {AC5["WB"]["k"]}. W2 itself answered almost every question with drafted SQL ({RT["heldout-4"]["W2_routes"].get("drafted", 0)} and {RT["heldout-5"]["W2_routes"].get("drafted", 0)} of 200). Of the questions W2 answered correctly and WB did not ({_r4["WB"]["W2_right_level_wrong"]} on set 4 and {_r5["WB"]["W2_right_level_wrong"]} on set 5), WB had answered {_r4["WB"]["lost_by_route"].get("trusted", 0)} and {_r5["WB"]["lost_by_route"].get("trusted", 0)} with a governed label: the business layer\'s metrics took questions they did not fit, which drafted SQL had answered correctly. At L2 and L3 on set 4, {_r4["L2"]["lost_by_route"].get("no_answer", 0)} of {_r4["L2"]["W2_right_level_wrong"]} and {_r4["L3"]["lost_by_route"].get("no_answer", 0)} of {_r4["L3"]["W2_right_level_wrong"]} such losses were stops on answerable questions ({_r5["L2"]["lost_by_route"].get("no_answer", 0)} of {_r5["L2"]["W2_right_level_wrong"]} and {_r5["L3"]["lost_by_route"].get("no_answer", 0)} of {_r5["L3"]["W2_right_level_wrong"]} on set 5). This breakdown is exploratory and describes these runs only.'))

add(H2('6.8  Robustness on database variants'))
rows = []
for key, name in [('heldout-4:P', 'P, one-shot SQL'), ('heldout-4:A', 'A, agent'), ('heldout-4:Am', 'A-model, agent + modeling'), ('heldout-4:L2', 'L2'), ('heldout-4:L3', 'L3'),
                  ('heldout-4:W2', 'W2'), ('heldout-4:WB', 'WB'), ('heldout-3:DQL levels', 'Set 3, all DQL levels, all models'), ('heldout-3:P', 'Set 3, P, all models'), ('heldout-3:A', 'Set 3, A, two models')]:
    v = VP.get(key)
    if not v: continue
    rows.append([name, str(v['n']), str(v['strict']), str(v['robust']), str(v['fragile']), str(v['not_checkable']), f"{100 * v['robust'] / v['n']:.1f}–{100 * (v['robust'] + v['not_checkable']) / v['n']:.1f}%"])
add(TABLE(['Condition (set 4 unless stated)', 'Answers', 'Strict-correct', 'Survive', 'Fragile', 'Not checkable', 'Surviving share'], rows, [3000, 900, 1100, 900, 900, 1200, 1360]))
add(CAP('**Table 12.** Strict-correct answers re-checked on two altered copies of the warehouse (Section 5). The surviving share counts not-checkable answers as wrong (lower) and as right (upper).'))
VPP = VAR['set4_paired']
_w = lambda k: VPP[k]['lower']
add(P(f'On the public set 3, no strict-correct answer of any model or condition was fragile once the variants preserved every question\'s meaning: the small warehouse did not, by this test, make coincidentally correct answers common. On set 4, {VP["heldout-4:DQL levels"]["fragile"]} of {VP["heldout-4:DQL levels"]["strict"]} strict-correct DQL answers, {VP["heldout-4:P"]["fragile"]} one-shot answers, {VP["heldout-4:A"]["fragile"]} agent answers and {VP.get("heldout-4:Am", {}).get("fragile", 0)} A-model answers were fragile; while set 4 is sealed we cannot check whether these reflect answer errors or questions that the variants made ambiguous. Counting only surviving answers as correct retains the advantage over one-shot SQL and establishes no advantage over A-model: W2 {_w("W2 vs Am")["k_left"]} against A-model {_w("W2 vs Am")["k_right"]} (exploratory {pstr(_w("W2 vs Am")["p_raw"])}), against the agent {_w("W2 vs A")["k_right"]} ({pstr(_w("W2 vs A")["p_raw"])}) and against one-shot SQL {_w("W2 vs P")["k_right"]} ({pstr(_w("W2 vs P")["p_raw"])}); A-model against the agent {pstr(_w("Am vs A")["p_raw"])}. The clone-based variants catch hard-coded values, missing filters and totals that hold only on the original rows; they do not catch every kind of error. Until the fragile set-4 cases are adjudicated, these checks add evidence; they are not a semantic validation of the answers.'))

TAXF = os.path.join(HERE, '..', 'taxonomy', 'taxonomy.json')
if os.path.exists(TAXF) and os.path.exists(os.path.join(HERE, 'paper_taxonomy_section.py')):
    TAX = json.load(open(TAXF))
    exec(open(os.path.join(HERE, 'paper_taxonomy_section.py')).read())

# ---- 7
add(H1('7  Changes to the system during the study'))
add(P('We changed DQL while running the benchmark and disclose each change with its source of evidence.'))
add(LIST([
    '**Near-fit certified blocks** (both measured builds). A block tag was treated as its name, and a block that only nearly fitted a question was served as governed before the drafter could answer. Found on the development set.',
    '**Metric name overriding the reading** (both builds). A question term that named a metric replaced the measure the model had read, so "the expense reserve amount of all claims" was measured as a count of claims. Found on the development set.',
    '**Short table names on DuckDB** (build 627009a1, levels LB and WB). A final check on the executed SQL rejected main.claim for the inspected acme_insurance.main.claim. The first half of this fix came from the development set; the second half was found from set-3 stop codes, after which LB and WB were rerun for every model on set 3; set 4 ran on the fixed build from the start. This is why set 3 is spent (Section 4.2).',
    '**Lists answered with a count** (written, not in any measured build). A list answered by a count metric that merged records is no longer labelled governed. Found on the development set; it is not in the build frozen for set 5 (627009a1), which keeps set 5 on the build already measured on set 4.',
], 'decimal'))
add(P('No change was made in response to set-4 or set-5 results.'))

# ---- 8
add(H1('8  Deviations from our own protocol'))
add(P('Our benchmark methodology (docs/methodology.md in the benchmark repository) says that numbers are published only from a released DQL version, with repeated runs, on an audited answer key. This paper meets none of the three fully: it reports development builds and single runs, and references audited on samples only. We list these and the other departures so that a reader can weigh them.'))
add(LIST([
    '**Unreleased builds.** All results come from development builds 49c0e1cb and 627009a1 of DQL 1.17.3. The experiments were run on these development commits, and a later tagged release that contains them will not make them release-build experiments; the release serves reproducibility only. The set-5 build was frozen at commit 627009a1 rather than at a tagged release.',
    '**Single runs.** Each condition ran once. Earlier repeated runs moved single levels by up to 4 of 40 questions.',
    '**Audit on samples.** The audit covers a random sample of each sealed set (Section 4.5); the other items are unaudited.',
    f'**Set 5: runtime failures re-asked.** In 2 of Claude Sonnet 5.5\'s 200 L3 answers on set 5, DQL\'s local runtime dropped the connection and gave no answer. Before re-asking, we added a rule to the freeze record (insurance/FREEZE-SET5.md, addendum of 3 October 2026): such answers are infrastructure failures, asked once more, and the first recording is kept and reported beside the result. The rule was decided after the failure counts were known. L3 answered {S5R["accuracy"]["heldout-5"]["sonnet55"]["L3"]["k"]} of 200 as recorded and {AC5["L3"]["k"]} after the re-ask; H1 is unaffected and no conclusion changes.',
    '**Set 5: statistics script.** The pre-registration says the set-3/4 statistics script runs unchanged except for the set name. Before set 5 was scored it gained outputs (A-model comparisons, trust precision over all questions, the consistent-column check) and a switch that selects set 5 with its pre-registered seed and families, and it now takes each DQL answer\'s rows from the run that answered the question (two set-5 questions shared a query whose shown rows differed). The functions that compute the pre-registered tests (Wilson, bootstrap, exact McNemar, Holm) are unchanged, and the set-4 output is identical with and without the switch.',
    '**Set 5: silent-error rate.** The pre-registered silent-error rate σ is reported for DQL levels as ω (Section 5), which has the same formula; the baselines\' σ = (n − k)/n is not reported, because comparing it with ω would be misleading (Section 5).',
    '**Set 5: secondary models.** GPT-6 Sol, a pre-registered secondary model and the writer of set 5, was not run on set 5 for this version. Qwen 3.8 27B, the other, is still running at the time of writing. Two incomplete Qwen attempts at WB (one stopped to raise an open-file limit, one paused to free the machine) were discarded before any of their answers were scored.',
    '**Analyses added after the pre-registration** and reported as secondary: the consistent-column check, trust precision over answerable and unanswerable questions together, the database variants (whose design was revised once, Section 5) and the taxonomy of wrong trusted answers.',
    '**Bootstrap seed.** Sets 3 and 4 use seed 20260930; set 5\'s primary interval uses seed 5, as pre-registered.',
    '**Commit identifiers.** The benchmark repository\'s history was rewritten before its first push, to remove three internal planning documents and a personal e-mail address. The pre-registration text is unchanged, but its commit identifier changed from f2e835a to 6f60a71; docs/HISTORY-REWRITE.md maps every old identifier to its published one.',
    '**Exposures of sealed questions,** listed in Sections 4.2 and 4.6 and in docs/SEALING.md.',
]))

# ---- 9
add(H1('9  Limitations and threats to validity'))
add(LIST([
    '**Post-hoc choices.** W2 was made the headline level, and A-model was added, after results were seen. The corrected tests in Section 6 do not remove this selection effect; set 5 tests the W2-against-A-model comparison as its pre-registered primary hypothesis (Section 6.1).',
    '**Different builds.** LB and WB ran on a build that includes a fix the other levels lack; comparisons across those levels mix a system change with a context change.',
    '**Warehouse size.** With 2 policies and 2 claims, many answers are one or two rows and the agent can explore the schema in a few calls. The study tests reasoning over an awkward schema, not scale.',
    '**One model on sets 4 and 5.** Sets 4 and 5 report Claude Sonnet 5.5 only; set 3 covers seven models at about ±14 points.',
    '**Single runs.** Each condition ran once. Earlier repeated runs moved individual levels by up to 4 of 40 questions.',
    '**Unequal reasoning settings.** Claude runs used DQL\'s per-step effort, GPT runs one fixed level each, and the Codex CLI adds its own instructions to every call.',
    '**AI-written references, audited on samples.** An author audited samples of sets 4 and 5 (Section 4.5); unsampled items may still hold reference errors. The question writers are AI models: Claude for sets 3 and 4, GPT for set 5 (Section 4.2).',
    '**Timing.** Runs shared one laptop and ran in parallel; reported times are indicative.',
    '**Not comparable with leaderboards.** BIRD and Spider 2.0 use many databases, larger schemas, other dialects and other protocols; our figures must not be read beside their scores.',
    '**One model in the pre-registered test.** GPT-6 Sol was not run on set 5 and Qwen 3.8 27B is still running at the time of writing, so the pre-registered results rest on Claude Sonnet 5.5.',
    '**Conflict of interest.** The authors develop DQL (see the statement below).',
]))

# ---- 10
add(H1('10  Conclusion'))
if HAS_AM:
    tm = PR4['W2_vs_Am']; tam = PR4['Am_vs_A']
    _u5 = [U5[L]['k'] for L in ('L2', 'L3', 'W2', 'WB')]
    add(P(f'This case study supports a narrow claim. In a pre-registered test on 200 questions written by a GPT model, DQL with modeled context (W2) answered {pct(AC5["W2"]["acc"])} correctly against {pct(AC5["P"]["acc"])} for one-shot SQL and {pct(AC5["Am"]["acc"])} for an agent given the same modeling knowledge as text. The advantage over that agent ({dpt(H1T)} points, {pstr(H1T["p_raw"])}) held under the strict rule and disappeared under the lenient one, so it is associated with the columns the answers returned, consistent with DQL\'s instructions on answer shape that the agent did not have (Section 4.3); on an earlier, exploratory set the same comparison was not established ({dpt(tm)} points, {pstr(tm["p_raw"])}). Governance labels need validation of their own: at the dbt-metric levels {P5L23["trusted_right"]} of {P5L23["trusted"]} governed answers were right under the strict rule, short of the pre-registered 95%; business-layer labels were wrong in {T4["WB"]["W_T"]} of {T4["WB"]["T"]} cases on set 4 and {T5["WB"]["W_T"]} of {T5["WB"]["T"]} on set 5; and no DQL level declined more unanswerable questions than the agents. For practitioners the main lesson is this distinction: a layer can make drafted SQL more accurate while its labels remain unreliable, so the two must be measured separately. Methodologically, pooled figures on a small set can look decisive while resting on four questions, and a baseline without the same context can make a pipeline look better than it is. We recommend that evaluations of governed or abstaining text-to-SQL systems report trust precision, coverage and abstention together with accuracy; give baselines the same knowledge; count distinct questions; correct for multiple comparisons; check answers on altered databases; pre-register the main comparison; and disclose every system change and every departure from the held-out protocol.'))
else:
    add(P(f'Three findings survive the corrections in this revision. First, DQL\'s modeled context made drafted SQL substantially more accurate than one-shot SQL over table definitions: {pct(W2["acc"])} against {pct(P4["acc"])} on 200 held-out questions, significant under both grading rules. Second, an advantage over an agent that explores the database is not established: the difference was not significant after correction, and its sign depended on the grading rule. Third, DQL\'s labels and abstention are not yet as reliable as its design intends. dbt-metric labels were mostly right but rare, business-layer labels were wrong about half the time, and DQL answered more unanswerable questions than the agent. The methodological lesson is the one that most changed this paper: pooled figures on a small set can look decisive while resting on four questions. We recommend that evaluations of governed or abstaining text-to-SQL systems report trust precision, coverage and abstention together with accuracy; count distinct questions; correct for multiple comparisons; and disclose every system change and every departure from the held-out protocol.'))

# ---- statements
add(H1('Statements'))
add(P('**Data and code availability.** The benchmark harness, conditions, development-set audit, recorded model outputs for the development set and set 3, statistics script (question-level bootstrap, McNemar and Holm), paper generator and the set-5 pre-registration are public at github.com/duckcode-ai-labs/dql-benchmarks. Sets 4 and 5, with their reports and audits, are added when this paper is posted; their hashes are already published there. DQL is open source under the Apache License 2.0 [16]. The experiments ran on development commits 49c0e1cb and 627009a1, public as branches of github.com/duckcode-ai-labs/dql; a tagged release containing them will be published for reproducibility, and the run archive (run stores, cassettes and project copies) will be deposited with a persistent identifier. Each result file records the DQL build, model identifier, CLI version and run settings.'))
add(P('**Use of generative AI.** This study made substantial use of AI tools, which we disclose consistent with arXiv\'s policy on generative AI tools. An AI coding assistant (Claude, Anthropic) wrote most of the benchmark harness and analysis code, ran the experiments, checked the bibliography against primary sources and drafted this manuscript under the authors\' direction. AI agents wrote the question sets and their reference SQL (Claude agents for sets 3 and 4; GPT-6 Sol for set 5) and drafted the business layer, which a second agent checked and a person certified. The root-cause and lenient-grade classifications in Section 6.9 and the redesign of the database variants were made by the AI assistant and are not yet confirmed by a person; the development-set reference disputes and the audits of sets 4 and 5 (Section 4.5) are an author\'s, and two AI models looked over the audit samples only as a second check. Every number in the text, tables and figures is generated by scripts from the saved result files. The authors have reviewed the manuscript and each reference and take full responsibility for its content.'))
add(P('**Competing interests.** The authors develop DQL at DuckCode AI Labs, which offers commercial services around it.'))

# ---- references
add(H1('References'))
REFS = [
    ('J. Sequeda, D. Allemang, B. Jacob. A Benchmark to Understand the Role of Knowledge Graphs on Large Language Model\'s Accuracy for Question Answering on Enterprise SQL Databases. arXiv preprint, 2023. ', 'arXiv:2311.07509', 'https://arxiv.org/abs/2311.07509'),
    ('data.world. cwd-benchmark-data: ACME Insurance schema, data, ontology, mappings and questions. GitHub, 2023. ', 'github.com/datadotworld/cwd-benchmark-data', 'https://github.com/datadotworld/cwd-benchmark-data'),
    ('J. Ganz, B. Perigaud. Semantic Layer vs. Text-to-SQL: 2026 Benchmark Update. dbt Developer Blog, 7 April 2026. ', 'docs.getdbt.com', 'https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026'),
    ('dbt Labs. dbt-llm-sl-bench. GitHub. ', 'github.com/dbt-labs/dbt-llm-sl-bench', 'https://github.com/dbt-labs/dbt-llm-sl-bench'),
    ('Cube. semantic-layer-benchmark. GitHub, 2026. ', 'github.com/cubedevinc/semantic-layer-benchmark', 'https://github.com/cubedevinc/semantic-layer-benchmark'),
    ('M. Rumiantsau, I. Fokeev. Semantic Layers for Reliable LLM-Powered Data Analytics: A Paired Benchmark of Accuracy and Hallucination Across Three Frontier Models. arXiv preprint, 2026. ', 'arXiv:2604.25149', 'https://arxiv.org/abs/2604.25149'),
    ('T. Jin, Y. Choi, Y. Zhu, D. Kang. Pervasive Annotation Errors Break Text-to-SQL Benchmarks and Leaderboards. arXiv preprint (v3), 2026. ', 'arXiv:2601.08778', 'https://arxiv.org/abs/2601.08778'),
    ('T. Jin, Y. Choi, Y. Zhu, D. Kang. Text-to-SQL Benchmarks are Broken: An In-Depth Analysis of Annotation Errors. CIDR 2026. ', 'vldb.org/cidrdb', 'https://www.vldb.org/cidrdb/papers/2026/p5-jin.pdf'),
    ('J. Li, B. Hui, G. Qu, J. Yang, B. Li, B. Li, et al. Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs. Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track, pp. 42330–42357. ', 'doi:10.52202/075280-1835', 'https://doi.org/10.52202/075280-1835'),
    ('F. Lei, J. Chen, Y. Ye, R. Cao, et al. Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows. ICLR 2025, pp. 28691–28735. ', 'arXiv:2411.07763', 'https://arxiv.org/abs/2411.07763'),
    ('BIRD Team (HKU) and Google Cloud. LiveSQLBench: A Dynamic and Contamination-Free Benchmark for Evaluating LLMs on Real-World Text-to-SQL Tasks. Accessed 30 September 2026. ', 'livesqlbench.ai', 'https://livesqlbench.ai/'),
    ('Q. McNemar. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. Psychometrika 12(2):153–157, 1947. ', 'doi:10.1007/BF02295996', 'https://doi.org/10.1007/BF02295996'),
    ('E. B. Wilson. Probable Inference, the Law of Succession, and Statistical Inference. Journal of the American Statistical Association 22(158):209–212, 1927. ', 'doi:10.1080/01621459.1927.10502953', 'https://doi.org/10.1080/01621459.1927.10502953'),
    ('J. A. Hanley, A. Lippman-Hand. If Nothing Goes Wrong, Is Everything All Right? Interpreting Zero Numerators. JAMA 249(13):1743–1745, 1983. ', 'doi:10.1001/jama.1983.03330370053031', 'https://doi.org/10.1001/jama.1983.03330370053031'),
    ('dbt Labs. About MetricFlow. dbt Developer Hub. Accessed 30 September 2026. ', 'docs.getdbt.com', 'https://docs.getdbt.com/docs/build/about-metricflow'),
    ('DuckCode AI Labs. DQL. GitHub. ', 'github.com/duckcode-ai-labs/dql', 'https://github.com/duckcode-ai-labs/dql'),
    ('R. El-Yaniv, Y. Wiener. On the Foundations of Noise-free Selective Classification. Journal of Machine Learning Research 11(53):1605–1641, 2010. ', 'jmlr.org', 'https://www.jmlr.org/papers/v11/el-yaniv10a.html'),
    ('Y. Geifman, R. El-Yaniv. Selective Classification for Deep Neural Networks. Advances in Neural Information Processing Systems 30 (NIPS 2017). ', 'arXiv:1705.08500', 'https://arxiv.org/abs/1705.08500'),
    ('R. Richardson. What Predicts Correctness in Text-to-SQL? A Selective-Prediction Study. arXiv preprint, 2026. ', 'arXiv:2607.06799', 'https://arxiv.org/abs/2607.06799'),
    ('K. Chen, Y. Chen, N. Koudas, X. Yu. Reliable Text-to-SQL with Adaptive Abstention. Proceedings of the ACM on Management of Data 3(1):1–30, 2025. ', 'doi:10.1145/3709719', 'https://doi.org/10.1145/3709719'),
    ('B. Wang, Y. Gao, Z. Li, J.-G. Lou. Know What I don\'t Know: Handling Ambiguous and Unknown Questions for Text-to-SQL. Findings of ACL 2023, pp. 5701–5714. ', 'doi:10.18653/v1/2023.findings-acl.352', 'https://doi.org/10.18653/v1/2023.findings-acl.352'),
    ('S. Holm. A Simple Sequentially Rejective Multiple Test Procedure. Scandinavian Journal of Statistics 6(2):65–70, 1979. ', 'jstor.org/stable/4615733', 'https://www.jstor.org/stable/4615733'),
    ('C. A. Field, A. H. Welsh. Bootstrapping Clustered Data. Journal of the Royal Statistical Society Series B 69(3):369–390, 2007. ', 'doi:10.1111/j.1467-9868.2007.00593.x', 'https://doi.org/10.1111/j.1467-9868.2007.00593.x'),
    ('G. Lee, W. Chay, S. Cho, E. Choi. TrustSQL: Benchmarking Text-to-SQL Reliability with Penalty-Based Scoring. arXiv preprint, 2024. ', 'arXiv:2403.15879', 'https://arxiv.org/abs/2403.15879'),
    ('M. Dong, N. A. Kumar, Y. Hu, A. Chauhan, C.-W. Hang, S. Chang, L. Pan, W. Lan, H. Zhu, J. Jiang, P. Ng, Z. Wang. PRACTIQ: A Practical Conversational Text-to-SQL dataset with Ambiguous and Unanswerable Queries. NAACL 2025, pp. 255–273. ', 'doi:10.18653/v1/2025.naacl-long.13', 'https://doi.org/10.18653/v1/2025.naacl-long.13'),
    ('R. Zhong, T. Yu, D. Klein. Semantic Evaluation for Text-to-SQL with Distilled Test Suites. EMNLP 2020. ', 'arXiv:2010.02840', 'https://arxiv.org/abs/2010.02840'),
]
for i, (t, lt, url) in enumerate(REFS, 1):
    add(para(run(f'[{i}]\t') + run(t) + LINK(lt, url), style='Reference'))

# ---------------------------------------------------------------- package
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>')
document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{"".join(B)}{sect}</w:body></w:document>'
BODY, HEAD = 'Times New Roman', 'Times New Roman'
def sty(sid, name, rpr, ppr='', based='Normal', nxt='Normal', typ='paragraph'):
    return f'<w:style w:type="{typ}" w:styleId="{sid}"><w:name w:val="{name}"/><w:basedOn w:val="{based}"/><w:next w:val="{nxt}"/><w:qFormat/><w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>'
styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    f'<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="{BODY}" w:hAnsi="{BODY}" w:cs="{BODY}" w:eastAsia="{BODY}"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
    f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="both"/></w:pPr><w:rPr><w:rFonts w:ascii="{BODY}" w:hAnsi="{BODY}" w:cs="{BODY}"/><w:color w:val="1B2630"/><w:sz w:val="22"/></w:rPr></w:style>'
    + sty('Title', 'Title', '<w:b/><w:sz w:val="34"/><w:szCs w:val="34"/>', '<w:jc w:val="center"/><w:spacing w:before="240" w:after="200" w:line="264" w:lineRule="auto"/>')
    + sty('Authors', 'Authors', '<w:sz w:val="23"/>', '<w:jc w:val="center"/><w:spacing w:after="60"/>')
    + sty('AbstractHeading', 'Abstract Heading', '<w:b/><w:sz w:val="22"/>', '<w:jc w:val="center"/><w:spacing w:before="280" w:after="80"/><w:keepNext/>')
    + sty('Abstract', 'Abstract', '<w:sz w:val="20"/>', '<w:ind w:left="720" w:right="720"/><w:jc w:val="both"/><w:spacing w:after="100"/>')
    + sty('Heading1', 'heading 1', '<w:b/><w:sz w:val="26"/><w:szCs w:val="26"/>', '<w:keepNext/><w:keepLines/><w:jc w:val="left"/><w:spacing w:before="320" w:after="120"/><w:outlineLvl w:val="0"/>')
    + sty('Heading2', 'heading 2', '<w:b/><w:i/><w:sz w:val="23"/><w:szCs w:val="23"/>', '<w:keepNext/><w:keepLines/><w:jc w:val="left"/><w:spacing w:before="220" w:after="80"/><w:outlineLvl w:val="1"/>')
    + sty('Caption', 'caption', '<w:sz w:val="19"/><w:color w:val="3A4A55"/>', '<w:jc w:val="center"/><w:spacing w:before="80" w:after="220"/>')
    + sty('TableText', 'Table Text', '<w:sz w:val="18"/><w:szCs w:val="18"/>', '<w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/>')
    + sty('Equation', 'Equation', '', '<w:spacing w:before="80" w:after="120"/><w:jc w:val="left"/>')
    + sty('ListParagraph', 'List Paragraph', '', '<w:ind w:left="360" w:hanging="360"/><w:spacing w:after="80"/>')
    + sty('Reference', 'Reference', '<w:sz w:val="19"/>', '<w:ind w:left="540" w:hanging="540"/><w:jc w:val="left"/><w:spacing w:after="60"/><w:tabs><w:tab w:val="left" w:pos="540"/></w:tabs>')
    + '</w:styles>')
abst = ('<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
        '<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>')
nums = ''.join(f'<w:num w:numId="{i}"><w:abstractNumId w:val="{0 if k == "bullet" else 1}"/>{"<w:lvlOverride w:ilvl=\"0\"><w:startOverride w:val=\"1\"/></w:lvlOverride>" if k != "bullet" else ""}</w:num>' for i, k in enumerate(NUMS, 1))
numbering = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">{abst}{nums}</w:numbering>'
footer = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
          '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
          '<w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>1</w:t></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '<Relationship Id="rIdNum" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
        '<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
        + ''.join(f'<Relationship Id="rIdImg{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/fig{i}.png"/>' for i in range(1, len(IMG) + 1))
        + ''.join(f'<Relationship Id="rIdL{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="{html.escape(u)}" TargetMode="External"/>' for i, u in enumerate(LINKS, 1))
        + '</Relationships>')
ctypes = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
          '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
          '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>')
root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>')
core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>Context, Trust Labels and Abstention in a Governed Text-to-SQL Layer: An Exploratory Case Study on an Insurance Warehouse</dc:title><dc:creator>DuckCode AI Labs</dc:creator></cp:coreProperties>')
out = os.path.join(HERE, 'paper.docx')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', ctypes); z.writestr('_rels/.rels', root_rels); z.writestr('docProps/core.xml', core)
    z.writestr('word/document.xml', document); z.writestr('word/styles.xml', styles); z.writestr('word/numbering.xml', numbering)
    z.writestr('word/footer1.xml', footer); z.writestr('word/_rels/document.xml.rels', rels)
    for i, png in enumerate(IMG, 1): z.write(png, f'word/media/fig{i}.png')
print(out, os.path.getsize(out), 'bytes;', len(IMG), 'figures;', len(LINKS), 'links;', len(NUMS), 'lists')

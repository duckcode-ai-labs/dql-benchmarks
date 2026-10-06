# Write arxiv-metadata.md from the built paper.docx: the fields the arXiv submission form asks for, with the
# abstract taken verbatim from the paper and an ASCII-only copy for the form.   python3 arxiv_metadata.py
import html, os, re, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
x = zipfile.ZipFile(os.path.join(HERE, 'paper.docx')).read('word/document.xml').decode()
paras = [html.unescape(re.sub(r'<[^>]+>', '', p)).strip() for p in re.findall(r'<w:p[ >].*?</w:p>', x, flags=re.S)]
paras = [p for p in paras if p]
title = paras[0]
authors = paras[1]
abstract = paras[paras.index('Abstract') + 1]
tables = len({m for m in re.findall(r'^Table (\d+)\.', '\n'.join(paras), flags=re.M)})
figures = len({m for m in re.findall(r'^Figure (\d+)\.', '\n'.join(paras), flags=re.M)})
ascii_map = {'−': '-', '–': '-', '—': '-', '’': "'", '‘': "'", '“': '"', '”': '"', 'π': 'pi', 'κ': 'kappa', 'ω': 'omega', 'α': 'alpha', '×': 'x', '≥': '>=', '≤': '<=', '…': '...'}
abstract_ascii = ''.join(ascii_map.get(c, c) for c in abstract)
bad = sorted({c for c in abstract_ascii if ord(c) > 127})
out = f"""# arXiv submission fields

Generated from paper.docx by arxiv_metadata.py; re-run after any change to the paper.

- **Title:** {title}
- **Authors:** {authors}{'  <- fill in before submitting' if '[' in authors else ''}
- **Primary category:** cs.DB (Databases); **cross-lists:** cs.CL, cs.AI
- **Comments:** <pages> pages, {figures} figures, {tables} tables. Code, data, pre-registration and run archive: https://github.com/duckcode-ai-labs/dql-benchmarks
- **License:** the author's choice (CC BY 4.0 lets others reuse the text with attribution; the arXiv default licence does not)
- **Abstract length:** {len(abstract)} characters (arXiv limit 1,920)

## Abstract (as in the paper)

{abstract}

## Abstract (ASCII, for the form)

{abstract_ascii}
""" + (f"\nNon-ASCII characters left in the ASCII abstract: {' '.join(bad)}\n" if bad else '')
open(os.path.join(HERE, 'arxiv-metadata.md'), 'w').write(out)
print(f'wrote arxiv-metadata.md: abstract {len(abstract)} chars, {figures} figures, {tables} tables' + (f'; non-ASCII left: {bad}' if bad else ''))

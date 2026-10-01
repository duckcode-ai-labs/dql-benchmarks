#!/bin/zsh
# Regenerate the paper's numbers from the saved reports and rebuild the page.
cd "$(dirname "$0")" && python3 paper_numbers.py > paper_numbers.json && python3 -c "
t=open('whitepaper.template.html').read(); d=open('paper_numbers.json').read().strip()
open('whitepaper.html','w').write(t.replace('/*DATA*/', d))" && echo rebuilt

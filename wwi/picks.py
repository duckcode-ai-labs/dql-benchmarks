import json,re,sqlite3,sys
run,arm,setname=sys.argv[1:4]
ROOT='.'
WORK='work/wwi'
TABLE=re.compile(r"\b(?:from|join)\s+([a-z_]+\.[a-z_]+)",re.I)
if setname=='fresh':
    rows=json.load(open('wwi/fresh-questions.json'))
    want={r['question'].strip():{t.lower() for t in r['tables']} for r in rows}
else:
    rows=json.load(open(f'{WORK}/dataset/evaluation.json'))
    want={r['question'].strip():set(TABLE.findall(r['SQL'].lower())) for r in rows if r['question_id'] not in (4,27)}
db=sqlite3.connect(f'{WORK}/runs/{run}/{arm}/pass-1/project/.dql/local/agent-runs.sqlite')
dec=0
for q,p in db.execute('select question,payload_json from agent_runs order by rowid'):
    need=want.get(q.strip())
    if not need: continue
    story=json.loads(p).get('diagnosticReceiptV9',{}).get('story',[])
    title=next((s.get('title','') for s in story if s.get('title','').startswith('Chose the table')),'')
    picked={'.'.join(x.lower().split('.')[-2:]) for x in re.findall(r'[a-z_]+\.[a-z_]+\.[a-z_]+',title,re.I)}
    miss=need-picked
    d=len([x for x in picked if x.startswith('legacy.')])
    dec+=d
    if miss: print(f"MISS {sorted(miss)} | {sorted(x.replace('legacy.','L:') for x in picked)} | {q[:70]}")
print('decoys picked',dec)

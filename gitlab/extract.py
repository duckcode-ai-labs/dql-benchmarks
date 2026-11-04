"""Business tables of GitLab's analytics dbt project, for the domain truth set (Q0).

python -I gitlab/extract.py <manifest.json> gitlab/tables.json

A business table is one a business question should be answered from: a
dim_/fct_/bdg_/mart_/rpt_/map_/pump_ model, or a model in the common*/marts
folders that is not a prep or staging model. Raw, staging, prep, workspace and
legacy models are left out; their layer is not what the truth set measures.
"""
import json, re, sys

manifest_path, out_path = sys.argv[1], sys.argv[2]
m = json.load(open(manifest_path))
project = m['metadata']['project_name']
rows = []
for uid, v in m['nodes'].items():
    if v['resource_type'] != 'model' or v.get('package_name') != project:
        continue
    if v.get('config', {}).get('materialized') == 'ephemeral':
        continue
    path, name = v.get('original_file_path', ''), v['name']
    if '/sources/' in path or name.endswith('_source') or '/legacy/' in path or '/workspaces/' in path or name.startswith('wk_'):
        continue
    if '/common_prep/' in path or name.startswith('prep_'):
        continue
    if not (re.match(r'(dim|fct|bdg|mart|rpt|map|pump)_', name) or '/common' in path or '/marts/' in path):
        continue
    rows.append({
        'id': uid,
        'name': name,
        'path': path,
        'schema': v.get('schema'),
        'tags': v.get('tags', []),
        'description': re.sub(r'\s+', ' ', v.get('description') or '').strip()[:400],
        'columns': list((v.get('columns') or {}).keys())[:30],
    })
rows.sort(key=lambda r: r['id'])
json.dump(rows, open(out_path, 'w'), indent=1)
print(len(rows), 'business tables')

#!/bin/bash
# Q5 "NBA in a crowd": the drafted NBA project (DA) inside a model too large to
# show whole. The NBA warehouse is copied with two unrelated data sets added
# as decoy schemas (the postcard data mart, and the owner's synthetic
# enterprise lab), drafted into their own Domains in hybrid mode. The NBA
# questions are then asked with Ask's area routing on and off.
#   DQL_CLI=<zlens dist/index.js> LAB_DB=<enterprise.duckdb> bash nba/build-dx.sh
set -euo pipefail
B=$(cd "$(dirname "$0")/.." && pwd); W=$B/work; CLI=${DQL_CLI:?}; LAB=${LAB_DB:?}
DB=$W/nba/dx-warehouse/enterprise_dw.duckdb
mkdir -p "$(dirname "$DB")"; rm -f "$DB" "$DB.wal" "$W"/nba/dx-warehouse/nba_dx.duckdb
"$W/nba/.venv/bin/python" -I - "$DB" "$W/nba/dbt/nba_analysis.duckdb" "$W/postcard/source/datamart.duckdb" "$LAB" <<'PY'
import sys, duckdb
db, nba, postcard, lab = sys.argv[1:5]
c = duckdb.connect(db)
# The NBA objects as tables: dbt's views name their own database
# ("nba_analysis"), which a copy under another name would break.
c.execute(f"ATTACH '{nba}' AS nba_analysis (READ_ONLY)")
rows = c.execute("select schema_name, table_name from duckdb_tables() where database_name = 'nba_analysis' union all select schema_name, view_name from duckdb_views() where database_name = 'nba_analysis' and not internal").fetchall()
for schema, name in rows:
    c.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    c.execute(f'CREATE OR REPLACE TABLE "{schema}"."{name}" AS SELECT * FROM nba_analysis."{schema}"."{name}"')
c.execute('DETACH nba_analysis')
print('nba objects', len(rows))
for alias, path, prefix in [('pc', postcard, 'postcard_'), ('lab', lab, 'ent_')]:
    c.execute(f"ATTACH '{path}' AS {alias} (READ_ONLY)")
    rows = c.execute(f"select schema_name, table_name from duckdb_tables() where database_name = '{alias}' union all select schema_name, view_name from duckdb_views() where database_name = '{alias}' and not internal").fetchall()
    for schema, name in rows:
        c.execute(f'CREATE SCHEMA IF NOT EXISTS "{prefix}{schema}"')
        c.execute(f'CREATE OR REPLACE TABLE "{prefix}{schema}"."{name}" AS SELECT * FROM {alias}."{schema}"."{name}"')
    c.execute(f'DETACH {alias}')
schemas = [r[0] for r in c.execute("select distinct schema_name from duckdb_tables() where schema_name like 'ent_%' or schema_name like 'postcard_%' order by 1").fetchall()]
open(db + '.schemas', 'w').write(','.join(schemas))
print('decoy schemas', len(schemas))
PY
P=$W/nba/projects/DX
rm -rf "$P"; rsync -a --exclude .dql/local --exclude .dql/cache --exclude logs "$W/nba/projects/DA/" "$P/"
[ -e "$P/.dql/connectors" ] || ln -sfn "$W/nba/connectors" "$P/.dql/connectors"
setcfg() { python3 -I - "$P/dql.config.json" "$@" <<'PY'
import json, sys
p, db, mode = sys.argv[1], sys.argv[2], sys.argv[3]
c = json.load(open(p)); c['connections']['default']['filepath'] = db; c['modeling'] = {'mode': 'hybrid'}
if mode != 'none': c.setdefault('metadataScopes', {}).setdefault('default', {})['mode'] = mode
json.dump(c, open(p, 'w'), indent=2)
PY
}
cd "$P"
setcfg "$DB" none
node "$CLI" sync warehouse . --database enterprise_dw --schemas "$(cat "$DB.schemas")" | grep -E "Warehouse catalog"
setcfg "$DB" selected_scopes
node "$CLI" model draft . --source warehouse --apply --passed-only | head -2
setcfg "$DB" dbt_plus_selected
node "$CLI" sync warehouse . | grep -E "Schema metadata|Warehouse catalog"
node "$CLI" compile . > /dev/null
python3 -I - <<'PY'
import json, collections
m = json.load(open('dql-manifest.json'))
ents = [e for e in m['modeling']['entities'].values() if e.get('status') != 'deprecated' and not e.get('useInstead')]
print('answer tables', len(ents), sorted(collections.Counter(e['domain'] for e in ents).items(), key=lambda x: -x[1]))
PY

# Database variants for test-suite evaluation (Zhong, Yu & Klein, EMNLP 2020): altered copies of the
# insurance warehouse on which a query that is right only by coincidence on the 2-policy original
# gives a different answer from the reference query. Only the dbt seed tables (schema main__seed)
# change; every relation in schema main is a view over them, so dbt models and DQL's business layer
# follow automatically.
#
#   V1 cloned book   a second, independent book of business: every entity copied with ids +100000,
#                    amounts x3+7, open/effective dates +400 days and close/end/expiration dates +410
#                    (durations change, so no ties), names replaced by distinct strings and street
#                    addresses and coordinates by distinct ones; cities, states, postal codes and codes kept. Catastrophes
#                    (named events that work as categories), Party_Role and the standalone FireClaim
#                    table are shared, not copied, so "the fire catastrophe" keeps its meaning.
#   V2 same period   as V1 but open/effective dates unchanged and close/end dates +10 days, so period
#                    filters now include the clone.
# A variant must keep every question meaningful: a question that names a property, person or event still
# identifies exactly one thing, and no question gains a tie. (An earlier design that also duplicated
# names, addresses and catastrophes broke those presuppositions and was dropped.)
#   .venv/bin/python analysis/insurance-2026-09-29/variants/build_variants.py <src.duckdb> <dst-dir>
# writes <dst-dir>/V1/acme_insurance.duckdb (and V2, V3) and prints integrity checks. The file must keep
# the name acme_insurance.duckdb: the views name their catalog after it.
import os, shutil, sys
import duckdb

SHIFT = 100000
KEEP = {'Party_Role', 'FireClaim', 'Catastrophe'}
SHARED_IDS = {'Catastrophe_Identifier'}
ID_EXTRA = {'Policy_Number', 'Company_Claim_Number', 'Company_Subclaim_Number'}
MEASURES = {'Claim_Amount', 'Policy_Amount'}
COORDS = {'Latitude_Value', 'Longitude_Value'}  # a different place, not a second property on the same spot
NAMES = {'First_Name', 'Middle_Name', 'Last_Name', 'Agreement_Name', 'Organization_Name', 'Alternate_Name'}
CLOSE_WORDS = ('Close', 'End', 'Expiration')


def columns(con, table):
    return con.execute("select column_name, data_type from information_schema.columns "
                       "where table_schema='main__seed' and table_name=? order by ordinal_position", [table]).fetchall()


def q(name):
    return '"' + name.replace('"', '""') + '"'


def clone_expr(col, typ, shift_open):
    c = q(col)
    if col in SHARED_IDS:
        return c
    if col.endswith('_Identifier') or col in ID_EXTRA:
        return f'{c} + {SHIFT}'
    if col in MEASURES:
        return f'{c} * 3 + 7'
    if col in COORDS:
        return f'{c} + 0.5'
    if typ == 'DATE':
        days = (shift_open + 10) if any(w in col for w in CLOSE_WORDS) else shift_open
        return f"{c} + INTERVAL {days} DAY" if days else c
    if col in NAMES and typ.startswith('VARCHAR'):
        return f"CASE WHEN {c} IS NULL THEN NULL ELSE 'Q' || substr(md5({c}), 1, 6) END"
    if col == 'Line_1_Address' and typ.startswith('VARCHAR'):
        return f"CASE WHEN {c} IS NULL THEN NULL ELSE CAST(Location_Address_Identifier + {SHIFT} AS VARCHAR) || ' Clone Road' END"
    return c


def clone_book(con, shift_open):
    tables = [r[0] for r in con.execute("select table_name from information_schema.tables "
                                        "where table_schema='main__seed' and table_type='BASE TABLE'").fetchall()]
    for t in tables:
        if t in KEEP:
            continue
        cols = columns(con, t)
        exprs = ', '.join(f'CAST({clone_expr(c, ty, shift_open)} AS {ty}) AS {q(c)}' for c, ty in cols)
        con.execute(f'CREATE TEMP TABLE _orig AS SELECT * FROM main__seed.{q(t)}')
        con.execute(f'INSERT INTO main__seed.{q(t)} SELECT {exprs} FROM _orig')
        con.execute('DROP TABLE _orig')


CHECKS = {
    'claims': 'select count(*) from main.claim',
    'policies': 'select count(*) from main.policy',
    'claim amounts': 'select count(*) from main.claim_amount',
    'claims without coverage': 'select count(*) from main.claim c where not exists (select 1 from main.claim_coverage cc where cc.claim_identifier = c.claim_identifier)',
    'amounts without claim': 'select count(*) from main.claim_amount a where not exists (select 1 from main.claim c where c.claim_identifier = a.claim_identifier)',
    'policy holders': "select count(*) from main.agreement_party_role where party_role_code = 'PH'",
    'total claim amount': 'select sum(claim_amount) from main.claim_amount',
    'catastrophes': 'select count(*) from main.catastrophe',
    'distinct addresses': 'select count(distinct line_1_address) from main.location_address',
    'distinct holder names': "select count(distinct pe.first_name || pe.last_name) from main.agreement_party_role r join main.person pe on pe.person_identifier = r.party_identifier where r.party_role_code = 'PH'",
    'tied longest close': "select count(*) from main.claim where date_diff('day', claim_open_date, claim_close_date) = (select max(date_diff('day', claim_open_date, claim_close_date)) from main.claim)",
}


def build(src, dst_dir, kinds=('V1', 'V2')):
    os.makedirs(dst_dir, exist_ok=True)
    out = {}
    for kind in kinds:
        os.makedirs(os.path.join(dst_dir, kind), exist_ok=True)
        dst = os.path.join(dst_dir, kind, 'acme_insurance.duckdb')
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copyfile(src, dst)
        con = duckdb.connect(dst)
        clone_book(con, shift_open=400 if kind == 'V1' else 0)
        con.execute('CHECKPOINT')
        con.close()
        out[kind] = dst
    return out


def check(path):
    con = duckdb.connect(path, read_only=True)
    try:
        return {k: con.execute(v).fetchone()[0] for k, v in CHECKS.items()}
    finally:
        con.close()


if __name__ == '__main__':
    src, dst_dir = sys.argv[1], sys.argv[2]
    print('original', check(src))
    for kind, path in build(src, dst_dir).items():
        print(kind, check(path))

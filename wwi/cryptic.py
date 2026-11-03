"""Build a copy of WideWorldImporters with cryptic, legacy-warehouse names.

    uv run --with 'psycopg[binary]' python wwi/cryptic.py build     # database wwicryptic
    uv run --with 'psycopg[binary]' python wwi/cryptic.py questions # fresh-questions-cryptic.json, checked

Every schema, table, view, column and constraint is renamed by one fixed rule:
split the name into English words, keep each word's first letter and its next
consonants up to three letters, and join them with underscores
(`sales.invoicelines.extendedprice` -> `sl.t_inv_lns.ext_prc`). The data, the
keys and the views are unchanged, so every gold answer still holds after its
names are rewritten, and `questions` proves that row for row.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
PGBIN = "/opt/homebrew/opt/postgresql@16/bin"
ADMIN = "host=127.0.0.1 port=55432 user=postgres dbname={db}"
SOURCE = "wideworldimporters"
TARGET = "wwicryptic"
SCHEMAS = {"application": "ap", "purchasing": "pu", "sales": "sl", "warehouse": "wh", "website": "ws", "legacy": "lg"}
MAP_PATH = ROOT / "wwi" / "cryptic-map.json"

SHORT_WORDS = {"id", "is", "to", "of", "by", "on", "at", "no", "per", "in", "or", "as", "up", "we"}
VOWELS = set("aeiou")


def dictionary():
    words = {w.strip().lower() for w in open("/usr/share/dict/words") if w.strip().isalpha()}
    base = {w for w in words if len(w) >= 3}
    # The list holds base forms; names hold plurals and -ing forms too.
    inflected = {f"{w}s" for w in base} | {f"{w}es" for w in base} | {f"{w[:-1]}ies" for w in base if w.endswith("y")} | {f"{w}ing" for w in base} | {f"{w}ed" for w in base}
    return base | inflected | SHORT_WORDS


WORDS = dictionary()


def segment(name):
    """Fewest dictionary words; a letter that fits no word stands alone."""
    n = len(name)
    best = [(0, [])] + [(10**9, [])] * n
    for end in range(1, n + 1):
        for start in range(max(0, end - 20), end):
            piece = name[start:end]
            cost = 1 if piece in WORDS else (5 if end - start == 1 else 10**8)
            total = best[start][0] + cost
            if total < best[end][0]:
                best[end] = (total, best[start][1] + [piece])
    return best[n][1]


def abbreviate(word):
    """First letter and the next consonants, up to three: extended -> ext, line -> ln."""
    if len(word) <= 3:
        return word
    out = word[0] + "".join(letter for letter in word[1:] if letter not in VOWELS)[:2]
    return out if len(out) >= 2 else word[:3]


def code(name):
    parts = []
    for chunk in re.split(r"[^a-z0-9]+", name.lower()):
        if not chunk:
            continue
        digits = re.match(r"^(.*?)(\d*)$", chunk)
        words = segment(digits.group(1)) if digits.group(1) else []
        parts += [abbreviate(word) for word in words] + ([digits.group(2)] if digits.group(2) else [])
    return "_".join(parts) or "x"


def keywords(conn):
    return {row[0] for row in conn.execute("select word from pg_get_keywords() where catcode <> 'U'")}


def build_map(conn):
    reserved = keywords(conn)
    tables = conn.execute(
        "select table_schema, table_name, table_type from information_schema.tables where table_schema = any(%s) order by 1, 2",
        (list(SCHEMAS),),
    ).fetchall()
    columns = conn.execute(
        "select table_schema, table_name, column_name from information_schema.columns where table_schema = any(%s) order by 1, 2, ordinal_position",
        (list(SCHEMAS),),
    ).fetchall()
    column_codes, used = {}, {}
    for _schema, _table, column in columns:
        if column in column_codes:
            continue
        base = code(column)
        if base in reserved:
            base = f"{base}_c"
        candidate, n = base, 2
        while candidate in used and used[candidate] != column:
            candidate, n = f"{base}{n}", n + 1
        used[candidate] = column
        column_codes[column] = candidate
    table_codes = {}
    for schema, table, kind in tables:
        base = f"{'v' if kind == 'VIEW' else 't'}_{code(table)}"
        taken = {v for (s, _), v in table_codes.items() if s == schema}
        candidate, n = base, 2
        while candidate in taken:
            candidate, n = f"{base}{n}", n + 1
        table_codes[(schema, table)] = candidate
    return {
        "schemas": SCHEMAS,
        "tables": [{"schema": s, "table": t, "kind": k, "code": table_codes[(s, t)]} for s, t, k in tables],
        "columns": column_codes,
    }


def run_sql(db, statements):
    with psycopg.connect(ADMIN.format(db=db), autocommit=True) as conn:
        for statement in statements:
            conn.execute(statement)


def build():
    with psycopg.connect(ADMIN.format(db=SOURCE), autocommit=True) as conn:
        mapping = build_map(conn)
    MAP_PATH.write_text(json.dumps(mapping, indent=1) + "\n")
    run_sql("postgres", [f"DROP DATABASE IF EXISTS {TARGET}", f"CREATE DATABASE {TARGET}"])
    dump = subprocess.run([f"{PGBIN}/pg_dump", "-h", "127.0.0.1", "-p", "55432", "-U", "postgres", "-d", SOURCE, "--no-owner", "--no-acl", "--no-comments"], capture_output=True, check=True)
    subprocess.run([f"{PGBIN}/psql", "-h", "127.0.0.1", "-p", "55432", "-U", "postgres", "-d", TARGET, "-q", "-v", "ON_ERROR_STOP=0"], input=dump.stdout, capture_output=True)
    q = lambda name: '"' + name.replace('"', '""') + '"'
    statements = []
    with psycopg.connect(ADMIN.format(db=TARGET), autocommit=True) as conn:
        # Constraint names spell the tables and columns they join: numbered instead.
        for n, (schema, table, constraint) in enumerate(conn.execute(
            "select n.nspname, c.relname, k.conname from pg_constraint k join pg_class c on c.oid = k.conrelid join pg_namespace n on n.oid = c.relnamespace where n.nspname = any(%s) order by 1, 2, 3",
            (list(SCHEMAS),),
        ).fetchall()):
            statements.append(f"ALTER TABLE {q(schema)}.{q(table)} RENAME CONSTRAINT {q(constraint)} TO {q(f'k{n:04d}')}")
        for n, (schema, index) in enumerate(conn.execute(
            "select schemaname, indexname from pg_indexes where schemaname = any(%s) and indexname not in (select conname from pg_constraint) order by 1, 2",
            (list(SCHEMAS),),
        ).fetchall()):
            statements.append(f"ALTER INDEX {q(schema)}.{q(index)} RENAME TO {q(f'ix{n:04d}')}")
    run_sql(TARGET, statements)
    statements = []
    with psycopg.connect(ADMIN.format(db=TARGET), autocommit=True) as conn:
        columns = conn.execute(
            "select table_schema, table_name, column_name from information_schema.columns where table_schema = any(%s)", (list(SCHEMAS),)
        ).fetchall()
    # Through a temporary name first: a new name may be another column's old one.
    for n, (schema, table, column) in enumerate(columns):
        statements.append(f"ALTER TABLE {q(schema)}.{q(table)} RENAME COLUMN {q(column)} TO {q(f'zz_tmp_{n}')}")
    for n, (schema, table, column) in enumerate(columns):
        statements.append(f"ALTER TABLE {q(schema)}.{q(table)} RENAME COLUMN {q(f'zz_tmp_{n}')} TO {q(mapping['columns'][column])}")
    for item in mapping["tables"]:
        verb = "VIEW" if item["kind"] == "VIEW" else "TABLE"
        statements.append(f"ALTER {verb} {q(item['schema'])}.{q(item['table'])} RENAME TO {q(item['code'])}")
    for schema, short in SCHEMAS.items():
        statements.append(f"ALTER SCHEMA {q(schema)} RENAME TO {q(short)}")
    # Routines and sequences keep their spelled names; nothing ZLens reads shows them.
    for short in SCHEMAS.values():
        statements += [f"GRANT USAGE ON SCHEMA {short} TO wwi_reader", f"GRANT SELECT ON ALL TABLES IN SCHEMA {short} TO wwi_reader"]
    statements.append(f"GRANT CONNECT ON DATABASE {TARGET} TO wwi_reader")
    run_sql(TARGET, statements)
    print(f"{TARGET}: {len(mapping['tables'])} relations and {len(mapping['columns'])} column names renamed")


def rewrite(sql, mapping):
    tables = {}
    for item in mapping["tables"]:
        tables.setdefault(item["table"], {})[item["schema"]] = item["code"]
    columns = mapping["columns"]
    schemas = mapping["schemas"]
    pieces = re.split(r"('(?:[^']|'')*')", sql)
    out = []
    for index, piece in enumerate(pieces):
        if index % 2 == 1:
            out.append(piece)
            continue
        def one(match):
            text = match.group(0)
            parts = text.split(".")
            lower = [p.lower() for p in parts]
            if len(parts) >= 2 and lower[-2] in schemas and lower[-1] in tables.get(lower[-1], {}) or (len(parts) >= 2 and lower[-2] in schemas and lower[-1] in tables):
                return ".".join(parts[:-2] + [schemas[lower[-2]], tables[lower[-1]][lower[-2]]])
            if len(parts) == 2 and lower[-1] in columns:
                return f"{parts[0]}.{columns[lower[-1]]}"
            if len(parts) == 1 and lower[0] in columns:
                return columns[lower[0]]
            return text
        out.append(re.sub(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", one, piece))
    return "".join(out)


def questions():
    mapping = json.loads(MAP_PATH.read_text())
    rows = json.loads((ROOT / "wwi" / "fresh-questions.json").read_text())
    reader = "host=127.0.0.1 port=55432 user=wwi_reader dbname={db}"
    out, bad = [], []
    with psycopg.connect(reader.format(db=SOURCE)) as src, psycopg.connect(reader.format(db=TARGET)) as dst:
        for row in rows:
            sql = rewrite(row["SQL"], mapping)
            want = sorted(map(repr, src.execute(row["SQL"]).fetchall()))
            try:
                got = sorted(map(repr, dst.execute(sql).fetchall()))
            except Exception as error:
                dst.rollback()
                got = f"error: {error}"
            if want != got:
                bad.append((row["question_id"], str(got)[:120]))
            tables = []
            for name in row["tables"]:
                schema, table = name.lower().split(".")
                tables.append(f"{mapping['schemas'][schema]}.{next(i['code'] for i in mapping['tables'] if i['schema'] == schema and i['table'] == table)}")
            out.append({**row, "SQL": sql, "tables": tables})
    (ROOT / "wwi" / "fresh-questions-cryptic.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(rows) - len(bad)} of {len(rows)} gold answers give the same rows on {TARGET}")
    for item in bad:
        print("  differs:", item)


if __name__ == "__main__":
    {"build": build, "questions": questions}[sys.argv[1]]()

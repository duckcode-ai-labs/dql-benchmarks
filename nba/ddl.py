"""The control arm's schema: every table's DDL from the DuckDB catalog, with the dbt
descriptions from the DuckDB-target manifest as comments.

    work/nba/.venv/bin/python -I nba/ddl.py   # writes work/nba/control-schema.sql

A table's dbt description goes on the line above it and a column's description
after the column, the way a documented `CREATE TABLE` reads. Nothing else is added:
no meaning files, no terms, no sample rows.
"""

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "work" / "nba" / "source" / "nba_analysis.duckdb"
MANIFEST = ROOT / "work" / "nba" / "dbt" / "target" / "manifest.json"
OUT = ROOT / "work" / "nba" / "control-schema.sql"


def descriptions():
    manifest = json.loads(MANIFEST.read_text())
    tables, columns = {}, {}
    for node in [*manifest["nodes"].values(), *manifest["sources"].values()]:
        if node["resource_type"] not in ("model", "source", "snapshot"):
            continue
        key = f"{node['schema']}.{node.get('alias') or node.get('identifier') or node['name']}".lower()
        text = " ".join((node.get("description") or "").split())
        if text and not tables.get(key):
            tables[key] = text
        for name, column in (node.get("columns") or {}).items():
            words = " ".join((column.get("description") or "").split())
            if words:
                columns.setdefault(key, {})[name.lower()] = words
    return tables, columns


def main():
    tables, columns = descriptions()
    con = duckdb.connect(str(DB), read_only=True)
    relations = con.execute("SELECT table_schema, table_name, table_type FROM information_schema.tables ORDER BY 1, 2").fetchall()
    parts = []
    for schema, name, kind in relations:
        key = f"{schema}.{name}".lower()
        cols = con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position", [schema, name]).fetchall()
        lines = []
        if key in tables:
            lines.append(f"-- {tables[key]}")
        lines.append(f"CREATE {'VIEW' if kind == 'VIEW' else 'TABLE'} {schema}.{name} (")
        for index, (column, data_type) in enumerate(cols):
            comma = "," if index < len(cols) - 1 else ""
            note = columns.get(key, {}).get(column.lower())
            lines.append(f"  {column} {data_type}{comma}{f'  -- {note}' if note else ''}")
        lines.append(");")
        parts.append("\n".join(lines))
    OUT.write_text("\n\n".join(parts) + "\n")
    print(f"{len(relations)} relations, {len(OUT.read_text())} characters, {sum(1 for k in tables)} table descriptions -> {OUT}")


if __name__ == "__main__":
    main()

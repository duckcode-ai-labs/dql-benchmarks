"""The agentic baseline's database tools (insurance/baseline-agent.mjs).

stdin:  {"database": "/abs/acme_insurance.duckdb", "schema": "main",
         "rowCap": 50, "cellChars": 200, "timeoutS": 30, "sampleMax": 5,
         "request": {"action": "list_tables" | "describe_table" | "sample_rows" | "run_sql", ...}}
stdout: one JSON observation, exactly what the model is shown.

The database is a per-run copy, opened read-only with file access switched
off (as lib/duckdb_query.py opens it), so a statement can read only the tables
already in it and can change nothing. A statement that runs longer than
timeoutS is interrupted. At most rowCap rows are fetched and returned; the
model is told when there were more.
"""

import json
import os
import sys
import threading

import duckdb

sys.dont_write_bytecode = True  # leave no __pycache__ in lib/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from duckdb_query import cell  # noqa: E402  the same value conversion the scorer uses


def clip(value, limit):
    value = cell(value)
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "…"
    return value


def tables(connection, schema):
    rows = connection.execute(
        "select t.table_name, t.table_type, count(c.column_name) "
        "from information_schema.tables t left join information_schema.columns c "
        "on c.table_schema = t.table_schema and c.table_name = t.table_name "
        "where t.table_schema = ? group by all order by 1",
        [schema],
    ).fetchall()
    return rows


def resolve(connection, schema, name):
    """The table's real name, matched without regard to case or quoting; None if unknown."""
    wanted = str(name or "").strip().strip('"').split(".")[-1].strip('"').lower()
    for table_name, _type, _count in tables(connection, schema):
        if table_name.lower() == wanted:
            return table_name
    return None


def fetch(connection, sql, cap, cell_chars):
    cursor = connection.execute(sql)
    columns = [column[0] for column in cursor.description or []]
    batch = cursor.fetchmany(cap + 1) if cursor.description else []
    rows = [[clip(value, cell_chars) for value in row] for row in batch[:cap]]
    out = {"columns": columns, "rows": rows, "rowCount": len(rows)}
    if len(batch) > cap:
        out["truncated"] = f"more than {cap} rows; only the first {cap} are shown"
    return out


def handle(connection, request, options):
    action = request.get("action")
    schema = options["schema"]
    if action == "list_tables":
        return {"tables": [{"name": name, "type": kind, "columns": count} for name, kind, count in tables(connection, schema)]}
    if action in ("describe_table", "sample_rows"):
        name = resolve(connection, schema, request.get("table"))
        if name is None:
            return {"error": f"no table or view named {request.get('table')!r}; call list_tables to see the names"}
        if action == "describe_table":
            columns = connection.execute(
                "select column_name, data_type, is_nullable from information_schema.columns "
                "where table_schema = ? and table_name = ? order by ordinal_position",
                [schema, name],
            ).fetchall()
            return {"table": name, "columns": [{"name": c, "type": t, "nullable": n == "YES"} for c, t, n in columns]}
        try:
            n = int(request.get("n", 3))
        except (TypeError, ValueError):
            n = 3
        n = max(1, min(options["sampleMax"], n))
        quoted = '"' + name.replace('"', '""') + '"'
        schema_quoted = '"' + schema.replace('"', '""') + '"'
        return {"table": name, **fetch(connection, f"select * from {schema_quoted}.{quoted} limit {n}", n, options["cellChars"])}
    if action == "run_sql":
        sql = request.get("sql")
        if not isinstance(sql, str) or not sql.strip():
            return {"error": "run_sql needs a non-empty sql string"}
        return fetch(connection, sql, options["rowCap"], options["cellChars"])
    return {"error": f"unknown action {action!r}"}


def main():
    payload = json.load(sys.stdin)
    options = {
        "schema": payload.get("schema", "main"),
        "rowCap": int(payload.get("rowCap", 50)),
        "cellChars": int(payload.get("cellChars", 200)),
        "sampleMax": int(payload.get("sampleMax", 5)),
    }
    connection = duckdb.connect(payload["database"], read_only=True)
    connection.execute("SET enable_external_access = false")
    connection.execute("SET lock_configuration = true")
    timer = threading.Timer(float(payload.get("timeoutS", 30)), connection.interrupt)
    timer.start()
    try:
        out = handle(connection, payload["request"], options)
    except Exception as error:  # the error text is the observation
        message = f"{type(error).__name__}: {error}"
        if "interrupt" in message.lower():
            message = f"the statement ran longer than {payload.get('timeoutS', 30)} s and was stopped"
        out = {"error": message[:1500]}
    finally:
        timer.cancel()
    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()

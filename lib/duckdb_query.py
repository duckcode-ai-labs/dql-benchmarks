"""Run read-only SQL against a DuckDB file and print the results as JSON.

stdin:  {"database": "/abs/path.duckdb", "queries": [{"id": "...", "sql": "..."}]}
stdout: {"<id>": {"columns": [...], "rows": [[...], ...]} | {"error": "..."}}

The database is opened read-only and file access is switched off, so a query
can read only the tables already in it.
"""

import datetime
import decimal
import json
import sys
import uuid

import duckdb


def cell(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, datetime.timedelta):
        return value.total_seconds()
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def main():
    request = json.load(sys.stdin)
    connection = duckdb.connect(request["database"], read_only=True)
    connection.execute("SET enable_external_access = false")
    connection.execute("SET lock_configuration = true")
    out = {}
    for query in request["queries"]:
        try:
            cursor = connection.execute(query["sql"])
            columns = [column[0] for column in cursor.description or []]
            rows = [[cell(value) for value in row] for row in cursor.fetchall()]
            out[query["id"]] = {"columns": columns, "rows": rows}
        except Exception as error:  # the error text is the result
            out[query["id"]] = {"error": f"{type(error).__name__}: {error}"}
    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()

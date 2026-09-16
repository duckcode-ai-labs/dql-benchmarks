#!/usr/bin/env bash
# Python environment for dbt (DuckDB adapter) and the publisher's grader.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"

if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet dbt-core dbt-duckdb duckdb pandas

REQUIREMENTS="$ROOT/data/spider2-dbt/Spider2/methods/spider-agent-dbt/requirements.txt"
if [ -f "$REQUIREMENTS" ]; then
  "$VENV/bin/pip" install --quiet -r "$REQUIREMENTS"
fi

"$VENV/bin/dbt" --version

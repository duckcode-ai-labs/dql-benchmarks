#!/usr/bin/env bash
# Python environment for dbt with the DuckDB adapter, used to build benchmark dbt projects.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"

# dbt is pinned so every result names the exact version that built the
# project. dbt Labs' insurance project uses dbt semantic models (dbt 1.6+);
# 1.9 builds it and is the last line before dbt's stricter 1.10 parsing.
PYTHON="${BENCH_PYTHON:-python3.12}"
if [ -x "$VENV/bin/python" ] && ! "$VENV/bin/python" -c 'import sys; sys.exit(0 if sys.version_info[:2] in ((3,11),(3,12)) else 1)'; then
  echo "Replacing $VENV: it was built with $("$VENV/bin/python" --version)."
  rm -rf "$VENV"
fi
if [ ! -x "$VENV/bin/python" ]; then
  "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet "dbt-core~=1.9.0" "dbt-duckdb~=1.9.0" duckdb
# Exact versions used, so a result can name them.
"$VENV/bin/pip" freeze --quiet > "$ROOT/requirements.lock"

"$VENV/bin/dbt" --version

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

# MetricFlow with the DuckDB adapter, in its own environment, at the version
# range DQL's own managed installer uses (apps/cli/src/metricflow-installer.ts).
# DQL uses the `mf` it finds first; a machine's own `mf` may lack the DuckDB
# adapter, so runs point DQL at this one (DQL_METRICFLOW_BIN in insurance/run.mjs).
MF_VENV="$ROOT/.venv-mf"
if [ ! -x "$MF_VENV/bin/mf" ]; then
  "$PYTHON" -m venv "$MF_VENV"
fi
"$MF_VENV/bin/pip" install --quiet --upgrade pip
"$MF_VENV/bin/pip" install --quiet "dbt-metricflow[dbt-duckdb]>=0.13,<0.14"
"$MF_VENV/bin/pip" freeze --quiet > "$ROOT/requirements-metricflow.lock"
"$MF_VENV/bin/mf" --version

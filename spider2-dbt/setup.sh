#!/usr/bin/env bash
# Python environment for dbt (DuckDB adapter) and the publisher's grader.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"

if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
# google-cloud-bigquery: the publisher's grader imports it at module load even
# for the DuckDB tasks, and fails to start without it.
"$VENV/bin/pip" install --quiet dbt-core dbt-duckdb duckdb pandas google-cloud-bigquery tqdm

# The publisher's reference agent (methods/spider-agent-dbt) is not used here:
# its requirements pull in GPU packages that do not build on every machine.

"$VENV/bin/dbt" --version

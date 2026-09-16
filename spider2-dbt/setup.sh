#!/usr/bin/env bash
# Python environment for dbt (DuckDB adapter) and the publisher's grader.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"

# The dbt version decides which starting projects even parse, so it is fixed
# to the benchmark's era: Spider 2.0-DBT was released in May 2025 against
# dbt 1.9, and the publisher's reference image is Python 3.11 with
# `pip install dbt-duckdb`. Newer dbt (1.10+) is stricter and rejects some
# starting projects before an agent can touch them.
PYTHON="${SPIDER2_PYTHON:-python3.12}"
if [ -x "$VENV/bin/python" ] && ! "$VENV/bin/python" -c 'import sys; sys.exit(0 if sys.version_info[:2] in ((3,11),(3,12)) else 1)'; then
  echo "Replacing $VENV: it was built with $("$VENV/bin/python" --version)."
  rm -rf "$VENV"
fi
if [ ! -x "$VENV/bin/python" ]; then
  "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
# google-cloud-bigquery: the publisher's grader imports it at module load even
# for the DuckDB tasks, and fails to start without it.
"$VENV/bin/pip" install --quiet "dbt-core~=1.9.0" "dbt-duckdb~=1.9.0" duckdb pandas google-cloud-bigquery tqdm
# Exact versions used, so a result can name them.
"$VENV/bin/pip" freeze --quiet > "$ROOT/spider2-dbt/requirements.lock"

# The publisher's reference agent (methods/spider-agent-dbt) is not used here:
# its requirements pull in GPU packages that do not build on every machine.

"$VENV/bin/dbt" --version

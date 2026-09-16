#!/usr/bin/env bash
# Fetch the two insurance benchmarks into data/dbt-sl-bench.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data/insurance"
mkdir -p "$DATA"

clone() {
  local url="$1" dir="$2"
  if [ ! -d "$DATA/$dir/.git" ]; then
    git clone --depth 1 "$url" "$DATA/$dir"
  fi
  git -C "$DATA/$dir" rev-parse HEAD > "$DATA/$dir.UPSTREAM_COMMIT"
}

clone https://github.com/datadotworld/cwd-benchmark-data.git cwd-benchmark-data
clone https://github.com/dbt-labs/dbt-llm-sl-bench.git dbt-llm-sl-bench
clone https://github.com/dbt-labs/semantic-layer-llm-benchmarking.git semantic-layer-llm-benchmarking

echo "Insurance benchmarks are in $DATA."

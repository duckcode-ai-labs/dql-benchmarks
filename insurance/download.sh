#!/usr/bin/env bash
# Fetch the insurance benchmark sources into data/insurance, at the commits
# our results were produced from.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data/insurance"
mkdir -p "$DATA"

clone() {
  local url="$1" dir="$2" commit="$3"
  if [ ! -d "$DATA/$dir/.git" ]; then
    git clone "$url" "$DATA/$dir"
  fi
  git -C "$DATA/$dir" fetch --quiet origin "$commit" 2>/dev/null || true
  git -C "$DATA/$dir" checkout --quiet "$commit"
  git -C "$DATA/$dir" rev-parse HEAD > "$DATA/$dir.UPSTREAM_COMMIT"
}

# data.world's questions, schema, ontology and data (the 2023 paper).
clone https://github.com/datadotworld/cwd-benchmark-data.git cwd-benchmark-data 0b75eb62eaf7ea315a863cd7611ebc908149f7e0
# dbt Labs' runner, corrected question file and published graded answers.
clone https://github.com/dbt-labs/dbt-llm-sl-bench.git dbt-llm-sl-bench a29f2429b1bb38cee9d591892299e96f1e197ff9
# dbt Labs' dbt project on the same data (main branch; the three extra models
# dbt Labs added later are on refresh-2025-additional-models @e4bdee5).
clone https://github.com/dbt-labs/semantic-layer-llm-benchmarking.git semantic-layer-llm-benchmarking ac20c9292fa88ec44d30aeeae61ee41a51e31748
git -C "$DATA/semantic-layer-llm-benchmarking" fetch --quiet origin refresh-2025-additional-models || true

echo "Insurance benchmarks are in $DATA."

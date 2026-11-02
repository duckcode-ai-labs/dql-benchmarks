#!/usr/bin/env bash
# Run every arm for three passes, then grade them. Arms run side by side.
#   DQL_CLI=<zlens dist/index.js> wwi/run-all.sh <run-id>
set -uo pipefail
cd "$(dirname "$0")/.."
RUN="$1"
GRADE=(uv run --quiet --with 'psycopg[binary]' python wwi/grade.py)
for pass in 1 2 3; do
  node wwi/control.mjs --run "$RUN" --pass "$pass" 2>&1 | tail -1 &
  for arm in W0 W1a WM; do
    node wwi/run.mjs --arm "$arm" --run "$RUN" --pass "$pass" 2>&1 | tail -1 &
  done
  wait
  for arm in C W0 W1a WM; do
    dir="results/wwi/$RUN/$arm/pass-$pass"
    "${GRADE[@]}" --arm "$dir/predictions.jsonl" --out "$dir/graded.json" 2>&1 | sed "s|^|$arm pass $pass: |"
  done
done
python3 wwi/compare.py --run "$RUN"

#!/usr/bin/env bash
# The same arms on the fixed build. See PREREGISTRATION.md.
#   DQL_CLI=<zlens dist/index.js> wwi/run-after-fixes.sh
set -uo pipefail
cd "$(dirname "$0")/.."
GRADE=(uv run --quiet --with 'psycopg[binary]' python wwi/grade.py)
node wwi/build.mjs --arm WM
mkdir -p results/wwi/r4 results/wwi/r5
cp -R results/wwi/r2/C results/wwi/r4/C
cp -R results/wwi/r3/C results/wwi/r5/C
for pass in 1 2 3; do
  for arm in W0 W1a WM; do
    node wwi/run.mjs --arm "$arm" --run r4 --pass "$pass" --line punctuated 2>&1 | tail -1 &
    node wwi/run.mjs --arm "$arm" --run r5 --pass "$pass" --line none 2>&1 | tail -1 &
  done
  wait
done
for run in r4 r5; do
  for pass in 1 2 3; do
    for arm in W0 W1a WM; do
      dir="results/wwi/$run/$arm/pass-$pass"
      "${GRADE[@]}" --arm "$dir/predictions.jsonl" --out "$dir/graded.json" 2>&1 | sed "s|^|$run $arm pass $pass: |"
    done
  done
done
python3 wwi/compare.py --run r4
python3 wwi/compare.py --run r5

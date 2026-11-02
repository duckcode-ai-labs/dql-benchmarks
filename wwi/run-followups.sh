#!/usr/bin/env bash
# The post-hoc runs in PREREGISTRATION.md's amendments.
#   DQL_CLI=<zlens dist/index.js> wwi/run-followups.sh
set -uo pipefail
cd "$(dirname "$0")/.."
GRADE=(uv run --quiet --with 'psycopg[binary]' python wwi/grade.py)
mkdir -p results/wwi/r2
cp -R results/wwi/r1/C results/wwi/r2/C
for pass in 1 2 3; do
  node wwi/control.mjs --run r3 --pass "$pass" --no-line 2>&1 | tail -1 &
  for arm in W0 W1a WM; do
    node wwi/run.mjs --arm "$arm" --run r2 --pass "$pass" --line punctuated 2>&1 | tail -1 &
    node wwi/run.mjs --arm "$arm" --run r3 --pass "$pass" --line none 2>&1 | tail -1 &
  done
  wait
done
for run in r2 r3; do
  for pass in 1 2 3; do
    for arm in C W0 W1a WM; do
      dir="results/wwi/$run/$arm/pass-$pass"
      "${GRADE[@]}" --arm "$dir/predictions.jsonl" --out "$dir/graded.json" 2>&1 | sed "s|^|$run $arm pass $pass: |"
    done
  done
done
python3 wwi/compare.py --run r2
python3 wwi/compare.py --run r3

#!/bin/bash
# Q5: the NBA questions on the DX arm (NBA inside a 95-table model), with
# Ask's area routing on and off, each graded on the DX warehouse.
set -uo pipefail
B=$(cd "$(dirname "$0")/.." && pwd); cd "$B"
export DQL_CLI=${DQL_CLI:?}
DB=work/nba/dx-warehouse/enterprise_dw.duckdb
for arm in on off; do
  run=Q5-$arm
  rm -rf "results/nba/$run" "work/nba/runs/$run"
  if [ "$arm" = off ]; then export ZLENS_ASK_AREA_ROUTING=off; else unset ZLENS_ASK_AREA_ROUTING; fi
  node nba/run.mjs --arm DX --run "$run" --questions nba/questions-p7.json --source-db "$DB" --keep-cache > "work/nba/$run.log" 2>&1
  BENCH_DB="$B/$DB" BENCH_QUESTIONS="$B/nba/questions-p7.json" work/nba/.venv/bin/python -I nba/grade.py --arm "results/nba/$run/DX/pass-1/predictions.jsonl" --out "results/nba/$run/DX/pass-1/graded.json" > "work/nba/$run-grade.log" 2>&1
  echo "$run done: $(tail -1 work/nba/$run.log)"
done
unset ZLENS_ASK_AREA_ROUTING

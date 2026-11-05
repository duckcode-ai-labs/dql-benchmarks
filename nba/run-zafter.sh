#!/bin/bash
# Simplification plan check: the NBA benchmarks after Z1, Z2 and Z3 must not be
# lower than before. DA (the NBA project alone, P7's arm) and DX (NBA inside the
# 95-table crowd, routing on, Q5-on's arm), on the same 40 P7 questions.
#   DQL_CLI=<zlens dist/index.js> nba/run-zafter.sh <run id>
set -uo pipefail
B=$(cd "$(dirname "$0")/.." && pwd); cd "$B"
export DQL_CLI=${DQL_CLI:?}
run=${1:?run id}
unset ZLENS_ASK_AREA_ROUTING
DX_DB=work/nba/dx-warehouse/enterprise_dw.duckdb
rm -rf "results/nba/$run" "work/nba/runs/$run"
node nba/run.mjs --arm DA --run "$run" --questions nba/questions-p7.json --keep-cache > "work/nba/$run-DA.log" 2>&1 &
node nba/run.mjs --arm DX --run "$run" --questions nba/questions-p7.json --source-db "$DX_DB" --keep-cache > "work/nba/$run-DX.log" 2>&1 &
wait
BENCH_QUESTIONS="$B/nba/questions-p7.json" work/nba/.venv/bin/python -I nba/grade.py --arm "results/nba/$run/DA/pass-1/predictions.jsonl" --out "results/nba/$run/DA/pass-1/graded.json" > "work/nba/$run-DA-grade.log" 2>&1
BENCH_DB="$B/$DX_DB" BENCH_QUESTIONS="$B/nba/questions-p7.json" work/nba/.venv/bin/python -I nba/grade.py --arm "results/nba/$run/DX/pass-1/predictions.jsonl" --out "results/nba/$run/DX/pass-1/graded.json" > "work/nba/$run-DX-grade.log" 2>&1
echo "DA: $(tail -1 work/nba/$run-DA.log)"
echo "DX: $(tail -1 work/nba/$run-DX.log)"

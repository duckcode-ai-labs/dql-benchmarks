#!/bin/bash
# Ask area-ranking proof (ask-area-ranking-design-2026-11-05, A3): routing on, on the build
# with R1-R3 (NEW_CLI) for the 40 Z4 questions as written and reworded, and on today's main
# (MAIN_CLI) for the reworded ones. Results in results/gitlab/<run>/on/shown.jsonl.
#   NEW_CLI=<dist/index.js> MAIN_CLI=<dist/index.js> gitlab/run-ra.sh
set -uo pipefail
B=$(cd "$(dirname "$0")/.." && pwd); cd "$B"
P=work/gitlab/project-z4
: "${NEW_CLI:?}" "${MAIN_CLI:?}"
RW=gitlab/rank/reworded-questions.json
DQL_CLI=$NEW_CLI node gitlab/run-routing.mjs --project $P/dbt/dql --db $P/gitlab_shape.duckdb --run RA --arm on > work/gitlab/RA-on.log 2>&1 &
DQL_CLI=$NEW_CLI node gitlab/run-routing.mjs --project $P/dbt/dql --db $P/gitlab_shape.duckdb --run RA-rw --arm on --questions $RW > work/gitlab/RA-rw-on.log 2>&1 &
DQL_CLI=$MAIN_CLI node gitlab/run-routing.mjs --project $P/dbt/dql --db $P/gitlab_shape.duckdb --run RA-rw-main --arm on --questions $RW > work/gitlab/RA-rw-main-on.log 2>&1 &
wait
for r in RA-on RA-rw-on RA-rw-main-on; do echo "$r: $(tail -1 work/gitlab/$r.log)"; done

#!/bin/sh
# Run ZLens arms side by side on the same build and questions (one pass each).
#   sh nba/run-arms.sh <run-id> [arms...]     default arms: D0 D1 D2 (R1 also ran W0 W1)
# Then: node nba/control.mjs --run <run-id>; nba/grade.py per arm; python3 nba/analyze.py --run <run-id>
run=$1; shift
arms=${*:-D0 D1 D2}
# R1: value-profile-guard (0a8f6621). R2: ZL=.../zlens/nba-fixes/apps/cli/dist/index.js RUN_FLAGS=--keep-cache
ZL=${ZL:-/Users/Kranthi_1/DuckCode-DQL/agent-worktrees/zlens/value-profile-guard/apps/cli/dist/index.js}
cd /Users/Kranthi_1/DuckCode-DQL/agent-worktrees/dql-benchmarks/wwi
for arm in $arms; do
  DQL_CLI=$ZL node nba/run.mjs --arm $arm --run $run $RUN_FLAGS > work/nba/$run-$arm.log 2>&1 &
done
wait
echo "all arms done"

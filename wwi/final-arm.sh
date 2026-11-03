#!/bin/sh
# label, arm, cli
label=$1; arm=$2; cli=$3
cd /Users/Kranthi_1/DuckCode-DQL/agent-worktrees/dql-benchmarks/wwi
DQL_CLI=$cli node wwi/run.mjs --arm $arm --run F1-$label --line none --questions wwi/fresh-questions.json

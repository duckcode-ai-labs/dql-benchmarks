#!/bin/sh
name=$1; arm=$2
ZL=/Users/Kranthi_1/DuckCode-DQL/agent-worktrees/zlens/report-match-xlsx
cd /Users/Kranthi_1/DuckCode-DQL/agent-worktrees/dql-benchmarks/wwi
PATH="$PWD/work/wwi/fakebin-index:$PATH" DQL_CLI=$ZL/apps/cli/dist/index.js node wwi/run.mjs --arm $arm --run $name --line none
PATH="$PWD/work/wwi/fakebin-index:$PATH" DQL_CLI=$ZL/apps/cli/dist/index.js node wwi/run.mjs --arm $arm --run $name-fresh --line none --questions wwi/fresh-questions.json
python3 wwi/recall.py --run $name --arm $arm --set nvidia
python3 wwi/recall.py --run $name-fresh --arm $arm --set fresh

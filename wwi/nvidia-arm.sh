#!/bin/sh
# label, arm, cli: one pass of NVIDIA's questions, plain, on one project
label=$1; arm=$2; cli=$3
cd $HOME/DuckCode-DQL/agent-worktrees/dql-benchmarks/wwi
DQL_CLI=$cli node wwi/run.mjs --arm $arm --run N1-$label --line none

#!/bin/sh
cd $HOME/DuckCode-DQL/agent-worktrees/dql-benchmarks/wwi
for pair in main:WL index:WL drafts:WD terms:WT; do
  label=${pair%%:*}; arm=${pair##*:}
  dir=results/wwi/F1-$label/$arm/pass-1
  uv run --quiet --with 'psycopg[binary]' python wwi/grade.py --gold-file wwi/fresh-questions.json --arm $dir/predictions.jsonl --out $dir/graded.json | head -1 | sed "s/^/$label: /"
done
rm -rf wwi/__pycache__

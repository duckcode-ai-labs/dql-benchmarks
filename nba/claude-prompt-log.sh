#!/bin/sh
# Logs each prompt ZLens sends to the claude CLI (stdin and arguments), then runs the real CLI.
REAL=/opt/homebrew/bin/claude
case "$1" in
  --version|auth) exec "$REAL" "$@";;
esac
LOG=$HOME/DuckCode-DQL/agent-worktrees/dql-benchmarks/wwi/work/nba/trace-prompts
stamp=$(date +%s)-$$
cat > "$LOG/$stamp.stdin"
printf '%s\n' "$@" > "$LOG/$stamp.args"
exec "$REAL" "$@" < "$LOG/$stamp.stdin"

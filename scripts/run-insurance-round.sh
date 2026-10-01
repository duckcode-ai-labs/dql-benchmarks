#!/bin/zsh
# One model's round on the insurance benchmark, as run for the paper (analysis/insurance-2026-09-29):
# one-shot SQL (P), then every DQL level but LB and WB on the main build, then LB and WB on the
# build with the short-table-name fix. A provider usage limit (exit code 3) is never scored: the
# round waits and resumes from the refused question.
#
#   DQL_CLI_MAIN=/path/to/dql@49c0e1cb/apps/cli/dist/index.js \
#   DQL_CLI_FIXED=/path/to/dql@627009a1/apps/cli/dist/index.js \
#   scripts/run-insurance-round.sh <run-id> <provider> <model> [effort]
#
# provider: claude-code | codex | ollama.  For codex, set CODEX_BENCH_HOME to an isolated, signed-in
# Codex home with no personal instructions, plugins, MCP servers or memories (see docs/REPRODUCE.md).
# SETS defaults to "heldout-3 heldout-3-unanswerable"; LIMIT_WAIT_S (default 1800) is the wait.
set -u
cd "$(dirname "$0")/.."
R=$1; P=$2; M=$3; E=${4:-}
: ${DQL_CLI_MAIN:?set DQL_CLI_MAIN to the CLI of DQL build 49c0e1cb}
: ${DQL_CLI_FIXED:?set DQL_CLI_FIXED to the CLI of DQL build 627009a1}
SETS=(${=SETS:-heldout-3 heldout-3-unanswerable}); WAIT=${LIMIT_WAIT_S:-1800}
extra=(); home=()
[ "$P" = codex ] && home=(--codex-home ${CODEX_BENCH_HOME:?set CODEX_BENCH_HOME for codex runs})
[ -n "$E" ] && [ "$P" = codex ] && extra+=(--codex-effort $E)
mkdir -p work/insurance
ts() { date +%H:%M:%S; }
retry() {  # retry <log> <command...>: resume after a provider limit
  local log=$1; shift; local tries=0
  while true; do
    "$@" > $log 2>&1; local c=$?
    [ $c -eq 0 ] && return 0
    [ $c -eq 3 ] || { echo "$(ts) FAILED (exit $c): $(tail -2 $log)"; return $c; }
    tries=$((tries+1)); [ $tries -gt 12 ] && { echo "$(ts) still refused after 12 waits"; return 3; }
    echo "$(ts) provider limit; waiting $((WAIT/60)) min"; sleep $WAIT
  done
}
level() {  # level <cli> <layer> <set>
  local out=work/insurance/runs/$R/$2/$3/report.json resume=()
  [ -f $out ] && python3 -c "import json,sys; sys.exit(1 if json.load(open('$out')).get('invalid') else 0)" && { echo "$(ts) $2/$3 already done"; return; }
  [ -f $out ] && resume=(--resume)
  DQL_CLI=$1 retry work/insurance/$R-$2-$3.log node insurance/run.mjs --layer $2 --set $3 --provider $P --model $M --run $R $resume $extra $home || exit $?
  echo "$(ts) $2/$3 done"
}
for L in L0 L1 L2 L3 LB W0 W1 W2 WB; do
  [ -f work/insurance/.built-$L ] && continue
  node insurance/build.mjs --layer $L --skip-gold > work/insurance/build-$L.log 2>&1 || { echo "build $L failed"; exit 1; }
  touch work/insurance/.built-$L
done
[ -f work/insurance/gold/heldout-3.json ] || node insurance/heldout.mjs --number 3 gold > work/insurance/gold-3.log 2>&1 || { echo "gold for set 3 failed"; exit 1; }
eff=(); [ -n "$E" ] && eff=(--effort $E)
[ -f work/insurance/runs/$R/baseline-full/heldout-3/report.json ] || \
  DQL_CLI=$DQL_CLI_MAIN retry work/insurance/$R-baseline.log node insurance/baseline-text2sql.mjs --provider $P --model $M $eff --ddl full --set heldout-3 --run $R $home || exit $?
for S in $SETS; do for L in L0 L1 L2 L3 W0 W1 W2; do level $DQL_CLI_MAIN $L $S; done; done
for S in $SETS; do for L in LB WB; do level $DQL_CLI_FIXED $L $S; done; done
echo "$(ts) round $R done"

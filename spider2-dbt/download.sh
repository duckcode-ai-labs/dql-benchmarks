#!/usr/bin/env bash
# Fetch Spider 2.0-DBT into data/spider2-dbt.
#
# The publisher's instructions (github.com/xlang-ai/Spider2, spider2-dbt/README.md)
# are: clone the repo, download two archives from Google Drive, then run
# `python setup.py` inside spider2-dbt. This script follows them. Check the
# README again before the first run; the archive ids below were copied from
# it on 2026-09-16.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data/spider2-dbt"
REPO="$DATA/Spider2"
VENV="$ROOT/.venv"

mkdir -p "$DATA"

if [ ! -d "$REPO/.git" ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/xlang-ai/Spider2.git "$REPO"
  git -C "$REPO" sparse-checkout set spider2-dbt methods/spider-agent-dbt
fi
git -C "$REPO" rev-parse HEAD > "$DATA/UPSTREAM_COMMIT"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Run spider2-dbt/setup.sh first (it creates $VENV)." >&2
  exit 1
fi

cd "$REPO/spider2-dbt"
"$VENV/bin/pip" install --quiet gdown
"$VENV/bin/gdown" "https://drive.google.com/uc?id=1N3f7BSWC4foj-V-1C9n8M2XmgV7FOcqL"
"$VENV/bin/gdown" "https://drive.google.com/uc?id=1s0USV_iQLo4oe05QqAMnhGGp5jeejCzp"
"$VENV/bin/python" setup.py

echo "Spider 2.0-DBT is in $REPO/spider2-dbt (upstream commit $(cat "$DATA/UPSTREAM_COMMIT"))."

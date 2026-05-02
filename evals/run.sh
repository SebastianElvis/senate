#!/usr/bin/env bash
# Thin wrapper around evals/scripts/run_eval.py.
# Usage:
#   evals/run.sh                                # all fixtures, default models
#   evals/run.sh fixtures/parliament-*.md       # one or more fixtures
#   evals/run.sh --judge-model claude-opus-4-7  # pass-through args
set -euo pipefail

cd "$(dirname "$0")"

if [[ $# -eq 0 ]]; then
  exec python3 scripts/run_eval.py fixtures/
fi

# If first arg looks like a flag, pass through with default fixture dir.
if [[ "$1" == --* ]]; then
  exec python3 scripts/run_eval.py "$@" fixtures/
fi

exec python3 scripts/run_eval.py "$@"

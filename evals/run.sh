#!/usr/bin/env bash
# Thin wrapper around evals/scripts/run_eval.py.
# Usage:
#   evals/run.sh                                # all fixtures, default models
#   evals/run.sh fixtures/parliament-*.md       # one or more fixtures
#   evals/run.sh --judge-model claude-opus-4-7  # pass-through args
#
# Fixture paths are resolved against the original cwd before this wrapper
# cd's into evals/, so callers can pass either `fixtures/foo.md` (from evals/)
# or `evals/fixtures/foo.md` (from repo root).
set -euo pipefail

# Resolve any existing path arg to absolute against the caller's cwd,
# so the cd into evals/ below doesn't break it.
args=()
for arg in "$@"; do
  if [[ "$arg" != --* && -e "$arg" ]]; then
    case "$arg" in
      /*) args+=("$arg") ;;
      *)  args+=("$PWD/$arg") ;;
    esac
  else
    args+=("$arg")
  fi
done

cd "$(dirname "$0")"

if [[ ${#args[@]} -eq 0 ]]; then
  exec python3 scripts/run_eval.py fixtures/
fi

# If first arg is a flag and no fixture path is present in the args (after
# absolute-path resolution above), append the default fixtures/ dir.
if [[ "${args[0]}" == --* ]]; then
  has_fixture=0
  for arg in "${args[@]}"; do
    if [[ -e "$arg" ]]; then
      has_fixture=1
      break
    fi
  done
  if [[ "$has_fixture" -eq 1 ]]; then
    exec python3 scripts/run_eval.py "${args[@]}"
  fi
  exec python3 scripts/run_eval.py "${args[@]}" fixtures/
fi

exec python3 scripts/run_eval.py "${args[@]}"

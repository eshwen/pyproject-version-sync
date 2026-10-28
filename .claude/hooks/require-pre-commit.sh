#!/usr/bin/env bash
# PreToolUse hook: block any Bash call that runs `git commit` unless pre-commit passes.
# Runs on all files rather than just staged ones, because the commit is often chained
# after a `git add` in the same command, which hasn't run yet when this hook fires.
set -uo pipefail

command=$(jq -r '.tool_input.command // ""')
if ! grep -Eq '(^|[;&|(][[:space:]]*)git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+commit([[:space:]]|$)' <<<"$command"; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 1
if ! output=$(uv run pre-commit run --all-files 2>&1); then
  {
    echo "pre-commit failed, so the commit was blocked. Fix the failures below, re-stage any files the hooks modified, then commit again."
    echo
    echo "$output"
  } >&2
  exit 2
fi

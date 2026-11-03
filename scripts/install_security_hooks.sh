#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if ! command -v gitleaks >/dev/null 2>&1; then
  echo 'STOP: install verified Gitleaks v8 before enabling hooks.' >&2
  exit 1
fi
# Git config is normally shared across linked worktrees; keep hooks per worktree.
git config --local extensions.worktreeConfig true
git config --worktree core.hooksPath .githooks
if ! test -x .githooks/pre-commit; then
  echo 'BLOCK: pre-commit hook is not executable; restore its Git mode (100755).' >&2
  exit 1
fi
echo 'Installed worktree-local confidentiality, dependency and Gitleaks pre-commit gates.'

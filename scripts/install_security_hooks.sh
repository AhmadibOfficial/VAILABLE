#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if ! command -v gitleaks >/dev/null 2>&1; then
  echo 'STOP: install verified Gitleaks v8 before enabling hooks.' >&2
  exit 1
fi
git config --local core.hooksPath .githooks
chmod u+x .githooks/pre-commit
echo 'Installed repository-local confidentiality, dependency and Gitleaks pre-commit gates.'

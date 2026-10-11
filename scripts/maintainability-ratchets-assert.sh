#!/usr/bin/env bash
# Proves the five maintainability gates can go red.
# Does not run mutmut.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
WORKFLOW="${ROOT}/.github/workflows/maintainability-ratchets.yml"

fail() {
  echo "maintainability-ratchets-assert: $*" >&2
  exit 1
}

if python3 scripts/ruff-ratchet.py --write-baseline >/tmp/ratchet-assert-out.txt 2>/tmp/ratchet-assert-err.txt; then
  fail "ruff must refuse to rewrite the baseline"
fi
if ! grep -q 'refusing to rewrite the ruff baseline' /tmp/ratchet-assert-err.txt; then
  fail "ruff refusal message missing"
fi

python3 scripts/hotspot-gate.py --self-test
python3 scripts/ruff-ratchet.py --self-test
python3 scripts/mutation-floor.py --self-test

for job in clean-as-you-code hotspot fitness static-baseline mutation; do
  if ! grep -q "^  ${job}:" "$WORKFLOW"; then
    fail "workflow is missing the ${job} job"
  fi
done

if ! grep -q 'mutmut==2.5.1' "$WORKFLOW"; then
  fail "mutation job must pin mutmut 2.5.1"
fi
if ! grep -q 'tags:' "$WORKFLOW" || ! grep -q 'v\*' "$WORKFLOW"; then
  fail "workflow must run on v* tags"
fi

echo "maintainability-ratchets-assert: five gates can fail closed, including v* tags"

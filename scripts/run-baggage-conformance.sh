#!/usr/bin/env bash
# Shared baggage contract: doctor + emit + language vector tests.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"

echo ">>> baggage doctor (stack-one)"
python3 -m tekton_dag_common.baggage_contract doctor --stack stacks/stack-one.yaml

echo ">>> baggage emit --all"
python3 -m tekton_dag_common.baggage_contract emit --stack stacks/stack-one.yaml --all >/dev/null

echo ">>> pytest: baggage contract + python client"
python3 -m pytest libs/tekton-dag-common/tests/test_baggage_contract.py libs/baggage-python/tests/test_baggage.py -v --tb=short

if command -v npm >/dev/null 2>&1; then
  echo ">>> vitest: baggage-node"
  (cd "$REPO_ROOT/libs/baggage-node" && npm install --silent && npm run test)
else
  echo ">>> SKIP baggage-node (npm missing)"
fi

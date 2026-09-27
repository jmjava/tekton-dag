#!/usr/bin/env bash
# Fail-closed hop-to-hop check against a hop-report body.
# Usage: ./scripts/validate-propagation-response.sh --chain "a b c" --header-val pr-42 --build-apps c --response '{"app":"a","session":"pr-42"}'
#        ./scripts/validate-propagation-response.sh ... --response -   # stdin
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"
exec python3 -m tekton_dag_common.propagation_validate evaluate "$@"

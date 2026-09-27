#!/usr/bin/env bash
# Validate stack propagation roles and print per-app override-header config.
# Usage: ./scripts/baggage-doctor.sh --stack stacks/stack-one.yaml
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"
exec python3 -m tekton_dag_common.baggage_contract doctor "$@"

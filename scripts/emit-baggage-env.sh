#!/usr/bin/env bash
# Emit baggage library env from a stack app so header name and role match YAML.
# Usage: ./scripts/emit-baggage-env.sh --stack stacks/stack-one.yaml --app demo-fe [--format env|vite|spring|dotenv]
#        ./scripts/emit-baggage-env.sh --stack stacks/stack-one.yaml --all
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"
exec python3 -m tekton_dag_common.baggage_contract emit "$@"

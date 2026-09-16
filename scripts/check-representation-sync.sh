#!/usr/bin/env bash
# Fail when Helm CRDs, Stack/Team conversion, or PipelineRun params drift.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

if [[ -x "$REPO_ROOT/.venv/bin/python3" ]]; then
  export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi

need python3
export PYTHONPATH="${REPO_ROOT}/libs/tekton-dag-common${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$SCRIPT_DIR/check-representation-sync.py" "$@"

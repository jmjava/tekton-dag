#!/usr/bin/env bash
# Strictest regression: cluster + required DAG verify pipeline + required Tekton Results / DB script.
# Fails if orchestrator, newman, stack-dag-verify, or tekton-results-api (namespace tekton-pipelines) missing.
#
# Extra args are forwarded to run-regression-stream.sh (e.g. --skip-playwright).
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/run-regression-stream.sh" --cluster --require-dag-verify --with-results-verify "$@"

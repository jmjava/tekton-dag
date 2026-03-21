#!/usr/bin/env bash
# Agent/human entrypoint: run the strictest regression possible for the current environment.
#
# - If kubectl has a reachable context: run cluster regression with --cluster --require-dag-verify
#   (orchestrator + newman + mandatory stack-dag-verify when pipeline exists).
# - Otherwise: run --local-only and print a clear banner that Tekton/Newman were skipped.
#
# Extra args are forwarded (e.g. --skip-playwright, --with-results-verify).
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

if kubectl cluster-info &>/dev/null; then
  echo "==> run-regression-agent: kubectl OK — running strict cluster regression (--cluster --require-dag-verify)"
  exec bash "$SCRIPT_DIR/run-regression-stream.sh" --cluster --require-dag-verify "$@"
else
  echo "==> run-regression-agent: NO kubectl context — running --local-only only" >&2
  echo "    Tekton PipelineRuns, Newman, and Results checks are NOT run." >&2
  exec bash "$SCRIPT_DIR/run-regression-stream.sh" --local-only "$@"
fi

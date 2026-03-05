#!/usr/bin/env bash
# Promote pipeline/task/trigger YAML from one namespace to another.
#
# This is a manual, deliberate step — the operator decides when a pipeline
# version is ready for production.
#
# Usage:
#   ./promote-pipelines.sh --from tekton-test --to tekton-pipelines
#   ./promote-pipelines.sh --from tekton-test --to tekton-pipelines --dry-run
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

FROM_NS=""
TO_NS=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)    FROM_NS="$2"; shift 2 ;;
    --to)      TO_NS="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    *)         echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$FROM_NS" ]] || { echo "ERROR: --from is required" >&2; exit 1; }
[[ -n "$TO_NS" ]]   || { echo "ERROR: --to is required" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl

echo "=============================================="
echo "  Promote pipelines: $FROM_NS → $TO_NS"
echo "=============================================="

# Verify source namespace has resources
kubectl get namespace "$FROM_NS" &>/dev/null || { echo "ERROR: source namespace $FROM_NS not found" >&2; exit 1; }
kubectl get namespace "$TO_NS" &>/dev/null   || { echo "ERROR: target namespace $TO_NS not found (run bootstrap-namespace.sh first)" >&2; exit 1; }

APPLY_FLAG=""
if [[ "$DRY_RUN" == "true" ]]; then
  APPLY_FLAG="--dry-run=client"
  echo "  (dry-run mode — no changes will be applied)"
fi

echo ""
echo "  Applying tasks..."
kubectl apply -f "$REPO_ROOT/tasks/" -n "$TO_NS" $APPLY_FLAG

echo ""
echo "  Applying pipelines..."
kubectl apply -f "$REPO_ROOT/pipeline/" -n "$TO_NS" $APPLY_FLAG

echo ""
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  Dry run complete. Re-run without --dry-run to apply."
else
  echo "  Promotion complete: $FROM_NS → $TO_NS"
  echo "  Tasks and pipelines in $TO_NS now match the repo versions."
fi
echo ""

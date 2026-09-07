#!/usr/bin/env bash
# Re-run the PR pipeline from deploy-intercepts onward, reusing results from
# a previous (failed) PipelineRun. Avoids re-fetching, re-resolving, re-cloning,
# and re-building when only a later step failed.
#
# Usage:
#   ./scripts/rerun-pr-from.sh <failed-pipelinerun-or-stackrun-name>
#
# Creates a StackRun with spec.continueFrom; the operator builds stack-pr-continue.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
need() { command -v "$1" >/dev/null 2>&1 || die "$1 is required"; }
need kubectl

[[ $# -ge 1 ]] || die "Usage: $0 <failed-pipelinerun-or-stackrun-name>"
FAILED_RUN="$1"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
TIMEOUT="${TIMEOUT:-900}"

echo "=============================================="
echo "  Re-run PR pipeline from deploy-intercepts"
echo "  continueFrom: $FAILED_RUN"
echo "=============================================="

if ! kubectl get pipelinerun "$FAILED_RUN" -n "$NAMESPACE" &>/dev/null \
  && ! kubectl get stackrun "$FAILED_RUN" -n "$NAMESPACE" &>/dev/null; then
  die "PipelineRun/StackRun $FAILED_RUN not found in namespace $NAMESPACE"
fi

RUN_SHORT=$(kubectl create -f - -o jsonpath='{.metadata.name}' <<EOF
apiVersion: tektondag.io/v1alpha1
kind: StackRun
metadata:
  generateName: stackrun-pr-continue-
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/part-of: tekton-job-standardization
    tektondag.io/mode: pr
spec:
  mode: pr
  continueFrom: ${FAILED_RUN}
EOF
)

echo "  StackRun: $RUN_SHORT"
echo ""

PHASE=""
for i in $(seq 1 $((TIMEOUT / 10))); do
  sleep 10
  PHASE=$(kubectl get stackrun "$RUN_SHORT" -n "$NAMESPACE" \
    -o jsonpath='{.status.phase}' 2>/dev/null || true)
  PR=$(kubectl get stackrun "$RUN_SHORT" -n "$NAMESPACE" \
    -o jsonpath='{.status.pipelineRunName}' 2>/dev/null || true)
  if [[ "$PHASE" == "Succeeded" ]]; then
    echo "  Continuation succeeded (PipelineRun ${PR})."
    break
  fi
  if [[ "$PHASE" == "Failed" || "$PHASE" == "Error" || "$PHASE" == "Cancelled" ]]; then
    echo "FAILED: StackRun phase $PHASE." >&2
    kubectl get stackrun "$RUN_SHORT" -n "$NAMESPACE" -o yaml >&2 || true
    exit 1
  fi
  echo "    ${i}0s... phase=${PHASE:-pending} pr=${PR:-}"
done

if [[ "$PHASE" != "Succeeded" ]]; then
  echo "FAILED: continuation timed out (last phase: ${PHASE:-unknown})." >&2
  exit 1
fi

echo ""
echo "=============================================="
echo "  Continuation pipeline passed."
echo "=============================================="

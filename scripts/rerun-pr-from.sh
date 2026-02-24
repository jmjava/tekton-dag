#!/usr/bin/env bash
# Re-run the PR pipeline from deploy-intercepts onward, reusing results from
# a previous (failed) PipelineRun. Avoids re-fetching, re-resolving, re-cloning,
# and re-building when only a later step failed.
#
# Usage:
#   ./scripts/rerun-pr-from.sh <failed-pipelinerun-name>
#
# Requirements:
#   - The failed PipelineRun must still exist in the cluster
#   - Tasks resolve-stack and build-apps must have succeeded in the failed run
#   - The shared-workspace PVC from the failed run must still exist
#     (volumeClaimTemplates are kept until the PipelineRun is deleted)
#
# What it does:
#   1. Reads task results from the failed run's child TaskRuns
#   2. Finds the workspace PVC name from the failed run
#   3. Creates a new PipelineRun using stack-pr-continue, which starts
#      from deploy-intercepts → validate → test → push → cleanup
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

die() { echo "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "$1 is required"; }
need kubectl
need jq

[[ $# -ge 1 ]] || die "Usage: $0 <failed-pipelinerun-name>"
FAILED_RUN="$1"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
GIT_SSH_SECRET_NAME="${GIT_SSH_SECRET_NAME:-git-ssh-key}"
TIMEOUT="${TIMEOUT:-900}"

echo "=============================================="
echo "  Re-run PR pipeline from deploy-intercepts"
echo "  Source run: $FAILED_RUN"
echo "=============================================="

# Verify the failed run exists
kubectl get pipelinerun "$FAILED_RUN" -n "$NAMESPACE" &>/dev/null \
  || die "PipelineRun $FAILED_RUN not found in namespace $NAMESPACE"

# Helper: get a task result from the failed run's child TaskRuns
get_result() {
  local task_name="$1" result_name="$2"
  local taskrun_name
  taskrun_name=$(kubectl get pipelinerun "$FAILED_RUN" -n "$NAMESPACE" \
    -o jsonpath="{.status.childReferences[?(@.pipelineTaskName=='${task_name}')].name}" 2>/dev/null)
  [[ -n "$taskrun_name" ]] || die "TaskRun for task '$task_name' not found in $FAILED_RUN"

  local val
  val=$(kubectl get taskrun "$taskrun_name" -n "$NAMESPACE" \
    -o jsonpath="{.status.results[?(@.name=='${result_name}')].value}" 2>/dev/null)
  [[ -n "$val" ]] || die "Result '$result_name' not found in TaskRun $taskrun_name (task '$task_name'). Did it succeed?"
  echo "$val"
}

echo ""
echo "  Extracting results from $FAILED_RUN..."

STACK_JSON=$(get_result resolve-stack stack-json)
BUILD_APPS=$(get_result resolve-stack build-apps)
PROPAGATION_CHAIN=$(get_result resolve-stack propagation-chain)
INTERCEPT_HEADER=$(get_result resolve-stack intercept-header-value)
APP_LIST=$(get_result resolve-stack app-list)
ENTRY_APP=$(get_result resolve-stack entry-app)
BUILT_IMAGES=$(get_result build-apps built-images)
BUMPED_VERSIONS=$(get_result bump-rc-version bumped-versions)

echo "  build-apps:    $BUILD_APPS"
echo "  entry-app:     $ENTRY_APP"
echo "  built-images:  $(echo "$BUILT_IMAGES" | head -c 120)..."

# Find the workspace PVC from the failed run
WORKSPACE_PVC=$(kubectl get pipelinerun "$FAILED_RUN" -n "$NAMESPACE" \
  -o jsonpath='{.status.childReferences[0].name}' 2>/dev/null | xargs -I{} \
  kubectl get taskrun {} -n "$NAMESPACE" \
  -o jsonpath='{.spec.workspaces[?(@.name=="source")].persistentVolumeClaim.claimName}' 2>/dev/null)

if [[ -z "$WORKSPACE_PVC" ]]; then
  WORKSPACE_PVC=$(kubectl get pipelinerun "$FAILED_RUN" -n "$NAMESPACE" \
    -o jsonpath='{.status.childReferences[0].name}' 2>/dev/null | xargs -I{} \
    kubectl get taskrun {} -n "$NAMESPACE" \
    -o jsonpath='{.spec.workspaces[?(@.name=="output")].persistentVolumeClaim.claimName}' 2>/dev/null)
fi

[[ -n "$WORKSPACE_PVC" ]] || die "Could not find workspace PVC from $FAILED_RUN. Was the run using a volumeClaimTemplate?"
echo "  workspace PVC: $WORKSPACE_PVC"

# Get git params from original run
GIT_URL=$(kubectl get pipelinerun "$FAILED_RUN" -n "$NAMESPACE" \
  -o jsonpath='{.spec.params[?(@.name=="git-url")].value}' 2>/dev/null)
GIT_REV=$(kubectl get pipelinerun "$FAILED_RUN" -n "$NAMESPACE" \
  -o jsonpath='{.spec.params[?(@.name=="git-revision")].value}' 2>/dev/null)

echo ""
echo "  Launching stack-pr-continue pipeline..."

# Escape JSON values for embedding in YAML
STACK_JSON_ESC=$(echo "$STACK_JSON" | jq -c .)
BUILT_IMAGES_ESC=$(echo "$BUILT_IMAGES" | jq -c .)
BUMPED_VERSIONS_ESC=$(echo "$BUMPED_VERSIONS" | jq -c .)

RUN_NAME=$(kubectl create -f - -o name <<EOF
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: stack-pr-continue-
  namespace: $NAMESPACE
spec:
  pipelineRef:
    name: stack-pr-continue
  taskRunTemplate:
    serviceAccountName: tekton-pr-sa
  params:
    - name: stack-json
      value: '$STACK_JSON_ESC'
    - name: build-apps
      value: "$BUILD_APPS"
    - name: propagation-chain
      value: "$PROPAGATION_CHAIN"
    - name: intercept-header-value
      value: "$INTERCEPT_HEADER"
    - name: app-list
      value: "$APP_LIST"
    - name: entry-app
      value: "$ENTRY_APP"
    - name: built-images
      value: '$BUILT_IMAGES_ESC'
    - name: bumped-versions
      value: '$BUMPED_VERSIONS_ESC'
    - name: git-url
      value: "${GIT_URL:-https://github.com/jmjava/tekton-dag.git}"
    - name: git-revision
      value: "${GIT_REV:-main}"
  workspaces:
    - name: shared-workspace
      persistentVolumeClaim:
        claimName: $WORKSPACE_PVC
    - name: ssh-key
      secret:
        secretName: $GIT_SSH_SECRET_NAME
EOF
)

RUN_SHORT=$(echo "$RUN_NAME" | sed 's|.*/||')
echo "  PipelineRun: $RUN_SHORT"
echo ""

PHASE=""
for i in $(seq 1 $((TIMEOUT / 10))); do
  sleep 10
  PHASE=$(kubectl get pipelinerun "$RUN_SHORT" -n "$NAMESPACE" \
    -o jsonpath='{.status.conditions[0].reason}' 2>/dev/null || true)
  if [[ "$PHASE" == "Succeeded" ]]; then
    echo "  Continuation pipeline succeeded."
    break
  fi
  if [[ "$PHASE" == "Failed" ]]; then
    echo "FAILED: Continuation pipeline failed." >&2
    kubectl get taskrun -n "$NAMESPACE" -l "tekton.dev/pipelineRun=$RUN_SHORT" \
      -o custom-columns='TASK:.metadata.labels.tekton\.dev/pipelineTask,STATUS:.status.conditions[0].reason,MSG:.status.conditions[0].message' \
      --no-headers 2>/dev/null
    exit 1
  fi
  echo "    ${i}0s..."
done

if [[ "$PHASE" != "Succeeded" ]]; then
  echo "FAILED: Continuation pipeline timed out (last phase: ${PHASE:-unknown})." >&2
  exit 1
fi

echo ""
echo "=============================================="
echo "  Continuation pipeline passed."
echo "=============================================="

#!/usr/bin/env bash
set -euo pipefail

# verify-dag-phase2.sh — Phase 2 of local DAG verification (cluster + Tekton).
# Runs the stack-dag-verify pipeline (fetch + resolve only), then compares
# resolve-stack task results to stack-graph.sh CLI output.
#
# Prerequisites: k8s cluster, Tekton Pipelines, tasks + pipelines applied,
#                 git-clone task (Tekton catalog), resolve-stack task.
# Usage: ./verify-dag-phase2.sh [--stack STACK] [--changed-app APP] [--git-url URL] [--git-revision REV]
#
# Example: ./verify-dag-phase2.sh --stack stack-one.yaml

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MILESTONE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$MILESTONE_DIR"

STACK_FILE="stack-one.yaml"
CHANGED_APP=""
# Default HTTPS so clone works without SSH keys (public repo)
GIT_URL="${GIT_URL:-https://github.com/jmjava/tekton-dag.git}"
GIT_REV="${GIT_REV:-main}"
STORAGE_CLASS="${STORAGE_CLASS:-}"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-120}"

DRY_RUN=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stack)        STACK_FILE="$2"; shift 2 ;;
    --changed-app) CHANGED_APP="$2"; shift 2 ;;
    --git-url)     GIT_URL="$2"; shift 2 ;;
    --git-revision) GIT_REV="$2"; shift 2 ;;
    --storage-class) STORAGE_CLASS="$2"; shift 2 ;;
    --timeout)     WAIT_TIMEOUT="$2"; shift 2 ;;
    --dry-run)     DRY_RUN=true; shift ;;
    *)             echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

STACK_PATH="stacks/$STACK_FILE"
[ -f "stacks/$STACK_FILE" ] || { echo "FAIL: stacks/$STACK_FILE not found" >&2; exit 1; }

die()  { echo "FAIL: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "required: $1"; }
need kubectl
need jq

echo "=============================================="
echo "  Phase 2: DAG verify (Tekton resolve vs CLI)"
echo "  Stack: $STACK_FILE"
echo "=============================================="

# Dry-run: print CLI expected values and skip cluster
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  (dry-run: no cluster; showing CLI expected values for comparison)"
  CLI_APP_LIST=$(./scripts/stack-graph.sh "stacks/$STACK_FILE" --topo | tr '\n' ' ' | xargs)
  CLI_ENTRY=$(./scripts/stack-graph.sh "stacks/$STACK_FILE" --entry | tr -d '\n')
  CLI_CHAIN=$(./scripts/stack-graph.sh "stacks/$STACK_FILE" --chain "$CLI_ENTRY" | tr '\n' ' ' | xargs)
  [ -n "$CHANGED_APP" ] && CLI_BUILD_APPS="$CHANGED_APP" || CLI_BUILD_APPS="$CLI_APP_LIST"
  echo ""
  echo "  Expected (CLI) values that Tekton resolve-stack should produce:"
  echo "    app-list:         $CLI_APP_LIST"
  echo "    entry-app:       $CLI_ENTRY"
  echo "    propagation-chain: $CLI_CHAIN"
  echo "    build-apps:       $CLI_BUILD_APPS"
  echo ""
  echo "  To run Phase 2 for real: apply pipeline/ and tasks/, then run without --dry-run."
  exit 0
fi

# Ensure pipeline and tasks exist
kubectl get pipeline stack-dag-verify -n "$NAMESPACE" >/dev/null 2>&1 || die "Pipeline stack-dag-verify not found. Apply pipeline/ and tasks/ first (or use --dry-run to print expected values)."
kubectl get task resolve-stack -n "$NAMESPACE" >/dev/null 2>&1 || die "Task resolve-stack not found. Apply tasks/ first."

# Create PipelineRun
RUN_NAME="dag-verify-$(date +%s)"
if [ -n "$STORAGE_CLASS" ]; then
  STORAGE_LINE="
          storageClassName: $STORAGE_CLASS"
else
  STORAGE_LINE=""
fi
cat <<EOF | kubectl create -f -
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  name: $RUN_NAME
  namespace: $NAMESPACE
spec:
  pipelineRef:
    name: stack-dag-verify
  params:
    - name: git-url
      value: "$GIT_URL"
    - name: git-revision
      value: "$GIT_REV"
    - name: stack-file
      value: "$STACK_PATH"
    - name: changed-app
      value: "$CHANGED_APP"
    - name: version-overrides
      value: "{}"
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:$STORAGE_LINE
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 2Gi
EOF

echo "  PipelineRun: $RUN_NAME (waiting up to ${WAIT_TIMEOUT}s, polling every 5s)..."
for i in $(seq 1 "$WAIT_TIMEOUT"); do
  if [ $((i % 5)) -eq 0 ]; then
    echo "    ${i}s..."
  fi
  STATUS=$(kubectl get pipelinerun "$RUN_NAME" -n "$NAMESPACE" -o jsonpath='{.status.conditions[0].reason}' 2>/dev/null || echo "")
  if [[ "$STATUS" == "Succeeded" ]]; then
    echo "  PipelineRun succeeded."
    break
  fi
  if [[ "$STATUS" == "Failed" ]]; then
    echo "  PipelineRun failed. Check: kubectl describe pipelinerun $RUN_NAME -n $NAMESPACE"
    kubectl get taskrun -n "$NAMESPACE" -l "tekton.dev/pipelineRun=$RUN_NAME" -o wide 2>/dev/null || true
    exit 1
  fi
  sleep 1
done
STATUS=$(kubectl get pipelinerun "$RUN_NAME" -n "$NAMESPACE" -o jsonpath='{.status.conditions[0].reason}' 2>/dev/null || echo "")
if [[ "$STATUS" != "Succeeded" ]]; then
  echo "  PipelineRun did not succeed within ${WAIT_TIMEOUT}s (reason: $STATUS). Check: kubectl describe pipelinerun $RUN_NAME -n $NAMESPACE"
  exit 1
fi

# Find the resolve-stack TaskRun for this PipelineRun (name contains resolve-stack)
TR_NAME=$(kubectl get taskrun -n "$NAMESPACE" -l "tekton.dev/pipelineRun=$RUN_NAME" -o json | jq -r '.items[] | .metadata.name' | grep -E "resolve-stack" | head -1)
[ -z "$TR_NAME" ] && die "Could not find resolve-stack TaskRun for run $RUN_NAME"

# Get results (Tekton v1: .status.results; older: .status.taskResults)
get_result() {
  kubectl get taskrun "$TR_NAME" -n "$NAMESPACE" -o json | jq -r --arg n "$1" '
    (.status.results // .status.taskResults // [])[] | select(.name == $n) | .value
  '
}
TEKTON_APP_LIST=$(get_result "app-list" | tr '\n' ' ' | xargs)
TEKTON_ENTRY=$(get_result "entry-app" | tr -d '\n')
TEKTON_CHAIN=$(get_result "propagation-chain" | tr '\n' ' ' | xargs)
TEKTON_BUILD_APPS=$(get_result "build-apps" | tr '\n' ' ' | xargs)

# CLI equivalents (normalize to space-separated single line)
CLI_APP_LIST=$(./scripts/stack-graph.sh "stacks/$STACK_FILE" --topo | tr '\n' ' ' | xargs)
CLI_ENTRY=$(./scripts/stack-graph.sh "stacks/$STACK_FILE" --entry | tr -d '\n')
CLI_CHAIN=$(./scripts/stack-graph.sh "stacks/$STACK_FILE" --chain "$CLI_ENTRY" | tr '\n' ' ' | xargs)
if [ -n "$CHANGED_APP" ]; then
  CLI_BUILD_APPS="$CHANGED_APP"
else
  CLI_BUILD_APPS="$CLI_APP_LIST"
fi

# Compare (order may differ for chain in fan-out; we compare sorted or exact per field)
compare() {
  local name="$1" a="$2" b="$3"
  if [[ "$a" == "$b" ]]; then
    echo "  OK: $name match"
    return 0
  else
    echo "  FAIL: $name mismatch"
    echo "    Tekton: $a"
    echo "    CLI:    $b"
    return 1
  fi
}
ERRORS=0
compare "app-list"       "$TEKTON_APP_LIST"   "$CLI_APP_LIST"   || ERRORS=$((ERRORS+1))
compare "entry-app"      "$TEKTON_ENTRY"     "$CLI_ENTRY"      || ERRORS=$((ERRORS+1))
compare "build-apps"     "$TEKTON_BUILD_APPS" "$CLI_BUILD_APPS" || ERRORS=$((ERRORS+1))

# Propagation chain: same set of apps, order may differ for DAGs with multiple terminals
CLI_CHAIN_SORTED=$(echo "$CLI_CHAIN" | tr ' ' '\n' | sort | tr '\n' ' ' | xargs)
TEKTON_CHAIN_SORTED=$(echo "$TEKTON_CHAIN" | tr ' ' '\n' | sort | tr '\n' ' ' | xargs)
if [[ "$CLI_CHAIN_SORTED" == "$TEKTON_CHAIN_SORTED" ]]; then
  echo "  OK: propagation-chain (same apps)"
else
  echo "  FAIL: propagation-chain"
  echo "    Tekton: $TEKTON_CHAIN"
  echo "    CLI:    $CLI_CHAIN"
  ERRORS=$((ERRORS+1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "  Phase 2 PASSED (Tekton resolve matches CLI)"
  exit 0
else
  echo "  Phase 2 FAILED ($ERRORS mismatch(es))"
  exit 1
fi

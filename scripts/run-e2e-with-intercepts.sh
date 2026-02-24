#!/usr/bin/env bash
# Run full E2E with live Telepresence intercepts: bootstrap (build + deploy full stack),
# then PR pipeline (build changed-app, deploy intercepts, run E2E through entry).
# Prerequisites: Kind, Tekton, Postgres, Results, Telepresence Traffic Manager.
# Required: Kubernetes secret with SSH key for cloning app repos, e.g.:
#   kubectl create secret generic git-ssh-key --from-file=id_ed25519=$HOME/.ssh/id_ed25519 -n tekton-pipelines
# Override name with GIT_SSH_SECRET_NAME.
#
# Usage: ./run-e2e-with-intercepts.sh [--stack STACK] [--changed-app APP] [--pr N] [--registry URL] [--skip-install-check] [--no-verify-db]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

STACK_FILE="stack-one.yaml"
STACK_PATH="stacks/$STACK_FILE"
CHANGED_APP="demo-fe"
PR_NUMBER="1"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-localhost:5000}"
GIT_URL="${GIT_URL:-https://github.com/jmjava/tekton-dag.git}"
GIT_REV="${GIT_REV:-main}"
GIT_SSH_SECRET_NAME="${GIT_SSH_SECRET_NAME:-git-ssh-key}"
SKIP_INSTALL_CHECK=false
NO_VERIFY_DB=false
BOOTSTRAP_TIMEOUT=900
PR_TIMEOUT=900

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stack)              STACK_FILE="$2"; STACK_PATH="stacks/$STACK_FILE"; shift 2 ;;
    --changed-app)        CHANGED_APP="$2"; shift 2 ;;
    --pr)                  PR_NUMBER="$2"; shift 2 ;;
    --registry)            IMAGE_REGISTRY="$2"; shift 2 ;;
    --skip-install-check)  SKIP_INSTALL_CHECK=true; shift ;;
    --no-verify-db)        NO_VERIFY_DB=true; shift ;;
    *)                     echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl
need jq

if [[ "$SKIP_INSTALL_CHECK" != "true" ]]; then
  kubectl cluster-info &>/dev/null || { echo "No cluster. Run kind-with-registry.sh and install-tekton.sh." >&2; exit 1; }
  kubectl get deployment tekton-results-api -n tekton-pipelines &>/dev/null || { echo "Tekton Results not found. Run install-postgres-kind.sh and install-tekton-results.sh." >&2; exit 1; }
  kubectl get deployment traffic-manager -n ambassador &>/dev/null || { echo "Telepresence Traffic Manager not found. Run install-telepresence-traffic-manager.sh." >&2; exit 1; }
  kubectl get secret "$GIT_SSH_SECRET_NAME" -n tekton-pipelines &>/dev/null || { echo "Secret $GIT_SSH_SECRET_NAME not found. Create it with: kubectl create secret generic $GIT_SSH_SECRET_NAME --from-file=id_ed25519=\$HOME/.ssh/id_ed25519 -n tekton-pipelines" >&2; exit 1; }
fi

[[ -f "$STACK_PATH" ]] || { echo "Stack not found: $STACK_PATH" >&2; exit 1; }

# Ensure SA and RBAC for pipeline (deploy in staging, etc.)
kubectl create serviceaccount tekton-pr-sa -n tekton-pipelines 2>/dev/null || true
kubectl create clusterrolebinding tekton-pr-sa-admin --clusterrole=cluster-admin --serviceaccount=tekton-pipelines:tekton-pr-sa 2>/dev/null || true

echo "=============================================="
echo "  E2E with live Telepresence intercepts"
echo "  Stack: $STACK_FILE  changed-app: $CHANGED_APP  pr: $PR_NUMBER"
echo "  Registry: $IMAGE_REGISTRY"
echo "=============================================="

# 1. Bootstrap: build all apps, deploy full stack
echo ""
echo ">>> Step 1: Bootstrap (build all + deploy full stack)"
BOOTSTRAP_RUN=$(kubectl create -f - -o name <<EOF
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: stack-bootstrap-
  namespace: tekton-pipelines
spec:
  pipelineRef:
    name: stack-bootstrap
  taskRunTemplate:
    serviceAccountName: tekton-pr-sa
  params:
    - name: git-url
      value: "$GIT_URL"
    - name: git-revision
      value: "$GIT_REV"
    - name: stack-file
      value: "$STACK_PATH"
    - name: image-registry
      value: "$IMAGE_REGISTRY"
    - name: image-tag
      value: "base-1"
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 10Gi
    - name: ssh-key
      secret:
        secretName: $GIT_SSH_SECRET_NAME
EOF
)
BOOTSTRAP_NAME=$(echo "$BOOTSTRAP_RUN" | sed 's|.*/||')
[[ -n "$BOOTSTRAP_NAME" ]] || { echo "FAILED: could not get bootstrap PipelineRun name" >&2; exit 1; }
echo "  PipelineRun: $BOOTSTRAP_NAME (waiting up to ${BOOTSTRAP_TIMEOUT}s)..."
PHASE=""
for i in $(seq 1 $((BOOTSTRAP_TIMEOUT/10))); do
  sleep 10
  PHASE=$(kubectl get pipelinerun "$BOOTSTRAP_NAME" -n tekton-pipelines -o jsonpath='{.status.conditions[0].reason}' 2>/dev/null || true)
  if [[ "$PHASE" == "Succeeded" ]]; then
    echo "  Bootstrap succeeded."
    break
  fi
  if [[ "$PHASE" == "Failed" ]]; then
    echo "FAILED: Bootstrap pipeline failed." >&2
    echo "  kubectl describe pipelinerun $BOOTSTRAP_NAME -n tekton-pipelines" >&2
    kubectl describe pipelinerun "$BOOTSTRAP_NAME" -n tekton-pipelines 2>&1 | tail -40
    exit 1
  fi
  echo "    ${i}0s..."
done
if [[ "$PHASE" != "Succeeded" ]]; then
  echo "FAILED: Bootstrap pipeline timed out (last phase: ${PHASE:-unknown})." >&2
  exit 1
fi

# 2. PR pipeline: build changed app, deploy intercepts, run E2E
echo ""
echo ">>> Step 2: PR pipeline (intercepts + E2E)"
./scripts/generate-run.sh --mode pr --stack "$STACK_FILE" --app "$CHANGED_APP" --pr "$PR_NUMBER" \
  --registry "$IMAGE_REGISTRY" --git-url "$GIT_URL" --git-revision "$GIT_REV" \
  --storage-class "" | kubectl create -f - || { echo "FAILED: creating PR PipelineRun" >&2; exit 1; }
sleep 3
PR_RUN_NAME=$(kubectl get pipelinerun -n tekton-pipelines -l tekton.dev/pipeline=stack-pr-test --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null)
[[ -n "$PR_RUN_NAME" ]] || { echo "FAILED: could not get PR PipelineRun name" >&2; exit 1; }
echo "  PipelineRun: $PR_RUN_NAME (waiting up to ${PR_TIMEOUT}s)..."
PHASE=""
for i in $(seq 1 $((PR_TIMEOUT/10))); do
  sleep 10
  PHASE=$(kubectl get pipelinerun "$PR_RUN_NAME" -n tekton-pipelines -o jsonpath='{.status.conditions[0].reason}' 2>/dev/null || true)
  if [[ "$PHASE" == "Succeeded" ]]; then
    echo "  PR pipeline (E2E) succeeded."
    break
  fi
  if [[ "$PHASE" == "Failed" ]]; then
    echo "FAILED: PR pipeline failed." >&2
    echo "  kubectl describe pipelinerun $PR_RUN_NAME -n tekton-pipelines" >&2
    kubectl describe pipelinerun "$PR_RUN_NAME" -n tekton-pipelines 2>&1 | tail -50
    exit 1
  fi
  echo "    ${i}0s..."
done
if [[ "$PHASE" != "Succeeded" ]]; then
  echo "FAILED: PR pipeline timed out (last phase: ${PHASE:-unknown})." >&2
  exit 1
fi

# 3. Verify Tekton Results DB (bootstrap + PR pipeline => at least 2 results stored)
if [[ "$NO_VERIFY_DB" != "true" ]]; then
  echo ""
  sleep 10
  echo ">>> Step 3: Verify Tekton Results DB"
  ./scripts/verify-results-in-db.sh --min-count 2 --namespace tekton-pipelines || { echo "FAILED: Tekton Results DB verification." >&2; exit 1; }
else
  echo ""
  echo "  (Skipping Tekton Results DB verification --no-verify-db)"
fi

echo ""
echo "=============================================="
echo "  E2E with intercepts passed (including Tekton Results DB)."
echo "=============================================="

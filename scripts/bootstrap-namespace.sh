#!/usr/bin/env bash
# Bootstrap a Tekton namespace with all required resources:
#   ServiceAccount, secrets, PVC (build-cache), RBAC, and catalog tasks.
#
# Usage:
#   ./bootstrap-namespace.sh <namespace>
#   ./bootstrap-namespace.sh tekton-test
#   ./bootstrap-namespace.sh tekton-test --ssh-key ~/.ssh/id_ed25519 --github-token ghp_xxx
#
# Defaults to tekton-pipelines if no namespace is given.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

NAMESPACE="${1:-tekton-pipelines}"
shift 2>/dev/null || true

SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/id_ed25519}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-}"
GIT_CLONE_URL="${TEKTON_GIT_CLONE_URL:-https://raw.githubusercontent.com/tektoncd/catalog/main/task/git-clone/0.9/git-clone.yaml}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ssh-key)        SSH_KEY_PATH="$2"; shift 2 ;;
    --github-token)   GITHUB_TOKEN="$2"; shift 2 ;;
    --webhook-secret) WEBHOOK_SECRET="$2"; shift 2 ;;
    *)                echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl

echo "=============================================="
echo "  Bootstrap namespace: $NAMESPACE"
echo "=============================================="

# 1. Create namespace if it doesn't exist
kubectl get namespace "$NAMESPACE" &>/dev/null || kubectl create namespace "$NAMESPACE"

# Relax Pod Security (needed for Kind and local clusters)
kubectl label namespace "$NAMESPACE" pod-security.kubernetes.io/enforce=privileged --overwrite 2>/dev/null || true
kubectl label namespace "$NAMESPACE" pod-security.kubernetes.io/audit=privileged --overwrite 2>/dev/null || true
kubectl label namespace "$NAMESPACE" pod-security.kubernetes.io/warn=privileged --overwrite 2>/dev/null || true

# 2. ServiceAccount
echo "  Creating ServiceAccount tekton-pr-sa..."
kubectl create serviceaccount tekton-pr-sa -n "$NAMESPACE" 2>/dev/null || true

# 3. RBAC — cluster-admin for the SA (pipeline needs to deploy to staging, create intercepts, etc.)
echo "  Creating ClusterRoleBinding..."
kubectl create clusterrolebinding "tekton-pr-sa-admin-${NAMESPACE}" \
  --clusterrole=cluster-admin \
  --serviceaccount="$NAMESPACE:tekton-pr-sa" 2>/dev/null || true

# 4. Secrets
echo "  Creating secrets..."

# SSH key for cloning app repos
if [[ -f "$SSH_KEY_PATH" ]]; then
  kubectl create secret generic git-ssh-key \
    --from-file=id_ed25519="$SSH_KEY_PATH" \
    -n "$NAMESPACE" 2>/dev/null || true
else
  echo "    SKIP: SSH key not found at $SSH_KEY_PATH (create manually: kubectl create secret generic git-ssh-key --from-file=id_ed25519=<path> -n $NAMESPACE)"
fi

# GitHub token (for post-pr-comment task)
if [[ -n "$GITHUB_TOKEN" ]]; then
  kubectl create secret generic github-token \
    --from-literal=token="$GITHUB_TOKEN" \
    -n "$NAMESPACE" 2>/dev/null || true
else
  echo "    SKIP: GITHUB_TOKEN not set (create manually if needed)"
fi

# Webhook secret (for EventListener validation)
if [[ -n "$WEBHOOK_SECRET" ]]; then
  kubectl create secret generic github-webhook-secret \
    --from-literal=secret="$WEBHOOK_SECRET" \
    -n "$NAMESPACE" 2>/dev/null || true
else
  echo "    SKIP: WEBHOOK_SECRET not set (create manually if needed)"
fi

# 5. Persistent build-cache PVC
echo "  Creating build-cache PVC..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: build-cache
  namespace: $NAMESPACE
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 5Gi
EOF

# 6. Catalog tasks (git-clone — installed per namespace for isolation)
echo "  Installing git-clone task..."
kubectl apply -f "$GIT_CLONE_URL" -n "$NAMESPACE" 2>/dev/null || \
  kubectl apply -f "$GIT_CLONE_URL" -n "$NAMESPACE" --server-side=true 2>/dev/null || true

# 7. This repo's tasks and pipelines
echo "  Applying stack tasks and pipelines..."
kubectl apply -f "$REPO_ROOT/tasks/" -n "$NAMESPACE"
kubectl apply -f "$REPO_ROOT/pipeline/" -n "$NAMESPACE"

echo ""
echo "  Namespace $NAMESPACE bootstrapped."
echo "  To run a pipeline:  NAMESPACE=$NAMESPACE ./scripts/generate-run.sh --mode pr --repo demo-fe --pr 1 --apply"
echo ""

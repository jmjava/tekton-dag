#!/usr/bin/env bash
# Install Tekton Pipelines and the git-clone task, then apply this repo's tasks and pipelines.
# Run after kind-with-registry.sh (or any cluster). Requires kubectl context set.
# Usage: ./install-tekton.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

MILESTONE_DIR="$REPO_ROOT"
cd "$MILESTONE_DIR"

TEKTON_PIPELINE_URL="${TEKTON_PIPELINE_URL:-https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml}"
TEKTON_TRIGGERS_URL="${TEKTON_TRIGGERS_URL:-https://storage.googleapis.com/tekton-releases/triggers/latest/release.yaml}"
TEKTON_TRIGGERS_INTERCEPTORS_URL="${TEKTON_TRIGGERS_INTERCEPTORS_URL:-https://storage.googleapis.com/tekton-releases/triggers/latest/interceptors.yaml}"
TEKTON_GIT_CLONE_URL="${TEKTON_GIT_CLONE_URL:-https://raw.githubusercontent.com/tektoncd/catalog/main/task/git-clone/0.9/git-clone.yaml}"

need kubectl

echo "=============================================="
echo "  Install Tekton (Pipelines + git-clone + stack tasks/pipelines)"
echo "=============================================="

# Ensure namespace exists (Tekton release may create it; create if not)
kubectl get namespace "$NAMESPACE" &>/dev/null || kubectl create namespace "$NAMESPACE"

# 1. Tekton Pipelines (kubectl apply is idempotent)
echo "  Installing Tekton Pipelines..."
kubectl apply -f "$TEKTON_PIPELINE_URL"
# Relax Pod Security for the target namespace (Kind enforces restricted; catalog/git-clone task pods need it)
echo "  Configuring namespace $NAMESPACE for Pod Security (Kind/local clusters)..."
kubectl label namespace "$NAMESPACE" pod-security.kubernetes.io/enforce=privileged --overwrite 2>/dev/null || true
kubectl label namespace "$NAMESPACE" pod-security.kubernetes.io/audit=privileged --overwrite 2>/dev/null || true
kubectl label namespace "$NAMESPACE" pod-security.kubernetes.io/warn=privileged --overwrite 2>/dev/null || true
echo "  Waiting for Tekton Pipelines to be ready..."
kubectl wait --for=condition=Ready pods -l app.kubernetes.io/part-of=tekton-pipelines -n "$NAMESPACE" --timeout=120s 2>/dev/null || true

# 2. Tekton Triggers (required for pipeline/triggers.yaml — EventListener, TriggerBinding, TriggerTemplate)
echo "  Installing Tekton Triggers..."
kubectl apply -f "$TEKTON_TRIGGERS_URL"
kubectl apply -f "$TEKTON_TRIGGERS_INTERCEPTORS_URL"
echo "  Waiting for Tekton Triggers to be ready..."
kubectl wait --for=condition=Ready pods -l app.kubernetes.io/part-of=tekton-triggers -n "$NAMESPACE" --timeout=120s 2>/dev/null || true

# 3. git-clone task (into target namespace so our pipelines can reference it)
echo "  Installing git-clone task..."
kubectl apply -f "$TEKTON_GIT_CLONE_URL" -n "$NAMESPACE" 2>/dev/null || \
  kubectl apply -f "$TEKTON_GIT_CLONE_URL" -n "$NAMESPACE" --server-side=true 2>/dev/null || true

# 4. This repo's tasks and pipelines (kubectl apply is idempotent; triggers apply now that Triggers is installed)
echo "  Applying stack tasks and pipelines..."
kubectl apply -f "$MILESTONE_DIR/tasks/" -n "$NAMESPACE"
kubectl apply -f "$MILESTONE_DIR/pipeline/" -n "$NAMESPACE"

echo ""
echo "  Done. For full PR pipeline (intercepts), also install the Traffic Manager:"
echo "    ./scripts/install-telepresence-traffic-manager.sh"
echo "  Then you can run:"
echo "    ./scripts/verify-dag-phase2.sh   # DAG verification (resolve vs CLI)"
echo "    ./scripts/generate-run.sh --mode merge --repo demo-fe --registry localhost:5000 --storage-class \"\" | kubectl create -f -"
echo "    ./scripts/generate-run.sh --mode pr --repo demo-fe --pr 42 --registry localhost:5000 --storage-class \"\" | kubectl create -f -  # full PR with intercepts"
echo ""

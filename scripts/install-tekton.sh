#!/usr/bin/env bash
# Install Tekton Pipelines and the git-clone task, then apply this repo's tasks and pipelines.
# Run after kind-with-registry.sh (or any cluster). Requires kubectl context set.
# Usage: ./install-tekton.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MILESTONE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$MILESTONE_DIR"

TEKTON_PIPELINE_URL="${TEKTON_PIPELINE_URL:-https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml}"
TEKTON_GIT_CLONE_URL="${TEKTON_GIT_CLONE_URL:-https://raw.githubusercontent.com/tektoncd/catalog/main/task/git-clone/0.9/git-clone.yaml}"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl

echo "=============================================="
echo "  Install Tekton (Pipelines + git-clone + stack tasks/pipelines)"
echo "=============================================="

# 1. Tekton Pipelines
echo "  Installing Tekton Pipelines..."
kubectl apply -f "$TEKTON_PIPELINE_URL"
# Relax Pod Security for tekton-pipelines (Kind enforces restricted; catalog/git-clone task pods need it)
echo "  Configuring namespace for Pod Security (Kind/local clusters)..."
kubectl label namespace tekton-pipelines pod-security.kubernetes.io/enforce=privileged --overwrite 2>/dev/null || true
kubectl label namespace tekton-pipelines pod-security.kubernetes.io/audit=privileged --overwrite 2>/dev/null || true
kubectl label namespace tekton-pipelines pod-security.kubernetes.io/warn=privileged --overwrite 2>/dev/null || true
echo "  Waiting for Tekton Pipelines to be ready..."
kubectl wait --for=condition=Ready pods -l app.kubernetes.io/part-of=tekton-pipelines -n tekton-pipelines --timeout=120s 2>/dev/null || true

# 2. git-clone task (into tekton-pipelines namespace so our pipelines can reference it)
echo "  Installing git-clone task..."
kubectl apply -f "$TEKTON_GIT_CLONE_URL" -n "$NAMESPACE" 2>/dev/null || \
  kubectl apply -f "$TEKTON_GIT_CLONE_URL" -n "$NAMESPACE" --server-side=true 2>/dev/null || true

# 3. This repo's tasks and pipelines
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

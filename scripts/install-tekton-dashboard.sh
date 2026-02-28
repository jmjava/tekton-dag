#!/usr/bin/env bash
# Install the official Tekton Dashboard in the cluster (read-only by default).
# Prerequisites: Tekton Pipelines installed (e.g. in tekton-pipelines namespace).
#
# Usage: ./install-tekton-dashboard.sh [--read-write] [--namespace NS]
#
# After install, access via:
#   ./scripts/port-forward-tekton-dashboard.sh   # or manually:
#   kubectl -n tekton-pipelines port-forward svc/tekton-dashboard 9097:9097
#   Then open http://localhost:9097
#
# PipelineRun detail URL: {DASHBOARD_BASE}/#/namespaces/{namespace}/pipelineruns/{name}
# e.g. http://localhost:9097/#/namespaces/tekton-pipelines/pipelineruns/stack-pr-1-abc12
#
# Uninstall: ./scripts/uninstall-tekton-dashboard.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${TEKTON_NAMESPACE:-tekton-pipelines}"
READ_WRITE=false
RELEASE_URL="https://infra.tekton.dev/tekton-releases/dashboard/latest/release.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --read-write) READ_WRITE=true; shift ;;
    --namespace)  NAMESPACE="$2"; shift 2 ;;
    *)            echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Default Dashboard installs into tekton-pipelines; manifest has namespace in it
if [[ "$NAMESPACE" != "tekton-pipelines" ]]; then
  echo "Note: Custom namespace ($NAMESPACE) may require using the upstream installer script instead of release.yaml."
  echo "See: https://github.com/tektoncd/dashboard/tree/main/docs/dev/installer.md"
fi

if [[ "$READ_WRITE" == "true" ]]; then
  RELEASE_URL="https://infra.tekton.dev/tekton-releases/dashboard/latest/release-full.yaml"
fi

echo "Installing Tekton Dashboard (read-only=$([ "$READ_WRITE" = true ] && echo false || echo true))..."
kubectl apply -f "$RELEASE_URL"

echo "Waiting for Dashboard deployment (up to 120s)..."
if kubectl wait --for=condition=available --timeout=120s deployment/tekton-dashboard -n tekton-pipelines 2>/dev/null; then
  echo "Tekton Dashboard is ready."
else
  echo "Wait timed out or deployment not found; check: kubectl get pods -n tekton-pipelines -l app.kubernetes.io/part-of=tekton-dashboard"
fi

echo ""
echo "To access the Dashboard:"
echo "  ./scripts/port-forward-tekton-dashboard.sh"
echo "  Then open http://localhost:9097"
echo ""
echo "PipelineRun detail URL: http://localhost:9097/#/namespaces/tekton-pipelines/pipelineruns/<run-name>"

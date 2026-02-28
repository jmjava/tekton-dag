#!/usr/bin/env bash
# Port-forward the Tekton Dashboard so you can open it in the browser.
# Run this and keep it in the foreground, or run in background:
#   ./scripts/port-forward-tekton-dashboard.sh &
#
# Usage: ./port-forward-tekton-dashboard.sh [PORT]
# Default PORT=9097. Then open http://localhost:9097
set -euo pipefail

NAMESPACE="${TEKTON_NAMESPACE:-tekton-pipelines}"
PORT="${1:-9097}"

if ! kubectl get svc tekton-dashboard -n "$NAMESPACE" &>/dev/null; then
  echo "Tekton Dashboard not found in namespace $NAMESPACE. Install it first:"
  echo "  ./scripts/install-tekton-dashboard.sh"
  exit 1
fi

echo "Forwarding http://localhost:$PORT -> tekton-dashboard ($NAMESPACE). Press Ctrl+C to stop."
kubectl -n "$NAMESPACE" port-forward svc/tekton-dashboard "$PORT:9097"

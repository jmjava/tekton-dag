#!/usr/bin/env bash
# Install Telepresence Traffic Manager in the cluster so PR pipeline intercepts can work.
# Run after the cluster is up (e.g. after kind-with-registry.sh). Requires helm and kubectl.
# Usage: ./install-telepresence-traffic-manager.sh [--version VERSION]
# Example: ./install-telepresence-traffic-manager.sh --version 2.20.0
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TELEPRESENCE_VERSION="${TELEPRESENCE_VERSION:-2.20.0}"
NAMESPACE="${TELEPRESENCE_NAMESPACE:-ambassador}"
CHART_OCI="oci://ghcr.io/telepresenceio/telepresence-oss"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) TELEPRESENCE_VERSION="$2"; shift 2 ;;
    --namespace) NAMESPACE="$2"; shift 2 ;;
    *)         echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need helm
need kubectl

echo "=============================================="
echo "  Install Telepresence Traffic Manager"
echo "  Version:  $TELEPRESENCE_VERSION"
echo "  Namespace: $NAMESPACE"
echo "=============================================="

# Install or upgrade so idempotent
if helm status traffic-manager -n "$NAMESPACE" >/dev/null 2>&1; then
  echo "  Upgrading existing traffic-manager..."
  helm upgrade --namespace "$NAMESPACE" --reuse-values \
    --version "$TELEPRESENCE_VERSION" \
    traffic-manager "$CHART_OCI"
else
  echo "  Installing traffic-manager..."
  helm install --create-namespace --namespace "$NAMESPACE" \
    --version "$TELEPRESENCE_VERSION" \
    traffic-manager "$CHART_OCI"
fi

echo "  Waiting for Traffic Manager to be ready..."
kubectl wait --for=condition=Available deployment/traffic-manager -n "$NAMESPACE" --timeout=120s 2>/dev/null || true

echo ""
echo "  Done. Traffic Manager is in namespace '$NAMESPACE'."
echo "  PR pipeline deploy-intercept pods will use it for intercepts."
echo "  (Sidecar image in deploy-intercept task should match; default tel2:2.20.0)"
echo ""

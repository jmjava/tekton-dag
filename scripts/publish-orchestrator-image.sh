#!/usr/bin/env bash
# Build and push the tekton-dag-orchestrator Docker image to the Kind registry.
#
# Usage:
#   ./scripts/publish-orchestrator-image.sh              # defaults: localhost:5001, tag latest
#   ./scripts/publish-orchestrator-image.sh myreg:5000   # override registry
#   ./scripts/publish-orchestrator-image.sh myreg:5000 v2 # registry and tag
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REGISTRY="${1:-localhost:5001}"
TAG="${2:-latest}"
IMAGE="${REGISTRY}/tekton-dag-orchestrator:${TAG}"

echo "=== Building orchestrator image ==="
echo "  Context: ${REPO_ROOT}/orchestrator"
echo "  Image:   ${IMAGE}"
echo ""

docker build -t "$IMAGE" "${REPO_ROOT}/orchestrator"

echo ""
echo "=== Pushing to registry ==="
docker push "$IMAGE"

echo ""
echo "=== Verifying ==="
curl -s "http://${REGISTRY}/v2/tekton-dag-orchestrator/tags/list" || echo "(registry verify skipped)"
echo ""
echo "Done. Pods can pull as localhost:5000/tekton-dag-orchestrator:${TAG}"

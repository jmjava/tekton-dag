#!/usr/bin/env bash
# Build and push the tekton-dag-operator image to the Kind local registry.
#
# Usage:
#   ./scripts/publish-operator-image.sh              # $IMAGE_REGISTRY (localhost:5000), tag latest
#   ./scripts/publish-operator-image.sh myreg:5000   # override registry
#   ./scripts/publish-operator-image.sh myreg:5000 v2 # registry and tag
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

REGISTRY="${1:-$IMAGE_REGISTRY}"
TAG="${2:-latest}"
IMAGE="${REGISTRY}/tekton-dag-operator:${TAG}"

echo "=== Building operator image ==="
echo "  Context: ${REPO_ROOT}/operator"
echo "  Image:   ${IMAGE}"
echo ""

docker build -t "$IMAGE" "${REPO_ROOT}/operator"

echo ""
echo "=== Pushing to registry ==="
docker push "$IMAGE"

echo ""
echo "=== Verifying ==="
curl -s "http://${REGISTRY}/v2/tekton-dag-operator/tags/list" || echo "(registry verify skipped)"
echo ""
echo "Done. Pods can pull as ${IMAGE}"

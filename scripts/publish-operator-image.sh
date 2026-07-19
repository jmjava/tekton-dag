#!/usr/bin/env bash
# Build and push the tekton-dag-operator image to the Kind local registry.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

IMAGE_REGISTRY="${IMAGE_REGISTRY:-localhost:5000}"
IMAGE="${IMAGE_REGISTRY}/tekton-dag-operator:latest"
TAG="${1:-}"

cd "$REPO_ROOT/operator"
echo "Building operator image ${IMAGE}..."
docker build -t "$IMAGE" .
if [[ -n "$TAG" ]]; then
  docker tag "$IMAGE" "${IMAGE_REGISTRY}/tekton-dag-operator:${TAG}"
fi
echo "Pushing ${IMAGE}..."
docker push "$IMAGE"
echo "OK: ${IMAGE}"

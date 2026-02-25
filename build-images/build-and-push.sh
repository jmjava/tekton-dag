#!/usr/bin/env bash
# Build and push all five tekton-dag build images to a registry.
# Usage: ./build-and-push.sh [REGISTRY] [TAG]
#   REGISTRY defaults to localhost:5000 (Kind), TAG defaults to latest.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${1:-localhost:5000}"
TAG="${2:-latest}"
IMAGE_BASE="tekton-dag-build"

TOOLS=(node maven gradle python php)

for tool in "${TOOLS[@]}"; do
  dockerfile="Dockerfile.$tool"
  image="${REGISTRY}/${IMAGE_BASE}-${tool}:${TAG}"
  echo "Building $image from $dockerfile..."
  docker build -t "$image" -f "$SCRIPT_DIR/$dockerfile" "$SCRIPT_DIR"
  echo "Pushing $image..."
  docker push "$image"
  echo "  -> $image"
done

echo ""
echo "All build images pushed. Use these refs for compile-image-* params:"
for tool in "${TOOLS[@]}"; do
  echo "  compile-image-${tool}: ${REGISTRY}/${IMAGE_BASE}-${tool}:${TAG}"
done

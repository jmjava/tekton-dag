#!/usr/bin/env bash
# Build and push tekton-dag build images to the same registry used by the pipelines.
# Replicate this whenever you need to publish the build images (e.g. after changing Dockerfiles,
# or on a new host/CI). Uses IMAGE_REGISTRY from .env or defaults to localhost:5001 (Kind test env).
#
# Prerequisites:
#   - Docker
#   - Registry reachable at REGISTRY (start with: docker run -d -p 5000:5000 --name registry registry:2)
#
# Usage:
#   ./scripts/publish-build-images.sh              # use .env IMAGE_REGISTRY or localhost:5001, tag latest
#   ./scripts/publish-build-images.sh myreg:5000  # override registry
#   ./scripts/publish-build-images.sh myreg:5000 v1 # registry and tag
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REGISTRY="${1:-}"
TAG="${2:-latest}"

# Default: Kind test env — registry on kind network (host port 5001). Override with .env IMAGE_REGISTRY or first arg.
if [[ -z "$REGISTRY" ]]; then
  set -a
  source "$REPO_ROOT/.env" 2>/dev/null || true
  set +a
  REGISTRY="${IMAGE_REGISTRY:-localhost:5001}"
fi

echo "Publishing build images to registry: $REGISTRY (tag: $TAG)"
echo ""

# Optional: warn if registry is not reachable
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://${REGISTRY}/v2/_catalog" 2>/dev/null | grep -q 200; then
  echo "Registry reachable."
else
  echo "WARN: Registry at $REGISTRY may not be reachable (curl failed). Continuing anyway."
fi
echo ""

"$REPO_ROOT/build-images/build-and-push.sh" "$REGISTRY" "$TAG"

echo ""
echo "Done. Pipelines use these when BUILD_IMAGES is true and IMAGE_REGISTRY is set."

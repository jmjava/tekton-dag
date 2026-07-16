#!/usr/bin/env bash
# Build and push the management-gui backend Docker image.
#
# Usage:
#   ./scripts/publish-management-gui-image.sh              # defaults: localhost:5001, tag latest
#   ./scripts/publish-management-gui-image.sh myreg:5000   # override registry
#   ./scripts/publish-management-gui-image.sh myreg:5000 v2
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REGISTRY="${1:-$IMAGE_REGISTRY}"
TAG="${2:-latest}"
IMAGE="${REGISTRY}/tekton-dag-management-gui:${TAG}"
CTX="${REPO_ROOT}/management-gui/backend"

echo "=== Building management-gui backend image ==="
echo "  Context: ${CTX}"
echo "  Image:   ${IMAGE}"
echo ""

STAGE_DIR="${CTX}/tekton_dag_common_pkg"
rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}"
cp -a "${REPO_ROOT}/libs/tekton-dag-common/." "${STAGE_DIR}/"
cleanup_stage() { rm -rf "${STAGE_DIR}"; mkdir -p "${STAGE_DIR}"; touch "${STAGE_DIR}/.gitkeep"; }
trap cleanup_stage EXIT

docker build -t "$IMAGE" "${CTX}"

echo ""
echo "=== Pushing to registry ==="
docker push "$IMAGE"

echo ""
echo "Done. Image: ${IMAGE}"

#!/usr/bin/env bash
# Build and push the tekton-dag-orchestrator Docker image to the Kind registry.
#
# Usage:
#   ./scripts/publish-orchestrator-image.sh              # defaults: $IMAGE_REGISTRY (localhost:5000), tag latest
#   ./scripts/publish-orchestrator-image.sh myreg:5000   # override registry
#   ./scripts/publish-orchestrator-image.sh myreg:5000 v2 # registry and tag
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REGISTRY="${1:-$IMAGE_REGISTRY}"
TAG="${2:-latest}"
IMAGE="${REGISTRY}/tekton-dag-orchestrator:${TAG}"

echo "=== Building orchestrator image ==="
echo "  Context: ${REPO_ROOT}/orchestrator"
echo "  Image:   ${IMAGE}"
echo ""

STAGE_DIR="${REPO_ROOT}/orchestrator/tekton_dag_common_pkg"
rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}"
cp -a "${REPO_ROOT}/libs/tekton-dag-common/." "${STAGE_DIR}/"
cleanup_stage() { rm -rf "${STAGE_DIR}"; mkdir -p "${STAGE_DIR}"; touch "${STAGE_DIR}/.gitkeep"; }
trap cleanup_stage EXIT

docker build -t "$IMAGE" "${REPO_ROOT}/orchestrator"

echo ""
echo "=== Pushing to registry ==="
docker push "$IMAGE"

echo ""
echo "=== Verifying ==="
curl -s "http://${REGISTRY}/v2/tekton-dag-orchestrator/tags/list" || echo "(registry verify skipped)"
echo ""
echo "Done. Pods can pull as localhost:5000/tekton-dag-orchestrator:${TAG}"

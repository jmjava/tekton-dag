#!/usr/bin/env bash
# M14 Kind smoke: build/push operator image and apply a sample StackRun.
# Requires: kind cluster with local registry (localhost:5000), kubectl, docker.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MODE="${1:-pr}" # pr | platform-upgrade
IMAGE_REGISTRY="${IMAGE_REGISTRY:-localhost:5000}"

echo "==> Publish operator image to ${IMAGE_REGISTRY}"
"$SCRIPT_DIR/publish-operator-image.sh"

echo "==> Apply CRDs"
kubectl apply -f "$REPO_ROOT/operator/config/crd/bases/"

NS="${TEKTON_NAMESPACE:-tekton-pipelines}"
kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create ns "$NS"

case "$MODE" in
  pr)
    SAMPLE="$REPO_ROOT/operator/config/samples/tektondag_v1alpha1_stackrun.yaml"
    ;;
  platform-upgrade)
    SAMPLE="$REPO_ROOT/operator/config/samples/tektondag_v1alpha1_stackrun_platform_upgrade.yaml"
    ;;
  *)
    echo "usage: $0 [pr|platform-upgrade]" >&2
    exit 2
    ;;
esac

echo "==> Apply sample StackRun ($MODE)"
kubectl apply -f "$SAMPLE"

echo "==> Wait briefly for PipelineRun status sync (operator must be deployed)"
sleep 3
kubectl get stackruns -n "$NS" -o wide || true
kubectl get pipelineruns -n "$NS" -l tektondag.io/mode=platform-upgrade -o wide 2>/dev/null || \
  kubectl get pipelineruns -n "$NS" --sort-by=.metadata.creationTimestamp | tail -5

echo "OK: smoke apply complete. Confirm operator Deployment is running and PipelineRun appears."

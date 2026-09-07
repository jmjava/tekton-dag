#!/usr/bin/env bash
# Install Stack/StackRun CRDs and the tekton-dag-operator on a Kind cluster
# that already has Tekton + the local registry (kind-with-registry.sh).
#
# Usage:
#   ./scripts/install-operator-kind.sh
#   ./scripts/install-operator-kind.sh --with-sample-run
#
# Env:
#   IMAGE_REGISTRY / CLUSTER_CI_REGISTRY  (default localhost:5000)
#   KIND_CLUSTER_NAME                     (default tekton-stack)
#   NAMESPACE                             (default tekton-pipelines)
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

WITH_SAMPLE_RUN=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-sample-run) WITH_SAMPLE_RUN=true; shift ;;
    --help|-h)
      sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown option: $1 (try --help)" >&2; exit 1 ;;
  esac
done

need docker
need kubectl
KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-tekton-stack}"
export IMAGE_REGISTRY="${CLUSTER_CI_REGISTRY:-${IMAGE_REGISTRY:-localhost:5000}}"
IMAGE="${IMAGE_REGISTRY}/tekton-dag-operator:latest"

echo ">>> CRDs (tektondag.io Stack / StackRun)"
kubectl apply -f "$REPO_ROOT/operator/config/crd/bases/"
kubectl wait --for=condition=Established crd/stacks.tektondag.io --timeout=60s
kubectl wait --for=condition=Established crd/stackruns.tektondag.io --timeout=60s

echo ">>> Build/push operator image ($IMAGE)"
bash "$SCRIPT_DIR/publish-operator-image.sh" "$IMAGE_REGISTRY" latest
if command -v kind >/dev/null 2>&1 && kind get clusters 2>/dev/null | grep -qx "$KIND_CLUSTER_NAME"; then
  kind load docker-image "$IMAGE" --name "$KIND_CLUSTER_NAME" \
    || warn "kind load skipped (image still pulled from registry)"
fi

echo ">>> Deploy operator"
kubectl apply -f "$REPO_ROOT/operator/config/kind/install.yaml"
if [[ "$IMAGE" != "localhost:5000/tekton-dag-operator:latest" ]]; then
  kubectl set image deployment/tekton-dag-operator manager="$IMAGE" -n "$NAMESPACE"
fi
kubectl rollout status deployment/tekton-dag-operator -n "$NAMESPACE" --timeout=180s
kubectl wait --for=condition=Ready pod -l app=tekton-dag-operator -n "$NAMESPACE" --timeout=120s

echo ">>> Sample Stack CR (stack-one)"
kubectl apply -f "$REPO_ROOT/operator/config/samples/tektondag_v1alpha1_stack.yaml"

if [[ "$WITH_SAMPLE_RUN" == "true" ]]; then
  echo ">>> Sample StackRun (bootstrap)"
  kubectl apply -f "$REPO_ROOT/operator/config/samples/tektondag_v1alpha1_stackrun.yaml"
  echo "  Waiting for operator to create a PipelineRun from the sample StackRun..."
  ELAPSED=0
  TIMEOUT="${STACKRUN_RECONCILE_TIMEOUT:-90}"
  while [[ "$ELAPSED" -lt "$TIMEOUT" ]]; do
    PR_NAME="$(kubectl get stackrun stackrun-bootstrap-sample -n "$NAMESPACE" \
      -o jsonpath='{.status.pipelineRunName}' 2>/dev/null || true)"
    if [[ -n "$PR_NAME" ]]; then
      echo "  StackRun stackrun-bootstrap-sample -> PipelineRun $PR_NAME"
      kubectl get pipelinerun "$PR_NAME" -n "$NAMESPACE"
      echo "OK: operator Kind install + sample StackRun reconciled"
      exit 0
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
  done
  echo "ERROR: sample StackRun was not reconciled within ${TIMEOUT}s" >&2
  kubectl get stackrun,pipelinerun -n "$NAMESPACE" || true
  kubectl logs -n "$NAMESPACE" -l app=tekton-dag-operator --tail=80 || true
  exit 1
fi

echo "OK: operator Kind install (CRDs + Deployment Ready)"

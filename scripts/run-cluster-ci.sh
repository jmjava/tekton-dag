#!/usr/bin/env bash
# Kind-backed cluster CI for S33: isolation-eval measurements, stack-dag-verify
# (Phase 2), and Newman against a live orchestrator. Playwright is a separate
# GitHub Actions job (no cluster).
#
# Not for pull requests. Intended for:
#   - GitHub Actions workflow_dispatch / nightly / version tags
#   - a laptop that already has Docker + Kind
#
# Usage:
#   ./scripts/run-cluster-ci.sh
#   ./scripts/run-cluster-ci.sh --skip-newman
#   ./scripts/run-cluster-ci.sh --with-operator
#   ./scripts/run-cluster-ci.sh --skip-operator
#   ./scripts/run-cluster-ci.sh --isolation-repeats 3
#   ./scripts/run-cluster-ci.sh --help
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"

SKIP_ISOLATION=false
SKIP_PHASE2=false
SKIP_NEWMAN=false
WITH_GRAPH=false
WITH_OPERATOR="${CLUSTER_CI_WITH_OPERATOR:-true}"
if [[ "$WITH_OPERATOR" == "0" || "$WITH_OPERATOR" == "false" || "$WITH_OPERATOR" == "no" ]]; then
  WITH_OPERATOR=false
else
  WITH_OPERATOR=true
fi
ISOLATION_REPEATS="${ISOLATION_EVAL_REPEATS:-1}"
HELP=false
KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-tekton-stack}"
# Kind registry host port (kind-with-registry.sh REG_PORT, default 5000).
# Override with CLUSTER_CI_REGISTRY; do not inherit a stale IMAGE_REGISTRY=5001.
export IMAGE_REGISTRY="${CLUSTER_CI_REGISTRY:-localhost:5000}"
GIT_REV="${CLUSTER_CI_GIT_REVISION:-${GITHUB_SHA:-$(git rev-parse HEAD)}}"
GIT_URL_CI="${CLUSTER_CI_GIT_URL:-${GIT_URL:-https://github.com/jmjava/tekton-dag.git}}"
PHASE2_TIMEOUT="${DAG_VERIFY_TIMEOUT:-420}"
ISOLATION_OUT="${ISOLATION_EVAL_OUT:-$REPO_ROOT/docs/research/seip/data/isolation-eval-measured-ci.csv}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-isolation) SKIP_ISOLATION=true; shift ;;
    --skip-phase2)    SKIP_PHASE2=true; shift ;;
    --skip-newman)    SKIP_NEWMAN=true; shift ;;
    --with-graph)     WITH_GRAPH=true; shift ;;
    --with-operator)  WITH_OPERATOR=true; shift ;;
    --skip-operator)  WITH_OPERATOR=false; shift ;;
    --isolation-repeats) ISOLATION_REPEATS="$2"; shift 2 ;;
    --out)            ISOLATION_OUT="$2"; shift 2 ;;
    --help|-h)        HELP=true; shift ;;
    *) echo "Unknown option: $1 (try --help)" >&2; exit 1 ;;
  esac
done

if [[ "$HELP" == "true" ]]; then
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

need docker
need kind
need kubectl
need jq
need python3
ensure_mikefarah_yq
need yq

if [[ -x "$REPO_ROOT/.venv/bin/python3" ]]; then
  export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi

echo "=============================================="
echo "  tekton-dag cluster CI (Kind)"
echo "  cluster=$KIND_CLUSTER_NAME git-rev=${GIT_REV:0:12} registry=$IMAGE_REGISTRY operator=$WITH_OPERATOR"
echo "=============================================="

echo ""
echo ">>> Kind cluster + local registry"
KIND_CLUSTER_NAME="$KIND_CLUSTER_NAME" bash "$SCRIPT_DIR/kind-with-registry.sh"
kubectl cluster-info >/dev/null
bash "$SCRIPT_DIR/install-kind-default-storage.sh"

if [[ "$SKIP_ISOLATION" != "true" ]]; then
  echo ""
  echo ">>> isolation-eval --cluster (dummy stacks; not Tekton)"
  bash "$SCRIPT_DIR/run-isolation-eval.sh" --cluster --repeats "$ISOLATION_REPEATS" --out "$ISOLATION_OUT"
fi

echo ""
echo ">>> Tekton Pipelines + stack tasks/pipelines"
bash "$SCRIPT_DIR/install-tekton.sh"
echo "  Waiting for Tekton control plane..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/part-of=tekton-pipelines \
  -n "$NAMESPACE" --timeout=180s
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/part-of=tekton-triggers \
  -n "$NAMESPACE" --timeout=180s || warn "Tekton Triggers pods not Ready yet (continuing)"

echo ""
echo ">>> Namespace bootstrap (SA + RBAC)"
bash "$SCRIPT_DIR/bootstrap-namespace.sh" "$NAMESPACE"

if [[ "$WITH_OPERATOR" == "true" ]]; then
  echo ""
  echo ">>> M14 operator (CRDs + image + Deployment)"
  sample_args=()
  if [[ "$SKIP_NEWMAN" == "true" ]]; then
    sample_args+=(--with-sample-run)
  fi
  bash "$SCRIPT_DIR/install-operator-kind.sh" "${sample_args[@]}"
fi

if [[ "$SKIP_PHASE2" != "true" ]]; then
  echo ""
  echo ">>> Phase 2: stack-dag-verify PipelineRun (git-revision=$GIT_REV)"
  bash "$SCRIPT_DIR/verify-dag-phase2.sh" \
    --timeout "$PHASE2_TIMEOUT" \
    --stack stack-one.yaml \
    --git-url "$GIT_URL_CI" \
    --git-revision "$GIT_REV"
fi

if [[ "$SKIP_NEWMAN" != "true" ]]; then
  need newman
  echo ""
  echo ">>> Stacks ConfigMap for orchestrator"
  _cm=$(mktemp -d)
  cp "$REPO_ROOT"/stacks/*.yaml "$_cm/"
  kubectl create configmap tekton-dag-stacks \
    -n "$NAMESPACE" \
    --from-file="$_cm" \
    --dry-run=client -o yaml | kubectl apply -f -
  rm -rf "$_cm"

  echo ""
  echo ">>> Build/push orchestrator image ($IMAGE_REGISTRY)"
  bash "$SCRIPT_DIR/publish-orchestrator-image.sh" "$IMAGE_REGISTRY" latest
  if kind get clusters 2>/dev/null | grep -qx "$KIND_CLUSTER_NAME"; then
    kind load docker-image "${IMAGE_REGISTRY}/tekton-dag-orchestrator:latest" \
      --name "$KIND_CLUSTER_NAME" || warn "kind load skipped (image still pulled from registry)"
  fi

  echo ""
  echo ">>> Deploy orchestrator"
  kubectl apply -f "$REPO_ROOT/orchestrator/k8s-deployment.yaml"
  kubectl patch deployment tekton-dag-orchestrator -n "$NAMESPACE" --type=strategic \
    -p '{"spec":{"template":{"spec":{"containers":[{"name":"orchestrator","imagePullPolicy":"IfNotPresent"}]}}}}'
  if [[ "$WITH_OPERATOR" != "true" ]]; then
    kubectl set env deployment/tekton-dag-orchestrator -n "$NAMESPACE" STACKRUN_VIA_CRD=false
  fi
  kubectl rollout status deployment/tekton-dag-orchestrator -n "$NAMESPACE" --timeout=180s

  newman_args=(--skip-integration)
  if [[ "$WITH_GRAPH" == "true" ]]; then
    echo ""
    echo ">>> Neo4j (graph Newman collection)"
    bash "$SCRIPT_DIR/install-neo4j-kind.sh"
    kubectl wait --for=condition=Ready pod -l app=graph-db -n "$NAMESPACE" --timeout=300s \
      || die "Neo4j not Ready (--with-graph)"
    newman_args+=(--all)
  fi

  echo ""
  echo ">>> Newman vs in-cluster orchestrator"
  if [[ "$WITH_OPERATOR" == "true" ]]; then
    export WAIT_STACKRUN_RECONCILE=1
  fi
  bash "$SCRIPT_DIR/run-orchestrator-tests.sh" "${newman_args[@]}"
fi

echo ""
echo "=============================================="
echo "  cluster CI finished OK"
echo "=============================================="

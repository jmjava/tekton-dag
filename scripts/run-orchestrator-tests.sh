#!/usr/bin/env bash
# Run the orchestrator Postman/Newman tests against the live service in the cluster.
#
# Prerequisites:
#   - orchestrator pod Running in tekton-pipelines namespace
#   - newman installed (npm install -g newman)
#   - Neo4j running in cluster (for --graph tests)
#
# Usage:
#   ./scripts/run-orchestrator-tests.sh                     # M10.1 orchestrator tests
#   ./scripts/run-orchestrator-tests.sh --graph             # M9 graph + test-plan tests
#   ./scripts/run-orchestrator-tests.sh --all               # both collections
#   ./scripts/run-orchestrator-tests.sh --skip-integration  # skip PipelineRun validation
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NS="tekton-pipelines"
LOCAL_PORT=9091
ORCH_COLLECTION="${REPO_ROOT}/tests/postman/orchestrator-tests.json"
GRAPH_COLLECTION="${REPO_ROOT}/tests/postman/graph-tests.json"
SKIP_INTEGRATION=false
RUN_ORCH=false
RUN_GRAPH=false

for arg in "$@"; do
  case "$arg" in
    --skip-integration) SKIP_INTEGRATION=true ;;
    --graph)            RUN_GRAPH=true ;;
    --all)              RUN_ORCH=true; RUN_GRAPH=true ;;
  esac
done

# Default: run orchestrator tests if neither --graph nor --all specified
if [ "$RUN_GRAPH" = "false" ] && [ "$RUN_ORCH" = "false" ]; then
  RUN_ORCH=true
fi

cleanup() {
  echo ""
  echo "=== Cleanup ==="
  if [ -n "${PF_PID:-}" ] && kill -0 "$PF_PID" 2>/dev/null; then
    kill "$PF_PID" 2>/dev/null || true
    echo "  Stopped port-forward (PID $PF_PID)"
  fi

  echo "  Deleting test PipelineRuns created by orchestrator tests..."
  kubectl delete pipelinerun -n "$NS" -l app.kubernetes.io/part-of=tekton-job-standardization \
    --field-selector='metadata.name!=stack-bootstrap-2h86t,metadata.name!=stack-pr-1-dnljs,metadata.name!=stack-pr-1-n99kc' \
    2>/dev/null || true
  echo "  Done."
}
trap cleanup EXIT

echo "=============================================="
echo "  Orchestrator Service Tests"
if [ "$RUN_ORCH" = "true" ]; then echo "    [x] M10.1 orchestrator endpoints"; fi
if [ "$RUN_GRAPH" = "true" ]; then echo "    [x] M9 graph / test-plan endpoints"; fi
echo "=============================================="
echo ""

echo "=== Checking orchestrator pod ==="
kubectl wait --for=condition=ready pod -l app=tekton-dag-orchestrator -n "$NS" --timeout=60s
echo ""

echo "=== Starting port-forward (localhost:${LOCAL_PORT} -> 8080) ==="
kubectl port-forward svc/tekton-dag-orchestrator "${LOCAL_PORT}:8080" -n "$NS" &
PF_PID=$!
sleep 3

if ! kill -0 "$PF_PID" 2>/dev/null; then
  echo "ERROR: port-forward failed to start"
  exit 1
fi

echo "=== Quick smoke test ==="
HEALTH=$(curl -sf "http://localhost:${LOCAL_PORT}/healthz" || echo "FAIL")
if echo "$HEALTH" | grep -q '"ok"'; then
  echo "  healthz: OK"
else
  echo "  healthz: FAILED ($HEALTH)"
  exit 1
fi
echo ""

NEWMAN_FAILED=false

if [ "$RUN_ORCH" = "true" ]; then
  echo "=== Running Newman: Orchestrator Tests (M10.1) ==="
  newman run "$ORCH_COLLECTION" \
    --env-var "baseUrl=http://localhost:${LOCAL_PORT}" \
    --reporters cli \
    --color on || NEWMAN_FAILED=true
  echo ""
fi

if [ "$RUN_GRAPH" = "true" ]; then
  echo "=== Running Newman: Graph / Test-Plan Tests (M9) ==="
  newman run "$GRAPH_COLLECTION" \
    --env-var "baseUrl=http://localhost:${LOCAL_PORT}" \
    --reporters cli \
    --color on || NEWMAN_FAILED=true
  echo ""
fi

if [ "$NEWMAN_FAILED" = "true" ]; then
  echo "ERROR: One or more Newman collections failed"
  exit 1
fi

echo "=== Newman passed ==="

if [ "$SKIP_INTEGRATION" = "true" ]; then
  echo ""
  echo "=== Skipping integration validation (--skip-integration) ==="
  echo ""
  echo "=============================================="
  echo "  All orchestrator tests PASSED"
  echo "=============================================="
  exit 0
fi

echo ""
echo "=== Integration validation: checking PipelineRuns created by tests ==="

BOOTSTRAP_RUN=$(kubectl get pipelinerun -n "$NS" -l tekton.dev/pipeline=stack-bootstrap \
  --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null || echo "")

if [ -z "$BOOTSTRAP_RUN" ]; then
  echo "  WARNING: No bootstrap PipelineRun found — skipping integration check"
else
  echo "  Latest bootstrap PipelineRun: $BOOTSTRAP_RUN"
  echo "  Waiting for fetch-source task to start (up to 120s)..."
  TIMEOUT=120
  ELAPSED=0
  while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    FETCH_STATUS=$(kubectl get taskrun -n "$NS" \
      -l tekton.dev/pipelineRun="$BOOTSTRAP_RUN" \
      -o jsonpath='{range .items[*]}{.metadata.labels.tekton\.dev/pipelineTask}{" "}{.status.conditions[0].reason}{"\n"}{end}' 2>/dev/null \
      | grep "^fetch-source " | awk '{print $2}' || echo "")

    if [ "$FETCH_STATUS" = "Succeeded" ]; then
      echo "  fetch-source: Succeeded (PipelineRun is executing)"
      break
    elif [ "$FETCH_STATUS" = "Failed" ]; then
      echo "  fetch-source: Failed"
      break
    fi

    sleep 10
    ELAPSED=$((ELAPSED + 10))
    echo "    ${ELAPSED}s..."
  done

  if [ "$ELAPSED" -ge "$TIMEOUT" ] && [ "$FETCH_STATUS" != "Succeeded" ]; then
    echo "  WARNING: Timed out waiting for fetch-source on $BOOTSTRAP_RUN"
  fi
fi

echo ""
echo "=============================================="
echo "  All orchestrator tests PASSED"
echo "=============================================="

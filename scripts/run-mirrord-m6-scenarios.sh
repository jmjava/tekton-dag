#!/usr/bin/env bash
# Milestone 6: Run mirrord test scenarios (3–5).
# Constraint: 1 intercept per app at a time. Concurrent PRs target different services.
# All test traffic originates from INSIDE the cluster (ephemeral curl pod).
#
# Requires: cluster with stack in staging, mirrord CLI on host.
# Usage: ./scripts/run-mirrord-m6-scenarios.sh [3|4|5|all]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POC="${REPO_ROOT}/docs/mirrord-poc"
CONFIG_PR1_BFF="${POC}/mirrord-pr-1-bff.json"
CONFIG_PR2_API="${POC}/mirrord-pr-2-api.json"
AGENT_WAIT=35
NAMESPACE="${NAMESPACE:-staging}"
BFF_SVC="http://release-lifecycle-demo.${NAMESPACE}.svc.cluster.local"
API_SVC="http://demo-api.${NAMESPACE}.svc.cluster.local"
CURL_POD="m6-curl-runner"

export PATH="${REPO_ROOT}:${PATH}"
MIRRORD_BIN=""
if [[ -x "${REPO_ROOT}/mirrord" ]]; then
  MIRRORD_BIN="${REPO_ROOT}/mirrord"
elif command -v mirrord &>/dev/null; then
  MIRRORD_BIN="mirrord"
else
  echo "mirrord not found. Run ./scripts/install-mirrord.sh"; exit 1
fi

# ---------------------------------------------------------------------------
# Ephemeral in-cluster curl pod
# ---------------------------------------------------------------------------
ensure_curl_pod() {
  if kubectl get pod "$CURL_POD" -n "$NAMESPACE" &>/dev/null; then return; fi
  echo "  Starting in-cluster curl pod ($CURL_POD)..."
  kubectl run "$CURL_POD" -n "$NAMESPACE" \
    --image=curlimages/curl:8.5.0 \
    --restart=Never \
    --command -- sleep 3600
  kubectl wait --for=condition=Ready pod/"$CURL_POD" -n "$NAMESPACE" --timeout=60s
}
cleanup_curl_pod() {
  kubectl delete pod "$CURL_POD" -n "$NAMESPACE" --grace-period=0 --force 2>/dev/null || true
}

in_cluster_curl() {
  local url="$1"; shift
  kubectl exec "$CURL_POD" -n "$NAMESPACE" -- curl -sS --max-time 10 "$@" "$url" 2>/dev/null
}

# ---------------------------------------------------------------------------
# mirrord session management
# ---------------------------------------------------------------------------
MIRRORD_PIDS=()
start_session() {
  local config=$1 port=$2 body=$3
  MIRRORD_M6_RESPONSE="$body" PORT="$port" "$MIRRORD_BIN" exec -f "$config" -- python3 "${POC}/local_server.py" &>/dev/null &
  MIRRORD_PIDS+=($!)
  echo $!
}
wait_agents() { echo "  Waiting ${AGENT_WAIT}s for mirrord agents..."; sleep "$AGENT_WAIT"; }
kill_pids() { for p in "$@"; do kill "$p" 2>/dev/null || true; done; wait "$@" 2>/dev/null || true; }
cleanup_sessions() {
  kill_pids "${MIRRORD_PIDS[@]}"
  MIRRORD_PIDS=()
  kubectl delete pods -n "$NAMESPACE" -l app=mirrord --force --grace-period=0 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------
assert_request() {
  local desc="$1" url="$2" header="$3" expect="$4"
  local resp
  if [[ -z "$header" ]]; then
    resp=$(in_cluster_curl "$url")
  else
    resp=$(in_cluster_curl "$url" -H "x-dev-session: $header")
  fi
  if [[ "$resp" != *"$expect"* ]]; then
    echo "  FAIL $desc: expected '$expect', got: $resp"
    return 1
  fi
  echo "  OK $desc"
  return 0
}

# ===========================================================================
# Scenario 3: Two concurrent intercepts on DIFFERENT services
# ===========================================================================
run_scenario_3() {
  echo "=== Scenario 3: Two concurrent intercepts (BFF + API, different services) ==="
  kubectl get deployment release-lifecycle-demo -n "$NAMESPACE" &>/dev/null || { echo "BFF not found"; return 1; }
  kubectl get deployment demo-api -n "$NAMESPACE" &>/dev/null || { echo "demo-api not found"; return 1; }
  local bff_pid api_pid err=0
  bff_pid=$(start_session "$CONFIG_PR1_BFF" 8080 "LOCAL-PR-1-BFF")
  api_pid=$(start_session "$CONFIG_PR2_API" 8080 "LOCAL-PR-2-API")
  wait_agents
  assert_request "BFF no header -> original"           "$BFF_SVC/" "" "tekton-dag-spring-boot"        || err=1
  assert_request "BFF x-dev-session: pr-1 -> local"    "$BFF_SVC/" "pr-1" "LOCAL-PR-1-BFF"            || err=1
  assert_request "API no header -> original"           "$API_SVC/" "" "tekton-dag-spring-boot-gradle" || err=1
  assert_request "API x-dev-session: pr-2 -> local"    "$API_SVC/" "pr-2" "LOCAL-PR-2-API"            || err=1
  cleanup_sessions
  return $err
}

# ===========================================================================
# Scenario 4: Normal traffic burst during single intercept
# ===========================================================================
run_scenario_4() {
  echo "=== Scenario 4: Normal traffic during intercept (20-request burst, no header) ==="
  kubectl get deployment release-lifecycle-demo -n "$NAMESPACE" &>/dev/null || { echo "Deployment not found"; return 1; }
  local pr1_pid err=0 fail=0
  pr1_pid=$(start_session "$CONFIG_PR1_BFF" 8080 "LOCAL-PR-1")
  wait_agents
  for i in $(seq 1 20); do
    resp=$(in_cluster_curl "$BFF_SVC/")
    if [[ "$resp" != *"tekton-dag-spring-boot"* ]]; then fail=$((fail+1)); fi
  done
  if [[ $fail -gt 0 ]]; then
    echo "  FAIL: $fail/20 no-header requests did not get original"
    err=1
  else
    echo "  OK 20/20 no-header requests -> original"
  fi
  cleanup_sessions
  return $err
}

# ===========================================================================
# Scenario 5: Combined — 2 intercepts (different services) + normal traffic
# ===========================================================================
run_scenario_5() {
  echo "=== Scenario 5: Combined (2 intercepts on different services + normal traffic) ==="
  kubectl get deployment release-lifecycle-demo -n "$NAMESPACE" &>/dev/null || { echo "BFF not found"; return 1; }
  kubectl get deployment demo-api -n "$NAMESPACE" &>/dev/null || { echo "demo-api not found"; return 1; }
  local bff_pid api_pid err=0
  bff_pid=$(start_session "$CONFIG_PR1_BFF" 8080 "LOCAL-PR-1-BFF")
  api_pid=$(start_session "$CONFIG_PR2_API" 8080 "LOCAL-PR-2-API")
  wait_agents
  for i in $(seq 1 5); do
    assert_request "round $i: BFF no header -> original"  "$BFF_SVC/" "" "tekton-dag-spring-boot"        || err=1
    assert_request "round $i: BFF pr-1 -> local"          "$BFF_SVC/" "pr-1" "LOCAL-PR-1-BFF"            || err=1
    assert_request "round $i: API no header -> original"  "$API_SVC/" "" "tekton-dag-spring-boot-gradle" || err=1
    assert_request "round $i: API pr-2 -> local"          "$API_SVC/" "pr-2" "LOCAL-PR-2-API"            || err=1
  done
  cleanup_sessions
  return $err
}

# ===========================================================================
# Main
# ===========================================================================
SCENARIO="${1:-all}"
TOTAL=0
FAILED=0
if [[ "$SCENARIO" != "3" && "$SCENARIO" != "4" && "$SCENARIO" != "5" && "$SCENARIO" != "all" ]]; then
  echo "Usage: $0 [3|4|5|all]"; exit 1
fi

trap 'cleanup_curl_pod; cleanup_sessions' EXIT
ensure_curl_pod

if [[ "$SCENARIO" == "3" || "$SCENARIO" == "all" ]]; then run_scenario_3 || FAILED=$((FAILED+1)); TOTAL=$((TOTAL+1)); fi
if [[ "$SCENARIO" == "4" || "$SCENARIO" == "all" ]]; then run_scenario_4 || FAILED=$((FAILED+1)); TOTAL=$((TOTAL+1)); fi
if [[ "$SCENARIO" == "5" || "$SCENARIO" == "all" ]]; then run_scenario_5 || FAILED=$((FAILED+1)); TOTAL=$((TOTAL+1)); fi

echo "=== Done: $((TOTAL - FAILED))/$TOTAL scenarios passed ==="
[[ $FAILED -eq 0 ]] || exit 1

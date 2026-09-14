#!/usr/bin/env bash
# Exercise the production trigger path:
# orchestrator -> StackRun -> operator -> PR PipelineRun -> intercept tests -> cleanup.
#
# The cluster, operator, orchestrator, Tasks/Pipelines, build images, registry,
# and SSH clone Secret must already be installed.
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

INTERCEPT_BACKEND="${INTERCEPT_BACKEND:-telepresence}"
STACK_FILE="${STACK_FILE:-stack-one.yaml}"
CHANGED_APP="${CHANGED_APP:-demo-fe}"
PR_NUMBER="${PR_NUMBER:-900001}"
API_URL="${ORCHESTRATOR_URL:-}"
ARTIFACT_DIR="${E2E_ARTIFACT_DIR:-$REPO_ROOT/artifacts/intercept-e2e}"
TIMEOUT="${INTERCEPT_E2E_TIMEOUT:-1800}"
POLL_INTERVAL="${INTERCEPT_E2E_POLL_INTERVAL:-10}"
KEEP_RESOURCES="${KEEP_E2E_RESOURCES:-false}"
PORT_FORWARD_PID=""
STACKRUNS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --intercept-backend) INTERCEPT_BACKEND="$2"; shift 2 ;;
    --stack) STACK_FILE="$2"; shift 2 ;;
    --changed-app) CHANGED_APP="$2"; shift 2 ;;
    --pr) PR_NUMBER="$2"; shift 2 ;;
    --artifact-dir) ARTIFACT_DIR="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --keep-resources) KEEP_RESOURCES=true; shift ;;
    --help|-h)
      sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) die "Unknown option: $1" ;;
  esac
done

[[ "$INTERCEPT_BACKEND" == "telepresence" || "$INTERCEPT_BACKEND" == "mirrord" ]] \
  || die "--intercept-backend must be telepresence or mirrord"
[[ "$PR_NUMBER" =~ ^[0-9]+$ ]] || die "--pr must be numeric"

need kubectl
need curl
need jq
mkdir -p "$ARTIFACT_DIR"

resolve_api_token() {
  if [[ -n "${API_MUTATION_TOKEN:-}" ]]; then
    return
  fi
  API_MUTATION_TOKEN="$(
    kubectl get secret tekton-dag-api-auth -n "$NAMESPACE" \
      -o jsonpath='{.data.token}' 2>/dev/null | base64 --decode
  )"
  [[ -n "$API_MUTATION_TOKEN" ]] \
    || die "API_MUTATION_TOKEN is unset and secret/tekton-dag-api-auth has no token"
}

start_port_forward() {
  if [[ -n "$API_URL" ]]; then
    return
  fi
  local port="${ORCHESTRATOR_E2E_PORT:-19091}"
  kubectl port-forward -n "$NAMESPACE" svc/tekton-dag-orchestrator "$port:8080" \
    >"$ARTIFACT_DIR/port-forward.log" 2>&1 &
  PORT_FORWARD_PID=$!
  API_URL="http://127.0.0.1:$port"
  for _ in $(seq 1 30); do
    if curl -fsS "$API_URL/readyz" >"$ARTIFACT_DIR/readyz.json" 2>/dev/null; then
      return
    fi
    sleep 1
  done
  die "orchestrator port-forward did not become ready"
}

collect_run_evidence() {
  local stackrun="$1" prefix="$2" pipeline_run
  kubectl get stackrun "$stackrun" -n "$NAMESPACE" -o yaml \
    >"$ARTIFACT_DIR/$prefix-stackrun.yaml" 2>&1 || true
  pipeline_run="$(kubectl get stackrun "$stackrun" -n "$NAMESPACE" \
    -o jsonpath='{.status.pipelineRunName}' 2>/dev/null || true)"
  [[ -n "$pipeline_run" ]] || return

  kubectl get pipelinerun "$pipeline_run" -n "$NAMESPACE" -o yaml \
    >"$ARTIFACT_DIR/$prefix-pipelinerun.yaml" 2>&1 || true
  kubectl get pipelinerun "$pipeline_run" -n "$NAMESPACE" -o json 2>/dev/null \
    | jq '{
        name: .metadata.name,
        condition: (.status.conditions[0] // {}),
        results: (.status.results // .status.pipelineResults // [])
      }' >"$ARTIFACT_DIR/$prefix-pipeline-results.json" || true
  kubectl get taskrun -n "$NAMESPACE" -l "tekton.dev/pipelineRun=$pipeline_run" -o yaml \
    >"$ARTIFACT_DIR/$prefix-taskruns.yaml" 2>&1 || true
  kubectl logs -n "$NAMESPACE" -l "tekton.dev/pipelineRun=$pipeline_run" \
    --all-containers=true --prefix=true \
    >"$ARTIFACT_DIR/$prefix-pod-logs.txt" 2>&1 || true
}

cleanup() {
  local exit_code=$?
  for i in "${!STACKRUNS[@]}"; do
    collect_run_evidence "${STACKRUNS[$i]}" "run-$((i + 1))"
  done
  kubectl get stackrun,pipelinerun,taskrun -n "$NAMESPACE" -o wide \
    >"$ARTIFACT_DIR/final-resources.txt" 2>&1 || true
  kubectl get pods,deployments,services -n staging -o wide \
    >"$ARTIFACT_DIR/final-staging-resources.txt" 2>&1 || true

  if [[ "$KEEP_RESOURCES" != "true" ]]; then
    for stackrun in "${STACKRUNS[@]}"; do
      pipeline_run="$(kubectl get stackrun "$stackrun" -n "$NAMESPACE" \
        -o jsonpath='{.status.pipelineRunName}' 2>/dev/null || true)"
      [[ -z "$pipeline_run" ]] || kubectl delete pipelinerun "$pipeline_run" \
        -n "$NAMESPACE" --ignore-not-found=true --wait=false >/dev/null 2>&1 || true
      kubectl delete stackrun "$stackrun" -n "$NAMESPACE" \
        --ignore-not-found=true --wait=false >/dev/null 2>&1 || true
    done
    kubectl delete pod -n staging -l app=mirrord --ignore-not-found=true \
      --wait=false >/dev/null 2>&1 || true
    kubectl delete pod -n staging -l app=mirrord-proxy --ignore-not-found=true \
      --wait=false >/dev/null 2>&1 || true
  fi
  [[ -z "$PORT_FORWARD_PID" ]] || kill "$PORT_FORWARD_PID" >/dev/null 2>&1 || true
  exit "$exit_code"
}
trap cleanup EXIT

trigger_run() {
  local mode="$1" payload="$2" response stackrun
  response="$(curl -fsS -X POST "$API_URL/api/run" \
    -H "Authorization: Bearer $API_MUTATION_TOKEN" \
    -H "Content-Type: application/json" \
    --data "$payload")"
  printf '%s\n' "$response" >"$ARTIFACT_DIR/trigger-$mode.json"
  stackrun="$(jq -er '.stackrun' <<<"$response")"
  STACKRUNS+=("$stackrun")
  TRIGGERED_STACKRUN="$stackrun"
}

wait_for_stackrun() {
  local stackrun="$1" label="$2" elapsed=0 phase="" pipeline_run=""
  local pipeline_status="" pipeline_reason=""
  while (( elapsed < TIMEOUT )); do
    phase="$(kubectl get stackrun "$stackrun" -n "$NAMESPACE" \
      -o jsonpath='{.status.phase}' 2>/dev/null || true)"
    pipeline_run="$(kubectl get stackrun "$stackrun" -n "$NAMESPACE" \
      -o jsonpath='{.status.pipelineRunName}' 2>/dev/null || true)"
    echo "  $label: phase=${phase:-Pending} pipelineRun=${pipeline_run:-Pending} elapsed=${elapsed}s"
    case "$phase" in
      Succeeded|Completed) return 0 ;;
      Failed|Cancelled|TimedOut)
        collect_run_evidence "$stackrun" "$label"
        die "$label StackRun $stackrun failed with phase $phase"
        ;;
    esac
    if [[ -n "$pipeline_run" ]]; then
      pipeline_status="$(kubectl get pipelinerun "$pipeline_run" -n "$NAMESPACE" \
        -o jsonpath='{.status.conditions[?(@.type=="Succeeded")].status}' 2>/dev/null || true)"
      pipeline_reason="$(kubectl get pipelinerun "$pipeline_run" -n "$NAMESPACE" \
        -o jsonpath='{.status.conditions[?(@.type=="Succeeded")].reason}' 2>/dev/null || true)"
      if [[ "$pipeline_status" == "False" ]]; then
        collect_run_evidence "$stackrun" "$label"
        die "$label PipelineRun $pipeline_run failed with reason ${pipeline_reason:-Unknown}"
      fi
    fi
    sleep "$POLL_INTERVAL"
    elapsed=$((elapsed + POLL_INTERVAL))
  done
  collect_run_evidence "$stackrun" "$label"
  die "$label StackRun $stackrun timed out after ${TIMEOUT}s"
}

verify_pr_evidence() {
  local stackrun="$1" pipeline_run run_tests
  pipeline_run="$(kubectl get stackrun "$stackrun" -n "$NAMESPACE" \
    -o jsonpath='{.status.pipelineRunName}')"
  run_tests="$(kubectl get taskrun -n "$NAMESPACE" \
    -l "tekton.dev/pipelineRun=$pipeline_run,tekton.dev/pipelineTask=run-tests" \
    -o json)"
  jq -e '.items | length > 0' <<<"$run_tests" >/dev/null \
    || die "PR PipelineRun has no run-tests TaskRun traffic evidence"
  jq -e 'all(.items[].status.conditions[0].status; . == "True")' \
    <<<"$run_tests" >/dev/null \
    || die "PR PipelineRun run-tests TaskRun did not succeed"
  kubectl logs -n "$NAMESPACE" -l \
    "tekton.dev/pipelineRun=$pipeline_run,tekton.dev/pipelineTask=run-tests" \
    --all-containers=true --prefix=true \
    >"$ARTIFACT_DIR/pr-traffic-evidence.log"
  [[ -s "$ARTIFACT_DIR/pr-traffic-evidence.log" ]] \
    || die "run-tests traffic evidence log is empty"
}

resolve_api_token
start_port_forward

echo ">>> Trigger bootstrap through authenticated orchestrator API"
bootstrap_payload="$(jq -nc --arg stack "stacks/$STACK_FILE" \
  '{mode:"bootstrap", stack_file:$stack, git_revision:"main"}')"
trigger_run bootstrap "$bootstrap_payload"
bootstrap_run="$TRIGGERED_STACKRUN"
wait_for_stackrun "$bootstrap_run" bootstrap

echo ">>> Trigger $INTERCEPT_BACKEND PR path through authenticated orchestrator API"
pr_payload="$(jq -nc \
  --arg stack "stacks/$STACK_FILE" \
  --arg app "$CHANGED_APP" \
  --arg backend "$INTERCEPT_BACKEND" \
  --argjson pr "$PR_NUMBER" \
  '{mode:"pr", stack_file:$stack, changed_app:$app, pr_number:$pr,
    git_revision:"main", intercept_backend:$backend}')"
trigger_run pr "$pr_payload"
pr_run="$TRIGGERED_STACKRUN"
wait_for_stackrun "$pr_run" pr
collect_run_evidence "$pr_run" pr
verify_pr_evidence "$pr_run"

echo "OK: trigger -> StackRun -> operator -> PR PipelineRun -> $INTERCEPT_BACKEND tests -> cleanup"

#!/usr/bin/env bash
# Verify that pipeline/task run results are stored in Tekton Results (query the API).
# Run after: Tekton Results installed, and at least one PipelineRun has completed.
#
# Usage: ./verify-results-in-db.sh [--min-count N] [--namespace NS]
#   --min-count  Require at least N results (default: 1)
#   --namespace  Parent namespace to list (default: tekton-pipelines). Use "-" for all.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
PARENT="${PARENT:-tekton-pipelines}"
MIN_COUNT=1
PORT_FWD_PID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --min-count)  MIN_COUNT="$2"; shift 2 ;;
    --namespace)  PARENT="$2"; shift 2 ;;
    *)            echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl
need jq

cleanup() {
  if [[ -n "$PORT_FWD_PID" ]]; then
    kill "$PORT_FWD_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "=============================================="
echo "  Verify Tekton Results DB (list results via API)"
echo "  Parent: $PARENT (use '-' for all namespaces)"
echo "  Min results required: $MIN_COUNT"
echo "=============================================="

# Ensure Results API is running
if ! kubectl get deployment tekton-results-api -n "$NAMESPACE" &>/dev/null; then
  echo "  FAIL: Tekton Results API not found in $NAMESPACE. Run install-tekton-results.sh first." >&2
  exit 1
fi

# Port-forward API to localhost so we can curl (avoids in-cluster cert issues)
echo "  Port-forwarding Results API to localhost:8080..."
kubectl port-forward -n "$NAMESPACE" svc/tekton-results-api-service 8080:8080 &
PORT_FWD_PID=$!
sleep 3

# Get a token (watcher SA has write; default or a readonly SA for list)
TOKEN=$(kubectl create token default -n "$NAMESPACE" 2>/dev/null || kubectl create token tekton-results-watcher -n "$NAMESPACE" 2>/dev/null || true)
if [[ -z "$TOKEN" ]]; then
  echo "  WARN: Could not create token; trying without auth (may fail)."
fi

# List results (REST: parents/-/results lists all; use -k for self-signed cert)
# https://tekton.dev/docs/results/api/ - parent "-" = across all parents
URL="https://127.0.0.1:8080/apis/results.tekton.dev/v1alpha2/parents/${PARENT}/results"
if [[ "$PARENT" == "-" ]]; then
  URL="https://127.0.0.1:8080/apis/results.tekton.dev/v1alpha2/parents/-/results"
fi

echo "  Querying: $URL"
RESPONSE=$(curl -sk -H "Authorization: Bearer ${TOKEN}" -H "Accept: application/json" "$URL" 2>/dev/null || echo '{}')

# Check for error in response
if echo "$RESPONSE" | jq -e '.error' &>/dev/null; then
  echo "  API error: $(echo "$RESPONSE" | jq -r '.error.message // .error')" >&2
  exit 1
fi

# Count results (API may return .results array or root array)
COUNT=$(echo "$RESPONSE" | jq 'if .results then (.results | length) elif .items then (.items | length) else (if type == "array" then length else 0 end) end' 2>/dev/null || echo "0")
if [[ -z "$COUNT" ]] || [[ "$COUNT" == "null" ]]; then
  COUNT=0
fi

echo "  Results in DB: $COUNT"
echo "$RESPONSE" | jq -r '(.results // .items // . // [])[]? | "    \(.name // .metadata.name // "?") - \(.summary.status // .status // "unknown")"' 2>/dev/null || true

if [[ "$COUNT" -lt "$MIN_COUNT" ]]; then
  echo "  FAIL: Expected at least $MIN_COUNT result(s), got $COUNT." >&2
  echo "  Run a pipeline (e.g. ./scripts/verify-dag-phase2.sh) then re-run this script." >&2
  exit 1
fi

echo "  OK: Results are stored in Tekton Results DB."
exit 0

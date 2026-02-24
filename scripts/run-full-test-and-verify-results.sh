#!/usr/bin/env bash
# Run the full test: DAG verify pipeline + verify that results landed in Tekton Results DB.
#
# Prerequisites (run once):
#   ./scripts/kind-with-registry.sh
#   ./scripts/install-tekton.sh
#   ./scripts/install-postgres-kind.sh   # optional StorageClass if PVC stays Pending
#   ./scripts/install-tekton-results.sh
#
# This script: runs stack-dag-verify PipelineRun, waits for completion, then queries
# the Results API to confirm at least one result was stored.
#
# Usage: ./run-full-test-and-verify-results.sh [--stack STACK] [--skip-install-check] [--no-verify-db]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

STACK_FILE="stack-one.yaml"
SKIP_INSTALL_CHECK=false
NO_VERIFY_DB=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stack)             STACK_FILE="$2"; shift 2 ;;
    --skip-install-check) SKIP_INSTALL_CHECK=true; shift ;;
    --no-verify-db)      NO_VERIFY_DB=true; shift ;;
    *)                   echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl
need jq

echo "=============================================="
echo "  Full test: DAG verify + Tekton Results verification"
echo "  Stack: $STACK_FILE"
echo "=============================================="

# Optional: quick check that cluster and Tekton Results are present
if [[ "$SKIP_INSTALL_CHECK" != "true" ]]; then
  if ! kubectl cluster-info &>/dev/null; then
    echo "  No cluster context. Run kind-with-registry.sh and install-tekton.sh first." >&2
    exit 1
  fi
  if ! kubectl get deployment tekton-results-api -n tekton-pipelines &>/dev/null; then
    echo "  Tekton Results API not found. Run install-postgres-kind.sh then install-tekton-results.sh." >&2
    exit 1
  fi
fi

# 1. Run DAG verify pipeline (clone + resolve)
echo ""
echo "  Step 1: Run stack-dag-verify pipeline..."
./scripts/verify-dag-phase2.sh --stack "$STACK_FILE" --timeout 180
echo "  Step 1: DAG verify completed."
echo ""

# 2. Give the Watcher a few seconds to write to Results
echo "  Waiting 10s for Results Watcher to persist run..."
sleep 10

# 3. Verify results in DB
if [[ "$NO_VERIFY_DB" == "true" ]]; then
  echo "  (Skipping DB verification --no-verify-db)"
  exit 0
fi

echo ""
echo "  Step 2: Verify results in Tekton Results DB..."
./scripts/verify-results-in-db.sh --min-count 1 --namespace tekton-pipelines

echo ""
echo "  Full test passed: pipeline ran and results are in the DB."
echo "=============================================="

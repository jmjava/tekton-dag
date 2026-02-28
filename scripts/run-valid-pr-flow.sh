#!/usr/bin/env bash
# Run the full valid PR flow: create PR → run PR pipeline → poll until success → merge PR.
# Merging triggers the merge pipeline via webhook (if configured), or you can run merge pipeline manually after.
#
# Prerequisites: .env with GITHUB_TOKEN; app repo cloned; cluster with Tekton, registry, git-ssh-key.
# For Kind: unset STORAGE_CLASS or set --storage-class "" so PVCs bind.
#
# Usage:
#   ./scripts/run-valid-pr-flow.sh --app demo-fe
#   ./scripts/run-valid-pr-flow.sh --app demo-fe --stack stack-one.yaml [--storage-class ""]
#
# Options:
#   --app              App name (e.g. demo-fe). Required.
#   --stack            Stack file (default: stack-one.yaml)
#   --storage-class    Passed to generate-run (default: "" for Kind; set for AWS)
#   --poll-interval    Seconds between status checks (default: 30)
#   --timeout          Max seconds to wait for PR pipeline (default: 900)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEKTON_DAG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STACKS_DIR="$TEKTON_DAG_ROOT/stacks"

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: $1 is required" >&2; exit 1; }; }
need kubectl
need yq

APP=""
STACK="stack-one.yaml"
STORAGE_CLASS=""
POLL_INTERVAL="${POLL_INTERVAL:-30}"
TIMEOUT="${TIMEOUT:-900}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)              APP="$2"; shift 2 ;;
    --stack)             STACK="$2"; shift 2 ;;
    --storage-class)     STORAGE_CLASS="$2"; shift 2 ;;
    --poll-interval)     POLL_INTERVAL="$2"; shift 2 ;;
    --timeout)           TIMEOUT="$2"; shift 2 ;;
    *)                   echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$APP" ]] || { echo "ERROR: --app is required (e.g. demo-fe)" >&2; exit 1; }
[[ -f "$STACKS_DIR/$STACK" ]] || { echo "ERROR: Stack not found: $STACKS_DIR/$STACK" >&2; exit 1; }

# Load .env for GITHUB_TOKEN
if [[ -f "$TEKTON_DAG_ROOT/.env" ]]; then
  set -a
  source "$TEKTON_DAG_ROOT/.env"
  set +a
fi

echo "=============================================="
echo "  Valid PR flow: create PR → run pipeline → poll → merge"
echo "  App: $APP  Stack: $STACK"
echo "=============================================="

# Step 1: Create PR in app repo
echo ""
echo "[1/4] Creating test PR in app repo..."
CREATE_OUT=$(cd "$TEKTON_DAG_ROOT" && set -a && source .env 2>/dev/null; set +a; unset STORAGE_CLASS; "$SCRIPT_DIR/create-test-pr.sh" --app "$APP" --stack "$STACK" 2>&1) || true
PR_NUMBER=$(echo "$CREATE_OUT" | sed -n 's/^PR_NUMBER=//p' | tr -d '\r')
BRANCH_NAME=$(echo "$CREATE_OUT" | sed -n 's/^BRANCH_NAME=//p' | tr -d '\r')
APP_FROM_OUT=$(echo "$CREATE_OUT" | sed -n 's/^APP=//p' | tr -d '\r')
[[ -n "$APP_FROM_OUT" ]] && APP="$APP_FROM_OUT"

if [[ -z "$PR_NUMBER" || "$PR_NUMBER" == " " ]]; then
  echo "WARNING: No PR number from create-test-pr (PR may not have been created). Output:"
  echo "$CREATE_OUT"
  echo "Create the PR manually on GitHub and re-run with PR number, or fix token/repo and try again."
  exit 1
fi
if [[ -z "$BRANCH_NAME" ]]; then
  echo "ERROR: Could not get BRANCH_NAME from create-test-pr output." >&2
  exit 1
fi

echo "  APP=$APP  PR_NUMBER=$PR_NUMBER  BRANCH_NAME=$BRANCH_NAME"

# Step 2: Start PR pipeline (use empty storage class for Kind so PVCs bind)
echo ""
echo "[2/4] Starting PR pipeline..."
PIPE_OUT=$(cd "$TEKTON_DAG_ROOT" && set -a && source .env 2>/dev/null; set +a; unset STORAGE_CLASS 2>/dev/null; "$SCRIPT_DIR/generate-run.sh" --mode pr --stack "$STACK" --app "$APP" --pr "$PR_NUMBER" --app-revision "$APP:$BRANCH_NAME" --storage-class "" --apply 2>&1)
RUN_NAME=$(echo "$PIPE_OUT" | grep -oE 'stack-pr-[0-9]+-[a-z0-9]+' | head -1)
if [[ -z "$RUN_NAME" ]]; then
  echo "ERROR: Could not get PipelineRun name from generate-run output." >&2
  echo "$PIPE_OUT"
  exit 1
fi
echo "  PipelineRun: $RUN_NAME"

# Step 3: Poll until Succeeded or Failed
echo ""
echo "[3/4] Polling for pipeline success (interval ${POLL_INTERVAL}s, timeout ${TIMEOUT}s)..."
ELAPSED=0
while [[ $ELAPSED -lt $TIMEOUT ]]; do
  STATUS=$(kubectl get pipelinerun "$RUN_NAME" -n tekton-pipelines -o jsonpath='{.status.conditions[0].status}' 2>/dev/null || echo "Unknown")
  REASON=$(kubectl get pipelinerun "$RUN_NAME" -n tekton-pipelines -o jsonpath='{.status.conditions[0].reason}' 2>/dev/null || echo "")
  if [[ "$STATUS" == "True" ]]; then
    echo "  Pipeline succeeded."
    break
  fi
  if [[ "$STATUS" == "False" ]]; then
    echo "  Pipeline failed: $REASON" >&2
    kubectl get pipelinerun "$RUN_NAME" -n tekton-pipelines -o yaml | tail -50 >&2
    exit 1
  fi
  echo "  $(date +%H:%M:%S)  status=$STATUS (${ELAPSED}s elapsed)"
  sleep "$POLL_INTERVAL"
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done
if [[ $ELAPSED -ge $TIMEOUT ]]; then
  echo "  Timeout waiting for pipeline." >&2
  exit 1
fi

# Step 4: Merge the PR (webhook will trigger merge pipeline if configured)
echo ""
echo "[4/4] Merging PR #$PR_NUMBER (app: $APP)..."
cd "$TEKTON_DAG_ROOT"
"$SCRIPT_DIR/merge-pr.sh" "$PR_NUMBER" --app "$APP"
echo ""
echo "Done. If the webhook is configured, the merge pipeline was triggered automatically."
echo "Otherwise run: ./scripts/generate-run.sh --mode merge --stack $STACK --app $APP --apply"
echo "Merge pipeline runs: kubectl get pipelinerun -n tekton-pipelines -l tekton.dev/pipeline=stack-merge-release"

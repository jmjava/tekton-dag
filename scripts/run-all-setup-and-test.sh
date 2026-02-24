#!/usr/bin/env bash
# Run full setup (Kind, Tekton, Postgres, Tekton Results) then run the test and verify results in DB.
# Idempotent: safe to re-run if cluster or components already exist.
#
# Every step is checked: non-zero exit or unexpected output must be fixed; do not ignore failures.
#
# Usage: ./run-all-setup-and-test.sh [--stack STACK] [--skip-postgres] [--skip-results] [--no-verify-db]
#   --stack           Stack file for DAG verify (default: stack-one.yaml)
#   --skip-postgres   Do not install Postgres (use if already running or not needed)
#   --skip-results    Do not install Tekton Results (skip DB verification)
#   --no-verify-db    Run test but skip the Results DB verification step
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Run a step and exit 1 with a clear message if it fails (so we never ignore a failed step).
run_step() {
  local step_name="$1"
  shift
  if ! "$@"; then
    echo "" >&2
    echo "FAILED: $step_name (exit code $?)" >&2
    echo "Fix the error above before re-running." >&2
    exit 1
  fi
}

STACK_FILE="stack-one.yaml"
SKIP_POSTGRES=false
SKIP_RESULTS=false
NO_VERIFY_DB=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stack)           STACK_FILE="$2"; shift 2 ;;
    --skip-postgres)   SKIP_POSTGRES=true; shift ;;
    --skip-results)    SKIP_RESULTS=true; shift ;;
    --no-verify-db)    NO_VERIFY_DB=true; shift ;;
    *)                 echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

echo "=============================================="
echo "  Run everything: setup + test + verify DB"
echo "  Stack: $STACK_FILE"
echo "=============================================="

# 1. Kind + registry (idempotent)
echo ""
echo ">>> 1. Kind cluster + registry"
run_step "1. Kind cluster + registry" ./scripts/kind-with-registry.sh

# 2. Tekton Pipelines + tasks + pipelines (idempotent)
echo ""
echo ">>> 2. Tekton Pipelines + stack tasks/pipelines"
run_step "2. Tekton Pipelines" ./scripts/install-tekton.sh

# 3. Postgres for Tekton Results (idempotent; --ephemeral so Kind works without StorageClass)
if [[ "$SKIP_POSTGRES" != "true" ]]; then
  echo ""
  echo ">>> 3. PostgreSQL for Tekton Results"
  run_step "3. PostgreSQL" ./scripts/install-postgres-kind.sh --ephemeral
else
  echo ""
  echo ">>> 3. PostgreSQL (skipped --skip-postgres)"
fi

# 4. Tekton Results API + Watcher (idempotent)
if [[ "$SKIP_RESULTS" != "true" ]]; then
  echo ""
  echo ">>> 4. Tekton Results"
  run_step "4. Tekton Results" ./scripts/install-tekton-results.sh
else
  echo ""
  echo ">>> 4. Tekton Results (skipped --skip-results)"
fi

# 5. Telepresence Traffic Manager (required for intercept E2E)
echo ""
echo ">>> 5. Telepresence Traffic Manager"
run_step "5. Telepresence Traffic Manager" ./scripts/install-telepresence-traffic-manager.sh

# 6. Git SSH key secret (required for clone-app-repos SSH pull; created from ~/.ssh if missing)
echo ""
echo ">>> 6. Git SSH key secret (prerequisite for app repo clone)"
run_step "6. Git SSH key secret" ./scripts/ensure-git-ssh-secret.sh

# 7. Full E2E with live intercepts (bootstrap + PR pipeline + DB verify)
echo ""
echo ">>> 7. Full E2E: bootstrap + PR pipeline (intercepts) + verify results in DB"
VERIFY_DB_FLAG=""
[[ "$NO_VERIFY_DB" == "true" ]] && VERIFY_DB_FLAG="--no-verify-db"
[[ "$SKIP_RESULTS" == "true" ]] && VERIFY_DB_FLAG="--no-verify-db"

run_step "7. Full E2E with intercepts + DB verify" ./scripts/run-e2e-with-intercepts.sh --stack "$STACK_FILE" --skip-install-check $VERIFY_DB_FLAG

echo ""
echo "=============================================="
echo "  All done: setup and E2E with intercepts passed."
echo "=============================================="

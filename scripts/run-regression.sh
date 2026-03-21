#!/usr/bin/env bash
# Comprehensive regression for tekton-dag. See docs/REGRESSION.md.
#
# Tiers (default = as much as your machine/cluster allows):
#   A — Always local: Phase-1 DAG verify (yq + bash), pytest×4, vitest
#   B — Local UI: Playwright (unless skipped)
#   C — Cluster (auto if kubectl + orchestrator Service exist, or --cluster)
#   D — Tekton DAG pipeline: verify-dag-phase2.sh (stack-dag-verify → Succeeded + CLI match)
#   E — Optional: Tekton Results DB check, GUI Newman, full Kind E2E
#
# Usage:
#   ./scripts/run-regression.sh                    # A + B + C + D (auto) + E if Results API exists
#   ./scripts/run-regression.sh --local-only       # A only (fast CI / laptop)
#   ./scripts/run-regression.sh --skip-playwright  # A + C (+ D flags) without browser E2E
#   ./scripts/run-regression.sh --skip-cluster     # A + B only
#   ./scripts/run-regression.sh --cluster          # require orchestrator in cluster (Newman)
#   ./scripts/run-regression.sh --with-results-verify   # require Tekton Results + run DAG verify + DB check
#   ./scripts/run-regression.sh --skip-results-verify   # never run run-full-test-and-verify-results.sh
#   ./scripts/run-regression.sh --require-dag-verify    # fail if stack-dag-verify pipeline missing (no silent skip)
#   ./scripts/run-regression.sh --skip-dag-verify       # skip Phase 2 Tekton PipelineRun (not recommended)
#   REGRESSION_RESULTS_VERIFY=auto|skip|yes
#   REGRESSION_DAG_VERIFY=auto|skip|yes               # default auto: run Phase 2 when pipeline exists
#   DAG_VERIFY_TIMEOUT=300                             # seconds for verify-dag-phase2.sh (--timeout)
#   REGRESSION_FREE_PORTS=0                            # skip freeing 9091/8080 before cluster steps
#   RESULTS_API_LOCAL_PORT                             # host port for Results API forward (default 8080); freed in prep + verify-results-in-db.sh
#   ./scripts/run-regression.sh --newman-skip-integration  # pass through to run-orchestrator-tests.sh
#   ./scripts/run-regression.sh --gui-newman       # Postman vs Flask on :5000
#   ./scripts/run-regression.sh --kind-e2e         # run-all-setup-and-test.sh (very long)
#   ./scripts/run-regression.sh --help
#
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"

LOCAL_ONLY=false
SKIP_PLAYWRIGHT=false
SKIP_CLUSTER=false
CLUSTER_REQUIRED=false
# results: auto = run DAG+Results DB script when API exists; skip = never; yes = require API
RESULTS_VERIFY_MODE="${REGRESSION_RESULTS_VERIFY:-auto}"
# dag verify: auto = run verify-dag-phase2 when stack-dag-verify exists; skip = never; yes = require pipeline
DAG_VERIFY_MODE="${REGRESSION_DAG_VERIFY:-auto}"
RUN_GUI_NEWMAN=false
RUN_KIND_E2E=false
NEWMAN_SKIP_INTEGRATION=false
HELP=false

for arg in "$@"; do
  case "$arg" in
    --local-only)              LOCAL_ONLY=true ;;
    --skip-playwright)         SKIP_PLAYWRIGHT=true ;;
    --skip-cluster)            SKIP_CLUSTER=true ;;
    --cluster)                 CLUSTER_REQUIRED=true ;;
    --with-results-verify)     RESULTS_VERIFY_MODE=yes ;;
    --skip-results-verify)     RESULTS_VERIFY_MODE=skip ;;
    --require-dag-verify)      DAG_VERIFY_MODE=yes ;;
    --skip-dag-verify)         DAG_VERIFY_MODE=skip ;;
    --gui-newman)              RUN_GUI_NEWMAN=true ;;
    --kind-e2e)                RUN_KIND_E2E=true ;;
    --newman-skip-integration) NEWMAN_SKIP_INTEGRATION=true ;;
    --help|-h)                 HELP=true ;;
    *)                         echo "Unknown option: $arg (try --help)" >&2; exit 1 ;;
  esac
done

if [[ "$HELP" == "true" ]]; then
  sed -n '2,45p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

if [[ "$LOCAL_ONLY" == "true" ]]; then
  SKIP_CLUSTER=true
  SKIP_PLAYWRIGHT=true
  RUN_GUI_NEWMAN=false
  RUN_KIND_E2E=false
  RESULTS_VERIFY_MODE=skip
  DAG_VERIFY_MODE=skip
  CLUSTER_REQUIRED=false
fi

if [[ "$SKIP_CLUSTER" == "true" ]] && [[ "$RESULTS_VERIFY_MODE" == "yes" ]]; then
  die "Incompatible: --with-results-verify needs cluster (omit --skip-cluster / --local-only)"
fi
if [[ "$SKIP_CLUSTER" == "true" ]] && [[ "$DAG_VERIFY_MODE" == "yes" ]]; then
  die "Incompatible: --require-dag-verify needs cluster (omit --skip-cluster / --local-only)"
fi

echo "=============================================="
echo "  tekton-dag regression (encompassing suite)"
echo "  REPO_ROOT=$REPO_ROOT"
echo "=============================================="

# Prefer repo .venv when default python3 has no pytest (common when venv not activated).
if ! python3 -c "import pytest" 2>/dev/null && [[ -x "$REPO_ROOT/.venv/bin/python3" ]]; then
  echo ">>> Using $REPO_ROOT/.venv/bin for Python (pytest not on PATH python3)"
  export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi

if ! python3 -c "import pytest" 2>/dev/null; then
  echo "" >&2
  echo "ERROR: python3 cannot import pytest." >&2
  echo "  One-shot setup:" >&2
  echo "    ./scripts/bootstrap-regression-venv.sh" >&2
  echo "  Or manually:" >&2
  echo "    python3 -m venv .venv && . .venv/bin/activate" >&2
  echo "    pip install -r orchestrator/requirements.txt \\" >&2
  echo "      -r management-gui/backend/requirements-dev.txt" >&2
  echo "    pip install -e 'libs/tekton-dag-common[test]' -e 'libs/baggage-python[test]'" >&2
  exit 1
fi

echo ""
echo ">>> Phase 1: DAG verification (no cluster) — scripts/verify-dag-phase1.sh"
need yq
bash "$SCRIPT_DIR/verify-dag-phase1.sh"

run_pytest_dir() {
  local name="$1"
  local dir="$2"
  shift 2
  echo ""
  echo ">>> pytest: $name ($dir)"
  (cd "$REPO_ROOT/$dir" && python3 -m pytest "$@" -v --tb=short)
}

run_pytest_dir "orchestrator" "orchestrator" tests/
run_pytest_dir "tekton-dag-common" "libs/tekton-dag-common" tests/
run_pytest_dir "management-gui backend" "management-gui/backend" tests/
run_pytest_dir "baggage-python" "libs/baggage-python" tests/

echo ""
echo ">>> vitest: libs/baggage-node"
need npm
(cd "$REPO_ROOT/libs/baggage-node" && npm install --silent && npm run test)

if [[ "$SKIP_PLAYWRIGHT" != "true" ]]; then
  echo ""
  echo ">>> Playwright: management-gui/frontend (Vite via playwright.config.js)"
  need npx
  (cd "$REPO_ROOT/management-gui/frontend" && npm install --silent && (npx playwright install chromium --with-deps 2>/dev/null || npx playwright install chromium))
  (cd "$REPO_ROOT/management-gui/frontend" && npx playwright test)
fi

cluster_has_orchestrator() {
  kubectl get svc tekton-dag-orchestrator -n "$NAMESPACE" &>/dev/null
}

cluster_has_results() {
  kubectl get deployment tekton-results-api -n tekton-pipelines &>/dev/null
}

cluster_has_dag_verify_pipeline() {
  kubectl get pipeline stack-dag-verify -n "$NAMESPACE" &>/dev/null
}

run_dag_verify_phase2() {
  echo ""
  echo ">>> Tekton: real PipelineRun stack-dag-verify — scripts/verify-dag-phase2.sh"
  echo "    (clone + resolve-stack; compares Task results to stack-graph.sh CLI)"
  need kubectl
  need jq
  local t="${DAG_VERIFY_TIMEOUT:-300}"
  "$SCRIPT_DIR/verify-dag-phase2.sh" --timeout "$t" --stack stack-one.yaml
}

run_newman_suites() {
  need kubectl
  need newman
  local extra=()
  [[ "$NEWMAN_SKIP_INTEGRATION" == "true" ]] && extra+=(--skip-integration)
  # Same default port as run-orchestrator-tests.sh; that script frees the port if stale.
  local pf_port="${ORCHESTRATOR_TEST_PORT:-9091}"
  echo ""
  echo ">>> Newman: orchestrator + graph — scripts/run-orchestrator-tests.sh --all (port ${pf_port})${extra[*]:+ ${extra[*]}}"
  ORCHESTRATOR_TEST_PORT="$pf_port" "$SCRIPT_DIR/run-orchestrator-tests.sh" --all "${extra[@]}"
}

run_results_verify() {
  echo ""
  echo ">>> Platform: DAG verify pipeline + Tekton Results DB — run-full-test-and-verify-results.sh"
  need jq
  "$SCRIPT_DIR/run-full-test-and-verify-results.sh" --skip-install-check
}

# run-full-test already runs verify-dag-phase2; avoid two stack-dag-verify runs in one regression.
will_run_full_results_verify() {
  [[ "$RESULTS_VERIFY_MODE" == "skip" ]] && return 1
  kubectl cluster-info &>/dev/null || return 1
  case "$RESULTS_VERIFY_MODE" in
    yes|auto) cluster_has_results ;;
    *) return 1 ;;
  esac
}

if [[ "$SKIP_CLUSTER" != "true" ]]; then
  if kubectl cluster-info &>/dev/null; then
    # ── Prep: release stale listeners before any port-forward (orchestrator, Results API, dev servers) ──
    if [[ "${REGRESSION_FREE_PORTS:-1}" != "0" ]]; then
      echo ""
      echo ">>> Prep: free TCP ports ${ORCHESTRATOR_TEST_PORT:-9091} (orchestrator) and ${RESULTS_API_LOCAL_PORT:-8080} (Tekton Results API)"
      free_tcp_port "${ORCHESTRATOR_TEST_PORT:-9091}" 1
      free_tcp_port "${RESULTS_API_LOCAL_PORT:-8080}" 1
    fi

    # ── Real Tekton pipeline (stack-dag-verify): must not be skipped on a full regression cluster ──
    if [[ "$DAG_VERIFY_MODE" != "skip" ]]; then
      if will_run_full_results_verify; then
        echo ""
        echo ">>> Tekton DAG verify: will run inside run-full-test-and-verify-results.sh (skipping duplicate verify-dag-phase2 here)"
      else
        case "$DAG_VERIFY_MODE" in
          yes)
            cluster_has_dag_verify_pipeline || die "REGRESSION_DAG_VERIFY=yes but Pipeline stack-dag-verify not found in $NAMESPACE (apply pipeline/ + tasks/)"
            run_dag_verify_phase2
            ;;
          auto)
            if cluster_has_dag_verify_pipeline; then
              run_dag_verify_phase2
            else
              echo ""
              echo ">>> SKIP Tekton DAG verify: Pipeline stack-dag-verify not in namespace $NAMESPACE"
              echo "    (No full PipelineRun executed — apply Tekton pipelines/tasks or use --require-dag-verify to fail here)"
            fi
            ;;
        esac
      fi
    fi

    if cluster_has_orchestrator; then
      if command -v newman &>/dev/null; then
        run_newman_suites
      else
        echo ""
        echo ">>> SKIP cluster Newman: 'newman' not on PATH (npm i -g newman)"
        [[ "$CLUSTER_REQUIRED" == "true" ]] && die "cluster required but newman missing"
      fi
    else
      echo ""
      if [[ "$CLUSTER_REQUIRED" == "true" ]]; then
        die "cluster required but svc/tekton-dag-orchestrator missing in namespace $NAMESPACE"
      else
        echo ">>> SKIP cluster Newman: orchestrator Service not found in $NAMESPACE"
      fi
    fi
  else
    echo ""
    if [[ "$CLUSTER_REQUIRED" == "true" ]]; then
      die "cluster required but kubectl context unreachable"
    elif [[ "$DAG_VERIFY_MODE" == "yes" ]]; then
      die "--require-dag-verify needs a working kubectl context"
    else
      echo ">>> SKIP cluster: kubectl context unreachable (no Newman, no Tekton DAG verify)"
    fi
  fi

  if [[ "$RESULTS_VERIFY_MODE" != "skip" ]]; then
    if ! kubectl cluster-info &>/dev/null; then
      [[ "$RESULTS_VERIFY_MODE" == "yes" ]] && die "--with-results-verify needs a working kubectl context"
    else
      case "$RESULTS_VERIFY_MODE" in
        yes)
          cluster_has_results || die "Tekton Results API not found (install tekton-results / postgres per docs)"
          run_results_verify
          ;;
        auto)
          if cluster_has_results; then
            run_results_verify
          else
            echo ""
            echo ">>> SKIP auto results verify: tekton-results-api not in cluster (optional: install Results or use --with-results-verify after install)"
          fi
          ;;
      esac
    fi
  fi
fi

if [[ "$RUN_GUI_NEWMAN" == "true" ]]; then
  need newman
  echo ""
  echo ">>> Newman: management-gui-tests.json → http://localhost:5000"
  newman run "$REPO_ROOT/tests/postman/management-gui-tests.json" \
    --env-var "baseUrl=http://localhost:5000" --reporters cli --color on
fi

if [[ "$RUN_KIND_E2E" == "true" ]]; then
  echo ""
  echo ">>> Full Kind + Tekton + intercept E2E — run-all-setup-and-test.sh"
  "$SCRIPT_DIR/run-all-setup-and-test.sh"
fi

echo ""
echo "=============================================="
echo "  Regression finished OK"
echo "=============================================="

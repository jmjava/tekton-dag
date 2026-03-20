#!/usr/bin/env bash
# scripts/common.sh — shared utilities for tekton-dag scripts.
# Source this at the top of any script:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "$SCRIPT_DIR/common.sh"

set -euo pipefail

# ── Path resolution ──────────────────────────────────────────────────
# SCRIPT_DIR must be set by the caller before sourcing.
REPO_ROOT="${REPO_ROOT:-$(cd "${SCRIPT_DIR:-.}/.." && pwd)}"
STACKS_DIR="${STACKS_DIR:-$REPO_ROOT/stacks}"

# ── Configurable defaults (override via env or flags) ────────────────
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-localhost:5001}"
GIT_SSH_SECRET_NAME="${GIT_SSH_SECRET_NAME:-git-ssh-key}"
GIT_URL="${GIT_URL:-https://github.com/jmjava/tekton-dag.git}"
GIT_REVISION="${GIT_REVISION:-main}"

# ── Logging / errors ────────────────────────────────────────────────
die() { echo "ERROR: $*" >&2; exit 1; }

need() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required but not found in PATH"
}

info()  { echo "==> $*"; }
warn()  { echo "WARNING: $*" >&2; }

# ── Port-forward helpers ─────────────────────────────────────────────
# Usage: start_port_forward <service> <local:remote> [namespace]
# Sets PF_PID. Caller should trap cleanup_port_forward EXIT.
PF_PID=""

start_port_forward() {
  local svc="$1" ports="$2" ns="${3:-$NAMESPACE}"
  kubectl port-forward "$svc" "$ports" -n "$ns" &
  PF_PID=$!
  sleep 3
  if ! kill -0 "$PF_PID" 2>/dev/null; then
    die "port-forward to $svc ($ports) failed to start"
  fi
}

cleanup_port_forward() {
  if [[ -n "${PF_PID:-}" ]] && kill -0 "$PF_PID" 2>/dev/null; then
    kill "$PF_PID" 2>/dev/null || true
  fi
}

# ── Registry helpers ─────────────────────────────────────────────────
# Kind maps localhost:5001 (host) -> localhost:5000 (in-cluster).
# Compile/pipeline image refs always use the in-cluster address.
resolve_compile_registry() {
  local reg="${1:-$IMAGE_REGISTRY}"
  if [[ "$reg" == "localhost:5001" ]]; then
    echo "localhost:5000"
  else
    echo "$reg"
  fi
}

# ── .env loader ──────────────────────────────────────────────────────
load_env() {
  local env_file="${1:-$REPO_ROOT/.env}"
  if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  fi
}

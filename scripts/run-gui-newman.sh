#!/usr/bin/env bash
# Start the management GUI Flask backend and run Newman against it.
#
# Usage:
#   ./scripts/run-gui-newman.sh
#
# Env:
#   API_MUTATION_TOKEN   Bearer token for mutation routes (generated if unset)
#   GUI_NEWMAN_PORT      Local Flask port (default 5000)
#   TEAM_NAME            Team filter for the backend (default *)
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"

need newman
need python3
need curl

if [[ -x "$REPO_ROOT/.venv/bin/python3" ]]; then
  export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi

API_MUTATION_TOKEN="${API_MUTATION_TOKEN:-$(openssl rand -hex 32)}"
export API_MUTATION_TOKEN
PORT="${GUI_NEWMAN_PORT:-5000}"
export PORT
export TEAM_NAME="${TEAM_NAME:-*}"
COLLECTION="${REPO_ROOT}/tests/postman/management-gui-tests.json"

GUI_PID=""
cleanup() {
  if [[ -n "$GUI_PID" ]] && kill -0 "$GUI_PID" 2>/dev/null; then
    kill "$GUI_PID" 2>/dev/null || true
    wait "$GUI_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "=============================================="
echo "  Management GUI Newman"
echo "  baseUrl=http://127.0.0.1:${PORT}"
echo "=============================================="

free_tcp_port "$PORT" 1
(
  cd "$REPO_ROOT/management-gui/backend"
  exec python3 app.py
) &
GUI_PID=$!

ready=false
for _ in $(seq 1 30); do
  if ! kill -0 "$GUI_PID" 2>/dev/null; then
    die "management GUI backend exited before becoming healthy"
  fi
  if curl -sf "http://127.0.0.1:${PORT}/api/health" | grep -q '"ok"'; then
    ready=true
    break
  fi
  sleep 1
done
[[ "$ready" == "true" ]] || die "management GUI backend did not become healthy on port ${PORT}"

echo "=== Running Newman: management-gui-tests.json ==="
newman run "$COLLECTION" \
  --env-var "baseUrl=http://127.0.0.1:${PORT}" \
  --env-var "apiMutationToken=$API_MUTATION_TOKEN" \
  --reporters cli \
  --color on

echo "=== GUI Newman passed ==="

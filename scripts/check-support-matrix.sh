#!/usr/bin/env bash
# Fail when docs/support-matrix.yaml drifts from GitHub Actions jobs.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

if [[ -x "$REPO_ROOT/.venv/bin/python3" ]]; then
  export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi

need python3
exec python3 "$SCRIPT_DIR/check-support-matrix.py" "$@"

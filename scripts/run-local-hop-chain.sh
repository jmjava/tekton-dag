#!/usr/bin/env bash
# Run originator → forwarder → terminal on localhost and fail-closed if pr-42 is rewritten.
# Uses libs/baggage-python install(); no cluster required.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"
if [[ -x "$REPO_ROOT/.venv/bin/python3" ]]; then
  export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi
exec python3 "$SCRIPT_DIR/local_hop_chain/run.py"

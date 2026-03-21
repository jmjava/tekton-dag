#!/usr/bin/env bash
# Run scripts/run-regression.sh with line-buffered output and a timestamp prefix on each line.
# Preserves the regression script exit code (unlike a naive pipe to while read).
#
# Usage: ./scripts/run-regression-stream.sh [same args as run-regression.sh]
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONUNBUFFERED=1
if command -v stdbuf >/dev/null 2>&1; then
  _run=(stdbuf -oL -eL bash "$SCRIPT_DIR/run-regression.sh" "$@")
else
  _run=(bash "$SCRIPT_DIR/run-regression.sh" "$@")
fi

set +e
"${_run[@]}" 2>&1 | while IFS= read -r line || [[ -n "${line:-}" ]]; do
  printf '[%s] %s\n' "$(date +%H:%M:%S)" "$line"
done
ec="${PIPESTATUS[0]}"
set -e
echo ""
echo "=== regression exit code: $ec ==="
exit "$ec"

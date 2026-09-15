#!/usr/bin/env bash
# Run operator unit tests and enforce the M17.6 per-package coverage floors.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

PIPELINE_FLOOR="${OPERATOR_PIPELINE_COVERAGE_FLOOR:-80}"
CONTROLLER_FLOOR="${OPERATOR_CONTROLLER_COVERAGE_FLOOR:-32}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

check_package() {
  local package="$1"
  local floor="$2"
  local profile="$TMP_DIR/${package##*/}.out"
  local measured

  (
    cd "$REPO_ROOT/operator"
    GOTOOLCHAIN=auto go test "$package" -race -coverprofile="$profile"
  )
  measured="$(
    cd "$REPO_ROOT/operator"
    go tool cover -func="$profile" |
      awk '/^total:/ {gsub(/%/, "", $3); print $3; exit}'
  )"

  [[ -n "$measured" ]] || die "coverage total missing for operator/$package"
  python3 - "$package" "$measured" "$floor" <<'PY'
import sys

package, measured_text, floor_text = sys.argv[1:]
measured = float(measured_text)
floor = float(floor_text)
if measured < floor:
    raise SystemExit(
        f"FAIL operator/{package}: {measured:.1f}% is below {floor:.1f}%"
    )
print(f"OK operator/{package}: {measured:.1f}% (floor {floor:.1f}%)")
PY
}

check_package ./internal/pipeline "$PIPELINE_FLOOR"
check_package ./internal/controller "$CONTROLLER_FLOOR"

echo ">>> go test: operator API packages"
(cd "$REPO_ROOT/operator" && GOTOOLCHAIN=auto go test ./api/... -race)

#!/usr/bin/env bash
# Maven, PHPUnit, and operator Go unit tests (no cluster).
# Usage: scripts/run-lang-unit-tests.sh
#   REGRESSION_LANG_TESTS=auto|skip|require  (default auto)
#   --require  fail if mvn/php/go missing
#   --skip     no-op
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"

MODE="${REGRESSION_LANG_TESTS:-auto}"
for arg in "$@"; do
  case "$arg" in
    --require) MODE=require ;;
    --skip)    MODE=skip ;;
    --auto)    MODE=auto ;;
    --help|-h)
      sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

if [[ "$MODE" == "skip" ]]; then
  echo ">>> SKIP lang unit tests (REGRESSION_LANG_TESTS=skip)"
  exit 0
fi

have() { command -v "$1" >/dev/null 2>&1; }

missing=()
have mvn || missing+=("mvn")
have php || missing+=("php")
have composer || missing+=("composer")
have go || missing+=("go")

if ((${#missing[@]})); then
  msg="lang unit tests need: ${missing[*]}"
  if [[ "$MODE" == "require" ]]; then
    die "$msg (install them or omit --require-lang-tests)"
  fi
  echo ">>> SKIP lang unit tests: $msg"
  exit 0
fi

echo ""
echo ">>> Maven: libs/baggage-spring-boot-starter"
(cd "$REPO_ROOT/libs/baggage-spring-boot-starter" && mvn -B -q test)

echo ""
echo ">>> Maven: libs/baggage-servlet-filter"
(cd "$REPO_ROOT/libs/baggage-servlet-filter" && mvn -B -q test)

echo ""
echo ">>> PHPUnit: libs/baggage-php"
(cd "$REPO_ROOT/libs/baggage-php" && composer install --no-interaction --quiet && ./vendor/bin/phpunit)

echo ""
echo ">>> go test: operator internal (no envtest / e2e)"
(cd "$REPO_ROOT/operator" && GOTOOLCHAIN=auto go test ./internal/pipeline/ ./internal/controller/ ./api/...)

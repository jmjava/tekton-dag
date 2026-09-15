#!/usr/bin/env bash
# Syntax-check and ShellCheck every tracked standalone shell script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

need shellcheck

mapfile -d '' shell_files < <(
  cd "$REPO_ROOT"
  git ls-files -z -- '*.sh'
)
((${#shell_files[@]} > 0)) || die "no tracked shell files found"

for file in "${shell_files[@]}"; do
  bash -n "$REPO_ROOT/$file"
done

(
  cd "$REPO_ROOT"
  shellcheck \
    --external-sources \
    --source-path=SCRIPTDIR \
    --severity=warning \
    "${shell_files[@]}"
)

echo "Validated ${#shell_files[@]} tracked shell file(s)."

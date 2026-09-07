#!/usr/bin/env bash
# Idempotent Cloud Agent install: Python regression venv + Newman (cluster CI).
# Docker/Kind/kubectl belong on the snapshot; this only refreshes repo-tied deps.
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"

bash "$SCRIPT_DIR/bootstrap-regression-venv.sh"

if ! command -v newman >/dev/null 2>&1; then
  sudo env "PATH=$PATH" npm install -g newman
fi

echo "OK: cloud-agent install (venv + newman)"

#!/usr/bin/env bash
# Create .venv and install everything needed for scripts/run-regression.sh (pytest + libs).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"

need python3
python3 -m venv "$REPO_ROOT/.venv"
# shellcheck disable=SC1091
source "$REPO_ROOT/.venv/bin/activate"
pip install -U pip -q
pip install -q -r orchestrator/requirements.txt -r management-gui/backend/requirements-dev.txt
pip install -q -e 'libs/tekton-dag-common[test]' -e 'libs/baggage-python[test]'
echo "OK: run regression with: bash scripts/run-regression-agent.sh"
echo "    (or: source .venv/bin/activate && bash scripts/run-regression.sh)"

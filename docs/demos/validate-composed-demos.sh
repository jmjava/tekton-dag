#!/usr/bin/env bash
# Validate composed segment MP4s: streams present, A/V drift, narration lint.
#
# This is a thin wrapper around the docgen CLI.
#
# Usage:  cd docs/demos && ./validate-composed-demos.sh
# Exit 0 = all checks pass; exit 1 = problems found (CI-friendly).

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec docgen --config "$DEMOS_DIR/docgen.yaml" validate --pre-push

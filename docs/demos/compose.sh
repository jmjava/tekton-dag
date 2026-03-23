#!/usr/bin/env bash
# compose.sh — Combine visual assets (Manim / VHS) with TTS audio using ffmpeg.
#
# This is a thin wrapper around the docgen CLI.
#
# Usage:
#   ./compose.sh              # compose default segments (01–11)
#   ./compose.sh 01 03 05     # compose specific segments
#   ./compose.sh 12 13 14     # M12.2 extension

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$DEMOS_DIR/.venv/bin/activate" ]; then
    source "$DEMOS_DIR/.venv/bin/activate"
fi
exec docgen --config "$DEMOS_DIR/docgen.yaml" compose "$@"

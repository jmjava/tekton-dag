#!/usr/bin/env bash
# generate-all.sh — Master script to produce all demo assets from scratch.
#
# This is a thin wrapper around the docgen CLI. Install docgen:
#   pip install -e /path/to/documentation-generator
#
# Usage:
#   cd docs/demos
#   ./generate-all.sh                 # full generation
#   ./generate-all.sh --skip-tts      # skip TTS only — USE THIS after new MP3s
#   ./generate-all.sh --skip-manim    # skip Manim render
#   ./generate-all.sh --skip-vhs      # skip VHS render
#   ./generate-all.sh --dry-run       # show plan only (TTS dry run)
#
# Prerequisites:
#   - docgen installed (pip install -e /path/to/documentation-generator)
#   - manim installed (pip install manim)
#   - vhs in PATH (go install github.com/charmbracelet/vhs@latest)
#   - ttyd in PATH (apt install ttyd)
#   - ffmpeg installed
#   - OPENAI_API_KEY set (in .env or environment)

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$DEMOS_DIR/.venv/bin/activate" ]; then
    source "$DEMOS_DIR/.venv/bin/activate"
fi

# Parse --dry-run specially (docgen generate-all doesn't have it)
DRY_RUN=false
ARGS=()
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=true
    else
        ARGS+=("$arg")
    fi
done

if [[ "$DRY_RUN" == "true" ]]; then
    echo "=== Dry run: showing TTS plan ==="
    exec docgen --config "$DEMOS_DIR/docgen.yaml" tts --dry-run
fi

exec docgen --config "$DEMOS_DIR/docgen.yaml" generate-all "${ARGS[@]}"

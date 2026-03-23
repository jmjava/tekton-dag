#!/usr/bin/env bash
# Regenerate TTS + composed MP4s for M12.2 segments (12–14) and rebuild full-demo-with-m12-2.
#
# Usage:  cd docs/demos && ./regenerate-m12-2.sh
# Requires: docgen installed, OPENAI_API_KEY in .env, ffmpeg, Manim outputs for 12–14.

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$DEMOS_DIR/.venv/bin/activate" ]; then
    source "$DEMOS_DIR/.venv/bin/activate"
fi
CFG="$DEMOS_DIR/docgen.yaml"

echo "==> TTS narration (12, 13, 14)…"
docgen --config "$CFG" tts --segment 12
docgen --config "$CFG" tts --segment 13
docgen --config "$CFG" tts --segment 14

echo "==> Compose segments 12–14…"
docgen --config "$CFG" compose 12 13 14

echo "==> Concat full-demo-with-m12-2…"
docgen --config "$CFG" concat --config-name full-demo-with-m12-2

echo "Done: recordings/full-demo-with-m12-2.mp4"

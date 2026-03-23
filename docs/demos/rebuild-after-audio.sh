#!/usr/bin/env bash
# Run this after you regenerate audio/*.mp3 (docgen tts / generate-narration.py).
# Rebuilds EVERYTHING that depends on audio length and visuals:
#   Manim → VHS → compose → validate → concat
#
# Same as: docgen generate-all --skip-tts
#
# Usage:  cd docs/demos && ./rebuild-after-audio.sh

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "═══ Rebuild after audio (Manim + VHS + compose + validate + concat) ═══"
echo "    (skipping TTS — using existing audio/*.mp3)"
echo ""
exec docgen --config "$DEMOS_DIR/docgen.yaml" rebuild-after-audio

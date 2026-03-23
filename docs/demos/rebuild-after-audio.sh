#!/usr/bin/env bash
# Run this after you regenerate audio/*.mp3 (generate-narration.py).
# Rebuilds EVERYTHING that depends on audio length and visuals:
#   Manim (9 scenes) → VHS (all tapes) → compose 01–11 → compose 12–14 → full-demo-with-m12-2.mp4
#
# Same as: ./generate-all.sh --skip-tts
#
# Usage:  cd docs/demos && ./rebuild-after-audio.sh

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "═══ Rebuild after audio (Manim + VHS + compose + full concat) ═══"
echo "    (skipping TTS — using existing audio/*.mp3)"
echo ""
exec "$HERE/generate-all.sh" --skip-tts

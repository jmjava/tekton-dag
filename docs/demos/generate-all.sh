#!/usr/bin/env bash
# generate-all.sh — Master script to produce all demo assets from scratch.
#
# Usage:
#   cd docs/demos
#   ./generate-all.sh                 # full generation
#   ./generate-all.sh --skip-tts      # skip audio generation (reuse existing)
#   ./generate-all.sh --skip-manim    # skip Manim render
#   ./generate-all.sh --skip-vhs      # skip VHS render
#   ./generate-all.sh --dry-run       # show plan only
#
# Prerequisites:
#   - .venv with manim + openai installed (pip install -r requirements.txt)
#   - vhs in PATH (go install github.com/charmbracelet/vhs@latest)
#   - ffmpeg installed
#   - OPENAI_API_KEY set (in .env or environment)

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DEMOS_DIR/.venv"
VHS_BIN="${VHS_BIN:-$(command -v vhs 2>/dev/null || echo "$HOME/go/bin/vhs")}"

SKIP_TTS=false
SKIP_MANIM=false
SKIP_VHS=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-tts)   SKIP_TTS=true; shift ;;
        --skip-manim) SKIP_MANIM=true; shift ;;
        --skip-vhs)   SKIP_VHS=true; shift ;;
        --dry-run)    DRY_RUN=true; shift ;;
        *)            echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

info() { echo "==> $*"; }
step() { echo ""; echo "──────────────────────────────────────────"; echo "  STEP: $*"; echo "──────────────────────────────────────────"; }

# Activate venv
if [[ -d "$VENV" ]]; then
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
else
    echo "ERROR: .venv not found at $VENV" >&2
    echo "Create it: python3 -m venv .venv && pip install -r requirements.txt" >&2
    exit 1
fi

# Verify tools
for cmd in python ffmpeg; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: $cmd not found" >&2; exit 1; }
done
[[ "$SKIP_VHS" == "true" ]] || [[ -x "$VHS_BIN" ]] || { echo "ERROR: vhs not found at $VHS_BIN" >&2; exit 1; }

# Load .env for OPENAI_API_KEY
ENV_FILE="$DEMOS_DIR/../../.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

echo "╔══════════════════════════════════════════════╗"
echo "║  tekton-dag Demo Asset Generator             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
info "Demos dir: $DEMOS_DIR"
info "Venv:      $VENV"
info "VHS:       $VHS_BIN"
info "Skip TTS:  $SKIP_TTS"
info "Skip Manim: $SKIP_MANIM"
info "Skip VHS:  $SKIP_VHS"
info "Dry run:   $DRY_RUN"

if [[ "$DRY_RUN" == "true" ]]; then
    echo ""
    echo "Steps that would run:"
    [[ "$SKIP_TTS" != "true" ]] && echo "  1. Generate narration audio (11 segments via OpenAI TTS)"
    [[ "$SKIP_MANIM" != "true" ]] && echo "  2. Render Manim animations (6 scenes)"
    [[ "$SKIP_VHS" != "true" ]] && echo "  3. Render VHS terminal recordings (7 tapes)"
    echo "  4. Compose final videos (ffmpeg)"
    echo ""
    echo "Would produce: 11 segment videos + full-demo.mp4 in recordings/"
    exit 0
fi

# ── Step 1: TTS narration ───────────────────────────────────────────
if [[ "$SKIP_TTS" != "true" ]]; then
    step "Generate narration audio"
    python "$DEMOS_DIR/generate-narration.py"
else
    step "Skipping TTS (--skip-tts)"
fi

# ── Step 2: Manim animations ────────────────────────────────────────
if [[ "$SKIP_MANIM" != "true" ]]; then
    step "Render Manim animations"
    cd "$DEMOS_DIR/animations"
    SCENES=(StackDAGScene HeaderPropagationScene InterceptRoutingScene LocalDebugScene MultiTeamScene BlastRadiusScene)
    for scene in "${SCENES[@]}"; do
        info "Rendering $scene..."
        manim -qm scenes.py "$scene"
    done
    cd "$DEMOS_DIR"
else
    step "Skipping Manim (--skip-manim)"
fi

# ── Step 3: VHS terminal recordings ─────────────────────────────────
if [[ "$SKIP_VHS" != "true" ]]; then
    step "Render VHS terminal recordings"
    mkdir -p "$DEMOS_DIR/terminal/rendered"
    for tape in "$DEMOS_DIR"/terminal/*.tape; do
        info "Recording $(basename "$tape")..."
        "$VHS_BIN" "$tape"
    done
else
    step "Skipping VHS (--skip-vhs)"
fi

# ── Step 4: Compose final videos ────────────────────────────────────
step "Compose final videos (ffmpeg)"
bash "$DEMOS_DIR/compose.sh"

# ── Summary ──────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Generation complete!                        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Audio:      $(ls "$DEMOS_DIR/audio/"*.mp3 2>/dev/null | wc -l) MP3 files"
echo "  Animations: $(ls "$DEMOS_DIR/animations/media/videos/scenes/720p30/"*.mp4 2>/dev/null | wc -l) Manim videos"
echo "  Terminal:   $(ls "$DEMOS_DIR/terminal/rendered/"*.mp4 2>/dev/null | wc -l) VHS recordings"
echo "  Recordings: $(ls "$DEMOS_DIR/recordings/"*.mp4 2>/dev/null | wc -l) composed videos"
echo ""
[[ -f "$DEMOS_DIR/recordings/full-demo.mp4" ]] && echo "  Full demo: recordings/full-demo.mp4"

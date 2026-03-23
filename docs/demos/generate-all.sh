#!/usr/bin/env bash
# generate-all.sh — Master script to produce all demo assets from scratch.
#
# ── Typical workflows ─────────────────────────────────────────────────
#   Fresh everything (TTS + Manim + VHS + all MP4s + full-demo-with-m12-2):
#       ./generate-all.sh
#
#   You already ran generate-narration.py and have new audio/*.mp3 — rebuild the rest:
#       ./rebuild-after-audio.sh
#   (equivalent to: ./generate-all.sh --skip-tts)
#
# Usage:
#   cd docs/demos
#   ./generate-all.sh                 # full generation
#   ./generate-all.sh --skip-tts      # skip TTS only — USE THIS after new MP3s
#   ./generate-all.sh --skip-manim    # skip Manim render
#   ./generate-all.sh --skip-vhs      # skip VHS render
#   ./generate-all.sh --dry-run       # show plan only
#
# Prerequisites:
#   - .venv with manim + openai installed (pip install -r requirements.txt)
#   - vhs in PATH (go install github.com/charmbracelet/vhs@latest)
#   - ttyd in PATH (VHS needs it; apt install ttyd, or download release binary to ~/.local/bin)
#   - ffmpeg installed
#   - OPENAI_API_KEY set (in .env or environment)

set -euo pipefail

# User-local ttyd (no sudo) is a common install path for VHS.
export PATH="${HOME}/.local/bin:${PATH}"

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
    [[ "$SKIP_TTS" != "true" ]] && echo "  1. Generate narration audio (14 segments via OpenAI TTS: 01–11 core + 12–14 M12.2)"
    [[ "$SKIP_MANIM" != "true" ]] && echo "  2. Render Manim animations (9 scenes)"
    [[ "$SKIP_VHS" != "true" ]] && echo "  3. Render VHS terminal recordings (all .tape under terminal/)"
    echo "  4. Compose core demo videos 01–11 (ffmpeg → recordings/)"
    echo "  5. Compose M12.2 extension 12–14 (Manim + TTS; or run ./regenerate-m12-2.sh for 12–14 only)"
    echo "  6. If all 14 segment MP4s exist: concat → full-demo-with-m12-2.mp4"
    echo ""
    echo "Would produce: core 11 + optional 3 segment videos; full-demo.mp4 (01–11);"
    echo "  optional full-demo-with-m12-2.mp4 when segments 12–14 composed."
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
    SCENES=(StackDAGScene HeaderPropagationScene InterceptRoutingScene LocalDebugScene MultiTeamScene BlastRadiusScene RegressionSuiteScene ManagementGUIArchitectureScene GUIExtensionScene)
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

# ── Step 4: Compose core demo videos (01–11) ────────────────────────
step "Compose core demo videos 01–11 (ffmpeg)"
bash "$DEMOS_DIR/compose.sh"

# ── Step 5: M12.2 extension segments 12–14 (Manim + existing audio) ───
step "Compose M12.2 extension segments 12–14"
bash "$DEMOS_DIR/compose.sh" 12 13 14

# ── Step 6: Optional extended full demo (01–14) ──────────────────────
compose_extended_demo() {
    local ext_ok=true
    local ext_list
    ext_list=$(mktemp)
    for seg in 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
        local narration_name stem f
        narration_name=$(ls "$DEMOS_DIR/narration/${seg}-"*.md 2>/dev/null | head -1 || true)
        [[ -n "$narration_name" ]] || { ext_ok=false; break; }
        stem=$(basename "${narration_name%.md}")
        f="$DEMOS_DIR/recordings/${stem}.mp4"
        if [[ ! -f "$f" ]]; then
            ext_ok=false
            break
        fi
        echo "file '$f'" >> "$ext_list"
    done
    if [[ "$ext_ok" == "true" ]]; then
        echo ""
        echo "--- Building full-demo-with-m12-2.mp4 (segments 01–14) ---"
        ffmpeg -y -f concat -safe 0 -i "$ext_list" -c copy \
            "$DEMOS_DIR/recordings/full-demo-with-m12-2.mp4" 2>/dev/null
        echo "  ✓ $DEMOS_DIR/recordings/full-demo-with-m12-2.mp4"
    else
        echo ""
        echo "  (skip full-demo-with-m12-2: not all 14 composed MP4s present)"
    fi
    rm -f "$ext_list"
}

step "Optional: concat full demo 01–14 (if all segments composed)"
compose_extended_demo

# ── Summary ──────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Generation complete!                      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Audio:      $(ls "$DEMOS_DIR/audio/"*.mp3 2>/dev/null | wc -l) MP3 files"
echo "  Animations: $(ls "$DEMOS_DIR/animations/media/videos/scenes/720p30/"*.mp4 2>/dev/null | wc -l) Manim videos"
echo "  Terminal:   $(ls "$DEMOS_DIR/terminal/rendered/"*.mp4 2>/dev/null | wc -l) VHS recordings"
echo "  Recordings: $(ls "$DEMOS_DIR/recordings/"*.mp4 2>/dev/null | wc -l) composed videos"
echo ""
[[ -f "$DEMOS_DIR/recordings/full-demo.mp4" ]] && echo "  Full demo: recordings/full-demo.mp4"

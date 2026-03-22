#!/usr/bin/env bash
# compose.sh — Combine visuals (Manim / VHS / still) with TTS audio (ffmpeg).
# Portable copy (tekton-dag documentation-generator). Place beside narration/, audio/, terminal/.
#
# Usage:
#   ./compose.sh              # DEFAULT_SEGMENTS below
#   ./compose.sh 01 02        # specific segments
#
set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIO_DIR="$DEMOS_DIR/audio"
MANIM_DIR_720="$DEMOS_DIR/animations/media/videos/scenes/720p30"
MANIM_DIR_480="$DEMOS_DIR/animations/media/videos/scenes/480p15"
MANIM_DIR="${MANIM_DIR_720}"
[[ -d "$MANIM_DIR" ]] || MANIM_DIR="$MANIM_DIR_480"
VHS_DIR="$DEMOS_DIR/terminal/rendered"
OUT_DIR="$DEMOS_DIR/recordings"

mkdir -p "$OUT_DIR"

# ── CUSTOMIZE FOR YOUR PROJECT ─────────────────────────────────────
# Segments compose when you run ./compose.sh with no arguments:
DEFAULT_SEGMENTS=(01 02)

# Ordered list; if non-empty and every segment composes successfully, build full-demo.mp4
FULL_CONCAT_SEGMENTS=(01 02)

# Segment → visual. Types: manim | vhs | mixed | still (hex RGB without 0x)
declare -A VISUAL_MAP
VISUAL_MAP[01]="still:2b3a56"
VISUAL_MAP[02]="vhs:02-terminal.mp4"

# Reference — tekton-dag production map (comment; delete in your project):
# VISUAL_MAP[01]="manim:StackDAGScene.mp4"
# VISUAL_MAP[02]="vhs:02-quickstart.mp4"
# VISUAL_MAP[03]="mixed:HeaderPropagationScene.mp4:03-bootstrap.mp4"
# ... see tekton-dag docs/demos/compose.sh
# ─────────────────────────────────────────────────────────────────

compose_simple() {
    local video="$1" audio="$2" output="$3"
    if [[ ! -f "$video" ]]; then
        echo "    SKIP: missing $video"
        return 1
    fi
    if [[ ! -f "$audio" ]]; then
        echo "    SKIP: missing $audio"
        return 1
    fi
    local audio_dur video_dur
    audio_dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$audio" | tr -d '\r')
    video_dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$video" | tr -d '\r')

    if awk -v v="$video_dur" -v a="$audio_dur" 'BEGIN { exit !(v < a) }'; then
        local pad
        pad=$(awk -v v="$video_dur" -v a="$audio_dur" 'BEGIN { printf "%.3f", a - v }')
        ffmpeg -y -i "$video" -i "$audio" \
            -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=${pad}[v]" \
            -map "[v]" -map 1:a:0 \
            -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
            -c:a aac -b:a 128k \
            -t "$audio_dur" -movflags +faststart \
            "$output" 2>/dev/null
        echo "    ✓ video=${video_dur}s + freeze ${pad}s → audio=${audio_dur}s"
    else
        ffmpeg -y -i "$video" -i "$audio" \
            -map 0:v:0 -map 1:a:0 \
            -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
            -c:a aac -b:a 128k \
            -t "$audio_dur" -movflags +faststart \
            "$output" 2>/dev/null
        echo "    ✓ video=${video_dur}s trimmed to audio=${audio_dur}s"
    fi
}

compose_mixed() {
    local video1="$1" video2="$2" audio="$3" output="$4"
    local concat_list
    concat_list=$(mktemp)

    for v in "$video1" "$video2"; do
        if [[ ! -f "$v" ]]; then
            echo "    SKIP: missing $v"
            rm -f "$concat_list"
            return 1
        fi
        echo "file '$v'" >> "$concat_list"
    done

    if [[ ! -f "$audio" ]]; then
        echo "    SKIP: missing $audio"
        rm -f "$concat_list"
        return 1
    fi

    ffmpeg -y -f concat -safe 0 -i "$concat_list" -i "$audio" \
        -c:v libx264 -preset fast -crf 23 \
        -c:a aac -b:a 128k \
        -shortest -movflags +faststart \
        "$output" 2>/dev/null
    rm -f "$concat_list"
    local ad
    ad=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$audio")
    echo "    ✓ mixed concat + audio=${ad}s"
}

compose_still() {
    local hex="$1" audio="$2" output="$3"
    if [[ ! -f "$audio" ]]; then
        echo "    SKIP: missing $audio"
        return 1
    fi
    ffmpeg -y -f lavfi -i "color=c=0x${hex}:s=1280x720:r=30" -i "$audio" \
        -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
        -c:a aac -b:a 128k -shortest -movflags +faststart \
        "$output" 2>/dev/null
    local ad
    ad=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$audio")
    echo "    ✓ still 1280x720 + audio=${ad}s"
}

echo "=== Composing demo videos ==="
composed=0
expected=0  # segments with a VISUAL_MAP entry in this run

segments=("$@")
if [[ ${#segments[@]} -eq 0 ]]; then
    segments=("${DEFAULT_SEGMENTS[@]}")
fi

for seg in "${segments[@]}"; do
    spec="${VISUAL_MAP[$seg]:-}"
    if [[ -z "$spec" ]]; then
        echo "  [$seg] unknown segment, skipping"
        continue
    fi
    ((expected++)) || true

    IFS=':' read -ra parts <<< "$spec"
    vtype="${parts[0]}"

    narration_name=$(ls "$DEMOS_DIR/narration/${seg}-"*.md 2>/dev/null | head -1 || true)
    stem=$(basename "${narration_name%.md}" 2>/dev/null || echo "$seg")
    audio="$AUDIO_DIR/${stem}.mp3"
    output="$OUT_DIR/${stem}.mp4"

    echo "  [$seg] $stem ($vtype)"

    case "$vtype" in
        manim)
            compose_simple "$MANIM_DIR/${parts[1]}" "$audio" "$output" && ((composed++)) || true
            ;;
        vhs)
            compose_simple "$VHS_DIR/${parts[1]}" "$audio" "$output" && ((composed++)) || true
            ;;
        mixed)
            compose_mixed "$MANIM_DIR/${parts[1]}" "$VHS_DIR/${parts[2]}" "$audio" "$output" && ((composed++)) || true
            ;;
        still)
            compose_still "${parts[1]}" "$audio" "$output" && ((composed++)) || true
            ;;
    esac
done

echo ""
echo "=== Composed $composed / $expected segment videos ==="

if [[ ${#FULL_CONCAT_SEGMENTS[@]} -gt 0 ]] && [[ "$composed" -eq "$expected" ]] && [[ "$expected" -gt 0 ]]; then
    all_ok=true
    concat_file=$(mktemp)
    for seg in "${FULL_CONCAT_SEGMENTS[@]}"; do
        narration_name=$(ls "$DEMOS_DIR/narration/${seg}-"*.md 2>/dev/null | head -1 || true)
        [[ -n "$narration_name" ]] || { all_ok=false; break; }
        stem=$(basename "${narration_name%.md}")
        f="$OUT_DIR/${stem}.mp4"
        if [[ ! -f "$f" ]]; then
            all_ok=false
            break
        fi
        echo "file '$f'" >> "$concat_file"
    done
    if [[ "$all_ok" == "true" ]]; then
        echo ""
        echo "--- Building full-demo.mp4 ---"
        ffmpeg -y -f concat -safe 0 -i "$concat_file" -c copy \
            "$OUT_DIR/full-demo.mp4" 2>/dev/null
        echo "  ✓ $OUT_DIR/full-demo.mp4"
    fi
    rm -f "$concat_file"
fi

echo ""
echo "=== Done ==="

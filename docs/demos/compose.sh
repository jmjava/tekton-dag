#!/usr/bin/env bash
# compose.sh — Combine visual assets (Manim / VHS) with TTS audio using ffmpeg.
#
# Usage:
#   ./compose.sh              # compose all segments
#   ./compose.sh 01 03 05     # compose specific segments

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIO_DIR="$DEMOS_DIR/audio"
MANIM_DIR_720="$DEMOS_DIR/animations/media/videos/scenes/720p30"
MANIM_DIR_480="$DEMOS_DIR/animations/media/videos/scenes/480p15"
MANIM_DIR="${MANIM_DIR_720}"
# Fallback to 480p if 720p not available
[[ -d "$MANIM_DIR" ]] || MANIM_DIR="$MANIM_DIR_480"
VHS_DIR="$DEMOS_DIR/terminal/rendered"
OUT_DIR="$DEMOS_DIR/recordings"

mkdir -p "$OUT_DIR"

# Segment → visual source mapping
# Format: segment:type:source_file
# type = manim | vhs | mixed (manim first half, vhs second half)
declare -A VISUAL_MAP
VISUAL_MAP[01]="manim:StackDAGScene.mp4"
VISUAL_MAP[02]="vhs:02-quickstart.mp4"
VISUAL_MAP[03]="mixed:HeaderPropagationScene.mp4:03-bootstrap.mp4"
VISUAL_MAP[04]="vhs:04-pr-pipeline.mp4"
VISUAL_MAP[05]="manim:InterceptRoutingScene.mp4"
VISUAL_MAP[06]="manim:LocalDebugScene.mp4"
VISUAL_MAP[07]="vhs:07-orchestrator-api.mp4"
VISUAL_MAP[08]="manim:MultiTeamScene.mp4"
VISUAL_MAP[09]="vhs:09-results-db.mp4"
VISUAL_MAP[10]="vhs:10-newman.mp4"
VISUAL_MAP[11]="mixed:BlastRadiusScene.mp4:11-graph-tests.mp4"

segments=("$@")
if [[ ${#segments[@]} -eq 0 ]]; then
    segments=(01 02 03 04 05 06 07 08 09 10 11)
fi

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
    audio_dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$audio")
    video_dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$video")

    ffmpeg -y -stream_loop -1 -i "$video" -i "$audio" \
        -c:v libx264 -preset fast -crf 23 \
        -c:a aac -b:a 128k \
        -t "$audio_dur" -movflags +faststart \
        "$output" 2>/dev/null
    echo "    ✓ video=${video_dur}s looped to audio=${audio_dur}s"
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
}

echo "=== Composing demo videos ==="
composed=0

for seg in "${segments[@]}"; do
    spec="${VISUAL_MAP[$seg]:-}"
    if [[ -z "$spec" ]]; then
        echo "  [$seg] unknown segment, skipping"
        continue
    fi

    IFS=':' read -ra parts <<< "$spec"
    vtype="${parts[0]}"

    # Find the narration file name
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
    esac
done

echo ""
echo "=== Composed $composed / ${#segments[@]} segment videos ==="

# Concatenate full demo if all segments present
if [[ $composed -eq 11 ]]; then
    echo ""
    echo "--- Building full demo video ---"
    concat_file=$(mktemp)
    for seg in 01 02 03 04 05 06 07 08 09 10 11; do
        narration_name=$(ls "$DEMOS_DIR/narration/${seg}-"*.md 2>/dev/null | head -1)
        stem=$(basename "${narration_name%.md}")
        echo "file '$OUT_DIR/${stem}.mp4'" >> "$concat_file"
    done
    ffmpeg -y -f concat -safe 0 -i "$concat_file" -c copy \
        "$OUT_DIR/full-demo.mp4" 2>/dev/null
    rm -f "$concat_file"
    echo "  ✓ $OUT_DIR/full-demo.mp4"
fi

echo ""
echo "=== Done ==="

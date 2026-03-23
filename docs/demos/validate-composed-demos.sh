#!/usr/bin/env bash
# Sanity-check composed segment MP4s: both audio and video streams present,
# durations roughly aligned (catches forgotten rebuild-after-audio / bad mux).
#
# Usage:  cd docs/demos && ./validate-composed-demos.sh
# Exit 0 = no issues; exit 1 = problems found (CI-friendly).
#
# Env: MAX_DRIFT (default 2.75 seconds) — slack for freeze-pad / frame rounding.

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REC="$DEMOS_DIR/recordings"
MAX_DRIFT="${MAX_DRIFT:-2.75}"

fail=0

probe_dur() {
    local f=$1 stream=$2
    ffprobe -v error -select_streams "$stream" -show_entries stream=duration \
        -of default=noprint_wrappers=1:nokey=1 "$f" 2>/dev/null | head -1 | tr -d '\r'
}

echo "=== Validating composed demos under $REC (max A/V drift ${MAX_DRIFT}s) ==="
shopt -s nullglob
for mp4 in "$REC"/*.mp4; do
    base=$(basename "$mp4")
    [[ "$base" == full-demo*.mp4 ]] && continue

    vd=$(probe_dur "$mp4" v:0)
    ad=$(probe_dur "$mp4" a:0)
    if [[ -z "$vd" || -z "$ad" || "$vd" == "N/A" || "$ad" == "N/A" ]]; then
        echo "FAIL $base: missing video or audio stream (vd=$vd ad=$ad)"
        fail=1
        continue
    fi
    if ! awk -v v="$vd" -v a="$ad" -v m="$MAX_DRIFT" 'BEGIN {
        d = v - a; if (d < 0) d = -d
        exit(d > m ? 1 : 0)
    }'; then
        drift=$(awk -v v="$vd" -v a="$ad" 'BEGIN { d=v-a; if (d<0) d=-d; printf "%.3f", d }')
        echo "FAIL $base: A/V drift ${drift}s (video=${vd}s audio=${ad}s)"
        fail=1
    fi
done

if [[ "$fail" -ne 0 ]]; then
    echo ""
    echo "Fix: regenerate from current audio — ./rebuild-after-audio.sh"
    exit 1
fi
echo "OK — all checked segments have audio+video and drift ≤ ${MAX_DRIFT}s"
exit 0

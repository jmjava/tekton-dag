#!/usr/bin/env bash
# Regenerate TTS + composed MP4s for M12.2 segments (12–14) and rebuild full-demo-with-m12-2.
# One command — no manual steps. Requires: .venv, OPENAI_API_KEY in repo-root .env, ffmpeg, Manim outputs for 12–14 (run generate-all.sh or manim first).
#
# Usage:  cd docs/demos && ./regenerate-m12-2.sh

set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DEMOS_DIR/.venv"

if [[ ! -d "$VENV" ]]; then
    echo "ERROR: $VENV missing — create venv and pip install -r requirements.txt" >&2
    exit 1
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ENV_FILE="$DEMOS_DIR/../../.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "ERROR: OPENAI_API_KEY not set (add to repo-root .env)" >&2
    exit 1
fi

echo "==> TTS narration (12, 13, 14)…"
for seg in 12 13 14; do
    python "$DEMOS_DIR/generate-narration.py" --segment "$seg"
done

echo "==> Compose segments 12–14…"
bash "$DEMOS_DIR/compose.sh" 12 13 14

list=$(mktemp)
trap 'rm -f "$list"' EXIT
for stem in \
    01-architecture \
    02-quickstart \
    03-bootstrap-dataflow \
    04-pr-pipeline \
    05-intercept-routing \
    06-local-debug \
    07-orchestrator \
    08-multi-team-helm \
    09-results-db \
    10-newman-tests \
    11-test-trace-graph \
    12-regression-suite \
    13-management-gui-architecture \
    14-gui-tekton-extension; do
    f="$DEMOS_DIR/recordings/${stem}.mp4"
    if [[ ! -f "$f" ]]; then
        echo "ERROR: missing $f — run ./compose.sh or ./generate-all.sh for core segments first" >&2
        exit 1
    fi
    echo "file '$f'" >>"$list"
done

echo "==> Concat full-demo-with-m12-2.mp4…"
ffmpeg -y -f concat -safe 0 -i "$list" -c copy \
    "$DEMOS_DIR/recordings/full-demo-with-m12-2.mp4"
echo "Done: recordings/full-demo-with-m12-2.mp4"

#!/usr/bin/env python3
"""
Extract paragraph-level timestamps from narration audio using OpenAI Whisper API.
Outputs a JSON timing map that Manim scenes use for precise sync.

Usage:
    source .venv/bin/activate
    python extract-timestamps.py            # all Manim segments
    python extract-timestamps.py --segment 01  # single segment
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEMOS_DIR = Path(__file__).resolve().parent
AUDIO_DIR = DEMOS_DIR / "audio"
NARRATION_DIR = DEMOS_DIR / "narration"
TIMING_FILE = DEMOS_DIR / "animations" / "timing.json"

MANIM_SEGMENTS = {
    "StackDAGScene": "01-architecture",
    "HeaderPropagationScene": "03-bootstrap-dataflow",
    "InterceptRoutingScene": "05-intercept-routing",
    "LocalDebugScene": "06-local-debug",
    "MultiTeamScene": "08-multi-team-helm",
    "BlastRadiusScene": "11-test-trace-graph",
}


def load_env():
    env_file = DEMOS_DIR.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def transcribe_with_timestamps(audio_path):
    """Use OpenAI Whisper API to get word-level timestamps."""
    from openai import OpenAI
    client = OpenAI()

    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    return result


def find_paragraph_boundaries(narration_text, segments):
    """Match transcript segments to narration paragraphs to find timing."""
    paragraphs = [p.strip() for p in narration_text.split("\n\n") if p.strip()]

    # Build word sequence for each paragraph (first 6 words as anchor)
    para_anchors = []
    for p in paragraphs:
        words = re.findall(r'\w+', p.lower())[:8]
        para_anchors.append(words)

    # Walk through transcript segments and match to paragraphs
    para_times = []
    para_idx = 0

    for seg in segments:
        if para_idx >= len(para_anchors):
            break
        seg_words = re.findall(r'\w+', seg.text.lower())
        anchor = para_anchors[para_idx]

        # Check if this segment starts a new paragraph
        if len(anchor) >= 3 and anchor[0] in seg_words[:5]:
            # Verify more words match
            match_count = sum(1 for w in anchor[:5] if w in seg_words[:10])
            if match_count >= 3:
                para_times.append({
                    "paragraph": para_idx,
                    "start": seg.start,
                    "first_words": " ".join(anchor[:5]),
                })
                para_idx += 1

    # Fill any remaining paragraphs with estimated times
    if para_times and para_idx < len(paragraphs):
        last_time = para_times[-1]["start"]
        total_dur = segments[-1].end if segments else 120
        remaining = len(paragraphs) - para_idx
        gap = (total_dur - last_time) / max(remaining, 1)
        for i in range(para_idx, len(paragraphs)):
            words = re.findall(r'\w+', paragraphs[i].lower())[:5]
            para_times.append({
                "paragraph": i,
                "start": last_time + gap * (i - para_idx + 1),
                "first_words": " ".join(words[:5]),
                "estimated": True,
            })

    return para_times, paragraphs


def process_segment(scene_name, seg_key):
    audio_file = AUDIO_DIR / f"{seg_key}.mp3"
    narration_file = NARRATION_DIR / f"{seg_key}.md"

    if not audio_file.exists():
        print(f"  SKIP: {audio_file} not found")
        return None

    print(f"  Transcribing {seg_key}...")
    result = transcribe_with_timestamps(audio_file)

    narration = narration_file.read_text().strip()
    para_times, paragraphs = find_paragraph_boundaries(narration, result.segments)

    total_dur = result.duration

    entry = {
        "scene": scene_name,
        "segment": seg_key,
        "total_duration": total_dur,
        "paragraph_count": len(paragraphs),
        "paragraphs": [],
    }

    for i, p in enumerate(paragraphs):
        t = next((pt for pt in para_times if pt["paragraph"] == i), None)
        start = t["start"] if t else 0
        # End = start of next paragraph, or total duration
        next_t = next((pt for pt in para_times if pt["paragraph"] == i + 1), None)
        end = next_t["start"] if next_t else total_dur

        entry["paragraphs"].append({
            "index": i,
            "start": round(start, 1),
            "end": round(end, 1),
            "duration": round(end - start, 1),
            "preview": p[:80] + "..." if len(p) > 80 else p,
        })

    return entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment", help="Process only this segment prefix (e.g. 01)")
    args = parser.parse_args()

    load_env()
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print("=== Extracting paragraph timestamps from audio ===\n")

    timing = {}
    for scene, seg_key in MANIM_SEGMENTS.items():
        if args.segment and not seg_key.startswith(args.segment):
            continue
        entry = process_segment(scene, seg_key)
        if entry:
            timing[scene] = entry
            print(f"  {scene}: {entry['total_duration']:.1f}s, "
                  f"{len(entry['paragraphs'])} paragraphs")
            for p in entry["paragraphs"]:
                print(f"    P{p['index']+1} [{p['start']:6.1f}s → {p['end']:6.1f}s] "
                      f"({p['duration']:5.1f}s) {p['preview'][:60]}")
            print()

    TIMING_FILE.parent.mkdir(parents=True, exist_ok=True)
    TIMING_FILE.write_text(json.dumps(timing, indent=2))
    print(f"\n=== Saved to {TIMING_FILE} ===")


if __name__ == "__main__":
    main()

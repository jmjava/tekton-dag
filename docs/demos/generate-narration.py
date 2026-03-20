#!/usr/bin/env python3
"""
Generate MP3 narration for each segment using OpenAI gpt-4o-mini-tts.

Usage:
    source .venv/bin/activate
    python generate-narration.py                 # all segments
    python generate-narration.py --segment 01    # single segment
    python generate-narration.py --dry-run       # show what would be generated

Requires OPENAI_API_KEY in environment or ../.env file.
"""

import argparse
import os
import sys
from pathlib import Path

DEMOS_DIR = Path(__file__).resolve().parent
NARRATION_DIR = DEMOS_DIR / "narration"
AUDIO_DIR = DEMOS_DIR / "audio"

MODEL = "gpt-4o-mini-tts"
VOICE = "coral"
INSTRUCTIONS = (
    "You are narrating a technical demo video about a CI/CD pipeline system "
    "called tekton-dag. Speak in a calm, professional tone like a senior "
    "engineer giving a conference talk. Moderate pace. Pause briefly between "
    "sentences. Pronounce technical terms clearly: Tekton, Kubernetes, "
    "mirrord, Neo4j, Newman, Kaniko, ArgoCD, Helm, kubectl, PipelineRun, "
    "Vue, Flask, Spring Boot, Gradle, Composer."
)


def load_env():
    env_file = DEMOS_DIR.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def get_narration_files(segment_filter=None):
    files = sorted(NARRATION_DIR.glob("*.md"))
    if segment_filter:
        files = [f for f in files if f.name.startswith(segment_filter)]
    return files


def generate_audio(narration_file, output_path, dry_run=False):
    text = narration_file.read_text().strip()
    if not text:
        print(f"  SKIP {narration_file.name} (empty)")
        return False

    print(f"  {narration_file.name} → {output_path.name} ({len(text)} chars)")
    if dry_run:
        return True

    from openai import OpenAI

    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model=MODEL,
        voice=VOICE,
        input=text,
        instructions=INSTRUCTIONS,
    ) as response:
        response.stream_to_file(str(output_path))
    size_kb = output_path.stat().st_size / 1024
    print(f"    ✓ {size_kb:.0f} KB")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate TTS narration audio")
    parser.add_argument("--segment", help="Generate only this segment prefix (e.g. 01)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without calling API")
    args = parser.parse_args()

    load_env()

    if not args.dry_run and not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set. Add to .env or export it.", file=sys.stderr)
        sys.exit(1)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    files = get_narration_files(args.segment)
    if not files:
        print("No narration files found.")
        sys.exit(1)

    print(f"=== Generating narration audio ({len(files)} segments) ===")
    print(f"  Model: {MODEL}  Voice: {VOICE}")
    if args.dry_run:
        print("  (dry run — no API calls)")
    print()

    generated = 0
    for f in files:
        stem = f.stem
        out = AUDIO_DIR / f"{stem}.mp3"
        if generate_audio(f, out, dry_run=args.dry_run):
            generated += 1

    print(f"\n=== Done: {generated} audio files {'planned' if args.dry_run else 'generated'} ===")


if __name__ == "__main__":
    main()

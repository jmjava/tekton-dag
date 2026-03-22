#!/usr/bin/env python3
"""
Generate MP3 narration per segment (OpenAI gpt-4o-mini-tts).

Usage:
  source .venv/bin/activate
  python generate-narration.py
  python generate-narration.py --segment 01
  python generate-narration.py --dry-run

Requires OPENAI_API_KEY (environment or .env — see load_env).

Portable copy (tekton-dag documentation-generator). Lives beside narration/ and audio/.

Markdown may include titles and editor notes; only speakable body is sent to TTS (see
markdown_to_tts_plain).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

DEMOS_DIR = Path(__file__).resolve().parent
NARRATION_DIR = DEMOS_DIR / "narration"
AUDIO_DIR = DEMOS_DIR / "audio"

MODEL = "gpt-4o-mini-tts"
VOICE = "coral"

# Customize for your product / demo tone.
INSTRUCTIONS = (
    "You are narrating a technical demo video. Speak in a calm, professional tone "
    "like a senior engineer. Moderate pace. Pause briefly between sentences. "
    "Pronounce acronyms and product names clearly."
)


def load_env():
    """Pick up OPENAI_API_KEY from common locations without overriding existing env."""
    candidates = [
        DEMOS_DIR / ".env",
        DEMOS_DIR.parent / ".env",
        DEMOS_DIR.parent.parent / ".env",
    ]
    for env_file in candidates:
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def get_narration_files(segment_filter: str | None = None):
    files = sorted(NARRATION_DIR.glob("*.md"))
    if segment_filter:
        files = [f for f in files if f.name.startswith(segment_filter)]
    return files


def _extract_script_section(markdown: str) -> str:
    text = markdown.strip()
    match = re.search(r"^##\s+Script[^\n]*\n", text, flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        return text
    rest = text[match.end() :]
    next_heading = re.search(r"^##\s+\S", rest, flags=re.MULTILINE)
    if next_heading:
        rest = rest[: next_heading.start()]
    return rest.strip()


def _inline_markdown_to_plain(line: str) -> str:
    line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
    line = re.sub(r"`([^`]+)`", r"\1", line)
    line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
    line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", line)
    return line.strip()


def markdown_to_tts_plain(markdown: str) -> str:
    """Strip markdown and optional '## Script' wrapper so TTS only speaks the script."""
    body = _extract_script_section(markdown)
    out_lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^#{1,6}\s", line):
            continue
        if re.search(r"(?i)target duration", line) and "**" in line:
            continue
        if re.search(r"(?i)\*\*visual\*\*\s*:", line) or re.search(
            r"(?i)^\*\*visual\*\*", line
        ):
            continue
        if line.startswith("*(") or line.startswith("(*"):
            continue
        if re.match(r"^\*\([^)]+\)\*$", line):
            continue
        if line in ("---", "***", "- - -"):
            continue
        line = re.sub(r"^\d+\.\s+", "", line)
        line = re.sub(r"^[-*]\s+", "", line)
        line = _inline_markdown_to_plain(line)
        if not line:
            continue
        out_lines.append(line)
    text = "\n\n".join(out_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_audio(narration_file: Path, output_path: Path, dry_run: bool = False) -> bool:
    raw = narration_file.read_text().strip()
    if not raw:
        print(f"  SKIP {narration_file.name} (empty)")
        return False

    text = markdown_to_tts_plain(raw)
    if not text:
        print(f"  SKIP {narration_file.name} (no speakable text after markdown strip)")
        return False

    print(
        f"  {narration_file.name} → {output_path.name} "
        f"({len(text)} chars TTS, {len(raw)} raw)"
    )
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TTS narration audio")
    parser.add_argument("--segment", help="Only files starting with this prefix (e.g. 01)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env()

    if not args.dry_run and not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    files = get_narration_files(args.segment)
    if not files:
        print("No narration files found.")
        sys.exit(1)

    print(f"=== Generating narration ({len(files)} files) ===")
    print(f"  Model: {MODEL}  Voice: {VOICE}")
    if args.dry_run:
        print("  (dry run)")
    print()

    generated = 0
    for f in files:
        out = AUDIO_DIR / f"{f.stem}.mp3"
        if generate_audio(f, out, dry_run=args.dry_run):
            generated += 1

    print(f"\n=== Done: {generated} audio files ===")


if __name__ == "__main__":
    main()

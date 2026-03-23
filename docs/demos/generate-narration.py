#!/usr/bin/env python3
"""
Generate MP3 narration for each segment using OpenAI gpt-4o-mini-tts.

Usage:
    cd docs/demos && source .venv/bin/activate
    python generate-narration.py                 # all segments
    python generate-narration.py --segment 01    # single segment
    python generate-narration.py --dry-run       # show what would be generated

Requires OPENAI_API_KEY. The script auto-loads the repository root .env (two levels
above docs/demos). If the key is not picked up, export it or run:
    set -a && source ../../.env && set +a

Narration wording aligns with docs/ENVIRONMENTS-AND-CLUSTERS.md (baseline / validation
cluster vs customer-facing production). After editing narration/*.md, re-run this script
so audio/*.mp3 stays in sync, then re-compose affected segments.

Markdown source files may include titles and editor notes (e.g. **Target duration**,
## Script). Only the speakable body is sent to TTS — never headings like "Narration —
Segment 12" or stage directions meant for humans.
"""

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
INSTRUCTIONS = (
    "You are narrating a technical demo video about a CI/CD pipeline system "
    "called tekton-dag, pronounced tekton dag. Speak in a calm, professional tone "
    "like a senior engineer giving a conference talk. Moderate pace. Pause briefly "
    "between sentences. Read slash in REST paths as the word slash. Say pull request "
    "in full, not P-R. Pronounce technical terms clearly: Tekton, Kubernetes, "
    "mirrord, Neo4j, Newman, Kaniko, ArgoCD, Helm, kubectl, PipelineRun, "
    "Vue, Flask, Spring Boot, Gradle, Composer, Postgres, Playwright, Artillery."
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
    files = sorted(
        f for f in NARRATION_DIR.glob("*.md") if f.name.lower() != "readme.md"
    )
    if segment_filter:
        files = [f for f in files if f.name.startswith(segment_filter)]
    return files


def _extract_script_section(markdown: str) -> str:
    """If the file has a '## Script' heading, return only that section; else full text."""
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
    """
    Turn narration markdown into plain text safe for TTS (no titles, meta, or md syntax).
    """
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


def generate_audio(narration_file, output_path, dry_run=False):
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
    if not args.dry_run and generated:
        print(
            "\nNext — rebuild Manim, VHS, composed MP4s, and full-demo-with-m12-2:\n"
            "  cd docs/demos && ./rebuild-after-audio.sh\n"
            "  (same as: ./generate-all.sh --skip-tts)\n",
        )


if __name__ == "__main__":
    main()

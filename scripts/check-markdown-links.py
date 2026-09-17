#!/usr/bin/env python3
"""Fail if relative Markdown links point at missing repo files.

Skips fenced code blocks (so example paths are not treated as links),
http(s)/mailto targets, and historical trees that are not maintained.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
}

# Not rewritten as product docs; broken historical links should not fail CI.
SKIP_PREFIXES = (
    "session-notes/",
    "docs/archive/",
    "documentation-generator/",
)

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")
LINK_RE = re.compile(r"(?<!`)\[([^\]]*)\]\(([^)]+)\)")
PLACEHOLDER_TARGETS = {"url", "path", "...", "link"}


def _iter_markdown() -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for name in filenames:
            if name.endswith(".md"):
                files.append(Path(dirpath) / name)
    return sorted(files)


def _strip_fences(text: str) -> str:
    """Replace fenced code blocks with blank lines so line numbers stay aligned."""
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        match = FENCE_RE.match(line.rstrip("\n"))
        if match:
            marker = match.group(2)[0]
            n = len(match.group(2))
            token = marker * n
            if fence is None:
                fence = token
                out.append("\n" if line.endswith("\n") else "")
                continue
            if line.lstrip().startswith(fence):
                fence = None
                out.append("\n" if line.endswith("\n") else "")
                continue
        if fence is not None:
            out.append("\n" if line.endswith("\n") else "")
        else:
            out.append(line)
    return "".join(out)


def _relative_target(url: str) -> str | None:
    raw = url.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    if not raw:
        return None
    # Optional title: [text](path "title")
    if raw.startswith('"') or raw.startswith("'"):
        return None
    if " " in raw and (raw.endswith('"') or raw.endswith("'")):
        raw = raw.rsplit(" ", 1)[0]
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data"}:
        return None
    if raw.startswith("//"):
        return None
    path_part = raw.split("#", 1)[0]
    path_part = unquote(path_part).strip()
    if not path_part:
        return None  # same-file anchor
    if path_part.lower() in PLACEHOLDER_TARGETS:
        return None
    return path_part


def main() -> int:
    broken: list[str] = []
    checked = 0
    for md in _iter_markdown():
        rel = md.relative_to(ROOT).as_posix()
        if rel.startswith(SKIP_PREFIXES):
            continue
        text = _strip_fences(md.read_text(encoding="utf-8", errors="replace"))
        for match in LINK_RE.finditer(text):
            target = _relative_target(match.group(2))
            if target is None:
                continue
            checked += 1
            dest = (md.parent / target).resolve()
            try:
                dest.relative_to(ROOT.resolve())
            except ValueError:
                broken.append(f"{rel}: {target} (outside repo)")
                continue
            if not dest.exists():
                broken.append(f"{rel}: {target}")

    if broken:
        print(f"Broken relative Markdown links ({len(broken)}):", file=sys.stderr)
        for item in broken:
            print(f"  {item}", file=sys.stderr)
        return 1
    print(f"Markdown link check passed ({checked} relative links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

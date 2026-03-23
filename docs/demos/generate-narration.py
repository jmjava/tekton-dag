#!/usr/bin/env python3
"""
Generate MP3 narration for each segment using OpenAI gpt-4o-mini-tts.

This is a thin wrapper — delegates to `docgen tts`.

Usage:
    cd docs/demos
    docgen tts                        # all segments
    docgen tts --segment 01           # single segment
    docgen tts --dry-run              # show what would be generated

Legacy (still works):
    python generate-narration.py                 # all segments
    python generate-narration.py --segment 01    # single segment
    python generate-narration.py --dry-run       # show plan
"""

import subprocess
import sys
from pathlib import Path

DEMOS_DIR = Path(__file__).resolve().parent
CONFIG = DEMOS_DIR / "docgen.yaml"


def main() -> None:
    cmd = ["docgen", "--config", str(CONFIG), "tts"]
    for arg in sys.argv[1:]:
        cmd.append(arg)
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(
            "ERROR: docgen not found. Install: pip install -e /path/to/documentation-generator",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

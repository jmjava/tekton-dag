"""Static acceptance checks for the M17.9 demo validation gate."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/demo-validation.yml"


def test_demo_sources_trigger_pre_push_validation():
    workflow = WORKFLOW.read_text()

    for path in (
        "docs/demos/docgen.yaml",
        "docs/demos/narration/**",
        "docs/demos/animations/**",
        "docs/demos/terminal/**",
        "docs/demos/recordings/**",
    ):
        assert path in workflow

    assert "docgen validate --pre-push" in workflow
    assert "lfs: true" in workflow


def test_demo_validation_installs_authoritative_media_checks():
    workflow = WORKFLOW.read_text()

    assert "ffmpeg tesseract-ocr" in workflow
    assert "A/V, narration, streams, and terminal OCR" in workflow
    assert "DOCGEN_GIT_REF: cb9f145efc7db49b2b72e7269fd25e4eba85730b" in workflow
    assert "if-no-files-found: error" in workflow


def test_demo_validation_actions_are_immutable():
    workflow = WORKFLOW.read_text()
    uses = re.findall(r"^\s*uses:\s*(\S+)", workflow, flags=re.MULTILINE)

    assert uses
    for action in uses:
        assert re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", action), action

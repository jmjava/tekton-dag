"""Static acceptance checks for M17.14 compatibility coverage."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_compatibility_workflow_covers_documented_runtimes():
    workflow = (ROOT / ".github/workflows/compatibility.yml").read_text()
    matrix = (ROOT / "docs/support-matrix.yaml").read_text()

    assert "schedule:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" in workflow
    assert 'python: ["3.11", "3.12"]' in workflow
    assert 'node: ["20", "22"]' in workflow
    assert 'java: ["21"]' in workflow
    assert 'php: ["8.3"]' in workflow
    assert "bash scripts/check-support-matrix.sh" in workflow
    assert 'workflow: ".github/workflows/compatibility.yml"' in matrix


def test_support_matrix_document_lists_cluster_pins():
    doc = (ROOT / "docs/SUPPORT-MATRIX.md").read_text()

    assert "3.11" in doc and "3.12" in doc
    assert "20" in doc and "22" in doc
    assert "v0.27.0" in doc
    assert "v1.6.0" in doc
    assert "v0.34.0" in doc
    assert "v0.20.0" in doc

"""Static acceptance checks for the M17.4 strict Results regression."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_results_workflow_is_scheduled_strict_and_retains_diagnostics():
    workflow = (ROOT / ".github/workflows/results-regression.yml").read_text()

    assert "workflow_dispatch:" in workflow
    assert "schedule:" in workflow
    assert "run-regression-agent-full.sh" in workflow
    assert "install-postgres-kind.sh --ephemeral" in workflow
    assert "install-tekton-results.sh" in workflow
    assert "if: failure()" in workflow
    assert "results-api.log" in workflow
    assert "results-watcher.log" in workflow
    assert "postgres.log" in workflow
    assert "if: always()" in workflow
    assert "actions/upload-artifact@" in workflow


def test_results_installers_are_pinned_and_fail_closed():
    results = (ROOT / "scripts/install-tekton-results.sh").read_text()
    postgres = (ROOT / "scripts/install-postgres-kind.sh").read_text()

    assert 'TEKTON_RESULTS_VERSION="${TEKTON_RESULTS_VERSION:-v0.20.0}"' in results
    assert "/previous/${TEKTON_RESULTS_VERSION}/release.yaml" in results
    assert "curl -fsSL" in results
    assert "deployment/tekton-results-api" in results
    assert "deployment/tekton-results-watcher" in results
    assert "ERROR: PostgreSQL did not become ready" in postgres

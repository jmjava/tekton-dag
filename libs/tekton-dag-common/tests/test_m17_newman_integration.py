"""Static acceptance checks for the M17.10 Newman execution gate."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_cluster_ci_requires_newman_checkpoint_with_operator():
    script = (ROOT / "scripts/run-cluster-ci.sh").read_text()

    assert "newman_args=()" in script
    assert 'if [[ "$WITH_OPERATOR" != "true" ]]' in script
    assert "newman_args+=(--skip-integration)" in script
    assert "newman_args=(--skip-integration)" not in script
    assert "export WAIT_STACKRUN_RECONCILE=1" in script


def test_newman_integration_failures_are_authoritative():
    script = (ROOT / "scripts/run-orchestrator-tests.sh").read_text()

    assert "Newman bootstrap StackRun did not reconcile to a PipelineRun" in script
    assert "authoritative execution checkpoint" in script
    assert "fetch-source failed for" in script
    assert "bootstrap PipelineRun $BOOTSTRAP_RUN failed" in script
    assert "timed out waiting for fetch-source" in script
    assert "WARNING: No bootstrap PipelineRun found" not in script
    assert "WARNING: Timed out waiting for fetch-source" not in script


def test_cluster_workflow_gates_newman_contract_changes():
    workflow = (ROOT / ".github/workflows/cluster-regression.yml").read_text()

    assert '"scripts/run-orchestrator-tests.sh"' in workflow
    assert '"tests/postman/orchestrator-tests.json"' in workflow
    assert "npm install -g newman@6.2.1" in workflow

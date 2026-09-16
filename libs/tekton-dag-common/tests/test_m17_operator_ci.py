"""Static acceptance checks for the M17.5 operator CI gate."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHA_PINNED_ACTION = re.compile(r"uses:\s+([\w.-]+/[\w.-]+)@([0-9a-f]{40})\b")


def _assert_sha_pinned(workflow: str, *actions: str) -> None:
    pins = {match.group(1) for match in SHA_PINNED_ACTION.finditer(workflow)}
    missing = [action for action in actions if action not in pins]
    assert not missing, f"SHA-pinned actions missing: {missing}"


def test_operator_workflow_runs_pinned_quality_and_domain_jobs():
    workflow = (ROOT / ".github/workflows/operator.yml").read_text()

    _assert_sha_pinned(
        workflow,
        "actions/checkout",
        "actions/setup-go",
        "actions/upload-artifact",
    )
    assert "make lint" in workflow
    assert "GOTOOLCHAIN: auto" in workflow
    assert "make test-envtest" in workflow
    assert workflow.count('"scripts/install-tekton.sh"') == 2
    assert "Kind StackRun domain E2E" in workflow
    assert "v0.27.0/kind-linux-amd64" in workflow
    assert "sha256sum -c -" in workflow
    assert "--skip-isolation --skip-phase2 --skip-newman" in workflow


def test_operator_domain_integration_covers_m17_lifecycle_contracts():
    test = (ROOT / "operator/test/integration/stackrun_reconcile_test.go").read_text()

    assert 't.Run("creation status and idempotency"' in test
    assert 't.Run("approval blocks then creates"' in test
    assert 't.Run("continuation carries results and pvc"' in test
    assert "TestInvalidStackRejectedByCRDSchema" in test


def test_tekton_install_retries_controller_owned_resource_apply_races():
    installer = (ROOT / "scripts/install-tekton.sh").read_text()

    assert "apply_with_retry()" in installer
    assert 'apply_with_retry -f "$MILESTONE_DIR/pipeline/"' in installer

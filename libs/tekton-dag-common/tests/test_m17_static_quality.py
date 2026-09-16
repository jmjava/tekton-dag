"""Static acceptance checks for the M17.7 quality gates."""

from pathlib import Path

try:
    from .workflow_pins import assert_actions_sha_pinned
except ImportError:
    from workflow_pins import assert_actions_sha_pinned

ROOT = Path(__file__).resolve().parents[3]


def test_static_quality_workflow_covers_required_domains():
    workflow = (ROOT / ".github/workflows/static-quality.yml").read_text()

    assert "python -m ruff check" in workflow
    assert "make lint-config" in workflow
    assert "make lint" in workflow
    assert "make vet" in workflow
    assert "bash scripts/check-shell-files.sh" in workflow
    assert "python scripts/check-structured-files.py" in workflow
    assert "actionlint -shellcheck=" in workflow
    assert "npm run lint" in workflow
    assert "npm run build" in workflow
    assert "bash scripts/check-helm-chart.sh" in workflow
    assert "bash scripts/check-representation-sync.sh" in workflow
    assert "bash scripts/check-support-matrix.sh" in workflow


def test_quality_tool_downloads_and_actions_are_immutable():
    workflow = (ROOT / ".github/workflows/static-quality.yml").read_text()

    assert_actions_sha_pinned(
        workflow,
        "actions/checkout",
        "actions/setup-python",
        "actions/setup-go",
        "actions/setup-node",
    )
    assert "SHELLCHECK_VERSION: v0.11.0" in workflow
    assert "ACTIONLINT_VERSION: 1.7.12" in workflow
    assert workflow.count("sha256sum -c -") == 3


def test_frontends_declare_lint_scripts():
    for frontend in (
        ROOT / "management-gui/frontend",
        ROOT / "reporting-gui/frontend",
    ):
        package = (frontend / "package.json").read_text()
        config = (frontend / "eslint.config.js").read_text()

        assert '"lint": "eslint . --max-warnings 0"' in package
        assert 'pluginVue.configs["flat/essential"]' in config


def test_helm_gate_validates_packaged_default_and_admin_renders():
    gate = (ROOT / "scripts/check-helm-chart.sh").read_text()

    assert 'helm lint --strict "$REPO_ROOT/helm/tekton-dag"' in gate
    assert "helm package" in gate
    assert 'helm lint --strict "$chart"' in gate
    assert gate.count("--include-crds") == 2
    assert "--set rbac.clusterAdmin=true" in gate
    assert "yaml.safe_load_all" in gate

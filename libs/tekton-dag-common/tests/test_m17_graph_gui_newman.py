"""Static acceptance checks for the M17.11 graph and GUI Newman suites."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_graph_gui_workflow_is_scheduled_and_retains_diagnostics():
    workflow = (ROOT / ".github/workflows/graph-gui-newman.yml").read_text()

    assert "pull_request:" in workflow
    assert '".github/workflows/graph-gui-newman.yml"' in workflow
    assert '"scripts/run-gui-newman.sh"' in workflow
    assert '"scripts/install-neo4j-kind.sh"' in workflow
    assert '"tests/postman/graph-tests.json"' in workflow
    assert '"tests/postman/management-gui-tests.json"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "schedule:" in workflow
    assert "run-gui-newman.sh" in workflow
    assert "run-cluster-ci.sh --skip-isolation --with-graph" in workflow
    assert "if: failure()" in workflow
    assert "graph-db.log" in workflow
    assert "if: always()" in workflow
    assert "actions/upload-artifact@" in workflow


def test_gui_newman_script_starts_live_backend():
    script = (ROOT / "scripts/run-gui-newman.sh").read_text()

    assert "management-gui-tests.json" in script
    assert "python3 app.py" in script
    assert "/api/health" in script
    assert "apiMutationToken=$API_MUTATION_TOKEN" in script
    assert "die \"management GUI backend did not become healthy" in script


def test_cluster_ci_can_require_graph_newman():
    script = (ROOT / "scripts/run-cluster-ci.sh").read_text()

    assert "--with-graph)" in script
    assert "install-neo4j-kind.sh" in script
    assert "newman_args+=(--all)" in script

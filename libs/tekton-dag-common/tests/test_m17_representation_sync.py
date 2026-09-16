"""Static acceptance checks for M17.12 representation synchronization."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_static_quality_runs_representation_sync():
    workflow = (ROOT / ".github/workflows/static-quality.yml").read_text()
    gate = (ROOT / "scripts/check-helm-chart.sh").read_text()

    assert "bash scripts/check-representation-sync.sh" in workflow
    assert "bash scripts/check-helm-chart.sh" in workflow
    assert "helm package" in gate
    assert gate.count("--include-crds") == 2


def test_representation_sync_script_covers_required_surfaces():
    script = (ROOT / "scripts/check-representation-sync.py").read_text()

    assert "tektondag.io_stackruns.yaml" in script
    assert "operator" in script and "helm" in script
    assert "stack_yaml_to_cr" in script
    assert "team_yaml_to_cr" in script
    assert "BuildPR" in script
    assert "build_pr_pipelinerun" in script
    assert "stack-pr-test" in script
    assert "stack-merge-release" in script

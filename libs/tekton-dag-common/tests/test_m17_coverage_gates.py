"""Static acceptance checks for the M17.6 coverage gates."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_python_regression_enforces_full_source_coverage_floors():
    regression = (ROOT / "scripts/run-regression.sh").read_text()

    assert '--cov-fail-under=92' in regression
    assert '--cov-fail-under=91' in regression
    assert '--cov-fail-under=83' in regression
    assert '--cov-fail-under=88' in regression
    assert '--cov=.' in regression
    assert '--cov=tekton_dag_common' in regression
    assert '--cov=tekton_dag_baggage' in regression

    for config in (
        ROOT / "orchestrator/.coveragerc",
        ROOT / "management-gui/backend/.coveragerc",
    ):
        coverage = config.read_text()
        assert "source = ." in coverage
        assert "tests/*" in coverage


def test_operator_gate_enforces_independent_package_floors():
    gate = (ROOT / "scripts/check-operator-coverage.sh").read_text()
    workflow = (ROOT / ".github/workflows/operator.yml").read_text()
    language_tests = (ROOT / "scripts/run-lang-unit-tests.sh").read_text()

    assert 'OPERATOR_PIPELINE_COVERAGE_FLOOR:-80' in gate
    assert 'OPERATOR_CONTROLLER_COVERAGE_FLOOR:-32' in gate
    assert "go tool cover -func=" in gate
    assert "check_package ./internal/pipeline" in gate
    assert "check_package ./internal/controller" in gate
    assert "bash ../scripts/check-operator-coverage.sh" in workflow
    assert "bash \"$SCRIPT_DIR/check-operator-coverage.sh\"" in language_tests

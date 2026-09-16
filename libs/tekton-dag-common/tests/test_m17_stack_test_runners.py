"""Static acceptance checks for M17.13 stack test runners."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_task_sources_extracted_runner_script():
    task = (ROOT / "tasks/run-stack-tests.yaml").read_text()
    installer = (ROOT / "scripts/install-tekton.sh").read_text()
    chart = (ROOT / "helm/tekton-dag/templates/configmap-run-stack-tests-runners.yaml").read_text()
    packager = (ROOT / "helm/tekton-dag/package.sh").read_text()
    script = (ROOT / "scripts/run-stack-tests-runners.sh").read_text()

    assert "name: run-stack-tests-runners" in task
    assert "mountPath: /opt/tekton-dag" in task
    assert "ERROR: run-stack-tests runners ConfigMap missing" in task
    assert "PHASE 2: Per-app tests" not in task
    assert "kubectl create configmap run-stack-tests-runners" in installer
    assert "raw/scripts/run-stack-tests-runners.sh" in chart
    assert "raw/scripts/run-stack-tests-runners.sh" in packager
    assert "run_newman" in script
    assert "run_playwright" in script
    assert "run_artillery" in script
    assert "stack-json is not valid JSON" in script


def test_runner_fixture_suite_covers_success_and_failure():
    tests = (ROOT / "libs/tekton-dag-common/tests/test_run_stack_tests_runners.py").read_text()

    assert "test_malformed_stack_json_fails" in tests
    assert '"{not-json"' in tests
    assert "test_runner_success_and_failure_paths" in tests
    assert '"newman"' in tests
    assert '"playwright"' in tests
    assert '"artillery"' in tests
    assert "[postman] PASS" in tests
    assert "[postman] FAIL" in tests
    assert "[playwright] PASS" in tests
    assert "[playwright] FAIL" in tests
    assert "[artillery] PASS" in tests
    assert "[artillery] FAIL" in tests

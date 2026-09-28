"""Static checks on Tekton YAML for M13 reliability / promote surfaces."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def _load(rel: str):
    return yaml.safe_load((ROOT / rel).read_text())


def test_pr_pipeline_compile_and_containerize_have_retries():
    pipe = _load("pipeline/stack-pr-pipeline.yaml")
    tasks = {t["name"]: t for t in pipe["spec"]["tasks"]}
    for name in (
        "build-compile-npm",
        "build-compile-maven",
        "build-compile-gradle",
        "build-compile-pip",
        "build-compile-composer",
        "build-containerize",
    ):
        assert tasks[name].get("retries") == 2, f"{name} should retry infra flakes"
    # Test tasks must not silently retry real failures
    assert tasks["run-tests"].get("retries", 0) == 0


def test_pr_pipeline_exposes_max_retries_param():
    pipe = _load("pipeline/stack-pr-pipeline.yaml")
    params = {p["name"]: p for p in pipe["spec"]["params"]}
    assert "max-retries" in params
    assert params["max-retries"].get("default") == "2"


def test_promote_pipeline_structure():
    pipe = _load("pipeline/stack-promote-pipeline.yaml")
    assert pipe["metadata"]["name"] == "stack-promote"
    params = {p["name"]: p for p in pipe["spec"]["params"]}
    for required in (
        "release-version",
        "target-environment",
        "image-registry",
        "target-registry",
        "changed-app",
        "apps",
        "max-retries",
    ):
        assert required in params
    assert "audit" in params["max-retries"]["description"].lower() or "fixed" in params[
        "max-retries"
    ]["description"].lower()
    ws = {w["name"]: w for w in pipe["spec"]["workspaces"]}
    assert ws["dockerconfig"].get("optional") is True
    tasks = {t["name"]: t for t in pipe["spec"]["tasks"]}
    assert tasks["promote"].get("retries") == 2
    assert tasks["promote"]["taskRef"]["name"] == "promote-images"
    # Resolved apps-csv (not raw params.apps) feeds promote so changed-app-only works
    promote_params = {p["name"]: p["value"] for p in tasks["promote"]["params"]}
    assert "apps-csv" in promote_params["changed-app"]
    resolve = tasks["resolve-stack-inline"]
    result_names = {r["name"] for r in resolve["taskSpec"]["results"]}
    assert "apps-csv" in result_names


def test_promote_images_task_has_results_and_splits_apps():
    task = _load("tasks/promote-images.yaml")
    assert task["metadata"]["name"] == "promote-images"
    result_names = {r["name"] for r in task["spec"]["results"]}
    assert "promoted-images" in result_names
    assert "promote-audit" in result_names
    script = task["spec"]["steps"][0]["script"]
    assert "tr ','" in script
    ws = {w["name"]: w for w in task["spec"].get("workspaces", [])}
    assert "dockerconfig" in ws


def test_deploy_full_stack_has_validate_secrets_param():
    task = _load("tasks/deploy-full-stack.yaml")
    params = {p["name"]: p for p in task["spec"]["params"]}
    assert "validate-secrets" in params
    assert params["validate-secrets"].get("default") == "true"
    script = task["spec"]["steps"][0]["script"]
    assert "envFrom" in script or "secretRef" in script
    assert "missing Secret" in script or "VALIDATE_SECRETS" in script
    assert "ConfigMap" in script
    assert "volname" in script or "ascii_downcase" in script
    assert "BAGGAGE_ENABLED" in script
    assert "BAGGAGE_ROLE" in script
    assert "DOWNSTREAM_URL" in script
    assert "APP_NAME" in script


def test_intercept_tasks_inject_baggage_env():
    for rel in ("tasks/deploy-intercept-mirrord.yaml",):
        script = _load(rel)["spec"]["steps"][0]["script"]
        assert "BAGGAGE_ENABLED" in script, rel
        assert "BAGGAGE_ROLE" in script, rel
        assert "APP_NAME" in script, rel


def test_mirrord_proxy_runs_as_own_service_account_and_fails_closed():
    """2026-09-27: the proxy ran as staging:default (403 on the target
    Deployment) and the deploy step only waited for a Ready flicker."""
    task = _load("tasks/deploy-intercept-mirrord.yaml")
    params = {p["name"]: p for p in task["spec"]["params"]}
    assert params["proxy-service-account"]["default"] == "mirrord-intercept"
    script = task["spec"]["steps"][0]["script"]
    assert "serviceAccountName: ${PROXY_SA}" in script
    assert "restartPolicy: Never" in script
    assert "Failed to create mirrord-agent|Failed to connect to the created mirrord-agent|Forbidden" in script
    assert "kubectl wait --for=condition=Ready \"pod/${PROXY_NAME}\"" not in script
    # Positive marker: the agent pod named in the proxy log must be Running
    # 40 s later. A generic 'ERROR mirrord' must NOT be treated as fatal
    # (mirrord prints a non-fatal machine-ID telemetry ERROR).
    assert "Created agent pod" in script
    assert "-ge 40" in script
    assert "grep -Eq 'ERROR mirrord" not in script
    rbac = (ROOT / "scripts/install-mirrord-intercept-rbac.sh").read_text()
    assert '"pods/portforward"' in rbac, "mirrord OSS connects to its agent via port-forward"


def test_validate_propagation_proves_routing_from_pr_pod_log():
    """/propagation echoes the header on baseline and PR pod alike, so the
    validator must read the PR pod's own access log (fail-closed)."""
    task = _load("tasks/validate-propagation.yaml")
    params = {p["name"]: p for p in task["spec"]["params"]}
    assert "deployed-pods" in params
    script = task["spec"]["steps"][0]["script"]
    assert "Routing proof (fail-closed)" in script
    assert "probehit" in script and "probemiss" in script
    assert "/pods/$2/log" in script
    assert "intercept steals all traffic" in script
    for rel in ("pipeline/stack-pr-pipeline.yaml", "pipeline/stack-pr-continue-pipeline.yaml"):
        pipeline = (ROOT / rel).read_text()
        assert "value: $(tasks.deploy-intercepts-result.results.deployed-pods)" in pipeline, rel
        assert "deploy-intercepts-telepresence" not in pipeline, rel


def test_resolve_stack_installs_jq_and_yq_without_swallowing_errors():
    """Kind cluster CI failed when mikefarah/yq:4 had no jq and apk was `|| true`."""
    task = _load("tasks/resolve-stack.yaml")
    assert task["metadata"]["name"] == "resolve-stack"
    step = task["spec"]["steps"][0]
    assert step["image"] == "alpine:3.21"
    script = step["script"]
    assert "apk add --no-cache jq yq-go" in script
    assert "apk add --no-cache jq >/dev/null 2>&1 || true" not in script
    assert "command -v jq" in script
    assert "command -v yq" in script
    assert "stack file not found" in script


def test_registries_yaml_loads():
    data = _load("stacks/registries.yaml")
    assert "registries" in data
    names = {r["name"] for r in data["registries"]}
    assert "staging" in names
    assert "production" in names

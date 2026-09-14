"""Static acceptance checks for M17 production-hardening defaults."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_pipeline_service_account_is_not_cluster_admin_by_default():
    values = yaml.safe_load((ROOT / "helm/tekton-dag/values.yaml").read_text())
    assert values["rbac"]["create"] is True
    assert values["rbac"]["clusterAdmin"] is False


def test_pipeline_rbac_has_explicit_least_privilege_fallback():
    template = (ROOT / "helm/tekton-dag/templates/rbac.yaml").read_text()
    assert "if .Values.rbac.clusterAdmin" in template
    assert 'name: cluster-admin' in template
    assert 'resources: ["secrets"]' in template
    assert 'verbs: ["get", "list", "watch"]' in template
    assert 'resources: ["pipelineruns", "taskruns"]' in template
    assert "deployments/scale" in template


def _render_chart(*values):
    helm = shutil.which("helm")
    if helm is None:
        pytest.skip("Helm is not installed")
    # RBAC rendering is independent of packaged Stack/Team CRs. A clean
    # checkout intentionally lacks those generated files until package.sh runs.
    command = [
        helm,
        "template",
        "m17",
        str(ROOT / "helm/tekton-dag"),
        "--set",
        "operator.enabled=false",
    ]
    for value in values:
        command.extend(["--set", value])
    rendered = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [document for document in yaml.safe_load_all(rendered) if document]


def test_helm_renders_least_privilege_pipeline_rbac_by_default():
    documents = _render_chart()
    role = next(
        document
        for document in documents
        if document["kind"] == "ClusterRole"
        and document["metadata"]["name"] == "tekton-pr-sa-pipeline-tekton-pipelines"
    )
    binding = next(
        document
        for document in documents
        if document["kind"] == "ClusterRoleBinding"
        and document["metadata"]["name"]
        == "tekton-pr-sa-pipeline-tekton-pipelines"
    )

    assert binding["roleRef"]["name"] == role["metadata"]["name"]
    assert all(rule.get("resources") != ["clusterrolebindings"] for rule in role["rules"])
    tekton_rule = next(
        rule for rule in role["rules"] if rule.get("apiGroups") == ["tekton.dev"]
    )
    assert "create" in tekton_rule["verbs"]
    stackrun_rule = next(
        rule
        for rule in role["rules"]
        if rule.get("apiGroups") == ["tektondag.io"]
        and rule.get("resources") == ["stackruns"]
    )
    assert "create" in stackrun_rule["verbs"]
    assert not any(
        document.get("roleRef", {}).get("name") == "cluster-admin"
        for document in documents
    )


def test_helm_renders_cluster_admin_only_when_explicitly_enabled():
    documents = _render_chart("rbac.clusterAdmin=true")

    assert any(
        document.get("roleRef", {}).get("name") == "cluster-admin"
        for document in documents
    )
    assert not any(
        document["kind"] == "ClusterRole"
        and "-pipeline-" in document["metadata"]["name"]
        for document in documents
    )


def test_cluster_bootstrap_and_regression_enforce_least_privilege_rbac():
    bootstrap = (ROOT / "scripts/bootstrap-namespace.sh").read_text()
    cluster_ci = (ROOT / "scripts/run-cluster-ci.sh").read_text()

    assert 'PIPELINE_RBAC_CLUSTER_ADMIN="${PIPELINE_RBAC_CLUSTER_ADMIN:-false}"' in bootstrap
    assert "--cluster-admin)" in bootstrap
    assert 'kubectl delete clusterrolebinding "tekton-pr-sa-admin-${NAMESPACE}"' in bootstrap
    assert "tekton-pr-sa unexpectedly has cluster-admin-equivalent access" in cluster_ci
    assert "tekton-pr-sa must not mutate Secrets" in cluster_ci


def test_newman_auth_negatives_override_collection_credentials():
    paths = (
        ROOT / "tests/postman/orchestrator-tests.json",
        ROOT / "tests/postman/management-gui-tests.json",
    )

    for path in paths:
        collection = json.loads(path.read_text())
        missing, invalid = collection["item"][0]["item"][:2]
        assert "auth" not in missing
        assert "auth" not in invalid
        assert missing["request"]["auth"] == {"type": "noauth"}
        assert invalid["request"]["auth"] == {"type": "noauth"}
        invalid_headers = {
            header["key"]: header["value"]
            for header in invalid["request"]["header"]
        }
        assert invalid_headers["Authorization"] == "Bearer invalid-token"


def test_local_regression_installs_checksum_verified_helm():
    workflow = (ROOT / ".github/workflows/local-regression.yml").read_text()

    assert "HELM_VERSION: v4.3.0" in workflow
    assert "86584a54def73570558f66f5111cc53dfed56689637ae32c1201205d494f54fb" in workflow
    assert "sha256sum -c -" in workflow


def test_rbac_changes_trigger_strict_cluster_regression():
    workflow = (ROOT / ".github/workflows/cluster-regression.yml").read_text()

    assert "pull_request:" in workflow
    assert '".github/workflows/cluster-regression.yml"' in workflow
    assert '"helm/tekton-dag/**"' in workflow
    assert '"scripts/bootstrap-namespace.sh"' in workflow
    assert '"scripts/run-cluster-ci.sh"' in workflow
    assert "Kind isolation-eval + Phase 2 + Newman" in workflow
    assert 'github.event_name }}" == "pull_request"' in workflow
    assert "extra+=(--skip-isolation)" in workflow


def test_orchestrator_mutation_token_is_secret_backed_and_fail_closed():
    values = yaml.safe_load((ROOT / "helm/tekton-dag/values.yaml").read_text())
    api_auth = values["orchestrationService"]["apiAuth"]
    assert api_auth == {"existingSecret": "", "key": "token"}

    template = (
        ROOT / "helm/tekton-dag/templates/orchestration-deployment.yaml"
    ).read_text()
    assert "API_MUTATION_TOKEN" in template
    assert "secretKeyRef:" in template
    assert ".Values.orchestrationService.apiAuth.existingSecret" in template

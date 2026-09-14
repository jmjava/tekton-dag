"""Static acceptance checks for M17 production-hardening defaults."""

from pathlib import Path

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

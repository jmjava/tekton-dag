"""Tests for pipelinerun_builder_base."""

import string

from tekton_dag_common.pipelinerun_builder_base import (
    STANDARD_LABELS,
    TEKTON_API_VERSION,
    base_pipelinerun,
    default_workspaces,
    random_suffix,
)


def test_random_suffix_length():
    assert len(random_suffix(3)) == 3
    assert len(random_suffix(12)) == 12


def test_random_suffix_chars():
    s = random_suffix(200)
    allowed = set(string.ascii_lowercase + string.digits)
    assert set(s) <= allowed


def test_base_pipelinerun_structure():
    params = [{"name": "git-url", "value": "https://example.git"}]
    ws = default_workspaces()
    run = base_pipelinerun(
        name="pr-1-abcde",
        pipeline_name="stack-pr-test",
        namespace="tekton-pipelines",
        params=params,
        workspaces=ws,
    )
    assert run["apiVersion"] == TEKTON_API_VERSION
    assert run["kind"] == "PipelineRun"
    assert run["metadata"]["name"] == "pr-1-abcde"
    assert run["metadata"]["namespace"] == "tekton-pipelines"
    assert run["metadata"]["labels"]["tekton.dev/pipeline"] == "stack-pr-test"
    assert run["metadata"]["labels"] == {
        "tekton.dev/pipeline": "stack-pr-test",
        **STANDARD_LABELS,
    }
    assert run["spec"]["pipelineRef"]["name"] == "stack-pr-test"
    assert run["spec"]["params"] == params
    assert run["spec"]["workspaces"] == ws
    assert run["spec"]["taskRunTemplate"]["serviceAccountName"] == "tekton-pr-sa"


def test_base_pipelinerun_custom_sa():
    run = base_pipelinerun(
        name="x",
        pipeline_name="stack-bootstrap",
        namespace="ns",
        params=[],
        workspaces=[],
        service_account="custom-sa",
    )
    assert run["spec"]["taskRunTemplate"]["serviceAccountName"] == "custom-sa"


def test_default_workspaces():
    ws = default_workspaces()
    assert len(ws) == 3
    assert {w["name"] for w in ws} == {"shared-workspace", "ssh-key", "build-cache"}
    shared = next(w for w in ws if w["name"] == "shared-workspace")
    assert shared["volumeClaimTemplate"]["spec"]["resources"]["requests"]["storage"] == "2Gi"
    ssh = next(w for w in ws if w["name"] == "ssh-key")
    assert ssh["secret"]["secretName"] == "ssh-key-secret"
    cache = next(w for w in ws if w["name"] == "build-cache")
    assert cache["persistentVolumeClaim"]["claimName"] == "build-cache"


def test_default_workspaces_custom_names():
    ws = default_workspaces(
        ssh_secret="my-git-secret",
        cache_pvc="my-cache-pvc",
        storage_size="10Gi",
    )
    shared = next(w for w in ws if w["name"] == "shared-workspace")
    assert shared["volumeClaimTemplate"]["spec"]["resources"]["requests"]["storage"] == "10Gi"
    ssh = next(w for w in ws if w["name"] == "ssh-key")
    assert ssh["secret"]["secretName"] == "my-git-secret"
    cache = next(w for w in ws if w["name"] == "build-cache")
    assert cache["persistentVolumeClaim"]["claimName"] == "my-cache-pvc"

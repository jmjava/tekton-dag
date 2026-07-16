"""Tests for PipelineRun manifest builders with deterministic names."""

from unittest.mock import patch

import pytest

import pipelinerun_builder as pb


@pytest.fixture
def fixed_suffix():
    with patch.object(pb, "_random_suffix", return_value="ab12x"):
        yield


def test_build_pr_pipelinerun_structure(fixed_suffix):
    run = pb.build_pr_pipelinerun(
        stack_file="stacks/demo.yaml",
        changed_app="fe",
        pr_number=99,
        git_url="https://github.com/o/r.git",
        git_revision="feature/x",
        image_registry="reg:5000",
        cache_repo="reg:5000/cache",
        intercept_backend="mirrord",
        app_revisions='{"fe":"abc"}',
        namespace="pipelines-ns",
    )
    assert run["apiVersion"] == "tekton.dev/v1"
    assert run["kind"] == "PipelineRun"
    assert run["metadata"]["name"] == "stack-pr-99-ab12x"
    assert run["metadata"]["namespace"] == "pipelines-ns"
    assert run["metadata"]["labels"]["tekton.dev/pipeline"] == "stack-pr-test"
    assert run["spec"]["pipelineRef"]["name"] == "stack-pr-test"
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["git-url"] == "https://github.com/o/r.git"
    assert params["git-revision"] == "feature/x"
    assert params["stack-file"] == "stacks/demo.yaml"
    assert params["changed-app"] == "fe"
    assert params["pr-number"] == "99"
    assert params["app-revisions"] == '{"fe":"abc"}'
    assert params["image-registry"] == "reg:5000"
    assert params["cache-repo"] == "reg:5000/cache"
    assert params["intercept-backend"] == "mirrord"
    ws_names = {w["name"] for w in run["spec"]["workspaces"]}
    assert ws_names == {"shared-workspace", "ssh-key", "build-cache"}
    assert run["spec"]["taskRunTemplate"]["serviceAccountName"] == "tekton-pr-sa"


def test_build_pr_default_app_revisions_and_compile_images(fixed_suffix):
    run = pb.build_pr_pipelinerun(
        stack_file="stacks/s.yaml",
        changed_app="a",
        pr_number=1,
        git_url="u",
        git_revision="r",
        image_registry="i",
        compile_images={
            "npm": "img:npm",
            "maven": "img:mvn",
            "gradle": "img:gr",
            "pip": "img:pip",
            "php": "img:php",
            "mirrord": "img:m",
        },
    )
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["app-revisions"] == "{}"
    assert params["compile-image-npm"] == "img:npm"
    assert params["compile-image-maven"] == "img:mvn"
    assert params["compile-image-gradle"] == "img:gr"
    assert params["compile-image-pip"] == "img:pip"
    assert params["compile-image-php"] == "img:php"
    assert params["compile-image-mirrord"] == "img:m"


def test_build_pr_optional_urls(fixed_suffix):
    run = pb.build_pr_pipelinerun(
        stack_file="stacks/s.yaml",
        changed_app="a",
        pr_number=2,
        git_url="u",
        git_revision="r",
        image_registry="i",
        dashboard_url="https://dash/",
        pr_repo_url="git@github.com:o/r.git",
    )
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["dashboard-url"] == "https://dash/"
    assert params["pr-repo-url"] == "git@github.com:o/r.git"


def test_build_bootstrap_pipelinerun(fixed_suffix):
    run = pb.build_bootstrap_pipelinerun(
        git_url="https://g",
        git_revision="main",
        stack_file="stacks/stack-one.yaml",
        image_registry="reg",
        cache_repo="reg/c",
        namespace="ns",
    )
    assert run["metadata"]["name"] == "stack-bootstrap-ab12x"
    assert run["metadata"]["labels"]["tekton.dev/pipeline"] == "stack-bootstrap"
    assert run["spec"]["pipelineRef"]["name"] == "stack-bootstrap"
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["git-url"] == "https://g"
    assert params["git-revision"] == "main"
    assert params["stack-file"] == "stacks/stack-one.yaml"
    assert params["image-registry"] == "reg"
    assert params["cache-repo"] == "reg/c"
    assert params["max-retries"] == "2"
    assert run["spec"]["timeouts"]["pipeline"] == "2h"


def test_build_bootstrap_compile_images_no_mirrord_key(fixed_suffix):
    run = pb.build_bootstrap_pipelinerun(
        git_url="u",
        git_revision="r",
        stack_file="s",
        image_registry="i",
        compile_images={"npm": "n1", "php": "p1"},
    )
    names = [p["name"] for p in run["spec"]["params"]]
    assert "compile-image-npm" in names
    assert "compile-image-php" in names
    assert "compile-image-mirrord" not in names


def test_build_merge_pipelinerun(fixed_suffix):
    run = pb.build_merge_pipelinerun(
        changed_app="api",
        git_url="https://g",
        git_revision="release",
        stack_file="stacks/prod.yaml",
        image_registry="reg.io",
        cache_repo="reg.io/cache",
        namespace="prod-ns",
    )
    assert run["metadata"]["name"] == "stack-merge-ab12x"
    assert run["metadata"]["labels"]["tekton.dev/pipeline"] == "stack-merge-release"
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["changed-app"] == "api"
    assert params["git-revision"] == "release"
    assert params["max-retries"] == "2"


def test_build_pr_custom_reliability(fixed_suffix):
    run = pb.build_pr_pipelinerun(
        stack_file="stacks/s.yaml",
        changed_app="a",
        pr_number=2,
        git_url="u",
        git_revision="r",
        image_registry="i",
        timeout="45m",
        max_retries=0,
    )
    assert run["spec"]["timeouts"]["pipeline"] == "45m"
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["max-retries"] == "0"


def test_build_promote_pipelinerun(fixed_suffix):
    run = pb.build_promote_pipelinerun(
        stack_file="stacks/stack-one.yaml",
        release_version="0.2.0",
        target_environment="staging",
        image_registry="reg:5000",
        target_registry="reg:5001",
        credentials_secret="reg-creds",
        changed_app="demo-fe,demo-api",
        namespace="tekton-pipelines",
        require_approval=True,
        approved_by="alice",
        timeout="30m",
        max_retries=1,
    )
    assert run["metadata"]["name"] == "stack-promote-staging-ab12x"
    assert run["metadata"]["labels"]["tekton.dev/pipeline"] == "stack-promote"
    assert run["metadata"]["labels"]["tekton-dag.io/environment"] == "staging"
    assert run["metadata"]["annotations"]["tekton-dag.io/approved-by"] == "alice"
    assert run["spec"]["pipelineRef"]["name"] == "stack-promote"
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["release-version"] == "0.2.0"
    assert params["target-environment"] == "staging"
    assert params["target-registry"] == "reg:5001"
    assert params["changed-app"] == "demo-fe,demo-api"
    assert params["apps"] == "demo-fe,demo-api"
    assert params["max-retries"] == "1"
    assert run["spec"]["timeouts"]["pipeline"] == "30m"
    ws = {w["name"]: w for w in run["spec"]["workspaces"]}
    assert "dockerconfig" in ws
    assert ws["dockerconfig"]["secret"]["secretName"] == "reg-creds"


def test_build_promote_without_creds_omits_dockerconfig(fixed_suffix):
    run = pb.build_promote_pipelinerun(
        stack_file="stacks/s.yaml",
        release_version="1.0.0",
        target_environment="staging",
        image_registry="reg",
        changed_app="a",
    )
    ws_names = {w["name"] for w in run["spec"]["workspaces"]}
    assert "dockerconfig" not in ws_names

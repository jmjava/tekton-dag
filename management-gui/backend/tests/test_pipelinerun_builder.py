"""Tests for pipelinerun_builder.py."""

import pipelinerun_builder as builder


def test_build_bootstrap():
    run = builder.build_bootstrap(
        git_url="https://github.com/jmjava/tekton-dag.git",
        git_revision="main",
        stack_file="stack-one.yaml",
        image_registry="localhost:5000",
    )
    assert run["kind"] == "PipelineRun"
    assert run["metadata"]["generateName"] == "stack-bootstrap-"
    assert run["spec"]["pipelineRef"]["name"] == "stack-bootstrap"

    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["stack-file"] == "stacks/stack-one.yaml"
    assert params["image-registry"] == "localhost:5000"


def test_build_pr():
    run = builder.build_pr(
        stack_file="stacks/stack-one.yaml",
        changed_app="demo-fe",
        pr_number=42,
        git_url="https://github.com/jmjava/tekton-dag.git",
        git_revision="main",
        image_registry="localhost:5000",
    )
    assert run["kind"] == "PipelineRun"
    assert run["metadata"]["generateName"] == "stack-pr-42-"
    assert run["spec"]["pipelineRef"]["name"] == "stack-pr-test"

    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["changed-app"] == "demo-fe"
    assert params["pr-number"] == "42"
    assert params["intercept-backend"] == "telepresence"


def test_build_merge():
    run = builder.build_merge(
        stack_file="stacks/stack-one.yaml",
        changed_app="demo-fe",
        git_url="https://github.com/jmjava/tekton-dag.git",
        git_revision="main",
        image_registry="localhost:5000",
    )
    assert run["kind"] == "PipelineRun"
    assert run["metadata"]["generateName"] == "stack-merge-"
    assert run["spec"]["pipelineRef"]["name"] == "stack-merge-release"

    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["changed-app"] == "demo-fe"


def test_bootstrap_prepends_stacks_prefix():
    run = builder.build_bootstrap(
        git_url="u", git_revision="r",
        stack_file="stack-one.yaml",
        image_registry="reg",
    )
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["stack-file"] == "stacks/stack-one.yaml"


def test_bootstrap_keeps_existing_prefix():
    run = builder.build_bootstrap(
        git_url="u", git_revision="r",
        stack_file="stacks/stack-one.yaml",
        image_registry="reg",
    )
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["stack-file"] == "stacks/stack-one.yaml"

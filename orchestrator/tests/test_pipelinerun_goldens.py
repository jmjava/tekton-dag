"""Assert Python PipelineRun builders match golden fixtures (shared with Go)."""

from __future__ import annotations

import json
from pathlib import Path

import pipelinerun_builder as orch

FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "libs"
    / "tekton-dag-common"
    / "tests"
    / "fixtures"
    / "pipelineruns"
)


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_pr_golden(monkeypatch):
    monkeypatch.setattr(orch, "_random_suffix", lambda length=5: "fixed")
    got = orch.build_pr_pipelinerun(
        stack_file="stacks/stack-one.yaml",
        changed_app="demo-fe",
        pr_number=42,
        git_url="https://github.com/jmjava/tekton-dag.git",
        git_revision="main",
        image_registry="localhost:5000",
        cache_repo="localhost:5000/kaniko-cache",
        app_revisions='{"demo-fe":"abc123"}',
        intercept_backend="telepresence",
        namespace="tekton-pipelines",
        timeout="2h",
        max_retries=2,
    )
    assert got == _load("pr.json")


def test_bootstrap_golden(monkeypatch):
    monkeypatch.setattr(orch, "_random_suffix", lambda length=5: "fixed")
    got = orch.build_bootstrap_pipelinerun(
        stack_file="stacks/stack-one.yaml",
        git_url="https://github.com/jmjava/tekton-dag.git",
        git_revision="main",
        image_registry="localhost:5000",
        cache_repo="localhost:5000/kaniko-cache",
        namespace="tekton-pipelines",
        timeout="2h",
        max_retries=2,
    )
    assert got == _load("bootstrap.json")


def test_merge_golden(monkeypatch):
    monkeypatch.setattr(orch, "_random_suffix", lambda length=5: "fixed")
    got = orch.build_merge_pipelinerun(
        changed_app="demo-fe",
        stack_file="stacks/stack-one.yaml",
        git_url="https://github.com/jmjava/tekton-dag.git",
        git_revision="main",
        image_registry="localhost:5000",
        cache_repo="localhost:5000/kaniko-cache",
        namespace="tekton-pipelines",
        timeout="2h",
        max_retries=2,
    )
    assert got == _load("merge.json")


def test_promote_golden(monkeypatch):
    monkeypatch.setattr(orch, "_random_suffix", lambda length=5: "fixed")
    got = orch.build_promote_pipelinerun(
        stack_file="stacks/stack-one.yaml",
        release_version="0.1.0",
        target_environment="staging",
        image_registry="localhost:5000",
        target_registry="ghcr.io/example",
        credentials_secret="regcred",
        changed_app="demo-fe",
        namespace="tekton-pipelines",
        timeout="2h",
        max_retries=2,
        require_approval=True,
        approved_by="alice",
    )
    assert got == _load("promote.json")

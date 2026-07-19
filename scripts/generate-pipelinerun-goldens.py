#!/usr/bin/env python3
"""Generate golden PipelineRun JSON fixtures shared by Python and Go builder tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "orchestrator"))
sys.path.insert(0, str(REPO / "libs" / "tekton-dag-common"))

import pipelinerun_builder as builder  # noqa: E402

# Deterministic names for golden comparisons.
builder._random_suffix = lambda length=5: "fixed"  # type: ignore[assignment]

OUT = REPO / "libs" / "tekton-dag-common" / "tests" / "fixtures" / "pipelineruns"
OUT_GO = REPO / "operator" / "internal" / "pipeline" / "testdata" / "golden"
OUT.mkdir(parents=True, exist_ok=True)
OUT_GO.mkdir(parents=True, exist_ok=True)

git_common = dict(
    stack_file="stacks/stack-one.yaml",
    git_url="https://github.com/jmjava/tekton-dag.git",
    git_revision="main",
    image_registry="localhost:5000",
    cache_repo="localhost:5000/kaniko-cache",
    namespace="tekton-pipelines",
    timeout="2h",
    max_retries=2,
)

fixtures = {
    "pr.json": builder.build_pr_pipelinerun(
        changed_app="demo-fe",
        pr_number=42,
        app_revisions='{"demo-fe":"abc123"}',
        intercept_backend="telepresence",
        **git_common,
    ),
    "bootstrap.json": builder.build_bootstrap_pipelinerun(**git_common),
    "merge.json": builder.build_merge_pipelinerun(changed_app="demo-fe", **git_common),
    "promote.json": builder.build_promote_pipelinerun(
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
    ),
}


def write(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path}")


for name, obj in fixtures.items():
    write(OUT / name, obj)
    write(OUT_GO / name, obj)

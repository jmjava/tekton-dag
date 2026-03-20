"""Tests for stack_resolver.py."""

import os
import tempfile

import pytest

from stack_resolver import StackResolver

STACK_ONE_YAML = """\
name: stack-one
description: "Demo 3-tier stack"

propagation:
  header-name: x-dev-session

defaults:
  namespace: staging

apps:
  - name: demo-fe
    repo: jmjava/tekton-dag-vue-fe
    role: frontend
    propagation-role: originator
    build:
      tool: npm
      runtime: vue
    downstream:
      - release-lifecycle-demo

  - name: release-lifecycle-demo
    repo: jmjava/tekton-dag-spring-boot
    role: middleware
    propagation-role: forwarder
    build:
      tool: maven
      runtime: spring-boot
    downstream:
      - demo-api

  - name: demo-api
    repo: jmjava/tekton-dag-spring-boot-gradle
    role: persistence
    propagation-role: terminal
    build:
      tool: maven
      runtime: spring-boot
    downstream: []
"""


@pytest.fixture
def stacks_dir():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "stack-one.yaml"), "w") as f:
            f.write(STACK_ONE_YAML)
        yield d


def test_list_stacks(stacks_dir):
    resolver = StackResolver(stacks_dir)
    stacks = resolver.list_stacks()
    assert len(stacks) == 1
    assert stacks[0]["name"] == "stack-one"
    assert len(stacks[0]["apps"]) == 3


def test_list_stacks_filtered(stacks_dir):
    resolver = StackResolver(stacks_dir)
    stacks = resolver.list_stacks(allowed_stacks=["stacks/stack-one.yaml"])
    assert len(stacks) == 1
    stacks = resolver.list_stacks(allowed_stacks=["stacks/other.yaml"])
    assert len(stacks) == 0


def test_get_dag(stacks_dir):
    resolver = StackResolver(stacks_dir)
    dag = resolver.get_dag("stacks/stack-one.yaml")
    assert dag is not None
    assert len(dag["nodes"]) == 3
    assert len(dag["edges"]) == 2

    names = [n["id"] for n in dag["nodes"]]
    assert "demo-fe" in names
    assert "release-lifecycle-demo" in names
    assert "demo-api" in names

    sources = [e["source"] for e in dag["edges"]]
    targets = [e["target"] for e in dag["edges"]]
    assert "demo-fe" in sources
    assert "release-lifecycle-demo" in targets


def test_get_dag_not_found(stacks_dir):
    resolver = StackResolver(stacks_dir)
    assert resolver.get_dag("stacks/nonexistent.yaml") is None


def test_get_all_repos(stacks_dir):
    resolver = StackResolver(stacks_dir)
    repos = resolver.get_all_repos()
    assert len(repos) == 3
    ids = [r["id"] for r in repos]
    assert "jmjava/tekton-dag-vue-fe" in ids
    assert "jmjava/tekton-dag-spring-boot" in ids


def test_resolve_repo(stacks_dir):
    resolver = StackResolver(stacks_dir)
    result = resolver.resolve_repo("tekton-dag-vue-fe")
    assert result is not None
    assert result["app_name"] == "demo-fe"
    assert result["stack_file"] == "stacks/stack-one.yaml"


def test_resolve_repo_not_found(stacks_dir):
    resolver = StackResolver(stacks_dir)
    assert resolver.resolve_repo("nonexistent") is None

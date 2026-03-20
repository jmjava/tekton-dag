"""Tests for team_registry.py."""

import os
import tempfile

import pytest

from team_registry import TeamRegistry

TEAM_DEFAULT_YAML = """\
name: default
namespace: tekton-pipelines
cluster: kind-tekton-stack
imageRegistry: localhost:5000
cacheRepo: localhost:5000/kaniko-cache
interceptBackend: telepresence
maxConcurrentRuns: 3
maxParallelBuilds: 5
stacks:
  - stacks/stack-one.yaml
"""

TEAM_EAST_YAML = """\
name: east
namespace: tekton-pipelines
cluster: staging-east
imageRegistry: registry.east.example.com
stacks:
  - stacks/stack-one.yaml
  - stacks/stack-two-vendor.yaml
"""


@pytest.fixture
def teams_dir():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "default"))
        with open(os.path.join(d, "default", "team.yaml"), "w") as f:
            f.write(TEAM_DEFAULT_YAML)
        os.makedirs(os.path.join(d, "east"))
        with open(os.path.join(d, "east", "team.yaml"), "w") as f:
            f.write(TEAM_EAST_YAML)
        yield d


def test_list_all_teams(teams_dir):
    registry = TeamRegistry(teams_dir, team_filter="*")
    teams = registry.list_teams()
    assert len(teams) == 2
    names = [t["name"] for t in teams]
    assert "default" in names
    assert "east" in names


def test_single_team_filter(teams_dir):
    registry = TeamRegistry(teams_dir, team_filter="default")
    teams = registry.list_teams()
    assert len(teams) == 1
    assert teams[0]["name"] == "default"
    assert registry.single_team_mode is True


def test_resolve_context(teams_dir):
    registry = TeamRegistry(teams_dir, team_filter="*")
    context, namespace = registry.resolve_context("default")
    assert context == "kind-tekton-stack"
    assert namespace == "tekton-pipelines"


def test_resolve_context_east(teams_dir):
    registry = TeamRegistry(teams_dir, team_filter="*")
    context, namespace = registry.resolve_context("east")
    assert context == "staging-east"
    assert namespace == "tekton-pipelines"


def test_resolve_context_unknown(teams_dir):
    registry = TeamRegistry(teams_dir, team_filter="*")
    context, namespace = registry.resolve_context("nonexistent")
    assert context is None
    assert namespace == "tekton-pipelines"


def test_get_team(teams_dir):
    registry = TeamRegistry(teams_dir, team_filter="*")
    team = registry.get_team("default")
    assert team is not None
    assert team["imageRegistry"] == "localhost:5000"
    assert team["stacks"] == ["stacks/stack-one.yaml"]


def test_get_team_not_found(teams_dir):
    registry = TeamRegistry(teams_dir, team_filter="*")
    assert registry.get_team("nonexistent") is None


def test_missing_teams_dir():
    registry = TeamRegistry("/nonexistent/path", team_filter="*")
    assert registry.list_teams() == []

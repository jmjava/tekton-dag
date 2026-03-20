"""Tests for Flask route blueprints — uses Flask test client with mocked backends."""

import json
from unittest.mock import patch, MagicMock

import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


@pytest.fixture
def client(tmp_path):
    teams_dir = tmp_path / "teams" / "default"
    teams_dir.mkdir(parents=True)
    (teams_dir / "team.yaml").write_text(
        "name: default\nnamespace: tekton-pipelines\ncluster: kind-kind\nstacks:\n  - stacks/stack-one.yaml\n"
    )

    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()
    (stacks_dir / "stack-one.yaml").write_text(
        "name: stack-one\napps:\n  - name: demo-fe\n    repo: https://github.com/jmjava/tekton-dag-vue-fe.git\n"
    )

    os.environ["TEAMS_DIR"] = str(tmp_path / "teams")
    os.environ["STACKS_DIR"] = str(stacks_dir)
    os.environ["TEAM_NAME"] = "*"

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

    os.environ.pop("TEAMS_DIR", None)
    os.environ.pop("STACKS_DIR", None)
    os.environ.pop("TEAM_NAME", None)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_list_teams(client):
    resp = client.get("/api/teams")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, (list, dict))


def test_list_stacks(client):
    resp = client.get("/api/teams/default/stacks")
    assert resp.status_code == 200


def test_list_stacks_unknown_team(client):
    resp = client.get("/api/teams/nosuchteam/stacks")
    assert resp.status_code == 404


def test_get_dag(client):
    resp = client.get("/api/teams/default/stacks/stacks/stack-one.yaml/dag")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "apps" in data or "nodes" in data or "name" in data


@patch("k8s_client.list_pipelineruns")
def test_list_pipelineruns(mock_list, client):
    mock_list.return_value = [
        {
            "metadata": {"name": "run-1", "namespace": "tekton-pipelines", "creationTimestamp": "2026-01-01T00:00:00Z"},
            "spec": {"pipelineRef": {"name": "stack-pr-test"}, "params": []},
            "status": {"conditions": [{"reason": "Succeeded", "message": "ok"}]},
        }
    ]
    resp = client.get("/api/teams/default/pipelineruns")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "run-1"


@patch("k8s_client.list_pipelineruns")
def test_list_pipelineruns_unknown_team(mock_list, client):
    resp = client.get("/api/teams/nosuchteam/pipelineruns")
    assert resp.status_code == 404


@patch("k8s_client.get_pipelinerun")
def test_get_pipelinerun(mock_get, client):
    mock_get.return_value = {
        "metadata": {"name": "run-abc", "namespace": "tekton-pipelines"},
        "spec": {"pipelineRef": {"name": "stack-pr-test"}, "params": []},
        "status": {"conditions": [{"reason": "Running"}]},
    }
    resp = client.get("/api/teams/default/pipelineruns/run-abc")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "run-abc"


@patch("k8s_client.get_pipelinerun")
def test_get_pipelinerun_not_found(mock_get, client):
    mock_get.return_value = None
    resp = client.get("/api/teams/default/pipelineruns/no-such-run")
    assert resp.status_code == 404


@patch("k8s_client.list_taskruns")
def test_list_taskruns(mock_list, client):
    mock_list.return_value = [
        {
            "metadata": {"name": "tr-1", "labels": {"tekton.dev/pipelineRun": "run-abc"}},
            "spec": {"taskRef": {"name": "build"}},
            "status": {"conditions": [{"reason": "Succeeded"}]},
        }
    ]
    resp = client.get("/api/teams/default/taskruns?pipelineRun=run-abc")
    assert resp.status_code == 200
    assert len(resp.get_json()["items"]) == 1


@patch("k8s_client.create_pipelinerun")
def test_trigger_bootstrap(mock_create, client):
    mock_create.return_value = "stack-bootstrap-xyz"
    resp = client.post(
        "/api/teams/default/trigger",
        data=json.dumps({"pipelineType": "bootstrap", "stack": "stacks/stack-one.yaml"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["pipelineRun"] == "stack-bootstrap-xyz"


@patch("k8s_client.create_pipelinerun")
def test_trigger_pr(mock_create, client):
    mock_create.return_value = "stack-pr-42-abc"
    resp = client.post(
        "/api/teams/default/trigger",
        data=json.dumps({
            "pipelineType": "pr", "stack": "stacks/stack-one.yaml",
            "app": "demo-fe", "prNumber": 42,
        }),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert "stack-pr-42" in resp.get_json()["pipelineRun"]


def test_trigger_missing_stack(client):
    resp = client.post(
        "/api/teams/default/trigger",
        data=json.dumps({"pipelineType": "pr", "app": "demo-fe"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "stack" in resp.get_json()["error"]


def test_trigger_invalid_type(client):
    resp = client.post(
        "/api/teams/default/trigger",
        data=json.dumps({"pipelineType": "invalid", "stack": "s"}),
        content_type="application/json",
    )
    assert resp.status_code == 400


@patch("github_client.list_branches")
def test_repo_branches(mock_branches, client):
    mock_branches.return_value = [{"name": "main", "sha": "abc"}]
    resp = client.get("/api/repos/jmjava/tekton-dag/branches")
    assert resp.status_code == 200
    assert len(resp.get_json()["items"]) == 1


@patch("github_client.list_tags")
def test_repo_tags(mock_tags, client):
    mock_tags.return_value = [{"name": "v1.0", "sha": "abc"}]
    resp = client.get("/api/repos/jmjava/tekton-dag/tags")
    assert resp.status_code == 200


@patch("github_client.list_commits")
def test_repo_commits(mock_commits, client):
    mock_commits.return_value = [{"sha": "abc", "message": "init", "date": None, "url": None}]
    resp = client.get("/api/repos/jmjava/tekton-dag/commits")
    assert resp.status_code == 200


@patch("github_client.list_prs")
def test_repo_prs(mock_prs, client):
    mock_prs.return_value = [{"number": 1, "title": "PR", "state": "open", "url": None}]
    resp = client.get("/api/repos/jmjava/tekton-dag/prs")
    assert resp.status_code == 200


@patch("github_client.list_prs_all_repos")
def test_all_prs(mock_all, client):
    mock_all.return_value = ([], ["r1"], [])
    resp = client.get("/api/prs")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data
    assert "reposQueried" in data


def test_list_repos(client):
    resp = client.get("/api/repos")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data

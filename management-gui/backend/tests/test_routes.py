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
        "name: stack-one\n"
        "apps:\n"
        "  - name: demo-fe\n"
        "    repo: https://github.com/jmjava/tekton-dag-vue-fe.git\n"
        "    role: frontend\n"
        "    secrets:\n"
        "      env-from: [demo-fe-db]\n"
        "    config:\n"
        "      env-from: [demo-fe-config]\n"
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


@patch("k8s_client.list_configmap_names")
@patch("k8s_client.list_secret_names")
def test_injection_status(mock_secrets, mock_cms, client):
    mock_secrets.return_value = {"demo-fe-db"}
    mock_cms.return_value = set()
    resp = client.get("/api/teams/default/apps/demo-fe/injection-status")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is False
    assert body["secrets"]["demo-fe-db"] == "present"
    assert body["configmaps"]["demo-fe-config"] == "missing"
    assert body["stack_file"] == "stacks/stack-one.yaml"


def test_injection_status_unknown_app(client):
    resp = client.get("/api/teams/default/apps/nope/injection-status")
    assert resp.status_code == 404


def test_injection_status_unknown_team(client):
    resp = client.get("/api/teams/nosuch/apps/demo-fe/injection-status")
    assert resp.status_code == 404


@patch("k8s_client.list_configmap_names")
@patch("k8s_client.list_secret_names")
def test_injection_status_respects_team_stack_allow_list(
    mock_secrets, mock_cms, tmp_path
):
    """App in a stack not listed for the team must 404."""
    import os
    from app import create_app

    teams_dir = tmp_path / "teams" / "default"
    teams_dir.mkdir(parents=True)
    (teams_dir / "team.yaml").write_text(
        "name: default\nnamespace: tekton-pipelines\ncluster: kind-kind\n"
        "stacks:\n  - stacks/other.yaml\n"
    )
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()
    (stacks_dir / "stack-one.yaml").write_text(
        "name: stack-one\napps:\n  - name: demo-fe\n    repo: o/r\n"
    )
    (stacks_dir / "other.yaml").write_text(
        "name: other\napps:\n  - name: other-app\n    repo: o/o\n"
    )
    os.environ["TEAMS_DIR"] = str(tmp_path / "teams")
    os.environ["STACKS_DIR"] = str(stacks_dir)
    os.environ["TEAM_NAME"] = "*"
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        resp = c.get("/api/teams/default/apps/demo-fe/injection-status")
        assert resp.status_code == 404
    os.environ.pop("TEAMS_DIR", None)
    os.environ.pop("STACKS_DIR", None)
    os.environ.pop("TEAM_NAME", None)


@patch("k8s_client.list_stackruns")
def test_list_stackruns(mock_list, client):
    mock_list.return_value = [
        {
            "metadata": {"name": "sr-1", "namespace": "tekton-pipelines", "creationTimestamp": "2026-01-01T00:00:00Z"},
            "spec": {"mode": "pr", "stackRef": "stack-one", "changedApp": "demo-fe"},
            "status": {"phase": "Succeeded", "pipelineRunName": "pr-1", "conditions": [{"reason": "Succeeded", "message": "ok"}]},
        }
    ]
    resp = client.get("/api/teams/default/stackruns")
    assert resp.status_code == 200
    item = resp.get_json()["items"][0]
    assert item["name"] == "sr-1"
    assert item["kind"] == "StackRun"
    assert item["mode"] == "pr"
    assert item["pipelineRunName"] == "pr-1"


@patch("k8s_client.get_pipelinerun")
@patch("k8s_client.get_stackrun")
def test_get_stackrun(mock_get_sr, mock_get_pr, client):
    mock_get_sr.return_value = {
        "metadata": {"name": "sr-abc", "namespace": "tekton-pipelines"},
        "spec": {"mode": "bootstrap", "stackRef": "stack-one"},
        "status": {"phase": "Running", "pipelineRunName": "pr-abc", "conditions": [{"reason": "Running"}]},
    }
    mock_get_pr.return_value = {
        "metadata": {"name": "pr-abc"},
        "spec": {"pipelineRef": {"name": "stack-bootstrap"}, "params": []},
        "status": {"conditions": [{"reason": "Running"}], "startTime": "2026-01-01T00:00:00Z"},
    }
    resp = client.get("/api/teams/default/stackruns/sr-abc")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["name"] == "sr-abc"
    assert body["pipeline"] == "stack-bootstrap"


@patch("k8s_client.get_stackrun")
def test_get_stackrun_not_found(mock_get, client):
    mock_get.return_value = None
    resp = client.get("/api/teams/default/stackruns/nope")
    assert resp.status_code == 404


@patch("k8s_client.patch_stackrun")
@patch("k8s_client.get_stackrun")
def test_patch_stackrun_approved_by(mock_get, mock_patch, client):
    mock_get.return_value = {
        "metadata": {"name": "sr-p"},
        "spec": {"mode": "promote", "requireApproval": True},
        "status": {"phase": "PendingApproval", "conditions": []},
    }
    mock_patch.return_value = {
        "metadata": {"name": "sr-p", "namespace": "tekton-pipelines"},
        "spec": {"mode": "promote", "requireApproval": True, "approvedBy": "alice"},
        "status": {"phase": "PendingApproval", "conditions": []},
    }
    resp = client.patch(
        "/api/teams/default/stackruns/sr-p",
        data=json.dumps({"approvedBy": "alice"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["approvedBy"] == "alice"
    mock_patch.assert_called_once()


def test_patch_stackrun_requires_approved_by(client):
    resp = client.patch(
        "/api/teams/default/stackruns/sr-p",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400


@patch("k8s_client.create_stackrun")
def test_trigger_promote(mock_create, client):
    mock_create.return_value = "stackrun-promote-xyz"
    resp = client.post(
        "/api/teams/default/trigger",
        data=json.dumps({
            "pipelineType": "promote",
            "stack": "stacks/stack-one.yaml",
            "app": "demo-fe",
            "releaseVersion": "1.2.0",
            "targetEnvironment": "staging",
            "requireApproval": True,
        }),
        content_type="application/json",
    )
    assert resp.status_code == 200
    manifest = mock_create.call_args.args[2]
    assert manifest["spec"]["mode"] == "promote"
    assert manifest["spec"]["requireApproval"] is True
    assert manifest["spec"]["releaseVersion"] == "1.2.0"


def test_trigger_promote_missing_fields(client):
    resp = client.post(
        "/api/teams/default/trigger",
        data=json.dumps({
            "pipelineType": "promote",
            "stack": "stacks/stack-one.yaml",
            "app": "demo-fe",
        }),
        content_type="application/json",
    )
    assert resp.status_code == 400


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


@patch("k8s_client.create_stackrun")
def test_trigger_bootstrap(mock_create, client):
    mock_create.return_value = "stackrun-bootstrap-xyz"
    resp = client.post(
        "/api/teams/default/trigger",
        data=json.dumps({"pipelineType": "bootstrap", "stack": "stacks/stack-one.yaml"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["pipelineRun"] == "stackrun-bootstrap-xyz"
    assert body["stackrun"] == "stackrun-bootstrap-xyz"
    manifest = mock_create.call_args.args[2]
    assert manifest["kind"] == "StackRun"
    assert manifest["spec"]["stackRef"] == "stack-one"


@patch("k8s_client.create_stackrun")
def test_trigger_pr(mock_create, client):
    mock_create.return_value = "stackrun-pr-abc"
    resp = client.post(
        "/api/teams/default/trigger",
        data=json.dumps({
            "pipelineType": "pr", "stack": "stacks/stack-one.yaml",
            "app": "demo-fe", "prNumber": 42,
        }),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["stackrun"] == "stackrun-pr-abc"


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

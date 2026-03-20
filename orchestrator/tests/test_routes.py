"""Flask route tests with mocked k8s_client, pipelinerun builder, and graph_client."""

import json
from unittest.mock import patch

import pytest


def test_healthz(client):
    rv = client.get("/healthz")
    assert rv.status_code == 200
    assert rv.get_json() == {"status": "ok"}


def test_readyz_reports_stack_count(client, flask_app):
    flask_app.config["RESOLVER"].list_stacks.return_value = [{"stack_file": "a"}, {"stack_file": "b"}]
    rv = client.get("/readyz")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["status"] == "ok"
    assert body["stacks_loaded"] == 2


def test_api_stacks(client, flask_app):
    stacks = [{"stack_file": "stacks/x.yaml", "name": "X", "description": "", "apps": []}]
    flask_app.config["RESOLVER"].list_stacks.return_value = stacks
    rv = client.get("/api/stacks")
    assert rv.status_code == 200
    assert rv.get_json() == stacks


def test_api_teams(client, flask_app):
    teams = {"t1": {"repos": ["a"]}}
    flask_app.config["RESOLVER"].list_teams.return_value = teams
    rv = client.get("/api/teams")
    assert rv.status_code == 200
    assert rv.get_json() == teams


@patch("routes.k8s_client.list_pipelineruns")
def test_api_runs_summarizes_pipelineruns(mock_list, client, flask_app):
    mock_list.return_value = [
        {
            "metadata": {
                "name": "pr-1",
                "creationTimestamp": "2024-01-01T00:00:00Z",
                "labels": {"tekton.dev/pipeline": "stack-pr-test"},
            },
            "status": {"conditions": [{"reason": "Succeeded"}]},
        },
        {
            "metadata": {
                "name": "pr-2",
                "creationTimestamp": "",
                "labels": {},
            },
            "status": {},
        },
    ]
    rv = client.get("/api/runs?limit=10")
    assert rv.status_code == 200
    mock_list.assert_called_once_with(namespace=flask_app.config["NAMESPACE"], limit=10)
    data = rv.get_json()
    assert data[0]["name"] == "pr-1"
    assert data[0]["pipeline"] == "stack-pr-test"
    assert data[0]["status"] == "Succeeded"
    assert data[1]["status"] == "Unknown"


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_pr_pipelinerun")
def test_api_run_pr_success(mock_build_pr, mock_create, client):
    mock_build_pr.return_value = {"metadata": {"name": "built"}}
    mock_create.return_value = "run-created"
    rv = client.post(
        "/api/run",
        data=json.dumps(
            {
                "mode": "pr",
                "changed_app": "fe",
                "pr_number": 42,
                "git_revision": "topic",
            }
        ),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json() == {"status": "created", "pipelinerun": "run-created", "mode": "pr"}
    mock_build_pr.assert_called_once()
    mock_create.assert_called_once()


@patch("routes.builder.build_pr_pipelinerun")
def test_api_run_pr_missing_changed_app(mock_build_pr, client):
    rv = client.post(
        "/api/run",
        data=json.dumps({"mode": "pr", "pr_number": 1}),
        content_type="application/json",
    )
    assert rv.status_code == 400
    assert "changed_app" in rv.get_json()["error"]
    mock_build_pr.assert_not_called()


@patch("routes.builder.build_pr_pipelinerun")
def test_api_run_pr_missing_pr_number(mock_build_pr, client):
    rv = client.post(
        "/api/run",
        data=json.dumps({"mode": "pr", "changed_app": "fe"}),
        content_type="application/json",
    )
    assert rv.status_code == 400
    mock_build_pr.assert_not_called()


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_merge_pipelinerun")
def test_api_run_merge_success(mock_build_merge, mock_create, client):
    mock_build_merge.return_value = {}
    mock_create.return_value = "merge-run"
    rv = client.post(
        "/api/run",
        data=json.dumps({"mode": "merge", "changed_app": "api"}),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json()["mode"] == "merge"
    mock_build_merge.assert_called_once()


@patch("routes.builder.build_merge_pipelinerun")
def test_api_run_merge_missing_changed_app(mock_build_merge, client):
    rv = client.post(
        "/api/run",
        data=json.dumps({"mode": "merge"}),
        content_type="application/json",
    )
    assert rv.status_code == 400
    mock_build_merge.assert_not_called()


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_bootstrap_pipelinerun")
def test_api_run_bootstrap_mode(mock_build_boot, mock_create, client):
    mock_build_boot.return_value = {}
    mock_create.return_value = "boot-1"
    rv = client.post(
        "/api/run",
        data=json.dumps({"mode": "bootstrap"}),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json()["mode"] == "bootstrap"
    mock_build_boot.assert_called_once()


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_bootstrap_pipelinerun")
def test_api_bootstrap_route(mock_build_boot, mock_create, client):
    mock_build_boot.return_value = {}
    mock_create.return_value = "boot-2"
    rv = client.post("/api/bootstrap", data=json.dumps({}), content_type="application/json")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["status"] == "created"
    assert body["mode"] == "bootstrap"


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_pr_pipelinerun")
def test_api_run_k8s_failure(mock_build, mock_create, client):
    mock_build.return_value = {}
    mock_create.side_effect = RuntimeError("apiserver down")
    rv = client.post(
        "/api/run",
        data=json.dumps({"mode": "pr", "changed_app": "x", "pr_number": 1}),
        content_type="application/json",
    )
    assert rv.status_code == 500
    assert "apiserver down" in rv.get_json()["error"]


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_pr_pipelinerun")
def test_webhook_ignores_non_pull_request(mock_build_pr, mock_create, client):
    rv = client.post(
        "/webhook/github",
        data=json.dumps({"action": "created"}),
        content_type="application/json",
        headers={"X-GitHub-Event": "issue"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "ignored"
    mock_create.assert_not_called()
    mock_build_pr.assert_not_called()


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_pr_pipelinerun")
def test_webhook_unknown_repo_ignored(mock_build_pr, mock_create, client, flask_app):
    flask_app.config["RESOLVER"].resolve_repo.return_value = None
    payload = _pr_payload("opened", repo_name="unknown-repo", pr_number=7)
    rv = client.post(
        "/webhook/github",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert rv.status_code == 200
    assert "unknown repo" in rv.get_json()["reason"]
    mock_create.assert_not_called()


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_pr_pipelinerun")
def test_webhook_opened_creates_pr(mock_build_pr, mock_create, client, flask_app):
    flask_app.config["RESOLVER"].resolve_repo.return_value = {
        "stack_file": "stacks/s.yaml",
        "app_name": "fe",
        "repo": "org/fe",
    }
    mock_create.return_value = "webhook-pr"
    payload = _pr_payload("opened", repo_name="demo-fe", pr_number=3, head_sha="abc123")
    rv = client.post(
        "/webhook/github",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["pipelinerun"] == "webhook-pr"
    mock_build_pr.assert_called_once()
    call_kw = mock_build_pr.call_args.kwargs
    assert call_kw["changed_app"] == "fe"
    assert call_kw["pr_number"] == 3
    assert '"fe"' in call_kw["app_revisions"] and "abc123" in call_kw["app_revisions"]


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_pr_pipelinerun")
def test_webhook_synchronize_creates_pr(mock_build_pr, mock_create, client, flask_app):
    mock_create.return_value = "sync-run"
    payload = _pr_payload("synchronize", repo_name="demo-fe", pr_number=9, head_sha="sha")
    rv = client.post(
        "/webhook/github",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert rv.status_code == 200
    mock_build_pr.assert_called_once()


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_merge_pipelinerun")
def test_webhook_closed_merged_creates_merge(mock_build_merge, mock_create, client):
    mock_create.return_value = "merge-run"
    payload = _pr_payload(
        "closed",
        repo_name="demo-fe",
        pr_number=2,
        merged=True,
    )
    rv = client.post(
        "/webhook/github",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["mode"] == "merge"
    mock_build_merge.assert_called_once()
    assert mock_build_merge.call_args.kwargs["git_revision"] == "main"


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_merge_pipelinerun")
def test_webhook_closed_not_merged_ignored(mock_build_merge, mock_create, client):
    payload = _pr_payload("closed", repo_name="demo-fe", pr_number=2, merged=False)
    rv = client.post(
        "/webhook/github",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "ignored"
    mock_build_merge.assert_not_called()


@patch("routes.k8s_client.create_pipelinerun")
@patch("routes.builder.build_pr_pipelinerun")
def test_webhook_pr_create_failure_500(mock_build_pr, mock_create, client):
    mock_create.side_effect = OSError("network")
    payload = _pr_payload("opened", repo_name="demo-fe", pr_number=1, head_sha="s")
    rv = client.post(
        "/webhook/github",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert rv.status_code == 500


def test_api_reload(client, flask_app):
    resolver = flask_app.config["RESOLVER"]
    resolver.list_stacks.return_value = [{"stack_file": "a"}]
    rv = client.post("/api/reload")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["status"] == "reloaded"
    assert body["stacks"] == 1
    resolver.reload.assert_called_once()


@patch("routes.graph_client.query_test_plan")
def test_api_test_plan_missing_app(mock_query, client):
    rv = client.get("/api/test-plan")
    assert rv.status_code == 400
    mock_query.assert_not_called()


@patch("routes.graph_client.query_test_plan")
def test_api_test_plan_success(mock_query, client):
    mock_query.return_value = {"tests": [], "message": "ok"}
    rv = client.get("/api/test-plan?app=demo-fe&radius=2")
    assert rv.status_code == 200
    mock_query.assert_called_once_with("demo-fe", radius=2)


@patch("routes.graph_client.query_test_plan")
def test_api_test_plan_graph_error(mock_query, client):
    mock_query.side_effect = ValueError("neo4j unavailable")
    rv = client.get("/api/test-plan?app=x")
    assert rv.status_code == 500
    assert "neo4j unavailable" in rv.get_json()["error"]


@patch("routes.graph_client.ingest_from_file")
def test_api_graph_ingest_fixture_file(mock_ingest, client):
    mock_ingest.return_value = 5
    rv = client.post(
        "/api/graph/ingest",
        data=json.dumps({"fixture_file": "/tmp/t.json"}),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json() == {"status": "ingested", "traces": 5}
    mock_ingest.assert_called_once_with("/tmp/t.json")


@patch("routes.graph_client.ingest_traces")
@patch("routes.graph_client.create_constraints")
@patch("routes.graph_client.clear_graph")
def test_api_graph_ingest_traces(mock_clear, mock_constraints, mock_ingest, client):
    traces = [{"test_id": "t1", "spans": []}]
    rv = client.post(
        "/api/graph/ingest",
        data=json.dumps({"traces": traces}),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json()["traces"] == 1
    mock_clear.assert_called_once()
    mock_constraints.assert_called_once()
    mock_ingest.assert_called_once_with(traces)


def test_api_graph_ingest_neither_key(client):
    rv = client.post(
        "/api/graph/ingest",
        data=json.dumps({"other": 1}),
        content_type="application/json",
    )
    assert rv.status_code == 400


@patch("routes.graph_client.ingest_from_file")
def test_api_graph_ingest_exception(mock_ingest, client):
    mock_ingest.side_effect = IOError("bad file")
    rv = client.post(
        "/api/graph/ingest",
        data=json.dumps({"fixture_file": "x"}),
        content_type="application/json",
    )
    assert rv.status_code == 500


@patch("routes.graph_client.graph_stats")
def test_api_graph_stats_ok(mock_stats, client):
    mock_stats.return_value = {"services": 1, "tests": 2, "touches_edges": 3, "calls_edges": 4}
    rv = client.get("/api/graph/stats")
    assert rv.status_code == 200
    assert rv.get_json()["services"] == 1


@patch("routes.graph_client.graph_stats")
def test_api_graph_stats_error(mock_stats, client):
    mock_stats.side_effect = RuntimeError("down")
    rv = client.get("/api/graph/stats")
    assert rv.status_code == 500


def test_create_app_defaults(monkeypatch, tmp_path):
    monkeypatch.delenv("NAMESPACE", raising=False)
    monkeypatch.setenv("STACKS_DIR", str(tmp_path))
    monkeypatch.setenv("TEAMS_DIR", str(tmp_path))
    from app import create_app

    app = create_app()
    assert app.config["NAMESPACE"] == "tekton-pipelines"
    assert "RESOLVER" in app.config
    assert app.config["RESOLVER"] is not None


def test_create_app_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("NAMESPACE", "prod")
    monkeypatch.setenv("MAX_PARALLEL_BUILDS", "12")
    monkeypatch.setenv("IMAGE_REGISTRY", "my.registry")
    monkeypatch.setenv("STACKS_DIR", str(tmp_path))
    monkeypatch.setenv("TEAMS_DIR", str(tmp_path))
    from app import create_app

    app = create_app()
    assert app.config["NAMESPACE"] == "prod"
    assert app.config["MAX_PARALLEL_BUILDS"] == 12
    assert app.config["IMAGE_REGISTRY"] == "my.registry"


def _pr_payload(action, repo_name, pr_number=1, head_sha="deadbeef", merged=False):
    return {
        "action": action,
        "number": pr_number,
        "pull_request": {
            "merged": merged,
            "head": {"sha": head_sha},
            "base": {
                "repo": {
                    "name": repo_name,
                    "ssh_url": f"git@github.com:org/{repo_name}.git",
                }
            },
        },
    }

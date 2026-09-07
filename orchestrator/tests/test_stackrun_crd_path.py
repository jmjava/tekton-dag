"""STACKRUN_VIA_CRD=true creates StackRun CRs instead of PipelineRuns."""

import json
from unittest.mock import patch


@patch("routes.k8s_client.create_stackrun")
@patch("routes.k8s_client.create_pipelinerun")
def test_api_run_bootstrap_via_crd(mock_pr, mock_sr, client, flask_app):
    flask_app.config["STACKRUN_VIA_CRD"] = True
    mock_sr.return_value = "stackrun-bootstrap-abc12"
    rv = client.post(
        "/api/run",
        data=json.dumps({"mode": "bootstrap"}),
        content_type="application/json",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["stackrun"] == "stackrun-bootstrap-abc12"
    assert body["pipelinerun"] == "stackrun-bootstrap-abc12"
    assert body["mode"] == "bootstrap"
    mock_sr.assert_called_once()
    mock_pr.assert_not_called()
    manifest = mock_sr.call_args.args[0]
    assert manifest["kind"] == "StackRun"
    assert manifest["spec"]["mode"] == "bootstrap"


@patch("routes.k8s_client.create_stackrun")
@patch("routes.builder.build_pr_pipelinerun")
def test_webhook_via_crd(mock_build_pr, mock_sr, client, flask_app):
    flask_app.config["STACKRUN_VIA_CRD"] = True
    mock_build_pr.return_value = {"kind": "PipelineRun"}
    mock_sr.return_value = "stackrun-pr-xyz"
    payload = {
        "action": "opened",
        "number": 3,
        "pull_request": {
            "merged": False,
            "head": {"sha": "abc"},
            "base": {"repo": {"name": "demo-fe", "ssh_url": "git@x:y.git"}},
        },
    }
    rv = client.post(
        "/webhook/github",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["stackrun"] == "stackrun-pr-xyz"
    mock_sr.assert_called_once()

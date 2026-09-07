"""Flask always creates StackRun CRs (M16: STACKRUN_VIA_CRD hatch retired)."""

import json
from unittest.mock import patch


@patch("routes.k8s_client.create_stackrun")
def test_api_run_bootstrap_creates_stackrun(mock_sr, client):
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
    manifest = mock_sr.call_args.args[0]
    assert manifest["kind"] == "StackRun"
    assert manifest["spec"]["mode"] == "bootstrap"
    assert manifest["spec"]["stackRef"] == "stack-one"


@patch("routes.k8s_client.create_stackrun")
def test_webhook_creates_stackrun(mock_sr, client):
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


@patch("routes.k8s_client.create_stackrun")
def test_api_run_promote_without_approved_by_creates_stackrun(mock_sr, client):
    """CRD path matches GUI: require_approval without approved_by is PendingApproval."""
    mock_sr.return_value = "stackrun-promote-wait"
    rv = client.post(
        "/api/run",
        data=json.dumps(
            {
                "mode": "promote",
                "release_version": "0.1.0",
                "target_environment": "production",
                "changed_app": "demo-fe",
                "target_registry": "reg:5001",
                "require_approval": True,
            }
        ),
        content_type="application/json",
    )
    assert rv.status_code == 200, rv.get_json()
    mock_sr.assert_called_once()
    spec = mock_sr.call_args.args[0]["spec"]
    assert spec["requireApproval"] is True
    assert "approvedBy" not in spec


def test_create_app_ignores_stackrun_via_crd_false(monkeypatch, tmp_path):
    monkeypatch.setenv("STACKRUN_VIA_CRD", "false")
    monkeypatch.setenv("STACKS_DIR", str(tmp_path))
    monkeypatch.setenv("TEAMS_DIR", str(tmp_path))
    from app import create_app

    app = create_app()
    assert "STACKRUN_VIA_CRD" not in app.config

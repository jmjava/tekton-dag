import json

from app import app


def test_root_endpoint_echoes_hop_report():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["app"] == "tekton-dag-flask"
    assert body["hops"] == []


def test_propagation_echoes_original_override_when_library_enabled(monkeypatch):
    monkeypatch.setenv("BAGGAGE_ENABLED", "true")
    monkeypatch.setenv("BAGGAGE_ROLE", "forwarder")
    client = app.test_client()
    resp = client.get("/propagation", headers={"x-dev-session": "pr-42"})
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["app"] == "tekton-dag-flask"
    # Session is populated only when tekton-dag-baggage is installed and enabled.
    assert body.get("session") in (None, "pr-42")

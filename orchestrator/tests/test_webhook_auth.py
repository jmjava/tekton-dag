"""Tests for GitHub webhook HMAC verification."""

import webhook_auth


def test_compute_and_verify_signature():
    body = b'{"action":"opened"}'
    secret = "topsecret"
    sig = webhook_auth.compute_signature(secret, body)
    assert sig.startswith("sha256=")
    assert webhook_auth.verify_signature(secret, body, sig) is True


def test_verify_rejects_bad_signature():
    body = b'{"action":"opened"}'
    assert webhook_auth.verify_signature("secret", body, "sha256=deadbeef") is False


def test_verify_rejects_missing_header_when_secret_set():
    assert webhook_auth.verify_signature("secret", b"{}", None) is False
    assert webhook_auth.verify_signature("secret", b"{}", "") is False


def test_verify_allows_when_secret_empty():
    assert webhook_auth.verify_signature("", b"{}", None) is True


def test_resolve_webhook_secret_prefers_configured():
    def fetch(_name, namespace=""):
        raise AssertionError("should not fetch")

    secret, status = webhook_auth.resolve_webhook_secret_status(
        configured_secret="from-env",
        secret_name="github-webhook-secret",
        fetch_secret=fetch,
    )
    assert secret == "from-env"
    assert status == webhook_auth.STATUS_OK


def test_resolve_webhook_secret_from_k8s():
    def fetch(name, namespace=""):
        assert name == "github-webhook-secret"
        return {"secret": "from-k8s"}

    secret, status = webhook_auth.resolve_webhook_secret_status(
        configured_secret="",
        secret_name="github-webhook-secret",
        namespace="ns",
        fetch_secret=fetch,
    )
    assert secret == "from-k8s"
    assert status == webhook_auth.STATUS_OK


def test_resolve_status_unset_when_no_name():
    secret, status = webhook_auth.resolve_webhook_secret_status(
        configured_secret="",
        secret_name="",
    )
    assert secret == ""
    assert status == webhook_auth.STATUS_UNSET


def test_resolve_status_missing_when_secret_absent():
    def fetch(_name, namespace=""):
        return None

    secret, status = webhook_auth.resolve_webhook_secret_status(
        configured_secret="",
        secret_name="github-webhook-secret",
        fetch_secret=fetch,
    )
    assert secret == ""
    assert status == webhook_auth.STATUS_MISSING


def test_resolve_status_missing_when_keys_empty():
    def fetch(_name, namespace=""):
        return {"other": "x"}

    secret, status = webhook_auth.resolve_webhook_secret_status(
        configured_secret="",
        secret_name="github-webhook-secret",
        fetch_secret=fetch,
    )
    assert status == webhook_auth.STATUS_MISSING


def test_resolve_status_unavailable_on_fetch_error():
    def fetch(_name, namespace=""):
        raise RuntimeError("no kubeconfig")

    secret, status = webhook_auth.resolve_webhook_secret_status(
        configured_secret="",
        secret_name="github-webhook-secret",
        fetch_secret=fetch,
    )
    assert secret == ""
    assert status == webhook_auth.STATUS_UNAVAILABLE


def test_legacy_resolve_webhook_secret_still_returns_string():
    assert (
        webhook_auth.resolve_webhook_secret(
            configured_secret="x",
            secret_name="y",
            fetch_secret=lambda *a, **k: None,
        )
        == "x"
    )
